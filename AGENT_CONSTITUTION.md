# AGENT_CONSTITUTION.md

## Universal Law of Harness & Loop Engineering

**Mandatory Law**: NO agent or project (current or future) is allowed to execute or return a final output without passing through a "Harness" (Automated Evaluation) and a "Loop" (Self-Correction) mechanism.

### The 3 Steps of the Loop
1. **Generate** - The agent produces its output
2. **Evaluate** - The Harness evaluates the output using Cloudflare Workers AI (`@cf/meta/llama-3.3-70b-instruct-fp8-fast`), scoring 0.0 to 1.0 based on agent-specific criteria
3. **Reflect & Retry** - If the score is < 0.8, a specific Reflection Prompt is generated and the task is retried. After max_retries (2) failures, the system logs `status: "harness_failed"` to D1 and returns the best attempt

### Mandatory Criteria by Agent Type
- **Trading agents** (e.g., `trader_daily`): Must contain valid price data and no hallucinated financial advice. **Stop-loss validation required.**
- **Content agents** (e.g., `leadrescue_daily`): Must contain professional outreach emails. **Tone validation required.**
- **SEO agents** (e.g., `seo_daily`): Must contain trending topics and valid keyword data.
- **Report agents** (e.g., `agencyreport_daily`): Must contain valid CSV report data and accurate financial summaries.
- **Template agents** (e.g., `templated_daily`): Must contain valid Notion template structure with proper formatting.

### BaseAgent Requirements
1. Every agent MUST inherit from `core/base_agent.py::BaseAgent`
2. Every agent MUST define a `criteria` class property with agent-specific evaluation criteria
3. The `execute()` method automatically wraps the core logic with `execute_with_self_correction`
4. The final payload sent to Cloudflare D1 `/api/logs` ALWAYS includes `harness_score` and `retries_used`
5. If the harness loop fails after max_retries, the system MUST NOT crash - it must log `status: "harness_failed"` to D1 and return the best attempt

### Rejection Rule
Any PR or new agent without `BaseAgent` inheritance will be rejected. The `criteria` class property is mandatory and must be a non-empty string.

### Zero Cost
The Harness evaluation uses the existing Cloudflare Workers AI binding (`@cf/meta/llama-3.3-70b-instruct-fp8-fast`). No external paid APIs are used.

***

**The Loop and Harness Engineering law is now universally enforced across the Nikzamir Holding. All current and future agents are bound by the BaseAgent class and this AGENT_CONSTITUTION.md.**