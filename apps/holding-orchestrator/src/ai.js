/**
 * Local AI Processing using Cloudflare Workers AI
 * Uses @cf/meta/llama-3.3-70b-instruct-fp8-fast model
 */

const AI_MODEL = '@cf/meta/llama-3.3-70b-instruct-fp8-fast';

/**
 * Process request with local AI
 */
export async function processWithAI(env, userRequest, context = {}) {
  if (!env.AI) {
    console.warn('[holding-orchestrator] AI binding not available');
    return {
      success: false,
      error: 'AI binding not configured',
      response: 'AI processing unavailable'
    };
  }

  try {
    console.log(`[holding-orchestrator] Processing with local AI: ${userRequest.substring(0, 100)}...`);

    // Build system prompt for the holding company context
    const systemPrompt = `You are the AI brain for Nikzamir Holding, a multi-tenant business automation platform. 
Analyze the user's request and provide:
1. A clear understanding of what they want
2. Suggested steps to accomplish it
3. Which systems/agents need to be involved (Woocommerce, Telegram, Social Media, Trading, etc.)
4. Any data requirements or prerequisites

Context: ${JSON.stringify(context)}

Respond in JSON format:
{
  "understanding": "What the user wants",
  "steps": ["step1", "step2", "step3"],
  "agents_needed": ["woocommere", "telegram", "instagram", "freqtrade"],
  "data_requirements": ["product_info", "credentials"],
  "response": "Human-readable summary for the user"
}`;

    const messages = [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userRequest }
    ];

    const response = await env.AI.run(AI_MODEL, { messages });
    
    let aiResponse = response.response || response.text || '';
    
    // Try to parse JSON from response
    let parsedResponse = null;
    try {
      // Extract JSON from response if wrapped in markdown or text
      const jsonMatch = aiResponse.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        parsedResponse = JSON.parse(jsonMatch[0]);
      }
    } catch (e) {
      console.warn('[holding-orchestrator] Could not parse AI response as JSON');
    }

    return {
      success: true,
      raw_response: aiResponse,
      parsed: parsedResponse,
      response: parsedResponse?.response || aiResponse,
      understanding: parsedResponse?.understanding || 'Request received',
      steps: parsedResponse?.steps || [],
      agents_needed: parsedResponse?.agents_needed || [],
      data_requirements: parsedResponse?.data_requirements || []
    };
  } catch (error) {
    console.error('[holding-orchestrator] AI processing error:', error);
    return {
      success: false,
      error: error.message,
      response: `AI processing failed: ${error.message}`
    };
  }
}

/**
 * Generate embeddings for Vectorize storage
 */
export async function generateEmbedding(env, text) {
  if (!env.AI) {
    return null;
  }

  try {
    const response = await env.AI.run('@cf/baai/bge-base-en-v1.5', { text });
    return response.data?.[0] || null;
  } catch (error) {
    console.error('[holding-orchestrator] Embedding generation error:', error);
    return null;
  }
}

/**
 * Analyze sentiment or categorize request
 */
export async function categorizeRequest(env, request) {
  if (!env.AI) return { category: 'general' };

  try {
    const response = await env.AI.run(AI_MODEL, {
      messages: [
        {
          role: 'system',
          content: 'Categorize this business request into one of: ecommerce, marketing, trading, operations, analytics, general. Respond with just the category name.'
        },
        { role: 'user', content: request }
      ]
    });
    return { category: (response.response || '').trim().toLowerCase() };
  } catch {
    return { category: 'general' };
  }
}