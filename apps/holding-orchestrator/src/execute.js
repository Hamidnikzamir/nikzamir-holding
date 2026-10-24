import { logToD1 } from './db.js';
import { callJarvis } from './jarvis.js';
import { processWithAI } from './ai.js';

/**
 * Main execute handler
 * Receives: { tenant_id, request, context? }
 * Returns: { success, response, log_id }
 */
export async function handleExecute(request, env, ctx, corsHeaders) {
  const startTime = Date.now();
  let body = null;
  
  try {
    body = await request.json();
    const { tenant_id, request: userRequest, context = {} } = body;

    if (!tenant_id || !userRequest) {
      return new Response(JSON.stringify({ 
        error: 'Missing required fields: tenant_id, request' 
      }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    console.log(`[holding-orchestrator] Execute request from tenant: ${tenant_id}`);

    // Step 1: Process with local AI (Workers AI - Llama 3.3 70B)
    const aiResult = await processWithAI(env, userRequest, context);
    
    // Step 2: Call Jarvis (the master brain) for complex orchestration
    const jarvisResult = await callJarvis(env, {
      tenant_id,
      request: userRequest,
      ai_preprocessing: aiResult,
      context
    });

    // Step 3: Combine results
    const finalResponse = {
      ai_analysis: aiResult,
      jarvis_orchestration: jarvisResult,
      combined: jarvisResult?.response || aiResult?.response || 'No response generated'
    };

    // Step 4: Log to D1
    const logId = await logToD1(env, {
      tenant_id,
      request: userRequest,
      response: JSON.stringify(finalResponse),
      status: 'success',
      jarvis_payload: JSON.stringify({ tenant_id, request: userRequest, ai_preprocessing: aiResult, context }),
      jarvis_response: JSON.stringify(jarvisResult)
    });

    const duration = Date.now() - startTime;
    console.log(`[holding-orchestrator] Completed in ${duration}ms, log_id: ${logId}`);

    return new Response(JSON.stringify({
      success: true,
      response: finalResponse,
      log_id: logId,
      duration_ms: duration
    }), {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });

  } catch (error) {
    console.error('[holding-orchestrator] Execute error:', error);
    
    // Log error to D1
    await logToD1(env, {
      tenant_id: body?.tenant_id || 'unknown',
      request: body?.request || 'unknown',
      response: null,
      status: 'error',
      error_message: error.message
    });

    return new Response(JSON.stringify({ 
      success: false, 
      error: error.message 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
}