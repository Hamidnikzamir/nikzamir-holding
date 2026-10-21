import {
	env,
	createExecutionContext,
	waitOnExecutionContext,
	SELF,
} from "cloudflare:test";
import { describe, it, expect } from "vitest";
import worker, { buildCatalogResponse, buildKnowledgeSnapshot, findProduct, isValidAddress, isValidCustomerName, isProductAvailable, mapWooCommerceProduct, normalizePhone, normalizePostalCode, validateSeedPayload } from "../src/index";

// For now, you'll need to do something like this to get a correctly-typed
// `Request` to pass to `worker.fetch()`.
const IncomingRequest = Request<unknown, IncomingRequestCfProperties>;

describe("DirectYar worker", () => {
	it("responds with the health message (unit style)", async () => {
		const request = new IncomingRequest("http://example.com");
		// Create an empty context to pass to `worker.fetch()`.
		const ctx = createExecutionContext();
		const response = await worker.fetch(request, env, ctx);
		// Wait for all `Promise`s passed to `ctx.waitUntil()` to settle before running test assertions
		await waitOnExecutionContext(ctx);
		expect(await response.text()).toMatchInlineSnapshot(`"✅ DirectYar Worker (Secure) is running!"`);
	});

	it("responds with the health message (integration style)", async () => {
		const response = await SELF.fetch("https://example.com");
		expect(await response.text()).toMatchInlineSnapshot(`"✅ DirectYar Worker (Secure) is running!"`);
	});

	it("does not select a product when the name is absent", () => {
		const product = { name: "پروتئین وی", price: 1200000, stock: "موجود", details: "", category: "" };
		expect(findProduct("ثبت سفارش", [product])).toBeNull();
	});

	it("finds products from natural short names", () => {
		const product = { name: "شامپو بیوکسین سبز ضد ریزش آرگان و کراتین", price: 855000, stock: "موجود", details: "", category: "" };
		expect(findProduct("بیوکسین سبز رو برام ثبت سفارش کن", [product])).toBe(product);
		expect(findProduct("شامپو دتاکس دگان پروهال", [{ name: "شامپو دتاکس دگان پروهال 1000 میل", price: 2450000, stock: "موجود", details: "", category: "" }])).not.toBeNull();
		expect(findProduct("شامپو دتاکس دگان پروهال داری", [{ name: "شامپو دتاکس دگان پروهال 1000 میل", price: 2450000, stock: "موجود", details: "", category: "" }])).not.toBeNull();
	});

	it("accepts only available products for invoicing", () => {
		expect(isProductAvailable({ name: "BCAA", price: 380000, stock: "ناموجود", details: "", category: "" })).toBe(false);
		expect(isProductAvailable({ name: "پروتئین وی", price: 1200000, stock: "موجود", details: "", category: "" })).toBe(true);
	});

	it("rejects incomplete seed data", () => {
		expect(validateSeedPayload({ business_name: "فروشگاه" })).toBe("admin_id is required");
		expect(validateSeedPayload({ business_name: "فروشگاه", admin_id: "admin", products: [{ name: "محصول", price: 0 }] })).toContain("each product requires");
		expect(validateSeedPayload({ business_name: "مشاوره", admin_id: "admin", business_type: "unknown" })).toBe("business_type is invalid");
		expect(validateSeedPayload({ business_name: "مشاوره", admin_id: "admin", business_type: "consulting", knowledge_status: "approved" })).toBeNull();
	});

	it("rejects seed requests without authorization", async () => {
		const request = new IncomingRequest("http://example.com/seed", {
			method: "POST",
			body: JSON.stringify({ business_name: "فروشگاه", admin_id: "admin" }),
			headers: { "Content-Type": "application/json" },
		});
		const ctx = createExecutionContext();
		const response = await worker.fetch(request, env, ctx);
		await waitOnExecutionContext(ctx);
		expect(response.status).toBe(401);
	});

	it("maps public WooCommerce products to the bot catalog format", () => {
		const product = mapWooCommerceProduct({
			name: "شامپو تست",
			permalink: "https://mrkeratine.ir/product/test/",
			short_description: "<p>برای موهای آسیب دیده</p>",
			prices: { price: "1250000" },
			is_in_stock: true,
			categories: [{ name: "شامپوها" }],
		});

		expect(product).toMatchObject({
			name: "شامپو تست",
			price: 1250000,
			stock: "موجود",
			category: "شامپوها",
			url: "https://mrkeratine.ir/product/test/",
		});
		expect(product?.details).toBe("برای موهای آسیب دیده");
	});

	it("answers catalog questions without calling AI", () => {
		const products = [
			{ name: "شامپو تست", price: 1250000, stock: "موجود", details: "برای موهای آسیب دیده", category: "شامپوها", brand: "بیوکسین" },
			{ name: "کراتین تست", price: 5000000, stock: "ناموجود", details: "برای موهای آسیب دیده", category: "کراتین", brand: "پروهال" },
		];

		expect(buildCatalogResponse("چه برندهایی موجود دارید", products)).toContain("بیوکسین");
		expect(buildCatalogResponse("برای موی آسیب دیده چی داری", products)).toContain("شامپو تست");
		expect(buildCatalogResponse("شامپو تست", products)).toContain("1,250,000");
		expect(buildCatalogResponse("خدمات مشاوره هم داری", products)).toContain("مراقبت و احیای مو");
		expect(buildCatalogResponse("پروتئین وی دارید؟", products)).toContain("بدنسازی یا مکمل");
		expect(buildCatalogResponse("همین فقط", products)).toContain("گزینه‌های بیشتر");
	});

	it("keeps order commands out of the catalog search", () => {
		const products = [
			{ name: "روغن آرگان اینوار", price: 907500, stock: "موجود", details: "", category: "روغنها" },
			{ name: "ماسک مو اینوار روغن آرگان", price: 3250000, stock: "موجود", details: "", category: "ماسک مو" },
			{ name: "کراتین تست", price: 5000000, stock: "موجود", details: "", category: "انواع کراتین مو" },
		];
		expect(findProduct("خود روغن آرگان", products)?.name).toBe("روغن آرگان اینوار");
		expect(findProduct("ثبت کن برام", products)).toBeNull();
		expect(buildCatalogResponse("میشه تو خونه از کراتین استفاده کنم", products)).toContain("مصرف حرفه‌ای");
	});

	it("validates customer identity and delivery details", () => {
		expect(isValidCustomerName("حمیدرضا نیک‌ضمیر")).toBe(true);
		expect(isValidCustomerName("سوسو")).toBe(false);
		expect(normalizePhone("09015050455")).toBe("+989015050455");
		expect(normalizePhone("+989015050455")).toBe("+989015050455");
		expect(normalizePhone("+14155552671")).toBe("+14155552671");
		expect(normalizePhone("021")).toBeNull();
		expect(isValidAddress("تهران، خیابان ولیعصر، کوچه سوم، پلاک ۱۲، واحد ۴")).toBe(true);
		expect(isValidAddress("نتسنش")).toBe(false);
		expect(normalizePostalCode("۱۳۱۲")).toBeNull();
		expect(normalizePostalCode("۱۲۳۴۵۶۷۸۹۰")).toBe("1234567890");
	});

	it("keeps product confirmations in the order flow", () => {
		const products = [{ name: "ماسک مکسی گلد", price: 3750000, stock: "موجود", details: "", category: "ماسک مو" }];
		expect(findProduct("میخوامش", products)).toBeNull();
		expect(buildCatalogResponse("ثبتش کن", products)).toBeNull();
	});

	it("uses the requested product type and tolerates small typos", () => {
		const products = [
			{ name: "کراتین مو مکسی گلد", price: 16585000, stock: "موجود", details: "", category: "انواع کراتین مو", brand: "مکسی" },
			{ name: "شامپو مکسی بوتاکس صورتی", price: 2980000, stock: "موجود", details: "", category: "شامپوها", brand: "مکسی" },
		];
		expect(findProduct("شامپو مکسی گاد", products)?.name).toBe("شامپو مکسی بوتاکس صورتی");
		expect(buildCatalogResponse("از برند مکسی چی دارید", products)).toContain("شامپو مکسی بوتاکس صورتی");
		expect(buildCatalogResponse("شامپو مکسی گلد", products)).toContain("شامپو مکسی بوتاکس صورتی");
	});

	it("builds a reviewable knowledge snapshot", () => {
		const snapshot = buildKnowledgeSnapshot("https://example.test", "woocommerce", [
			{ name: "محصول ۱", price: 100, stock: "موجود", details: "", category: "شامپوها, مراقبت مو", brand: "برند الف" },
			{ name: "محصول ۲", price: 200, stock: "موجود", details: "", category: "ماسک مو", brand: "برند الف" },
		], {
			pages: [{ title: { rendered: "راهنمای مشتری" }, content: { rendered: "<p>ارسال و مرجوعی</p>" } }],
			articles: [{ title: { rendered: "مقاله تخصصی" }, content: { rendered: "<p>مشاوره مو</p>" } }],
		});
		expect(snapshot).toMatchObject({
			source_url: "https://example.test",
			source_type: "woocommerce",
			products_count: 2,
			brands: ["برند الف"],
		});
		expect(snapshot.categories).toEqual(expect.arrayContaining(["ماسک مو", "مراقبت مو", "شامپوها"]));
		expect(snapshot.pages_count).toBe(1);
		expect(snapshot.articles_count).toBe(1);
		expect(snapshot.content_titles).toEqual(["راهنمای مشتری", "مقاله تخصصی"]);
		expect(snapshot.content_excerpt).toContain("ارسال و مرجوعی");
	});
});
