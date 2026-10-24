export async function handleHealth(request, env, corsHeaders) {
  return new Response(JSON.stringify({
    status: 'healthy',
    service: 'holding-orchestrator',
    timestamp: new Date().toISOString(),
    bindings: {
      ai: !!env.AI,
      db: !!env.DB,
      kv: !!env.STATE_KV,
      vectorize: !!env.RADAR_INDEX
    }
  }), {
    status: 200,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}