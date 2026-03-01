import { useState } from 'react';
import {
  Tabs,
  Container,
  Header,
  SpaceBetween,
  Box,
  ColumnLayout,
  KeyValuePairs,
  Badge,
} from '@cloudscape-design/components';
import { Span, Trace } from '../types/models';

interface SpanDetailsProps {
  span: Span;
  trace: Trace;
}

export default function SpanDetails({ span, trace }: SpanDetailsProps) {
  const [activeTab, setActiveTab] = useState('details');

  // Extract messages from span or trace
  const messages: Array<{ role: string; content: string }> = [];

  // Add user input if exists
  if (span.userMessage) {
    messages.push({ role: 'user', content: span.userMessage });
  } else if (trace.userInput) {
    messages.push({ role: 'user', content: trace.userInput });
  }

  // Add tool call if this is a tool span
  if (span.spanType === 'tool' && span.toolName) {
    if (span.toolInput) {
      messages.push({
        role: 'tool_call',
        content: `Tool: ${span.toolName}\nArguments: ${JSON.stringify(span.toolInput, null, 2)}`,
      });
    }
    if (span.toolOutput) {
      messages.push({
        role: 'tool_result',
        content: JSON.stringify(span.toolOutput, null, 2),
      });
    }
  }

  // Add assistant output if exists
  if (span.assistantMessage) {
    messages.push({ role: 'assistant', content: span.assistantMessage });
  } else if (trace.assistantOutput && span.spanType === 'llm') {
    messages.push({ role: 'assistant', content: trace.assistantOutput });
  }

  const getRoleStyle = (role: string) => {
    const styles = {
      user: { bg: '#f2f8fd', border: '#0972d3', label: 'USER' },
      assistant: { bg: '#f2f8f4', border: '#037f0c', label: 'ASSISTANT' },
      tool_call: { bg: '#fffbf2', border: '#e07b00', label: 'TOOL CALL' },
      tool_result: { bg: '#fffbf2', border: '#e07b00', label: 'TOOL RESULT' },
      system: { bg: '#f2f3f3', border: '#5f6b7a', label: 'SYSTEM' },
    };
    return styles[role as keyof typeof styles] || styles.system;
  };

  return (
    <SpaceBetween size="l">
      <Header variant="h2">
        {span.name}
        <Box variant="small" color="text-body-secondary" margin={{ top: 'xxxs' }}>
          {span.spanId}
        </Box>
      </Header>

      <Tabs
        activeTabId={activeTab}
        onChange={({ detail }) => setActiveTab(detail.activeTabId)}
        tabs={[
          {
            id: 'details',
            label: 'Details',
            content: (
              <SpaceBetween size="l">
                {/* Basic Info */}
                <Container header={<Header variant="h3">Span Information</Header>}>
                  <ColumnLayout columns={2} variant="text-grid">
                    <div>
                      <KeyValuePairs
                        columns={1}
                        items={[
                          { label: 'Type', value: <Badge>{span.spanType.toUpperCase()}</Badge> },
                          { label: 'Duration', value: `${span.durationMs.toFixed(2)}ms` },
                          { label: 'Kind', value: span.kind },
                        ]}
                      />
                    </div>
                    <div>
                      <KeyValuePairs
                        columns={1}
                        items={[
                          { label: 'Trace ID', value: trace.traceId },
                          { label: 'Session ID', value: trace.sessionId },
                          { label: 'Actor ID', value: trace.actorId },
                        ]}
                      />
                    </div>
                  </ColumnLayout>
                </Container>

                {/* LLM Details */}
                {span.spanType === 'llm' && (
                  <Container header={<Header variant="h3">LLM Invocation</Header>}>
                    <ColumnLayout columns={2} variant="text-grid">
                      <KeyValuePairs
                        columns={1}
                        items={[
                          { label: 'Model', value: span.llmModel || 'N/A' },
                          { label: 'Temperature', value: span.llmTemperature?.toString() || 'N/A' },
                        ]}
                      />
                      <KeyValuePairs
                        columns={1}
                        items={[
                          { label: 'Input Tokens', value: (span.llmInputTokens || 0).toLocaleString() },
                          { label: 'Output Tokens', value: (span.llmOutputTokens || 0).toLocaleString() },
                          {
                            label: 'Total Tokens',
                            value: ((span.llmInputTokens || 0) + (span.llmOutputTokens || 0)).toLocaleString(),
                          },
                        ]}
                      />
                    </ColumnLayout>
                  </Container>
                )}

                {/* Tool Details */}
                {span.spanType === 'tool' && span.toolName && (
                  <Container header={<Header variant="h3">Tool Call</Header>}>
                    <SpaceBetween size="m">
                      <KeyValuePairs
                        columns={1}
                        items={[{ label: 'Tool Name', value: span.toolName }]}
                      />
                      {span.toolInput !== undefined && span.toolInput !== null && (
                        <div>
                          <Box variant="awsui-key-label">Arguments</Box>
                          <div
                            style={{
                              padding: '8px',
                              backgroundColor: '#1e1e1e',
                              borderRadius: '4px',
                              overflow: 'auto',
                            }}
                          >
                            <pre
                              style={{
                                margin: 0,
                                whiteSpace: 'pre-wrap',
                                fontFamily: 'Monaco, "Courier New", monospace',
                                fontSize: '12px',
                                color: '#d4d4d4',
                              }}
                            >
                              {JSON.stringify(span.toolInput, null, 2)}
                            </pre>
                          </div>
                        </div>
                      )}
                      {span.toolOutput !== undefined && span.toolOutput !== null && (
                        <div>
                          <Box variant="awsui-key-label">Result</Box>
                          <div
                            style={{
                              padding: '8px',
                              backgroundColor: '#1e1e1e',
                              borderRadius: '4px',
                              overflow: 'auto',
                            }}
                          >
                            <pre
                              style={{
                                margin: 0,
                                whiteSpace: 'pre-wrap',
                                fontFamily: 'Monaco, "Courier New", monospace',
                                fontSize: '12px',
                                color: '#d4d4d4',
                              }}
                            >
                              {JSON.stringify(span.toolOutput, null, 2)}
                            </pre>
                          </div>
                        </div>
                      )}
                    </SpaceBetween>
                  </Container>
                )}

                {/* Messages */}
                {messages.length > 0 && (
                  <Container header={<Header variant="h3">Messages</Header>}>
                    <SpaceBetween size="s">
                      {messages.map((msg, idx) => {
                        const style = getRoleStyle(msg.role);
                        // Extract tool name for tool_result display
                        let label = style.label;
                        if (msg.role === 'tool_result' && span.toolName) {
                          label = `TOOL RESULT: ${span.toolName}`;
                        } else if (msg.role === 'tool_call' && span.toolName) {
                          label = `TOOL CALL: ${span.toolName}`;
                        }

                        return (
                          <div
                            key={idx}
                            style={{
                              marginBottom: '12px',
                              padding: '12px 16px',
                              backgroundColor: style.bg,
                              borderLeft: `4px solid ${style.border}`,
                              borderRadius: '2px',
                              fontFamily: '"Amazon Ember", "Helvetica Neue", Roboto, Arial, sans-serif',
                            }}
                          >
                            <div
                              style={{
                                fontWeight: 700,
                                fontSize: '12px',
                                color: '#16191f',
                                marginBottom: '8px',
                                letterSpacing: '0.5px',
                              }}
                            >
                              {label}
                            </div>
                            <div
                              style={{
                                fontSize: '13px',
                                fontFamily: '"Amazon Ember", "Helvetica Neue", Roboto, Arial, sans-serif',
                                color: '#16191f',
                                lineHeight: '1.6',
                                whiteSpace: 'pre-wrap',
                                wordBreak: 'break-word',
                              }}
                            >
                              {msg.content}
                            </div>
                          </div>
                        );
                      })}
                    </SpaceBetween>
                  </Container>
                )}
              </SpaceBetween>
            ),
          },
          {
            id: 'metadata',
            label: 'Metadata',
            content: (
              <Container>
                <SpaceBetween size="m">
                  <KeyValuePairs
                    columns={2}
                    items={[
                      { label: 'Span ID', value: span.spanId },
                      { label: 'Trace ID', value: span.traceId },
                      { label: 'Parent Span ID', value: span.parentSpanId || 'N/A' },
                      { label: 'Name', value: span.name },
                      { label: 'Kind', value: span.kind },
                      { label: 'Type', value: span.spanType },
                      { label: 'Start Time', value: new Date(span.startTime / 1_000_000).toISOString() },
                      { label: 'End Time', value: new Date(span.endTime / 1_000_000).toISOString() },
                      { label: 'Duration (ms)', value: span.durationMs.toFixed(2) },
                    ]}
                  />
                </SpaceBetween>
              </Container>
            ),
          },
          {
            id: 'raw',
            label: 'Raw',
            content: (
              <Container>
                <div
                  style={{
                    padding: '12px',
                    backgroundColor: '#1e1e1e',
                    borderRadius: '4px',
                    overflow: 'auto',
                    maxHeight: '600px',
                  }}
                >
                  <pre
                    style={{
                      margin: 0,
                      whiteSpace: 'pre-wrap',
                      fontFamily: 'Monaco, "Courier New", monospace',
                      fontSize: '12px',
                      color: '#d4d4d4',
                    }}
                  >
                    {JSON.stringify(
                      {
                        span,
                        trace: {
                          traceId: trace.traceId,
                          sessionId: trace.sessionId,
                          actorId: trace.actorId,
                          durationMs: trace.durationMs,
                        },
                      },
                      null,
                      2
                    )}
                  </pre>
                </div>
              </Container>
            ),
          },
        ]}
      />
    </SpaceBetween>
  );
}
