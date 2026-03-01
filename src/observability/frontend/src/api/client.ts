/**
 * API client for observability dashboard backend.
 */

import { Agent, Session, Trace } from '../types/models';

const API_BASE = '/api';

/**
 * Fetch agents from backend.
 */
export async function fetchAgents(): Promise<Agent[]> {
  const response = await fetch(`${API_BASE}/agents`);

  if (!response.ok) {
    throw new Error(`Failed to fetch agents: ${response.statusText}`);
  }

  const data = await response.json();
  return data.agents;
}

/**
 * Fetch sessions for an agent.
 */
export async function fetchSessions(
  agentLogGroup: string,
  hours: number = 24,
  limit: number = 100
): Promise<Session[]> {
  const params = new URLSearchParams({
    agent: agentLogGroup,
    hours: hours.toString(),
    limit: limit.toString(),
  });

  const response = await fetch(`${API_BASE}/sessions?${params}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch sessions: ${response.statusText}`);
  }

  const data = await response.json();
  return data.sessions;
}

/**
 * Fetch trace details.
 */
export async function fetchTrace(traceId: string): Promise<Trace> {
  const response = await fetch(`${API_BASE}/traces/${traceId}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch trace: ${response.statusText}`);
  }

  const data = await response.json();
  return data.trace;
}

/**
 * Health check.
 */
export async function healthCheck(): Promise<{ status: string; region: string }> {
  const response = await fetch(`${API_BASE}/health`);

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.statusText}`);
  }

  return response.json();
}
