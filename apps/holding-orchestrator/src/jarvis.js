/**
 * Jarvis API Client - Calls the master brain at jarvis-command.rohanagent.workers.dev
 */

const JARVIS_BASE_URL = 'https://jarvis-command.rohanagent.workers.dev';

/**
 * Call Jarvis API for complex orchestration
 * Expected payload based on reverse-engineering:
 * {
 *   tenant_id: string,
 *   request: string,
 *   ai_preprocessing?: object,
 *   context?: object
 * }
 */
export async function callJarvis(env, payload) {
  try {
    console.log(`[holding-orchestrator] Calling Jarvis for tenant: ${payload.tenant_id}`);
    
    const response = await fetch(`${JARVIS_BASE_URL}/api/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.warn(`[holding-orchestrator] Jarvis returned ${response.status}: ${errorText}`);
      
      // If Jarvis is unavailable, return a structured error response
      return {
        success: false,
        error: `Jarvis API error: ${response.status}`,
        fallback: true,
        response: `Jarvis unavailable (${response.status}). Local AI processing used instead.`
      };
    }

    const data = await response.json();
    console.log(`[holding-orchestrator] Jarvis response received`);
    
    return {
      success: true,
      ...data
    };
  } catch (error) {
    console.error('[holding-orchestrator] Jarvis call failed:', error);
    return {
      success: false,
      error: error.message,
      fallback: true,
      response: `Jarvis connection failed: ${error.message}. Local AI processing used instead.`
    };
  }
}

/**
 * Health check for Jarvis
 */
export async function checkJarvisHealth() {
  try {
    const response = await fetch(`${JARVIS_BASE_URL}/api/health`, {
      method: 'GET'
    });
    return response.ok;
  } catch {
    return false;
  }
}