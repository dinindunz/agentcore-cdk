/**
 * TypeScript type definitions for observability dashboard.
 */

export interface Agent {
  name: string;
  logGroup: string;
  lastActivity: string; // ISO datetime string
}

export interface Span {
  spanId: string;
  traceId: string;
  parentSpanId: string | null;
  name: string;
  kind: string;
  startTime: number; // Nanoseconds
  endTime: number;
  durationMs: number;
  spanType: 'llm' | 'tool' | 'session' | 'other';

  // LLM attributes
  llmModel?: string;
  llmInputTokens?: number;
  llmOutputTokens?: number;
  llmTemperature?: number;

  // Tool attributes
  toolName?: string;
  toolInput?: unknown;
  toolOutput?: unknown;

  // Messages
  userMessage?: string;
  assistantMessage?: string;

  // Strands telemetry attributes
  triggerType?: 'user' | 'tool_result';
  finishReason?: 'end_turn' | 'tool_use';

  // Full attributes
  attributes: Record<string, unknown>;
  events: unknown[];
}

export interface Trace {
  traceId: string;
  sessionId: string;
  actorId: string;
  startTime: string; // ISO datetime string
  endTime: string;
  durationMs: number;

  totalLlmCalls: number;
  totalToolCalls: number;
  totalInputTokens: number;
  totalOutputTokens: number;
  totalCostUsd?: number;

  userInput?: string;
  assistantOutput?: string;

  spans: Span[];
}

export interface Session {
  sessionId: string;
  actorId: string;
  agentName: string;
  firstInteraction: string; // ISO datetime string
  lastInteraction: string;
  traceCount: number;
  totalLlmCalls: number;
  totalToolCalls: number;
  totalTokens: number;
  traces: Trace[];
}
