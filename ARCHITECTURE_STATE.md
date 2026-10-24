# ARCHITECTURE STATE REPORT – Holding Infrastructure (as of 2026‑10‑22)

---

## 1. Monorepo Structure (GitHub MCP)

| App (directory) | Entry‑point | Main dependencies (as declared in `package.json`) | Current status |
|---|---|---|---|
| **directyar‑worker** (`apps/directyar-worker`) | `src/index.ts` | `@sentry/cloudflare`, `@cloudflare/vitest‑plugin`, `vitest`, `typescript`, `wrangler` | Deployed (production) – last modification 2026‑10‑20 22:35 UTC |
| **holding‑core** (`apps/holding-core`) | `src/index.ts` | `@sentry/cloudflare` | Deployed (production) – last modification 2026‑09‑30 01:10 UTC |
| **sultan‑trust** (`apps/sultan-trust`) | `src/index.ts` | `@sentry/cloudflare` | Deployed (production) – last modification 2026‑10‑17 19:45 UTC |
| **quantum‑admin** (`apps/quantum-admin`) | `src/index.ts` | `@sentry/cloudflare`, `jest`, `ts‑jest`, `typescript`, `wrangler` | Deployed (production) – last modification 2026‑10‑20 11:03 UTC |
| **directyar‑tg** (`apps/directyar-tg`) | `src/index.js` | (no extra deps listed) | Deployed (production) – last modification 2026‑09‑19 21:26 UTC |
| **directyar‑api** (`apps/directyar-api`) | `src/index.ts` | (no extra deps listed) | Deployed (production) – last modification 2026‑09‑14 20:43 UTC |

*Root `package.json` does **not** declare a `workspaces` field, so the repository is not configured as a Yarn/NPM workspace monorepo. Dependencies are managed per‑app.*

---

## 2. Cloudflare Workers Status (Cloudflare MCP)

| Worker | URL (derived from service name) | Environment vars (names only) | Bindings (type → name / ID) | Last deployment (modified date) | Requests (last 24 h) |
|---|---|---|---|---|---|
| **holding‑core** | `https://holding-core.<account>.workers.dev` | `SENTRY_DSN` | • AI (`AI`)  <br>• Plain‑text `ADMIN_CHAT_ID`  <br>• Plain‑text `GROQ_KEY`  <br>• KV `HUB_STATE` (`namespace_id: 88191e99214e470d9dd005603c5c55d4`)  <br>• D1 `HQ_DB` (`id: 20efefb6-2db8-4fd1-b1b6-6230e42dea9f`)  <br>• Secret `HQ_INGEST_KEY`, `HQ_TG_SECRET`, `HQ_TG_TOKEN`  <br>• Plain‑text `OPENROUTER_KEY`, `PPLX_KEY` | 2026‑09‑30 01:10 UTC | *not available via MCP* |
| **directyar‑worker** | `https://directyar-worker.<account>.workers.dev` | `SENTRY_DSN` | • AI (`AI`)  <br>• KV `BOT_KV` (`namespace_id: 098fc3b1ffa8497487320afde0f4f993`)  <br>• KV `USERS_DB` (`namespace_id: 4301a6ec1aad4d75b05d282c38126ca6`)  <br>• Secret `SEED_SECRET`, `TELEGRAM_BOT_TOKEN`, `WC_CONSUMER_KEY`, `WC_CONSUMER_SECRET`, `WC_SITE_URL` | 2026‑10‑20 22:35 UTC | *not available via MCP* |
| **quantum‑admin** | `https://quantum-admin.<account>.workers.dev` | *(no `vars` block – only secrets via bindings)* | • AI (`AI`)  <br>• Assets (`ASSETS`)  <br>• KV `BOT_KV` (same ID as above)  <br>• D1 `DB` (`id: 20efefb6-2db8-4fd1-b1b6-6230e42dea9f`)  <br>• Vectorize `PRODUCTS_INDEX` (`index_name: products_index`)  <br>• Secret `WOOCOMMERCE_CONSUMER_KEY`, `WOOCOMMERCE_CONSUMER_SECRET`, `WOOCOMMERCE_STORE_URL` | 2026‑10‑20 11:03 UTC | *not available via MCP* |
| **sultan‑trust** | `https://sultan-trust.<account>.workers.dev` | `SENTRY_DSN` | • AI (`AI`)  <br>• Plain‑text `ASSETS_HTML_N` (value `4`)  <br>• Plain‑text `ASSETS_P00` (large CSS payload) | 2026‑10‑17 19:45 UTC | *not available via MCP* |
| **directyar‑tg** | `https://directyar-tg.<account>.workers.dev` | *(no `vars`)* | • AI (`AI`) | 2026‑09‑19 21:26 UTC | *not available via MCP* |
| **directyar‑api** | `https://directyar-api.<account>.workers.dev` | *(no `vars`)* | • AI (`AI`)  <br>• Assets (`ASSETS`) | 2026‑09‑14 20:43 UTC | *not available via MCP* |

*All workers use the same Cloudflare **account ID** `2a06db34b39e89c679ea1a88648f3d40`.*

---

## 3. Sentry Projects (Sentry MCP)

| Sentry project (derived from DSN) | Public DSN (full) | # issues | Environments |
|---|---|---|---|
| **holding‑core** | `https://0e272ff8933881f3a9a5925c09bdb82f@o4512295679819776.ingest.de.sentry.io/4512297391030352` | *MCP tool not available* | *unknown* |
| **directyar‑worker** | `https://5072667bc21b5a60c9a1172ce6912a2a@o4512295679819776.ingest.de.sentry.io/4512297377202256` | *MCP tool not available* | *unknown* |
| **sultan‑trust** | `https://32f3516020c9c672a2328bdb97999710@o4512295679819776.ingest.de.sentry.io/4512297386508368` | *MCP tool not available* | *unknown* |

The only data we can retrieve without a dedicated Sentry MCP tool are the DSNs embedded in each worker’s `wrangler.jsonc`. Issue counts and environment configuration could not be fetched.

---

## 4. KV Namespaces & D1 Databases (derived from Cloudflare bindings)

### KV Namespaces
| Namespace ID | Name (binding) | Workers that use it |
|---|---|---|
| `88191e99214e470d9dd005603c5c55d4` | `HUB_STATE` | `holding-core` |
| `098fc3b1ffa8497487320afde0f4f993` | `BOT_KV` | `directyar-worker`, `quantum-admin` |
| `4301a6ec1aad4d75b05d282c38126ca6` | `USERS_DB` | `directyar-worker` |

### D1 Databases
| D1 DB ID | Name (binding) | Workers that use it |
|---|---|---|
| `20efefb6-2db8-4fd1-b1b6-6230e42dea9f` | `HQ_DB` (holding‑core) / `DB` (quantum‑admin) | `holding-core`, `quantum-admin` |

### Vectorize Indexes
| Index name | Binding | Workers that use it |
|---|---|---|
| `products_index` | `PRODUCTS_INDEX` | `quantum-admin` |

---

## 5. Current Architecture Summary

| Area | Working / Deployed | Placeholder / Incomplete | Missing integrations |
|---|---|---|---|
| **Workers** | All six services listed above have a production deployment with recent `modified_on` timestamps. | – | – |
| **Bindings** | KV, D1, AI and Asset bindings are present and correctly attached to the corresponding workers. | – | No Redis‑like cache or additional Vectorize indexes besides `PRODUCTS_INDEX`. |
| **Sentry** | DSNs are set as env‑vars; error reporting is wired in each worker. | Issue counts & environment tags unknown (no Sentry MCP). | – |
| **Secrets** | Secrets are stored as `secret_text` bindings (Sentry DSN, various API keys). | Actual secret values not visible (by design). | No webhook / Telegram bot integration status exposed via MCP. |
| **GitHub repo** | `apps/` folder contains the four core workers and two auxiliary services. | No global workspace configuration in `package.json`. | – |

---

## 6. Critical Issues & Blockers

| Issue | Impact | Action needed (outside this report) |
|---|---|---|
| **Sentry MCP unavailable** – cannot retrieve issue counts or configured environments. | Monitoring visibility is unknown. | Use Sentry UI or request a Sentry MCP integration. |
| **Request‑count metrics unavailable** – Cloudflare MCP does not expose per‑worker request totals. | No data on traffic load; scaling decisions lack evidence. | Use Cloudflare Dashboard or enable Cloudflare Analytics via a separate API call (if permitted). |
| **No workspaces field in root `package.json`** – tools that rely on Yarn/NPM workspaces may mis‑behave. | Build scripts may need manual path handling. | Consider adding a `workspaces` array if monorepo tooling is desired. |
| **Secret values not retrievable** – by design, but some automation scripts may need to know which secret bindings exist. | May hinder CI setup. | Verify that CI pipelines reference the correct binding names (e.g., `SENTRY_DSN`). |
| **Potential duplicate bindings** – `BOT_KV` is shared between `directyar-worker` and `quantum-admin`. | Could cause unintended cross‑service data leakage if the KV namespace stores unrelated data. | Review the data stored in `BOT_KV`; consider splitting into service‑specific namespaces if isolation is required. |

*No immediate blocking errors were found in the deployed workers; all have recent deployment timestamps and their configuration files contain the expected Sentry DSNs and bindings.*

---

*This file should be reviewed and updated at least once a month to keep the architecture state current.*

## 7. Account Skills

The following account‑skill modules are installed in the Freebuff Desktop configuration. Keep this list up‑to‑date with any new skills you add.

| Skill | Path |
|---|---|
| accessibility | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\accessibility\\SKILL.md` |
| adversarial-fix | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\adversarial-fix\\SKILL.md` |
| agent-browser | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\agent-browser\\SKILL.md` |
| agent-reach | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\agent-reach\\SKILL.md` |
| architect | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\architect\\SKILL.md` |
| audit | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\audit\\SKILL.md` |
| azure-ai | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\azure-ai\\SKILL.md` |
| brainstorm | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\brainstorm\\SKILL.md` |
| brainstorming | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\brainstorming\\SKILL.md` |
| deploy-to-vercel | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\deploy-to-vercel\\SKILL.md` |
| excalidraw-diagram-generator | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\excalidraw-diagram-generator\\SKILL.md` |
| executing-plans | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\executing-plans\\SKILL.md` |
| extract-design-system | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\extract-design-system\\SKILL.md` |
| find-skills | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\find-skills\\SKILL.md` |
| finishing-a-development-branch | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\finishing-a-development-branch\\SKILL.md` |
| frontend-design | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\frontend-design\\SKILL.md` |
| git-commit | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\git-commit\\SKILL.md` |
| github-actions-docs | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\github-actions-docs\\SKILL.md` |
| image-to-code | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\image-to-code\\SKILL.md` |
| improve-codebase-architecture | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\improve-codebase-architecture\\SKILL.md` |
| mcp-builder | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\mcp-builder\\SKILL.md` |
| multi-stage-dockerfile | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\multi-stage-dockerfile\\SKILL.md` |
| performance | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\performance\\SKILL.md` |
| planning-with-files | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\planning-with-files\\SKILL.md` |
| receiving-code-review | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\receiving-code-review\\SKILL.md` |
| requesting-code-review | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\requesting-code-review\\SKILL.md` |
| security-review | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\security-review\\SKILL.md` |
| setup-pre-commit | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\setup-pre-commit\\SKILL.md` |
| shadcn-ui | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\shadcn-ui\\SKILL.md` |
| skill-creator | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\skill-creator\\SKILL.md` |
| spec-brainstorm | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\spec-brainstorm\\SKILL.md` |
| systematic-debugging | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\systematic-debugging\\SKILL.md` |
| tailwind-design-system | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\tailwind-design-system\\SKILL.md` |
| tdd | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\tdd\\SKILL.md` |
| test | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\test\\SKILL.md` |
| test-driven-development | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\test-driven-development\\SKILL.md` |
| typescript-advanced-types | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\typescript-advanced-types\\SKILL.md` |
| using-git-worktrees | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\using-git-worktrees\\SKILL.md` |
| vercel-composition-patterns | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\vercel-composition-patterns\\SKILL.md` |
| vercel-react-native-skills | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\vercel-react-native-skills\\SKILL.md` |
| vercel-react-view-transitions | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\vercel-react-view-transitions\\SKILL.md` |
| verification-before-completion | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\verification-before-completion\\SKILL.md` |
| web-design-guidelines | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\web-design-guidelines\\SKILL.md` |
| webapp-testing | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\webapp-testing\\SKILL.md` |
| writing-plans | `C:\\Users\\nikza\\.config\\freebuff-desktop\\account-skills\\c3c5dae81873c5d6b2086678671e07ef10e84da42a256ea071d216dcc2079f23\\f4c3ba52b9af4ab63e8d6194462ff25be4c3ec497db7096e172fa42324ed44dd\\writing-plans\\SKILL.md` |


