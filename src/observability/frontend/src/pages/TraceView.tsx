import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Header,
  SpaceBetween,
  BreadcrumbGroup,
  Alert,
  Box,
  ColumnLayout,
  KeyValuePairs,
  Spinner,
} from '@cloudscape-design/components';
import { fetchTrace } from '../api/client';
import { Trace } from '../types/models';

export default function TraceView() {
  const { traceId } = useParams<{ traceId: string }>();
  const navigate = useNavigate();

  const [trace, setTrace] = useState<Trace | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (traceId) {
      loadTrace(traceId);
    }
  }, [traceId]);

  const loadTrace = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchTrace(id);
      setTrace(data);
    } catch (err) {
      setError(`Failed to load trace: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  const formatDateTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleString('en-AU', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  return (
    <SpaceBetween size="l">
      <BreadcrumbGroup
        items={[
          { text: 'Dashboard', href: '/' },
          { text: `Trace ${traceId}`, href: '#' },
        ]}
        onFollow={(e) => {
          e.preventDefault();
          if (e.detail.href === '/') {
            navigate('/');
          }
        }}
      />

      {error && (
        <Alert type="error" dismissible onDismiss={() => setError(null)}>
          {error}
        </Alert>
      )}

      {loading && (
        <Container>
          <Box textAlign="center" padding="xxl">
            <Spinner size="large" />
            <Box variant="p" color="text-body-secondary">
              Loading trace details...
            </Box>
          </Box>
        </Container>
      )}

      {!loading && trace && (
        <>
          <Container header={<Header variant="h2">Trace Summary</Header>}>
            <ColumnLayout columns={2} variant="text-grid">
              <KeyValuePairs
                columns={1}
                items={[
                  { label: 'Trace ID', value: trace.traceId },
                  { label: 'Session ID', value: trace.sessionId },
                  { label: 'Actor ID', value: trace.actorId },
                  { label: 'Start Time', value: formatDateTime(trace.startTime) },
                  { label: 'Duration', value: `${trace.durationMs.toFixed(2)}ms` },
                ]}
              />
              <KeyValuePairs
                columns={1}
                items={[
                  { label: 'LLM Calls', value: trace.totalLlmCalls },
                  { label: 'Tool Calls', value: trace.totalToolCalls },
                  { label: 'Input Tokens', value: trace.totalInputTokens.toLocaleString() },
                  { label: 'Output Tokens', value: trace.totalOutputTokens.toLocaleString() },
                  { label: 'Total Tokens', value: (trace.totalInputTokens + trace.totalOutputTokens).toLocaleString() },
                ]}
              />
            </ColumnLayout>
          </Container>

          {trace.userInput && (
            <Container header={<Header variant="h3">User Input</Header>}>
              <Box variant="code">{trace.userInput}</Box>
            </Container>
          )}

          {trace.assistantOutput && (
            <Container header={<Header variant="h3">Assistant Output</Header>}>
              <Box variant="code">{trace.assistantOutput}</Box>
            </Container>
          )}

          <Container header={<Header variant="h3">Spans ({trace.spans.length})</Header>}>
            <SpaceBetween size="m">
              {trace.spans.map((span) => (
                <Container key={span.spanId} header={<Header>{span.name}</Header>}>
                  <ColumnLayout columns={2} variant="text-grid">
                    <KeyValuePairs
                      columns={1}
                      items={[
                        { label: 'Span ID', value: span.spanId },
                        { label: 'Type', value: span.spanType },
                        { label: 'Duration', value: `${span.durationMs.toFixed(2)}ms` },
                      ]}
                    />
                    {span.spanType === 'llm' && (
                      <KeyValuePairs
                        columns={1}
                        items={[
                          { label: 'Model', value: span.llmModel || 'N/A' },
                          { label: 'Input Tokens', value: span.llmInputTokens || 0 },
                          { label: 'Output Tokens', value: span.llmOutputTokens || 0 },
                          { label: 'Temperature', value: span.llmTemperature || 'N/A' },
                        ]}
                      />
                    )}
                    {span.spanType === 'tool' && (
                      <KeyValuePairs
                        columns={1}
                        items={[
                          { label: 'Tool Name', value: span.toolName || 'N/A' },
                          { label: 'Input', value: JSON.stringify(span.toolInput, null, 2) },
                          { label: 'Output', value: JSON.stringify(span.toolOutput, null, 2) },
                        ]}
                      />
                    )}
                  </ColumnLayout>
                </Container>
              ))}
            </SpaceBetween>
          </Container>
        </>
      )}
    </SpaceBetween>
  );
}
