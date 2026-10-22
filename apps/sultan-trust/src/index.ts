/**
 * sultan-trust
 * Placeholder for the Sultan-Trust Cloudflare Worker.
 */
import * as Sentry from "@sentry/cloudflare";

export const handler = async (request: Request, env: any, ctx: ExecutionContext) => {
  if (env?.SENTRY_DSN) {
    Sentry.init({
      dsn: env.SENTRY_DSN,
      environment: "production",
      release: "nikzamir-holding@1.0.0",
    });
  }
  return new Response("Sultan-Trust worker placeholder", { status: 200 });
};
