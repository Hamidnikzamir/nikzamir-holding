// src/index.ts
// دایرکت یار - نسخه نهایی امن: ضد توهم + منطق شرطی فروش

export interface Env {
  // Added WooCommerce integration variables
  WC_SITE_URL?: string;
  WC_CONSUMER_KEY?: string;
  WC_CONSUMER_SECRET?: string;
  AI: any;
  BOT_KV: KVNamespace;
  USERS_DB: KVNamespace;
  TELEGRAM_BOT_TOKEN: string;
  SEED_SECRET?: string;
  TELEGRAM_WEBHOOK_SECRET?: string;
}

export interface UserConfig {
  business_name: string;
  business_type: BusinessType;
  knowledge_status: "pending" | "approved";
  capabilities: BusinessCapabilities;
  admin_id: string;
  admin_chat_id?: number;
  tone: string;
  platform: string;
  products: Product[];
  rules: string;
  payment_info?: PaymentInfo;
}

export type BusinessType = "product" | "service" | "consulting" | "hybrid";

export interface BusinessCapabilities {
  ai_replies: boolean;
  consultation: boolean;
  catalog: boolean;
  cart: boolean;
  ordering: boolean;
  payment: boolean;
  admin_handover: boolean;
}

export interface KnowledgeSnapshot {
  source_url: string;
  source_type: "website" | "woocommerce";
  synced_at: string;
  products_count: number;
  categories: string[];
  brands: string[];
  pages_count: number;
  articles_count: number;
  content_titles: string[];
  content_excerpt: string;
}

export interface Product {
  name: string;
  price: number;
  stock: string;
  details: string;
  category: string;
  brand?: string;
  url?: string;
}

export interface PaymentInfo {
  card_number: string;
  card_holder: string;
  sheba?: string;
}

interface ConversationState {
  productName?: string;
  cart?: CartItem[];
  orderMode?: "telegram" | "website";
  orderStage?: "confirm_product" | "add_more" | "confirm_cart" | "choose_mode" | "name" | "phone" | "address" | "postal_code" | "shipping" | "payment";
  customerName?: string;
  phone?: string;
  address?: string;
  postalCode?: string;
  shippingMethod?: "post" | "tipax" | "courier";
}

interface CartItem {
  productName: string;
  quantity: number;
}

interface SeedPayload {
  userId?: string;
  business_name?: string;
  business_type?: BusinessType;
  knowledge_status?: "pending" | "approved";
  capabilities?: Partial<BusinessCapabilities>;
  source_url?: string;
  source_type?: "website" | "woocommerce";
  admin_id?: string;
  admin_chat_id?: number;
  tone?: string;
  platform?: string;
  payment_info?: PaymentInfo;
  products?: Product[];
  rules?: string;
}

interface WooCommerceProduct {
  name?: string;
  permalink?: string;
  short_description?: string;
  description?: string;
  prices?: { price?: string };
  is_in_stock?: boolean;
  categories?: Array<{ name?: string }>;
  attributes?: Array<{ name?: string; terms?: Array<{ name?: string }> }>;
}

interface WordPressContentItem {
  title?: { rendered?: string };
  content?: { rendered?: string };
  link?: string;
}

const CATALOG_CACHE_KEY = "catalog:mrkeratine:v2";
const CATALOG_URL = "https://mrkeratine.ir/wp-json/wc/store/v1/products?per_page=100";

const DEFAULT_CAPABILITIES: BusinessCapabilities = {
  ai_replies: true,
  consultation: true,
  catalog: true,
  cart: true,
  ordering: true,
  payment: false,
  admin_handover: true,
};

export const DIRECTYAR_PATHS = ["/seed", "/knowledge/refresh", "/knowledge/status", "/webhook"] as const;

export function isDirectYarPath(pathname: string): boolean {
  const path = pathname.replace(/\/+$/, "") || "/";
  return (DIRECTYAR_PATHS as readonly string[]).includes(path);
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const pathname = url.pathname.replace(/\/+$/, "") || "/";
    if (request.method === "POST" && pathname === "/seed") return await handleSeed(request, env);
    if (request.method === "POST" && pathname === "/knowledge/refresh") return await handleKnowledgeRefresh(request, env);
    if (request.method === "GET" && pathname === "/knowledge/status") return await handleKnowledgeStatus(request, env);
    if (request.method === "POST" && pathname === "/webhook") return await handleTelegramWebhook(request, env);
    if (pathname === "/") return new Response("✅ DirectYar Worker (Secure) is running!", { headers: { "content-type": "text/plain" } });
    return jsonResponse({ ok: false, error: { code: "not_found" } }, 404);
  },
};

function isSeedAuthorized(request: Request, env: Env): boolean {
  if (!env.SEED_SECRET) return false;
  return request.headers.get("Authorization") === `Bearer ${env.SEED_SECRET}`;
}

async function handleTelegramWebhook(request: Request, env: Env): Promise<Response> {
  if (env.TELEGRAM_WEBHOOK_SECRET) {
    const provided = request.headers.get("X-Telegram-Bot-Api-Secret-Token") || "";
    if (provided !== env.TELEGRAM_WEBHOOK_SECRET) return new Response("Unauthorized", { status: 401 });
  }
  if (!env.TELEGRAM_BOT_TOKEN) {
    console.error('Telegram bot token not configured');
    return new Response('Telegram token not configured', { status: 500 });
  }
  try {
    const update = await request.json<any>();
    // Handle callback queries for approval workflow
    if (update.callback_query) {
      const callback = update.callback_query;
      const data = callback.data;
      const callbackChatId = callback.message?.chat?.id;
      if (!callbackChatId) {
        return new Response("OK", { status: 200 });
      }
      const callbackUserId = String(callbackChatId);
      const stored = await env.BOT_KV.get(`approval:${callbackUserId}:${callbackChatId}`, { type: "json" }) as any;
      if (!stored) {
        await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ chat_id: callbackChatId, text: "هیچ درخواست تأییدی پیدا نشد.", parse_mode: "Markdown" }) });
        return new Response("OK", { status: 200 });
      }
      if (data === "approve_woo") {
          // Load user config for potential admin notification and logging
          const userConfig = await getUserConfig(env.USERS_DB, String(callbackChatId));
        // Post to WooCommerce API
        try {
          const url = `${env.WC_SITE_URL}/wp-json/wc/v3/products`;
          const auth = btoa(`${env.WC_CONSUMER_KEY}:${env.WC_CONSUMER_SECRET}`);
          const resp = await fetch(url, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Basic ${auth}`
            },
            body: JSON.stringify(stored.a)
          });
          if (resp.ok) {
            await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ chat_id: callbackChatId, text: "✅ محصول با موفقیت در سایت ثبت شد!", parse_mode: "Markdown" }) });
          } else {
            await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ chat_id: callbackChatId, text: `خطا در ثبت محصول: ${resp.status}`, parse_mode: "Markdown" }) });
          }
        } catch (e) {
          await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ chat_id: callbackChatId, text: `خطا در اتصال به ووکامرس: ${e instanceof Error ? e.message : String(e)}`, parse_mode: "Markdown" }) });
        }
        await env.BOT_KV.delete(`approval:${callbackUserId}:${callbackChatId}`);
        return new Response("OK", { status: 200 });
      } else if (data === "approve_ig") {
        await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ chat_id: callbackChatId, text: "✅ کپشن اینستاگرام در حافظه ذخیره شد. (در فاز بعدی به صورت خودکار منتشر خواهد شد)", parse_mode: "Markdown" }) });
        await env.BOT_KV.delete(`approval:${callbackUserId}:${callbackChatId}`);
        return new Response("OK", { status: 200 });
      } else if (data === "cancel") {
        await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ chat_id: callbackChatId, text: "❌ عملیات لغو شد.", parse_mode: "Markdown" }) });
        await env.BOT_KV.delete(`approval:${callbackUserId}:${callbackChatId}`);
        return new Response("OK", { status: 200 });
      }
    }

    if (!update.message || !update.message.text) return new Response("OK", { status: 200 });

    const chatId = update.message.chat.id;
    const userId = String(chatId);
    const userText = update.message.text.trim();
    // New command for orchestrator approval workflow
    if (userText.startsWith("دستور:") || userText.startsWith("/newproduct")) {
      const prompt = userText.replace(/^دستور:\s*/,"").replace(/^\/newproduct\s*/,"");
      // show typing action
      await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendChatAction`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chat_id: chatId, action: "typing" })
      });
      // call orchestrator
      const orchResp = await fetch("https://quantum-admin.nikzamir.workers.dev/api/quantum-admin/orchestrate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt })
      });
      const orchData: any = await orchResp.json();
      // store for callbacks
      await env.BOT_KV.put(`approval:${userId}:${chatId}`, JSON.stringify(orchData), { expirationTtl: 3600 });
      // format Persian message
      const message = `📝 خلاصه محصول: ${orchData.a?.name || ""}${orchData.a?.price ? ` - ${orchData.a?.price.toLocaleString()} تومان` : ""}\n📰 پیشنهاد بلاگ: ${orchData.b || ""}\n📸 کپشن اینستاگرام: ${orchData.c || ""}\n📢 پیام تلگرام: ${orchData.d || ""}`;
      const inlineKeyboard = {
        inline_keyboard: [
          [{ text: "✅ ثبت محصول در سایت", callback_data: "approve_woo" }],
          [{ text: "✅ ذخیره کپشن اینستاگرام", callback_data: "approve_ig" }],
          [{ text: "❌ لغو", callback_data: "cancel" }]
        ]
      };
      await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chat_id: chatId, text: message, parse_mode: "Markdown", reply_markup: inlineKeyboard })
      });
      return new Response("OK", { status: 200 });
    }

    const userStoredConfig = await getUserConfig(env.USERS_DB, userId);
    const defaultConfig = userId === "default_user" ? null : await getUserConfig(env.USERS_DB, "default_user");
    const storedConfig = userStoredConfig
      ? {
          ...defaultConfig,
          ...userStoredConfig,
          payment_info: userStoredConfig.payment_info || defaultConfig?.payment_info,
          admin_chat_id: userStoredConfig.admin_chat_id || defaultConfig?.admin_chat_id,
        }
      : defaultConfig;
    const catalog = await getCatalog(env.BOT_KV);
    const userConfig = storedConfig
      ? { ...storedConfig, products: catalog || storedConfig.products }
      : catalog
      ? createCatalogConfig(catalog)
      : null;


    if (userText === "/start") {
      await env.BOT_KV.delete(`conversation:${userId}:${chatId}`);
      await sendMenuMsg(
        env.TELEGRAM_BOT_TOKEN,
        chatId,
        "شما با مشاوره هوشمند فروشگاه مسترکراتینه در گفت‌وگو هستید. خوش آمدید 🌿\n\nمی‌تونم درباره محصولات مراقبت و احیای مو، قیمت، موجودی و انتخاب محصول مناسب راهنمایی‌تون کنم.",
        userConfig,
      );
      return new Response("OK", { status: 200 });
    }

    const conversationResponse = await handleOrderConversation(env, userId, chatId, userText, userConfig);
    if (conversationResponse) return conversationResponse;

    // مدیریت دکمه‌های منو
    if (userText === "📋 لیست محصولات") return await sendProductList(env, userConfig, chatId);
    if (userText === "💬 مشاوره با ادمین") return await handleSmartHandover(env, userConfig, chatId, "درخواست از منو", userId);
    if (userConfig && /(سبد خرید|سبدم|سبد خریدم)/.test(normalizeText(userText))) {
      const state = await getConversationState(env.BOT_KV, userId, chatId);
      if (state?.cart?.length) {
        await sendOrderChoice(env, chatId, formatCartSummary(state.cart, userConfig.products), ["✅ تأیید سبد", "➕ ادامه خرید"], userConfig);
      } else {
        await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, "سبد خرید شما هنوز خالی است. نام محصول موردنظر را بفرستید.", userConfig);
      }
      return new Response("OK", { status: 200 });
    }
    if (userText === "🛒 پیگیری سفارش") {
      await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, "برای پیگیری، کد رهگیری رو بفرست یا با ادمین تماس بگیر.", userConfig);
      return new Response("OK", { status: 200 });
    }

    // تشخیص قصد کاربر
    const intent = detectIntent(userText, userConfig?.products || []);

    if (intent === 'admin_request') return await handleSmartHandover(env, userConfig, chatId, userText, userId);
    
    // ⚠️ نکته حیاتی: فقط اگر محصول واقعاً در لیست باشد اجازه صدور فاکتور می‌دهیم
    if (intent === 'order_confirm' && userConfig) {
      const state = await getConversationState(env.BOT_KV, userId, chatId);
      const product = findProduct(userText, userConfig.products) ??
        userConfig.products.find((item) => item.name === state?.productName);

      if (!product) {
        await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, "لطفاً نام محصولی که می‌خوای رو بفرست تا فاکتور دقیق صادر کنم.", userConfig);
        return new Response("OK", { status: 200 });
      }

      await saveConversationState(env.BOT_KV, userId, chatId, {
        productName: product.name,
        cart: addCartItem(state?.cart || [], product.name),
        orderStage: "confirm_product",
      });
      await sendOrderChoice(env, chatId, `محصول «${product.name}» به سبد اضافه شد. برای ادامه چه کاری انجام بدهم؟`, ["✅ تأیید محصول", "➕ ادامه خرید", "🧾 ثبت سفارش"], userConfig);
      return new Response("OK", { status: 200 });
    }

    if (userConfig) {
      const state = await getConversationState(env.BOT_KV, userId, chatId);
      const previousProduct = userConfig.products.find((item) => item.name === state?.productName);
      if (previousProduct && isProductSelectionConfirmation(userText)) {
        await saveConversationState(env.BOT_KV, userId, chatId, {
          productName: previousProduct.name,
          cart: addCartItem(state?.cart || [], previousProduct.name),
          orderStage: "confirm_product",
        });
        await sendOrderChoice(env, chatId, `محصول «${previousProduct.name}» به سبد اضافه شد. برای ادامه چه کاری انجام بدهم؟`, ["✅ تأیید محصول", "➕ ادامه خرید", "🧾 ثبت سفارش"], userConfig);
        return new Response("OK", { status: 200 });
      }
    }

    const catalogResponse = buildCatalogResponse(userText, userConfig?.products || []);
    if (catalogResponse) {
      const mentionedProduct = findProduct(userText, userConfig?.products || []);
      if (mentionedProduct) {
        const currentState = await getConversationState(env.BOT_KV, userId, chatId);
        await saveConversationState(env.BOT_KV, userId, chatId, { ...currentState, productName: mentionedProduct.name });
      }
      await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, catalogResponse, userConfig);
      return new Response("OK", { status: 200 });
    }

    // پاسخ هوشمند
    const mentionedProduct = findProduct(userText, userConfig?.products || []);
    if (mentionedProduct) {
      const currentState = await getConversationState(env.BOT_KV, userId, chatId);
      await saveConversationState(env.BOT_KV, userId, chatId, { ...currentState, productName: mentionedProduct.name });
    }
    return await handleAIResponse(env, userConfig, chatId, userText, userId);

  } catch (error) {
    console.error("Webhook Error:", error);
    return new Response("Error", { status: 500 });
  }
}

function detectIntent(text: string, products: Product[]): string {
  const lowerText = normalizeText(text);
  
  // اولویت ۱: درخواست ادمین (حتی اگر عصبانی باشد)
  if (['ادمین', 'پشتیبانی', 'مسئول', 'انسان', 'اپراتور', 'بیشعور', 'نمیخوام'].some(k => lowerText.includes(k))) 
    return 'admin_request';

  // اولویت ۲: تایید سفارش (فقط اگر کلمات کلیدی خیلی صریح باشند)
  if (['بله سفارش میدم', 'ثبت سفارش', 'ثبت کن', 'سفارش بده', 'میخوام بخرم', 'واریز میکنم', 'همین جا', 'همینجا'].some(k => lowerText.includes(k))) 
    return 'order_confirm';

  return 'general_question';
}

export function findProduct(text: string, products: Product[]): Product | null {
  const queryTokens = getSearchTokens(text);
  if (!queryTokens.length) return null;

  return products
    .map((product) => {
      const productTokens = getSearchTokens(`${product.name} ${product.category} ${product.brand || ""}`);
      const overlap = queryTokens.filter((token) => productTokens.some((candidate) => tokensMatch(token, candidate))).length;
      const queryCoverage = overlap / queryTokens.length;
      const productCoverage = overlap / productTokens.length;
      const exactPhrase = normalizeText(text).includes(normalizeText(product.name));
      const requestedType = getProductType(queryTokens);
      const productType = getProductType(productTokens);
      const typeScore = requestedType && requestedType === productType ? 5 : 0;
      return { product, overlap, queryCoverage, productCoverage, exactPhrase, typeScore };
    })
    .filter(({ overlap, queryCoverage }) => overlap >= 2 && queryCoverage >= 0.5)
    .sort((left, right) => {
      if (right.exactPhrase !== left.exactPhrase) return Number(right.exactPhrase) - Number(left.exactPhrase);
      if (right.typeScore !== left.typeScore) return right.typeScore - left.typeScore;
      if (right.overlap !== left.overlap) return right.overlap - left.overlap;
      if (right.queryCoverage !== left.queryCoverage) return right.queryCoverage - left.queryCoverage;
      return right.productCoverage - left.productCoverage;
    })[0]?.product ?? null;
}

function getSearchTokens(value: string): string[] {
  const stopWords = new Set(["ثبت", "سفارش", "میخوام", "می", "خوام", "برای", "رو", "را", "برام", "لطفا", "لطفاً", "موجود", "دارید", "داری", "دارین", "هست", "هستید", "میباشد"]);
  return normalizeText(value)
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .split(/\s+/)
    .filter((token) => token.length > 1 && !stopWords.has(token));
}

function tokensMatch(left: string, right: string): boolean {
  if (left === right) return true;
  if (left.length < 4 || right.length < 4) return false;
  return levenshteinDistance(left, right) <= 1;
}

function getProductType(tokens: string[]): string | null {
  const typeAliases: Array<[string, string[]]> = [
    ["shampoo", ["شامپو"]],
    ["mask", ["ماسک"]],
    ["oil", ["روغن", "ارگان"]],
    ["keratin", ["کراتین"]],
    ["protein", ["پروتئین"]],
    ["botox", ["بوتاکس"]],
    ["serum", ["سرم"]],
  ];
  return typeAliases.find(([, aliases]) => aliases.some((alias) => tokens.some((token) => tokensMatch(token, alias))))?.[0] || null;
}

function getProductTypes(tokens: string[]): string[] {
  const typeAliases: Array<[string, string[]]> = [
    ["shampoo", ["شامپو"]],
    ["mask", ["ماسک"]],
    ["oil", ["روغن", "ارگان"]],
    ["keratin", ["کراتین"]],
    ["protein", ["پروتئین"]],
    ["botox", ["بوتاکس"]],
    ["serum", ["سرم"]],
  ];
  return typeAliases
    .filter(([, aliases]) => aliases.some((alias) => tokens.some((token) => tokensMatch(token, alias))))
    .map(([type]) => type);
}

function levenshteinDistance(left: string, right: string): number {
  const previous = Array.from({ length: right.length + 1 }, (_, index) => index);
  for (let leftIndex = 1; leftIndex <= left.length; leftIndex++) {
    const current = [leftIndex];
    for (let rightIndex = 1; rightIndex <= right.length; rightIndex++) {
      current[rightIndex] = Math.min(
        current[rightIndex - 1] + 1,
        previous[rightIndex] + 1,
        previous[rightIndex - 1] + (left[leftIndex - 1] === right[rightIndex - 1] ? 0 : 1),
      );
    }
    previous.splice(0, previous.length, ...current);
  }
  return previous[right.length];
}

export function isProductAvailable(product: Product): boolean {
  const stock = product.stock.trim().toLocaleLowerCase('fa-IR');
  return stock === "موجود" || stock === "available";
}

function createCatalogConfig(products: Product[]): UserConfig {
  return {
    business_name: "مسترکراتینه",
    business_type: "product",
    knowledge_status: "approved",
    capabilities: DEFAULT_CAPABILITIES,
    admin_id: "",
    tone: "صمیمی و حرفه‌ای",
    platform: "telegram",
    products,
    rules: "قیمت و موجودی فقط بر اساس کاتالوگ فعلی سایت اعلام شود.",
  };
}

export function buildCatalogResponse(text: string, products: Product[]): string | null {
  if (!products.length) return null;
  const normalizedText = normalizeText(text);

  if (containsUnsupportedFitnessContent(normalizedText)) {
    return "فروشگاه مسترکراتینه فقط محصولات مراقبت و احیای مو دارد و محصول بدنسازی یا مکمل ارائه نمی‌کند.";
  }

  if (/^(همین|همین فقط|دیگه چی|چی دیگه|گزینه دیگه|بیشتر)/.test(normalizedText)) {
    return "حتماً. برای دیدن گزینه‌های بیشتر، نوع محصول موردنظرتان مثل ماسک، روغن، شامپو یا کراتین را بفرستید تا فقط از کاتالوگ واقعی پیشنهاد بدهم.";
  }

  if (/(میتونم|می تونم|میشه|چطور|چگونه).*(خونه|خانه).*(کراتین|پروتئین)/.test(normalizedText) || /(کراتین|پروتئین).*(خونه|خانه)/.test(normalizedText)) {
    const professionalProducts = products.filter((product) => /(کراتین|پروتئین|بوتاکس)/.test(normalizeText(`${product.name} ${product.category}`)) && isProductAvailable(product));
    const list = professionalProducts.slice(0, 5).map((product) => `• ${product.name} - ${product.price.toLocaleString()} تومان`).join("\n");
    return `برخی محصولات کراتین و پروتئین سایت برای مصرف حرفه‌ای معرفی شده‌اند و اجرای آن‌ها در خانه، بدون آموزش و تهویه مناسب، توصیه نمی‌شود. برای مصرف خانگی بهتر است از محصولات مراقبتی و ترمیمی استفاده کنید؛ برای انتخاب دقیق‌تر نوع مو و سابقه دکلره را بفرستید.\n\nمحصولات مرتبط موجود:\n${list}`;
  }

  if (/(مشاوره|راهنمایی|مشاور)/.test(normalizedText)) {
    return "بله، مشاوره هوشمند انتخاب محصولات مراقبت و احیای مو داریم. نوع مو، مشکل اصلی مثل خشکی، آسیب حرارتی یا ریزش، و محصولی که مدنظرتونه رو بفرستید تا بر اساس کاتالوگ واقعی سایت راهنمایی‌تون کنم.";
  }

  if (/(برند|برندهایی|مارک)/.test(normalizedText)) {
    const requestedBrand = products.find((product) => product.brand && normalizedText.includes(normalizeText(product.brand)))?.brand;
    if (requestedBrand) {
      const brandProducts = products.filter((product) => product.brand === requestedBrand && isProductAvailable(product)).slice(0, 12);
      return brandProducts.length
        ? `محصولات موجود از برند ${requestedBrand}:\n\n${formatProductListItems(brandProducts)}`
        : `در حال حاضر محصول موجودی از برند ${requestedBrand} پیدا نکردم.`;
    }
    const brands = [...new Set(products.map((product) => product.brand).filter(Boolean))];
    return brands.length
      ? `برندهای موجود در کاتالوگ سایت:\n${brands.map((brand) => `• ${brand}`).join("\n")}`
      : "برند محصولات در کاتالوگ سایت ثبت نشده است. نام محصول یا دسته‌بندی را بفرستید تا دقیق بررسی کنم.";
  }

  const requestedTypes = getProductTypes(getSearchTokens(text));
  const hasCatalogQuestion = /(چی داری|چه محصول|محصولات|موجود|برای|میخوام|می خواهم)/.test(normalizedText);
  if (requestedTypes.length && hasCatalogQuestion) {
    const queryTokens = getSearchTokens(text);
    const typedProducts = products.filter((product) => {
      const productTokens = getSearchTokens(`${product.name} ${product.category} ${product.brand || ""}`);
      const productType = getProductType(productTokens);
      const overlap = queryTokens.filter((token) => productTokens.some((candidate) => tokensMatch(token, candidate))).length;
      return productType && requestedTypes.includes(productType) && overlap >= Math.min(2, queryTokens.length);
    }).slice(0, 12);
    if (typedProducts.length) return `محصولات مرتبط در کاتالوگ سایت:\n\n${formatProductListItems(typedProducts)}`;
  }

  const exactProduct = findProduct(text, products);
  if (exactProduct) return formatProduct(exactProduct);

  const matchingProducts = products.filter((product) => {
    const searchableText = normalizeText(`${product.name} ${product.category} ${product.details}`);
    return ["آسیب دیده", "آسیب", "دکلره", "خشک", "فر", "صاف", "شامپو", "کراتین", "بوتاکس", "پروتئین", "ماسک"]
      .map(normalizeText)
      .some((keyword) => normalizedText.includes(keyword) && searchableText.includes(keyword));
  });

  if (matchingProducts.length && /(چی داری|چه محصول|محصولات|موجود|برای)/.test(normalizedText)) {
    return formatProductList(matchingProducts.slice(0, 8));
  }

  return null;
}

function isProductSelectionConfirmation(text: string): boolean {
  const normalizedText = normalizeText(text);
  return /^(بله|اره|آره|میخوامش|می خوامش|میخوام|می خوام|ثبتش کن|ثبتش کن برام|انتخابش کردم|همین محصول|همینو میخوام)$/.test(normalizedText) ||
    /(ثبت سفارش|ثبت سفارش کنید|ثبتش کن|سفارش بده)/.test(normalizedText);
}

function formatProduct(product: Product): string {
  const status = isProductAvailable(product) ? "موجود" : "ناموجود";
  const details = product.details ? `\n${product.details}` : "";
  const link = product.url ? `\nلینک: ${product.url}` : "";
  return `${product.name}\nقیمت: ${product.price.toLocaleString()} تومان\nوضعیت: ${status}${details}${link}`;
}

function formatProductList(products: Product[]): string {
  return `محصولات مرتبط در کاتالوگ سایت:\n\n${formatProductListItems(products)}`;
}

function formatProductListItems(products: Product[]): string {
  return products.map((product) => `• ${product.name} - ${product.price.toLocaleString()} تومان (${isProductAvailable(product) ? "موجود" : "ناموجود"})`).join("\n");
}

function normalizeText(value: string): string {
  return value.trim().toLocaleLowerCase('fa-IR')
    .replace(/[يى]/g, "ی")
    .replace(/ك/g, "ک")
    .replace(/[أإآ]/g, "ا")
    .replace(/ة/g, "ه")
    .replace(/\u200c/g, " ")
    .replace(/\s+/g, " ");
}

function containsUnsupportedFitnessContent(value: string): boolean {
  const normalizedValue = normalizeText(value);
  return /(بدنسازی|مکمل|پروتئین وی|bcaa|کراتین وی|گینر|پری ورک ?اوت)/i.test(normalizedValue);
}

async function handleAIResponse(env: Env, config: UserConfig | null, chatId: number, userText: string, userId: string): Promise<Response> {
  const cacheKey = `reply:v2:${userId}:${chatId}:${userText}`;
  const cachedResponse = await env.BOT_KV.get(cacheKey);
  let aiResponse: string;

  if (cachedResponse) {
    aiResponse = cachedResponse;
  } else {
    try {
      const systemPrompt = buildSafeConsultativePrompt(config);
      const response = await env.AI.run("@cf/meta/llama-3.1-8b-instruct-fast", {
        messages: [
          { role: "system", content: systemPrompt },
          { role: "user", content: userText }
        ],
        max_tokens: 400,
        temperature: 0.4
      });
      aiResponse = response.response;
      if (containsUnsupportedFitnessContent(aiResponse) || /example\.com|ثبت محصول|نام مشتری: نام مشتری/.test(aiResponse)) {
        aiResponse = "فروشگاه مسترکراتینه فقط در زمینه محصولات مراقبت و احیای مو فعالیت می‌کند. درباره نوع مو یا مشکل موهایتان بفرمایید تا از کاتالوگ واقعی راهنمایی‌تان کنم.";
      }
      await env.BOT_KV.put(cacheKey, aiResponse, { expirationTtl: 3600 });
    } catch (aiError) {
      aiResponse = "یه لحظه سیستم ما مشغوله، چند دقیقه دیگه پیام بده عزیزم 🙏";
    }
  }

  await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, aiResponse, config);
  return new Response("OK", { status: 200 });
}

async function handleSmartHandover(env: Env, config: UserConfig | null, chatId: number, userText: string, userId: string): Promise<Response> {
  await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, "پیامت رو به ادمین فرستادم. به زودی جوابت رو می‌گیری 💪", config);
  if (config?.admin_chat_id) {
    await sendTelegramMessage(env.TELEGRAM_BOT_TOKEN, config.admin_chat_id, 
      `🔔 پشتیبانی!\n👤 ${chatId}\n💬 ${userText}\n⏰ ${new Date().toLocaleString('fa-IR')}`);
  }
  return new Response("OK", { status: 200 });
}

async function handleOrderProcess(env: Env, config: UserConfig | null, chatId: number, userId: string, product: Product): Promise<Response> {
  if (!config?.payment_info) {
    await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, "اطلاعات پرداخت ثبت نشده. لطفاً با ادمین تماس بگیر.", config);
    return new Response("OK", { status: 200 });
  }

  if (!isProductAvailable(product)) {
    await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, `متأسفانه ${product.name} در حال حاضر موجود نیست.`, config);
    return new Response("OK", { status: 200 });
  }

  const invoiceId = generateInvoiceId();
  const total = product.price;

  const productLink = product.url ? `\n\nلینک محصول: ${product.url}` : "";
  await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId,
    `فاکتور سفارش: ${product.name}\n\n🔑 کد رهگیری: #${invoiceId}\nمبلغ: ${total.toLocaleString()} تومان\n\nکارت: ${config.payment_info.card_number}\nبه نام: ${config.payment_info.card_holder}${productLink}\n\n📸 عکس رسید رو با کد #${invoiceId} بفرست.`, config);
  return new Response("OK", { status: 200 });
}

async function sendProductList(env: Env, config: UserConfig | null, chatId: number): Promise<Response> {
  if (!config?.products.length) {
    await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, "هنوز محصولی ثبت نشده.", config);
    return new Response("OK", { status: 200 });
  }
  let msg = "📋 لیست محصولات:\n\n";
  config.products.forEach(p => msg += `• ${p.name} - ${p.price.toLocaleString()} تومان (${p.stock})\n`);
  await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, msg, config);
  return new Response("OK", { status: 200 });
}

// ============================================
// پرامپت ضد توهم و ضد سوال‌پیچ کردن
// ============================================
function buildSafeConsultativePrompt(config: UserConfig | null): string {
  if (!config) return `تو یک دستیار هوشمند و صمیمی هستی. کوتاه و مفید پاسخ بده.`;

  const productsText = config.products.map((p: Product) => 
    `- ${p.name} (${p.category}): ${p.price.toLocaleString()} تومان | ${p.stock} | ${p.details}`
  ).join('\n');

  return `تو "دایرکت یار"، مشاور متخصص "${config.business_name}" هستی.

## لحن:
- آمیانه، دوستانه و حرفه‌ای. هرگز دستوری صحبت نکن.

## قوانین حیاتی (هرگز نقض نکن):
1. **فقط از لیست محصولات زیر استفاده کن.**
2. **قانون ضد سوال‌پیچ:** اگر کاربر نام یک محصول غیرمرتبط (مثل لوازم یدکی ماشین، غذا، لباس یا مکمل ورزشی) را آورد، **هرگز نپرس "منظورت چیه؟"**. بلافاصله و مودبانه بگو: "عزیزم، ما فقط محصولات مراقبت و احیای مو داریم و متأسفانه [نام محصول کاربر] رو نداریم."
3. **قانون ضد فروش اجباری:** هرگز بدون اینکه کاربر صراحتاً نام یک محصول موجود را تایید کرده باشد، فاکتور صادر نکن یا شماره کارت نفرست. اگر کاربر فقط گفت "بله" یا "میخوام"، بپرس: "کدوم محصول رو می‌خوای عزیزم؟"
4. اگر محصولی نبود، صادقانه بگو: "راستش اینو نداریم، ولی می‌تونم چیزای دیگه‌ای پیشنهاد بدم."
5. پاسخ‌ها حداکثر -۴ جمله باشد.

## محصولات:
${productsText}

## قوانین فروشگاه:
${config.rules || "ارسال رایگان بالای ۵۰۰ هزار تومان."}

## مثال رفتار صحیح:
کاربر: میل لنگ پراید دارید؟
تو: عزیزم، ما فقط محصولات مراقبت و احیای مو داریم و متأسفانه میل لنگ پراید رو نداریم. ولی برای تقویت مو روغن آرگان خالص داریم.

کاربر: برای موی آسیب دیده چی دارید؟
تو: عزیزم، آسیب موهات در اثر حرارته یا دکلره؟ (چون درمانشون متفاوته). ولی به طور کلی ماسک کراتینه (۳۵۰ تومن) عالیه.

کاربر: بله میخوام
تو: کدوم محصول مراقبت مو رو می‌خوای عزیزم؟ اسم محصول رو بفرست تا دقیق راهنمایی‌ات کنم.`;
}

function generateInvoiceId(): string {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  let result = '';
  for (let i = 0; i < 4; i++) result += chars.charAt(Math.floor(Math.random() * chars.length));
  return result;
}

async function getUserConfig(db: KVNamespace, userId: string): Promise<UserConfig | null> {
  try {
    const config = await db.get<UserConfig>(`user:${userId}:config`, { type: "json" });
    const products = await db.get<Product[]>(`user:${userId}:products`, { type: "json" });
    const rules = await db.get(`user:${userId}:rules`, { type: "text" });
    if (!config) return null;
    return { ...config, products: products || [], rules: rules || "" };
  } catch { return null; }
}

async function getConversationState(kv: KVNamespace, userId: string, chatId: number): Promise<ConversationState | null> {
  return await kv.get<ConversationState>(`conversation:${userId}:${chatId}`, { type: "json" });
}

async function saveConversationState(kv: KVNamespace, userId: string, chatId: number, state: ConversationState): Promise<void> {
  await kv.put(`conversation:${userId}:${chatId}`, JSON.stringify(state), { expirationTtl: 86400 });
}

async function handleOrderConversation(env: Env, userId: string, chatId: number, text: string, config: UserConfig | null): Promise<Response | null> {
  const state = await getConversationState(env.BOT_KV, userId, chatId);
  if (!state?.orderStage || !config) return null;

  const normalizedText = normalizeText(text);
  const cart = state.cart || [];
  const product = config.products.find((item) => item.name === state.productName);

  if (state.orderStage === "confirm_product") {
    if (/تایید|بله|اضافه/.test(normalizedText)) {
      await saveConversationState(env.BOT_KV, userId, chatId, { ...state, orderStage: "add_more" });
      await sendOrderChoice(env, chatId, "محصول تأیید شد. محصول یا خدمت دیگری مدنظرتان هست تا به سبد اضافه کنم؟", ["➕ ادامه خرید", "✅ ثبت سبد"], config);
      return new Response("OK", { status: 200 });
    }
    if (/ادامه خرید|خرید بیشتر/.test(normalizedText)) {
      await saveConversationState(env.BOT_KV, userId, chatId, { ...state, orderStage: undefined });
      await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, "حتماً. نام محصول دیگری را بفرستید تا به سبد اضافه کنم.", config);
      return new Response("OK", { status: 200 });
    }
    if (/ثبت سفارش|ثبت سبد|فاکتور|ثبت نهایی|همین دوتا|همین دو تا/.test(normalizedText)) {
      await saveConversationState(env.BOT_KV, userId, chatId, { ...state, orderStage: "confirm_cart" });
      await sendOrderChoice(env, chatId, formatCartSummary(cart, config.products), ["✅ تأیید سبد", "➕ ادامه خرید"], config);
      return new Response("OK", { status: 200 });
    }
    return null;
  }

  if (state.orderStage === "add_more") {
    if (/ادامه خرید|خرید بیشتر/.test(normalizedText)) {
      await saveConversationState(env.BOT_KV, userId, chatId, { ...state, orderStage: undefined });
      await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, "نام محصول دیگری را بفرستید تا به سبد اضافه کنم.", config);
      return new Response("OK", { status: 200 });
    }
    if (/ثبت سبد|ثبت سفارش|فاکتور|ثبت نهایی|همین دوتا|همین دو تا|تمام|ندارم/.test(normalizedText)) {
      await saveConversationState(env.BOT_KV, userId, chatId, { ...state, orderStage: "confirm_cart" });
      await sendOrderChoice(env, chatId, formatCartSummary(cart, config.products), ["✅ تأیید سبد", "➕ ادامه خرید"], config);
      return new Response("OK", { status: 200 });
    }
    return null;
  }

  if (state.orderStage === "confirm_cart") {
    if (/تأیید|تایید|بله|ثبت نهایی/.test(normalizedText)) {
      await saveConversationState(env.BOT_KV, userId, chatId, { ...state, orderStage: "choose_mode" });
      await sendOrderChoice(env, chatId, "سبد خرید تأیید شد. سفارش را همین‌جا در ربات ثبت کنم یا لینک ثبت سفارش سایت را بفرستم؟", ["🛍️ همین‌جا ثبت کن", "🔗 لینک سایت"], config);
      return new Response("OK", { status: 200 });
    }
    if (/ادامه خرید|خرید بیشتر/.test(normalizedText)) {
      await saveConversationState(env.BOT_KV, userId, chatId, { ...state, orderStage: undefined });
      await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, "نام محصول دیگری را بفرستید تا به سبد اضافه کنم.", config);
      return new Response("OK", { status: 200 });
    }
    return null;
  }

  if (!product) return null;

  if (state.orderStage === "choose_mode") {
    if (/(لینک|سایت)/.test(normalizedText)) {
      await saveConversationState(env.BOT_KV, userId, chatId, { productName: product.name, orderMode: "website" });
      await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, product.url ? `لینک ثبت سفارش ${product.name}:\n${product.url}` : "لینک این محصول در سایت در دسترس نیست. سفارش را همین‌جا ادامه می‌دهم؟", config);
      return new Response("OK", { status: 200 });
    }
    if (/(همین|ربات|اینجا)/.test(normalizedText)) {
      await saveConversationState(env.BOT_KV, userId, chatId, { productName: product.name, orderMode: "telegram", orderStage: "name" });
      await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, "حتماً. لطفاً نام و نام خانوادگی گیرنده را بفرستید.", config);
      return new Response("OK", { status: 200 });
    }
    return null;
  }

  if (state.orderMode !== "telegram") return null;
  if (state.orderStage === "name") {
    if (!isValidCustomerName(text)) {
      await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, "لطفاً نام و نام خانوادگی واقعی را وارد کنید؛ مثال: حمیدرضا نیک‌ضمیر.", config);
      return new Response("OK", { status: 200 });
    }
    await saveConversationState(env.BOT_KV, userId, chatId, { ...state, customerName: text.trim(), orderStage: "phone" });
    await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, "شماره تماس گیرنده را بفرستید.", config);
    return new Response("OK", { status: 200 });
  }
  if (state.orderStage === "phone") {
    const phone = normalizePhone(text);
    if (!phone) {
      await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, "شماره تماس معتبر نیست. شماره ایران را مثل 09015050455 یا +989015050455 وارد کنید؛ شماره بین‌المللی هم باید با قالب + و کد کشور باشد.", config);
      return new Response("OK", { status: 200 });
    }
    await saveConversationState(env.BOT_KV, userId, chatId, { ...state, phone, orderStage: "address" });
    await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, "آدرس دقیق دریافت سفارش را بفرستید.", config);
    return new Response("OK", { status: 200 });
  }
  if (state.orderStage === "address") {
    if (!isValidAddress(text)) {
      await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, "آدرس کوتاه یا ناقص است. لطفاً استان، شهر، خیابان، کوچه/پلاک و واحد را در یک پیام بنویسید.", config);
      return new Response("OK", { status: 200 });
    }
    await saveConversationState(env.BOT_KV, userId, chatId, { ...state, address: text.trim(), orderStage: "postal_code" });
    await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, "کد پستی را بفرستید؛ این مورد اختیاری است و می‌توانید «ندارم» بنویسید.", config);
    return new Response("OK", { status: 200 });
  }
  if (state.orderStage === "postal_code") {
    const postalCode = normalizePostalCode(text);
    if (normalizedText !== "ندارم" && !postalCode) {
      await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, "کد پستی باید ۱۰ رقم باشد؛ اگر کد پستی ندارید، «ندارم» بنویسید.", config);
      return new Response("OK", { status: 200 });
    }
    await saveConversationState(env.BOT_KV, userId, chatId, { ...state, postalCode: postalCode || undefined, orderStage: "shipping" });
    await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, "روش ارسال را انتخاب کنید: پست، تیپاکس یا پیک.", config);
    return new Response("OK", { status: 200 });
  }
  if (state.orderStage === "shipping") {
    const shippingMethod = normalizedText.includes("تیپاکس") ? "tipax" : normalizedText.includes("پیک") ? "courier" : normalizedText.includes("پست") ? "post" : null;
    if (!shippingMethod) {
      await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, "لطفاً یکی از گزینه‌های پست، تیپاکس یا پیک را انتخاب کنید.", config);
      return new Response("OK", { status: 200 });
    }
    await saveConversationState(env.BOT_KV, userId, chatId, { ...state, shippingMethod, orderStage: "payment" });
    await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, "اطلاعات سفارش ذخیره شد. روش پرداخت را انتخاب کنید: درگاه سایت یا کارت/شبا.", config);
    return new Response("OK", { status: 200 });
  }
  if (state.orderStage === "payment") {
    const total = cart.reduce((sum, item) => {
      const product = config.products.find((candidate) => candidate.name === item.productName);
      return sum + (product?.price || 0) * item.quantity;
    }, 0);
    const invoiceId = generateInvoiceId();
    await saveConversationState(env.BOT_KV, userId, chatId, { ...state, orderStage: "payment" });
    if (config.payment_info) {
      await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, `فاکتور سفارش #${invoiceId}\nمبلغ: ${total.toLocaleString()} تومان\n\nکارت: ${config.payment_info.card_number}\nبه نام: ${config.payment_info.card_holder}\n\n📸 عکس رسید را با کد #${invoiceId} بفرست.`, config);
    } else {
      await sendMenuMsg(env.TELEGRAM_BOT_TOKEN, chatId, `فاکتور سفارش #${invoiceId}\nمبلغ: ${total.toLocaleString()} تومان\n\nپرداخت از طریق درگاه سایت.\nلینک پرداخت: ${config.products[0]?.url || "https://mrkeratine.ir"}`, config);
    }
    return new Response("OK", { status: 200 });
  }

  return null;
}

export function normalizePhone(value: string): string | null {
  const digits = toEnglishDigits(value).replace(/[\s().-]/g, "");
  if (/^09\d{9}$/.test(digits)) return `+98${digits.slice(1)}`;
  if (/^989\d{9}$/.test(digits)) return `+${digits}`;
  if (/^\+\d{8,15}$/.test(digits)) return digits;
  return null;
}

export function isValidCustomerName(value: string): boolean {
  const name = value.trim().replace(/\u200c/g, " ").replace(/\s+/g, " ");
  if (name.length < 5 || name.length > 80 || /\d/.test(toEnglishDigits(name))) return false;
  if (!/^[\p{L} .'-]+$/u.test(name)) return false;
  return name.split(" ").filter(Boolean).length >= 2;
}

export function isValidAddress(value: string): boolean {
  const address = value.trim();
  if (address.length < 15 || address.length > 300) return false;
  if (!/[\p{L}]/u.test(address)) return false;
  return address.split(/\s+/).filter(Boolean).length >= 4;
}

export function normalizePostalCode(value: string): string | null {
  const postalCode = toEnglishDigits(value).replace(/[\s-]/g, "");
  return /^\d{10}$/.test(postalCode) ? postalCode : null;
}

function toEnglishDigits(value: string): string {
  return value.replace(/[۰-۹]/g, (digit) => String(digit.charCodeAt(0) - "۰".charCodeAt(0)))
    .replace(/[٠-٩]/g, (digit) => String(digit.charCodeAt(0) - "٠".charCodeAt(0)));
}

async function getCatalog(kv: KVNamespace): Promise<Product[] | null> {
  const cachedCatalog = await kv.get<Product[]>(CATALOG_CACHE_KEY, { type: "json" });
  if (cachedCatalog?.length) return cachedCatalog;

  try {
    const response = await fetch(CATALOG_URL);
    if (!response.ok) return null;
    const products = await response.json<WooCommerceProduct[]>();
    const catalog = products
      .map(mapWooCommerceProduct)
      .filter((product): product is Product => product !== null);
    if (!catalog.length) return null;
    await kv.put(CATALOG_CACHE_KEY, JSON.stringify(catalog), { expirationTtl: 600 });
    return catalog;
  } catch (error) {
    console.error("Catalog sync error:", error);
    return null;
  }

}

function addCartItem(cart: CartItem[], productName: string): CartItem[] {
  const existing = cart.find((item) => item.productName === productName);
  if (existing) return cart.map((item) => item.productName === productName ? { ...item, quantity: item.quantity + 1 } : item);
  return [...cart, { productName, quantity: 1 }];
}

function formatCartSummary(cart: CartItem[], products: Product[]): string {
  const lines = cart.map((item) => {
    const product = products.find((candidate) => candidate.name === item.productName);
    return product ? `• ${product.name} × ${item.quantity} = ${(product.price * item.quantity).toLocaleString()} تومان` : null;
  }).filter((line): line is string => Boolean(line));
  const total = cart.reduce((sum, item) => {
    const product = products.find((candidate) => candidate.name === item.productName);
    return sum + (product?.price || 0) * item.quantity;
  }, 0);
  return `سبد خرید شما:\n\n${lines.join("\n")}\n\nمبلغ تقریبی: ${total.toLocaleString()} تومان`;
}

async function sendOrderChoice(env: Env, chatId: number, text: string, choices: string[], config: UserConfig | null): Promise<void> {
  const keyboard = {
    keyboard: choices.map((choice) => [{ text: choice }]),
    resize_keyboard: true,
    one_time_keyboard: false,
  };
  await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, text, parse_mode: "Markdown", reply_markup: keyboard }),
  });
}

export function mapWooCommerceProduct(product: WooCommerceProduct): Product | null {
  const price = Number(product.prices?.price);
  if (!product.name?.trim() || !Number.isFinite(price) || price <= 0) return null;

  return {
    name: product.name.trim(),
    price,
    stock: product.is_in_stock ? "موجود" : "ناموجود",
    details: stripHtml(product.short_description || product.description || "").slice(0, 500),
    category: product.categories?.map((category) => category.name?.trim()).filter(Boolean).join(", ") || "محصولات مراقبت مو",
    brand: product.attributes?.find((attribute) => normalizeText(attribute.name || "") === "برند")?.terms?.map((term) => term.name?.trim()).filter(Boolean).join(", "),
    url: product.permalink,
  };
}

function stripHtml(value: string): string {
  return value.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
}

async function sendTelegramMessage(token: string, chatId: number, text: string) {
  await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, text, parse_mode: "Markdown" }),
  });
}

async function sendMenuMsg(token: string, chatId: number, text: string, config: UserConfig | null) {
  const keyboard = {
    keyboard: [[{ text: "📋 لیست محصولات" }, { text: "🛒 پیگیری سفارش" }], [{ text: "💬 مشاوره با ادمین" }]],
    resize_keyboard: true, one_time_keyboard: false
  };
  const chunks = splitTelegramText(text);
  for (const [index, chunk] of chunks.entries()) {
    await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chat_id: chatId, text: chunk, parse_mode: "Markdown", ...(index === chunks.length - 1 ? { reply_markup: keyboard } : {}) }),
    });
  }
}

function splitTelegramText(text: string, maxLength = 3900): string[] {
  if (text.length <= maxLength) return [text];
  const chunks: string[] = [];
  let remaining = text;
  while (remaining.length > maxLength) {
    let splitAt = remaining.lastIndexOf("\n", maxLength);
    if (splitAt < Math.floor(maxLength * 0.6)) splitAt = maxLength;
    chunks.push(remaining.slice(0, splitAt));
    remaining = remaining.slice(splitAt).trimStart();
  }
  if (remaining) chunks.push(remaining);
  return chunks;
}

async function handleSeed(request: Request, env: Env): Promise<Response> {
  if (!isSeedAuthorized(request, env)) return new Response("Unauthorized", { status: 401 });
  try {
    const data = await request.json<SeedPayload>();
    const validationError = validateSeedPayload(data);
    if (validationError) {
      return new Response(JSON.stringify({ error: validationError }), { status: 400, headers: { "Content-Type": "application/json" } });
    }
    const userId = data.userId || "default_user";
    await env.USERS_DB.put(`user:${userId}:config`, JSON.stringify({
      business_name: data.business_name,
      business_type: data.business_type || "product",
      knowledge_status: data.knowledge_status || "pending",
      capabilities: { ...DEFAULT_CAPABILITIES, ...data.capabilities },
      admin_id: data.admin_id,
      admin_chat_id: data.admin_chat_id, tone: data.tone || "صمیمی و آمیانه",
      platform: data.platform || "telegram", payment_info: data.payment_info
    }));
    if (data.source_url) {
      await env.USERS_DB.put(`user:${userId}:source`, JSON.stringify({
        source_url: data.source_url,
        source_type: data.source_type || "website",
      }));
    }
    if (data.products) await env.USERS_DB.put(`user:${userId}:products`, JSON.stringify(data.products));
    if (data.rules) await env.USERS_DB.put(`user:${userId}:rules`, data.rules);
    return new Response(JSON.stringify({ success: true }), { headers: { "Content-Type": "application/json" } });
  } catch {
    return new Response(JSON.stringify({ error: "Invalid data" }), { status: 400, headers: { "Content-Type": "application/json" } });
  }
}

async function handleKnowledgeRefresh(request: Request, env: Env): Promise<Response> {
  if (!isSeedAuthorized(request, env)) return new Response("Unauthorized", { status: 401 });
  try {
    const data = await request.json<{ userId?: string; source_url?: string; source_type?: "website" | "woocommerce" }>();
    const userId = data.userId || "default_user";
    const source = data.source_url
      ? { source_url: data.source_url, source_type: data.source_type || "website" }
      : await env.USERS_DB.get<{ source_url: string; source_type: "website" | "woocommerce" }>(`user:${userId}:source`, { type: "json" });
    if (!source?.source_url) return jsonResponse({ error: "source_url is required" }, 400);

    const catalog = await getCatalog(env.BOT_KV);
    if (!catalog) return jsonResponse({ error: "catalog could not be synchronized" }, 502);
    const content = await fetchWordPressKnowledge(source.source_url);
    const snapshot = buildKnowledgeSnapshot(source.source_url, source.source_type, catalog, content);
    await env.USERS_DB.put(`user:${userId}:knowledge`, JSON.stringify(snapshot));
    return jsonResponse({ success: true, knowledge_status: "pending", snapshot }, 200);
  } catch {
    return jsonResponse({ error: "Invalid data" }, 400);
  }
}

async function handleKnowledgeStatus(request: Request, env: Env): Promise<Response> {
  if (!isSeedAuthorized(request, env)) return new Response("Unauthorized", { status: 401 });
  const url = new URL(request.url);
  const userId = url.searchParams.get("userId") || "default_user";
  const snapshot = await env.USERS_DB.get<KnowledgeSnapshot>(`user:${userId}:knowledge`, { type: "json" });
  return jsonResponse({ knowledge_status: snapshot ? "pending" : "not_synced", snapshot }, 200);
}

export function buildKnowledgeSnapshot(
  sourceUrl: string,
  sourceType: "website" | "woocommerce",
  products: Product[],
  content: { pages: WordPressContentItem[]; articles: WordPressContentItem[] } = { pages: [], articles: [] },
): KnowledgeSnapshot {
  const contentItems = [...content.pages, ...content.articles];
  const contentTitles = contentItems.map((item) => stripHtml(item.title?.rendered || "")).filter(Boolean).slice(0, 200);
  const contentExcerpt = contentItems
    .map((item) => stripHtml(item.content?.rendered || ""))
    .filter(Boolean)
    .join("\n")
    .slice(0, 20000);
  return {
    source_url: sourceUrl,
    source_type: sourceType,
    synced_at: new Date().toISOString(),
    products_count: products.length,
    categories: [...new Set(products.flatMap((product) => product.category.split(",").map((category) => category.trim())).filter(Boolean))].sort(),
    brands: [...new Set(products.map((product) => product.brand).filter((brand): brand is string => Boolean(brand)))].sort(),
    pages_count: content.pages.length,
    articles_count: content.articles.length,
    content_titles: contentTitles,
    content_excerpt: contentExcerpt,
  };
}

async function fetchWordPressKnowledge(sourceUrl: string): Promise<{ pages: WordPressContentItem[]; articles: WordPressContentItem[] }> {
  const { origin } = new URL(sourceUrl);
  const [pages, articles] = await Promise.all([
    fetchWordPressCollection(`${origin}/wp-json/wp/v2/pages?per_page=100&_fields=title,content,link`),
    fetchWordPressCollection(`${origin}/wp-json/wp/v2/posts?per_page=100&_fields=title,content,link`),
  ]);
  return { pages, articles };
}

async function fetchWordPressCollection(url: string): Promise<WordPressContentItem[]> {
  try {
    const response = await fetch(url);
    if (!response.ok) return [];
    const data = await response.json<WordPressContentItem[]>();
    return Array.isArray(data) ? data : [];
  } catch (error) {
    console.error("WordPress knowledge sync error:", error);
    return [];
  }
}

function jsonResponse(body: unknown, status: number): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

export function validateSeedPayload(data: unknown): string | null {
  if (!data || typeof data !== "object") return "Payload must be an object";

  const payload = data as SeedPayload;
  if (!payload.business_name?.trim()) return "business_name is required";
  if (!payload.admin_id?.trim()) return "admin_id is required";
  if (payload.business_type !== undefined && !["product", "service", "consulting", "hybrid"].includes(payload.business_type)) return "business_type is invalid";
  if (payload.knowledge_status !== undefined && !["pending", "approved"].includes(payload.knowledge_status)) return "knowledge_status is invalid";
  if (payload.capabilities !== undefined && (typeof payload.capabilities !== "object" || Array.isArray(payload.capabilities))) return "capabilities must be an object";
  if (payload.admin_chat_id !== undefined && !Number.isInteger(payload.admin_chat_id)) return "admin_chat_id must be an integer";
  if (payload.products !== undefined && !Array.isArray(payload.products)) return "products must be an array";

  for (const product of payload.products || []) {
    if (!product || typeof product !== "object") return "each product must be an object";
    if (!product.name?.trim() || !product.stock?.trim() || !product.details?.trim() || !product.category?.trim()) {
      return "each product requires name, stock, details, and category";
    }
    if (!Number.isFinite(product.price) || product.price <= 0) return "each product price must be a positive number";
  }

  if (payload.payment_info !== undefined && (!payload.payment_info || !payload.payment_info.card_number?.trim() || !payload.payment_info.card_holder?.trim())) {
    return "payment_info requires card_number and card_holder";
  }

  return null;
}