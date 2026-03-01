import { useState } from 'react';
import { Box, Spinner } from '@cloudscape-design/components';
import { Session, Trace, Span } from '../types/models';

interface TraceTreeProps {
  sessions: Session[];
  loading?: boolean;
  onSpanSelect: (span: Span, trace: Trace) => void;
}

export default function TraceTree({
  sessions,
  loading = false,
  onSpanSelect,
}: TraceTreeProps) {
  const [expandedTraces, setExpandedTraces] = useState<Set<string>>(new Set());
  const [selectedSpanId, setSelectedSpanId] = useState<string | null>(null);

  const toggleTrace = (traceId: string) => {
    const newExpanded = new Set(expandedTraces);
    if (newExpanded.has(traceId)) {
      newExpanded.delete(traceId);
    } else {
      newExpanded.add(traceId);
    }
    setExpandedTraces(newExpanded);
  };

  const handleSpanClick = (span: Span, trace: Trace) => {
    setSelectedSpanId(span.spanId);
    onSpanSelect(span, trace);
  };

  const formatDateTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleString('en-AU', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getSpanLabel = (span: Span) => {
    // Labeling based on trigger type and finish reason
    // For strands.telemetry.tracer events
    if (span.triggerType && span.finishReason) {
      const trigger = span.triggerType === 'user' ? 'User' : 'Tool Result';

      if (span.finishReason === 'tool_use') {
        // LLM invoked a tool
        if (span.toolName) {
          return `Tool Call: ${span.toolName}`;
        }
        return `LLM Invoke: ${trigger} (Tool Call)`;
      } else if (span.finishReason === 'end_turn') {
        // LLM produced a response
        return `LLM Invoke: ${trigger}`;
      }
    }

    // Fallback to legacy logic for other span types
    switch (span.spanType) {
      case 'llm':
        if (span.userMessage) {
          return 'LLM Invoke: User';
        } else if (span.assistantMessage) {
          return 'LLM Invoke: Tool Result';
        }
        return 'LLM Invoke';

      case 'tool':
        if (span.toolName) {
          return `Tool Call: ${span.toolName}`;
        }
        return 'Tool Call';

      case 'session':
        // For session spans without trigger/finish data, use generic label
        return span.name || 'Session';

      default:
        // Fallback to span name
        return span.name || 'Unknown';
    }
  };

  if (loading) {
    return (
      <Box textAlign="center" padding="xxl">
        <Spinner size="large" />
        <Box variant="p" color="text-body-secondary">
          Loading traces...
        </Box>
      </Box>
    );
  }

  if (sessions.length === 0) {
    return (
      <Box textAlign="center" padding="xxl">
        <Box variant="p" color="text-body-secondary">
          No sessions found for the selected time window.
        </Box>
      </Box>
    );
  }

  return (
    <div style={{ maxHeight: '800px', overflowY: 'auto' }}>
      {sessions.map((session) => (
        <div key={session.sessionId} style={{ marginBottom: '16px' }}>
          {/* Session Header */}
          <div
            style={{
              padding: '8px 12px',
              backgroundColor: '#f2f3f3',
              borderLeft: '3px solid #0972d3',
              fontSize: '12px',
              fontWeight: 600,
              color: '#16191f',
              fontFamily: '"Amazon Ember", "Helvetica Neue", Roboto, Arial, sans-serif',
            }}
          >
            <div>{session.sessionId.substring(0, 24)}...</div>
            <div style={{ fontSize: '11px', color: '#5f6b7a', fontWeight: 400 }}>
              {formatDateTime(session.firstInteraction)} • {session.traceCount} trace
              {session.traceCount !== 1 ? 's' : ''}
            </div>
          </div>

          {/* Traces */}
          {session.traces.map((trace, idx) => (
            <div key={trace.traceId} style={{ marginLeft: '12px', marginTop: '4px' }}>
              {/* Trace Header */}
              <div
                onClick={() => toggleTrace(trace.traceId)}
                style={{
                  padding: '6px 8px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  fontWeight: 500,
                  color: '#16191f',
                  backgroundColor: expandedTraces.has(trace.traceId)
                    ? '#e3f2fd'
                    : 'transparent',
                  borderLeft: expandedTraces.has(trace.traceId)
                    ? '2px solid #0972d3'
                    : '2px solid transparent',
                  transition: 'all 0.2s',
                  fontFamily: '"Amazon Ember", "Helvetica Neue", Roboto, Arial, sans-serif',
                }}
                onMouseEnter={(e) => {
                  if (!expandedTraces.has(trace.traceId)) {
                    e.currentTarget.style.backgroundColor = '#fafafa';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!expandedTraces.has(trace.traceId)) {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }
                }}
              >
                <span style={{ marginRight: '8px' }}>
                  {expandedTraces.has(trace.traceId) ? '▼' : '▶'}
                </span>
                Trace {idx + 1}
                <span style={{ float: 'right', fontSize: '11px', color: '#5f6b7a' }}>
                  {trace.durationMs.toFixed(0)}ms
                </span>
              </div>

              {/* Spans (when expanded) */}
              {expandedTraces.has(trace.traceId) && (
                <div style={{ marginLeft: '20px' }}>
                  {trace.spans.map((span) => (
                    <div
                      key={span.spanId}
                      onClick={() => handleSpanClick(span, trace)}
                      style={{
                        padding: '4px 8px',
                        cursor: 'pointer',
                        fontSize: '12px',
                        color: '#16191f',
                        backgroundColor:
                          selectedSpanId === span.spanId ? '#e3f2fd' : 'transparent',
                        borderLeft:
                          selectedSpanId === span.spanId
                            ? '2px solid #0972d3'
                            : '2px solid transparent',
                        transition: 'all 0.2s',
                        fontFamily:
                          '"Amazon Ember", "Helvetica Neue", Roboto, Arial, sans-serif',
                      }}
                      onMouseEnter={(e) => {
                        if (selectedSpanId !== span.spanId) {
                          e.currentTarget.style.backgroundColor = '#fafafa';
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (selectedSpanId !== span.spanId) {
                          e.currentTarget.style.backgroundColor = 'transparent';
                        }
                      }}
                    >
                      {getSpanLabel(span)}
                      <span
                        style={{
                          float: 'right',
                          fontSize: '11px',
                          color: '#5f6b7a',
                          fontFamily: 'Monaco, "Courier New", monospace',
                        }}
                      >
                        {span.durationMs.toFixed(0)}ms
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
