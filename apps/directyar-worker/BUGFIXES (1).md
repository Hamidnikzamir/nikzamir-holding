# رفع باگ‌های `directyar-worker` — پچ‌های آماده‌ی اعمال

هرکدوم مستقل هستن؛ می‌تونی جدا جدا اعمالشون کنی.

---

## ۱. سفارش تکمیل‌شده هیچ‌وقت به ادمین اطلاع داده نمی‌شد

**مشکل:** در مرحله‌ی `payment`، فقط به مشتری شماره‌کارت نشون داده می‌شد؛
هیچ پیامی به ادمین نمی‌رفت و هیچ‌جا ذخیره نمی‌شد.

**محل:** داخل `handleOrderConversation`، بلوک `state.orderStage === "payment"`،
درست بعد از ساخت `invoiceId` و `total`.

```ts
const invoiceId = generateInvoiceId();
const total = cart.reduce((sum, item) => {
  const itemProduct = config.products.find((c) => c.name === item.productName);
  return sum + (itemProduct?.price || 0) * item.quantity;
}, 0);

// ✅ جدید: ذخیره‌ی سفارش در KV تا قابل پیگیری باشه
const order = {
  invoiceId,
  userId,
  chatId,
  items: cart,
  total,
  customerName: state.customerName,
  phone: state.phone,
  address: state.address,
  postalCode: state.postalCode,
  shippingMethod: state.shippingMethod,
  createdAt: new Date().toISOString(),
  status: "awaiting_payment",
};
await env.USERS_DB.put(`order:${userId}:${invoiceId}`, JSON.stringify(order), {
  expirationTtl: 60 * 60 * 24 * 90, // ۹۰ روز
});

// ✅ جدید: اطلاع‌رسانی واقعی به ادمین
if (config.admin_chat_id) {
  await sendTelegramMessage(
    env.TELEGRAM_BOT_TOKEN,
    config.admin_chat_id,
    `🧾 سفارش جدید #${invoiceId}\n👤 ${state.customerName}\n📞 ${state.phone}\n📍 ${state.address}\n💰 ${total.toLocaleString()} تومان\n\n${formatCartSummary(cart, config.products)}`
  );
}

await saveConversationState(env.BOT_KV, userId, chatId, { ...state, invoiceId });
```

---

## ۲. پیام گمراه‌کننده در Handover

**مشکل:** `handleSmartHandover` همیشه می‌گفت «پیامت رو فرستادم»، حتی وقتی
`admin_chat_id` تنظیم نشده بود.

```ts
async function handleSmartHandover(env, config, chatId, userText, userId) {
  const notified = Boolean(config?.admin_chat_id);
  await sendMenuMsg(
    env.TELEGRAM_BOT_TOKEN,
    chatId,
    notified
      ? "پیامت رو به ادمین فرستادم. به زودی جوابت رو می‌گیری 💪"
      : "پیامت ثبت شد. تیم پشتیبانی به‌محض دسترسی بهت پاسخ می‌ده.",
    config
  );
  if (notified) {
    await sendTelegramMessage(
      env.TELEGRAM_BOT_TOKEN,
      config.admin_chat_id,
      `🔔 پشتیبانی!\n👤 ${chatId}\n💬 ${userText}\n⏰ ${new Date().toLocaleString("fa-IR")}`
    );
  }
  return new Response("OK", { status: 200 });
}
```

---

## ۳. وبهوک تلگرام بدون احراز هویت

**مشکل:** هرکسی که آدرس `/webhook` رو بدونه می‌تونه Update جعلی بفرسته.

**راه‌حل:** موقع ثبت وبهوک نزد تلگرام، یک `secret_token` تعریف کن (با
`setWebhook`) و مقدارش رو به `env.TELEGRAM_WEBHOOK_SECRET` بده. سپس:

```ts
if (request.method === "POST" && url.pathname === "/webhook") {
  const secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token");
  if (secret !== env.TELEGRAM_WEBHOOK_SECRET) {
    return new Response("Unauthorized", { status: 401 });
  }
  return await handleTelegramWebhook(request, env);
}
```

---

## ۴. CORS بیش از حد باز

**مشکل:** `Access-Control-Allow-Origin` همیشه origin درخواست‌دهنده یا `*` رو
منعکس می‌کرد — هر سایتی می‌تونست به `/chat` وصل بشه و هزینه‌ی AI رو بالا ببره.

```ts
function corsHeaders(request, env) {
  const origin = request?.headers.get("Origin") || "";
  const allowed = (env.ALLOWED_ORIGINS || "").split(",").map((o) => o.trim());
  const isAllowed = allowed.includes(origin);
  return {
    "Access-Control-Allow-Origin": isAllowed ? origin : "null",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Vary": "Origin",
  };
}
```
`ALLOWED_ORIGINS` رو به‌صورت متغیر محیطی (`wrangler.jsonc` → `vars`) با
لیست دامنه‌های مجاز (مثل `https://mrkeratine.ir`) ست کن.

---

## ۵. `userId` بدون احراز هویت قابل جعل بود

**مشکل:** در `/chat` و `/feedback`، هر کلاینتی می‌تونست `userId` دلخواه
بفرسته و روی داده‌ی مستأجر دیگه بنویسه.

**راه‌حل کوتاه‌مدت:** به‌جای پذیرفتن `userId` خام از بدنه، اون رو از یک
توکن امضاشده (مثلاً JWT کوتاه‌مدت که هنگام بارگذاری ویجت روی سایت صادر
می‌شه) استخراج کن، نه از فیلد آزاد JSON.

---

## ۶. سیستم `capabilities` تعریف شده ولی هیچ‌جا چک نمی‌شد

**مشکل:** پرچم‌هایی مثل `payment`, `ordering`, `cart` ذخیره می‌شدن ولی
هیچ مسیر کدی بهشون نگاه نمی‌کرد.

```ts
// مثال: قبل از ورود به مرحله‌ی پرداخت
if (state.orderStage === "choose_mode" && config.capabilities?.ordering === false) {
  await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, "ثبت سفارش آنلاین برای این فروشگاه فعال نیست؛ لطفاً از طریق سایت اقدام کنید.", config);
  return new Response("OK", { status: 200 });
}
```
این الگو رو برای هر capability، دقیقاً قبل از ورودش به همون مسیر تکرار کن.

---

## ۷. صفحه‌بندی ناقص کاتالوگ WooCommerce

**مشکل:** فقط ۱۰۰ محصول اول گرفته می‌شد.

```ts
async function fetchAllProducts(origin: string): Promise<any[]> {
  const all: any[] = [];
  let page = 1;
  while (page <= 10) { // سقف ایمنی
    const res = await fetch(`${origin}/wp-json/wc/store/v1/products?per_page=100&page=${page}`);
    if (!res.ok) break;
    const batch = await res.json();
    if (!Array.isArray(batch) || !batch.length) break;
    all.push(...batch);
    if (batch.length < 100) break;
    page++;
  }
  return all;
}
```

---

## ۸. نگه نداشتن نقش پیام‌های قبلی در `/chat`

**مشکل:** `previousMessages` بدون در نظر گرفتن نقش (user/assistant) همه
با نقش `"user"` به مدل داده می‌شد.

**راه‌حل:** کلاینت (ویجت سایت) باید آرایه‌ای از `{role, content}` بفرسته،
نه فقط رشته؛ و سرور همون نقش رو عیناً پاس بده (این ساختار در
`smart-assistant.ts` جدید (`ConversationContext.previousMessages`) رعایت شده).
