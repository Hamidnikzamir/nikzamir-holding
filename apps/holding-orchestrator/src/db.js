/**
 * D1 Database operations for holding-orchestrator
 */

export async function logToD1(env, logEntry) {
  const { tenant_id, request, response, status, error_message, jarvis_payload, jarvis_response } = logEntry;
  
  try {
    const result = await env.DB.prepare(`
      INSERT INTO execution_logs (tenant_id, request, response, status, error_message, jarvis_payload, jarvis_response)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `).bind(
      tenant_id,
      request,
      response,
      status,
      error_message || null,
      jarvis_payload || null,
      jarvis_response || null
    ).run();

    return result.meta.last_row_id;
  } catch (error) {
    console.error('[holding-orchestrator] D1 log error:', error);
    throw error;
  }
}

export async function getTenant(env, tenantId) {
  try {
    const result = await env.DB.prepare(`
      SELECT * FROM tenants WHERE id = ?
    `).bind(tenantId).first();
    return result;
  } catch (error) {
    console.error('[holding-orchestrator] Get tenant error:', error);
    return null;
  }
}

export async function createTenant(env, tenantId, name, config = {}) {
  try {
    await env.DB.prepare(`
      INSERT OR REPLACE INTO tenants (id, name, config)
      VALUES (?, ?, ?)
    `).bind(tenantId, name, JSON.stringify(config)).run();
    return true;
  } catch (error) {
    console.error('[holding-orchestrator] Create tenant error:', error);
    return false;
  }
}

export async function getExecutionLogs(env, tenantId, limit = 50) {
  try {
    const result = await env.DB.prepare(`
      SELECT * FROM execution_logs 
      WHERE tenant_id = ? 
      ORDER BY created_at DESC 
      LIMIT ?
    `).bind(tenantId, limit).all();
    return result.results || [];
  } catch (error) {
    console.error('[holding-orchestrator] Get logs error:', error);
    return [];
  }
}

export async function storeRadarKnowledge(env, tenantId, vectorId, content, metadata = {}) {
  try {
    const result = await env.DB.prepare(`
      INSERT INTO radar_knowledge (tenant_id, vector_id, content, metadata)
      VALUES (?, ?, ?, ?)
    `).bind(tenantId, vectorId, content, JSON.stringify(metadata)).run();
    return result.meta.last_row_id;
  } catch (error) {
    console.error('[holding-orchestrator] Store radar knowledge error:', error);
    throw error;
  }
}

export async function searchRadarKnowledge(env, tenantId, vectorId) {
  try {
    const result = await env.DB.prepare(`
      SELECT * FROM radar_knowledge WHERE tenant_id = ? AND vector_id = ?
    `).bind(tenantId, vectorId).first();
    return result;
  } catch (error) {
    console.error('[holding-orchestrator] Search radar knowledge error:', error);
    return null;
  }
}