// ============================================================================
// Smart Assistant Module — DirectYar
// مسئول: جمع‌آوری اطلاعات از سایت/پیج/کانال، تشخیص Intent بدون کلیدواژه‌ی
// هاردکد (مبتنی بر LLM و چندزبانه)، و پاسخ‌دهی به‌عنوان متخصص همان کسب‌وکار،
// با یک حلقه‌ی یادگیری از فیدبک که رفتار عامل را بدون دیپلوی مجدد بهبود می‌دهد.
//
// یادداشت صادقانه‌ی معماری:
// Cloudflare Workers امکان fine-tune واقعی مدل را در لبه (edge) نمی‌دهد.
// معادل عملیِ «خودآموزی» که این ماژول پیاده می‌کند:
//   ۱) تشخیص intent صرفاً با استدلال معنایی مدل (بدون لیست کلیدواژه)،
//   ۲) ذخیره‌ی تصحیح‌های ادمین/کاربر در KV،
//   ۳) تزریق جدیدترین تصحیح‌ها به‌صورت few-shot در هر فراخوانی،
//   ۴) به‌روزرسانی خودکار «کارت دانش کسب‌وکار» از منابع متصل بدون کد نویسی مجدد.
// این یعنی رفتار عامل با گذشت زمان و بدون دست‌کاری کد، دقیق‌تر می‌شود.
// ============================================================================

export type Channel = "instagram" | "telegram" | "website";
export type BusinessType = "product" | "service" | "both";
export type Intent = "purchase" | "question" | "consultation" | "support";
export type AssistantMode = "basic" | "smart";

export interface SmartAssistantConfig {
  channels: Channel[];
  businessType: BusinessType;
  language: "fa" | "en" | "ar" | "auto";
  mode: AssistantMode;
  /** نام کسب‌وکار؛ برای ساخت persona تخصصی استفاده می‌شود */
  businessName: string;
  /** حوزه‌ی فعالیت به زبان خود کاربر، مثلا "مراقبت و احیای مو" */
  domain?: string;
}

export interface ConversationContext {
  userId: string;
  channel: Channel;
  userMessage: string;
  previousMessages: { role: "user" | "assistant"; content: string }[];
}

export interface ProductInfo {
  id: string;
  name: string;
  description: string;
  price: number;
  category: string;
  isSpecialized: boolean;
  requiredTools?: string[];
  inStock?: boolean;
}

/** یک آیتم دانش عمومی کسب‌وکار (از صفحات/پست‌ها/توضیحات) — برای رفتار متخصصانه لازم است */
export interface KnowledgeItem {
  title: string;
  content: string;
  sourceUrl?: string;
}

export interface BusinessKnowledge {
  sourceUrl: string;
  domain: string;
  syncedAt: string;
  summary: string; // خلاصه‌ای که مدل به‌عنوان "دانش متخصصانه" از آن استفاده می‌کند
  products: ProductInfo[];
  articles: KnowledgeItem[];
}

export interface IntentResult {
  intent: Intent;
  confidence: number; // 0..1
  language: string; // زبان تشخیص داده‌شده‌ی پیام کاربر (ISO یا نام رایج)
  reasoning: string;
}

export interface LearningExample {
  message: string;
  correctIntent: Intent;
  note?: string;
  createdAt: string;
}

export interface FollowUpDecision {
  needsClarification: boolean;
  clarifyingQuestion?: string;
  candidateProducts: ProductInfo[];
}

/** حداقل قرارداد لازم از Workers AI (env.AI.run) تا این ماژول به cloudflare:workers-types وابسته نباشد */
export interface AIRunner {
  run(model: string, input: Record<string, unknown>): Promise<{ response?: string }>;
}

/** حداقل قرارداد لازم از یک KV Namespace */
export interface KVLike {
  get(key: string, options?: { type: "json" | "text" }): Promise<any>;
  put(key: string, value: string, options?: { expirationTtl?: number }): Promise<void>;
}

const MODEL = "@cf/meta/llama-3.1-8b-instruct-fast";
const MAX_LEARNING_EXAMPLES = 40;

export class SmartAssistant {
  private config: SmartAssistantConfig;
  private ai: AIRunner;
  private kv: KVLike;
  private tenantId: string;

  constructor(config: SmartAssistantConfig, ai: AIRunner, kv: KVLike, tenantId: string) {
    this.config = config;
    this.ai = ai;
    this.kv = kv;
    this.tenantId = tenantId;
  }

  // --------------------------------------------------------------------
  // ۱) جمع‌آوری اطلاعات از سایت/پیج/کانال
  // --------------------------------------------------------------------

  /**
   * از منبع داده‌شده (سایت WooCommerce/Shopify، یا هر URL عمومی) اطلاعات را
   * جمع می‌کند، خلاصه‌ی "دانش تخصصی" کسب‌وکار را می‌سازد و در KV ذخیره می‌کند.
   * این خروجی همان چیزی است که persona متخصص عامل را می‌سازد.
   */
  async collectBusinessInfo(sourceUrl: string): Promise<BusinessKnowledge> {
    const origin = new URL(sourceUrl).origin;

    const [products, articles] = await Promise.all([
      this.tryFetchWooCommerceCatalog(origin),
      this.tryFetchGenericContent(origin),
    ]);

    const summary = await this.summarizeBusinessDomain(products, articles);

    const knowledge: BusinessKnowledge = {
      sourceUrl,
      domain: this.config.domain || summary.slice(0, 120),
      syncedAt: new Date().toISOString(),
      summary,
      products,
      articles,
    };

    await this.kv.put(
      `tenant:${this.tenantId}:knowledge`,
      JSON.stringify(knowledge),
      { expirationTtl: 60 * 60 * 24 } // هر ۲۴ ساعت رفرش می‌شود
    );

    return knowledge;
  }

  private async tryFetchWooCommerceCatalog(origin: string): Promise<ProductInfo[]> {
    try {
      const res = await fetch(`${origin}/wp-json/wc/store/v1/products?per_page=100`);
      if (!res.ok) return [];
      const raw: any[] = await res.json();
      return raw
        .map((p) => this.mapProduct(p))
        .filter((p): p is ProductInfo => p !== null);
    } catch {
      return [];
    }
  }

  private mapProduct(p: any): ProductInfo | null {
    const price = Number(p?.prices?.price);
    if (!p?.name?.trim() || !Number.isFinite(price) || price <= 0) return null;
    const description: string = stripHtml(p.short_description || p.description || "");
    return {
      id: String(p.id ?? p.slug ?? p.name),
      name: p.name.trim(),
      description: description.slice(0, 500),
      price,
      category: (p.categories || []).map((c: any) => c?.name).filter(Boolean).join(", "),
      isSpecialized: /(حرفه‌ای|سالن|professional|specialist)/i.test(description),
      inStock: Boolean(p.is_in_stock),
    };
  }

  private async tryFetchGenericContent(origin: string): Promise<KnowledgeItem[]> {
    try {
      const res = await fetch(`${origin}/wp-json/wp/v2/pages?per_page=30&_fields=title,content,link`);
      if (!res.ok) return [];
      const raw: any[] = await res.json();
      return raw.map((item) => ({
        title: stripHtml(item?.title?.rendered || ""),
        content: stripHtml(item?.content?.rendered || "").slice(0, 1000),
        sourceUrl: item?.link,
      }));
    } catch {
      return [];
    }
  }

  /** یک خلاصه‌ی "زبان متخصص" برای این کسب‌وکار می‌سازد — پایه‌ی persona عامل */
  private async summarizeBusinessDomain(products: ProductInfo[], articles: KnowledgeItem[]): Promise<string> {
    if (!products.length && !articles.length) {
      return this.config.domain || "کسب‌وکار متصل، اطلاعات کافی هنوز جمع‌آوری نشده است.";
    }
    const catalogPreview = products.slice(0, 30).map((p) => `${p.name} — ${p.category}`).join("\n");
    const articlePreview = articles.slice(0, 10).map((a) => a.title).join("\n");
    try {
      const out = await this.ai.run(MODEL, {
        messages: [
          {
            role: "system",
            content:
              "You are analyzing a business's product catalog and content titles to write a 2-3 sentence profile of what this business specializes in, written in the same language as the input. Be specific about the domain expertise implied (e.g. hair keratin treatments, not just 'beauty products'). Return only the profile text.",
          },
          { role: "user", content: `Products:\n${catalogPreview}\n\nContent:\n${articlePreview}` },
        ],
        max_tokens: 200,
        temperature: 0.2,
      });
      return (out.response || this.config.domain || "").trim();
    } catch {
      return this.config.domain || "";
    }
  }

  // --------------------------------------------------------------------
  // ۲) تشخیص Intent — چندزبانه، بدون کلیدواژه‌ی هاردکد
  // --------------------------------------------------------------------

  /**
   * intent را صرفاً با استدلال معنایی مدل تشخیص می‌دهد (نه regex/کلیدواژه).
   * به همین دلیل هر زبانی که کاربر بنویسد پشتیبانی می‌شود، بدون نیاز به
   * تعریف دستی کلیدواژه برای هر زبان.
   */
  async detectIntent(message: string): Promise<IntentResult> {
    const examples = await this.getRecentLearningExamples();
    const fewShot = examples
      .map((e) => `Message: "${e.message}" -> Intent: ${e.correctIntent}${e.note ? ` (${e.note})` : ""}`)
      .join("\n");

    try {
      const out = await this.ai.run(MODEL, {
        messages: [
          {
            role: "system",
            content:
              `You are a multilingual intent classifier for a business assistant. Detect the user's intent regardless of what language or dialect they write in. ` +
              `Classify into exactly one of: purchase, question, consultation, support. ` +
              `"purchase" = ready to buy / confirming an order. "question" = asking about price/availability/general info. ` +
              `"consultation" = needs expert guidance to pick the right option (describes a problem or need without naming a specific product). ` +
              `"support" = complaint, delivery/order problem, or wants to reach a human. ` +
              `Use these corrected examples from real conversations as guidance when relevant:\n${fewShot || "(none yet)"}\n\n` +
              `Return JSON only: {"intent": "...", "confidence": 0-1, "language": "...", "reasoning": "short"}`,
          },
          { role: "user", content: message },
        ],
        max_tokens: 200,
        temperature: 0,
      });

      const match = (out.response || "").match(/\{[\s\S]*\}/);
      if (!match) throw new Error("no json");
      const parsed = JSON.parse(match[0]);
      const intent: Intent = ["purchase", "question", "consultation", "support"].includes(parsed.intent)
        ? parsed.intent
        : "question";
      return {
        intent,
        confidence: typeof parsed.confidence === "number" ? parsed.confidence : 0.5,
        language: parsed.language || "unknown",
        reasoning: parsed.reasoning || "",
      };
    } catch {
      // شکست مدل هرگز نباید مکالمه را متوقف کند
      return { intent: "question", confidence: 0.2, language: "unknown", reasoning: "fallback" };
    }
  }

  // --------------------------------------------------------------------
  // ۳) حلقه‌ی یادگیری از فیدبک (جایگزین عملی «آموزش مداوم»)
  // --------------------------------------------------------------------

  /** وقتی ادمین یا کاربر تشخیص intent را تصحیح می‌کند، اینجا ثبت می‌شود */
  async recordCorrection(message: string, correctIntent: Intent, note?: string): Promise<void> {
    const key = `tenant:${this.tenantId}:learning`;
    const existing: LearningExample[] = (await this.kv.get(key, { type: "json" })) || [];
    const next = [...existing, { message, correctIntent, note, createdAt: new Date().toISOString() }].slice(
      -MAX_LEARNING_EXAMPLES
    );
    await this.kv.put(key, JSON.stringify(next));
  }

  private async getRecentLearningExamples(): Promise<LearningExample[]> {
    const key = `tenant:${this.tenantId}:learning`;
    const existing: LearningExample[] = (await this.kv.get(key, { type: "json" })) || [];
    return existing.slice(-12); // آخرین نمونه‌ها به‌عنوان few-shot، برای کنترل طول prompt
  }

  // --------------------------------------------------------------------
  // ۴) تصمیم به سؤال هدفمند یا معرفی محصول (رفتار "مشاور متخصص")
  // --------------------------------------------------------------------

  async decideFollowUp(context: ConversationContext, knowledge: BusinessKnowledge): Promise<FollowUpDecision> {
    const catalogPreview = knowledge.products
      .slice(0, 60)
      .map((p) => `- ${p.name} (${p.category}): ${p.description.slice(0, 100)}`)
      .join("\n");

    try {
      const out = await this.ai.run(MODEL, {
        messages: [
          {
            role: "system",
            content:
              `You are a domain expert for "${this.config.businessName}" (${knowledge.domain}). ` +
              `A customer described a need. If their need is too vague to recommend a specific product confidently ` +
              `(e.g. they mention a general problem but not its cause, severity, or context), ask ONE short clarifying ` +
              `question in the same language as the customer, like a real specialist would. ` +
              `If you already have enough to recommend, pick the most relevant products from the catalog. ` +
              `Catalog:\n${catalogPreview}\n\n` +
              `Return JSON only: {"needsClarification": bool, "clarifyingQuestion": "...", "productNames": string[]}`,
          },
          ...context.previousMessages.slice(-4).map((m) => ({ role: m.role, content: m.content })),
          { role: "user", content: context.userMessage },
        ],
        max_tokens: 250,
        temperature: 0.3,
      });
      const match = (out.response || "").match(/\{[\s\S]*\}/);
      const parsed = match ? JSON.parse(match[0]) : {};
      const names: string[] = Array.isArray(parsed.productNames) ? parsed.productNames : [];
      const candidateProducts = knowledge.products.filter((p) => names.includes(p.name));
      return {
        needsClarification: Boolean(parsed.needsClarification),
        clarifyingQuestion: parsed.clarifyingQuestion,
        candidateProducts,
      };
    } catch {
      return { needsClarification: false, candidateProducts: [] };
    }
  }

  // --------------------------------------------------------------------
  // ۵) تولید پاسخ نهایی — همیشه با persona متخصصِ همان کسب‌وکار
  // --------------------------------------------------------------------

  async generateResponse(context: ConversationContext, knowledge: BusinessKnowledge): Promise<string> {
    const intentResult = await this.detectIntent(context.userMessage);

    if (intentResult.intent === "support") {
      return this.buildHandoverMessage();
    }

    const followUp = await this.decideFollowUp(context, knowledge);
    if (followUp.needsClarification && followUp.clarifyingQuestion) {
      return followUp.clarifyingQuestion;
    }

    const productList = (followUp.candidateProducts.length ? followUp.candidateProducts : knowledge.products.slice(0, 20))
      .map((p) => `- ${p.name}: ${p.price.toLocaleString()} — ${p.description.slice(0, 120)}`)
      .join("\n");

    try {
      const out = await this.ai.run(MODEL, {
        messages: [
          { role: "system", content: this.buildExpertPersonaPrompt(knowledge) },
          { role: "user", content: `Catalog options:\n${productList}\n\nCustomer message: ${context.userMessage}` },
        ],
        max_tokens: 400,
        temperature: 0.4,
      });
      return (out.response || "").trim() || this.buildFallbackMessage();
    } catch {
      return this.buildFallbackMessage();
    }
  }

  /**
   * قانون ثابت: عامل همیشه باید مثل یک متخصص واقعی همان حوزه رفتار کند،
   * نه یک ربات عمومی که فقط از روی کاتالوگ می‌خواند.
   */
  private buildExpertPersonaPrompt(knowledge: BusinessKnowledge): string {
    return [
      `You are a genuine domain specialist working for "${this.config.businessName}".`,
      `Business profile (established from real business data — treat this as your area of expertise): ${knowledge.summary}`,
      `Rules:`,
      `- Speak like a real expert in this exact field, not a generic sales bot.`,
      `- Only recommend items from the provided catalog; never invent products or prices.`,
      `- Reply in the same language the customer used.`,
      `- Keep replies under 4 short sentences unless detail is explicitly requested.`,
      `- If information is insufficient, say so honestly instead of guessing.`,
    ].join("\n");
  }

  private buildHandoverMessage(): string {
    return "متوجه شدم — این مورد رو به یک نفر از تیم پشتیبانی منتقل می‌کنم تا دقیق‌تر بهتون کمک کنه.";
  }

  private buildFallbackMessage(): string {
    return "برای راهنمایی دقیق‌تر، لطفاً کمی بیشتر توضیح بدید تا بهترین گزینه رو پیشنهاد بدم.";
  }
}

function stripHtml(value: string): string {
  return value.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
}
