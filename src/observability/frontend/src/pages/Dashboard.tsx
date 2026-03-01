import { useState, useEffect } from 'react';
import {
  AppLayout,
  Container,
  Header,
  SpaceBetween,
  Select,
  SelectProps,
  Button,
  Alert,
} from '@cloudscape-design/components';
import { fetchAgents, fetchSessions } from '../api/client';
import { Agent, Session, Trace, Span } from '../types/models';
import TraceTree from '../components/TraceTree';
import SpanDetails from '../components/SpanDetails';

export default function Dashboard() {
  // State
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [hours, setHours] = useState<number>(24);
  const [loadingAgents, setLoadingAgents] = useState(false);
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedSpan, setSelectedSpan] = useState<Span | null>(null);
  const [selectedTrace, setSelectedTrace] = useState<Trace | null>(null);

  // Time window options
  const timeWindowOptions: SelectProps.Option[] = [
    { label: 'Last 1 Hour', value: '1' },
    { label: 'Last 6 Hours', value: '6' },
    { label: 'Last 24 Hours', value: '24' },
    { label: 'Last 48 Hours', value: '48' },
  ];

  const selectedTimeWindow =
    timeWindowOptions.find((opt) => opt.value === hours.toString()) ||
    timeWindowOptions[2];

  // Load agents on mount
  useEffect(() => {
    loadAgents();
  }, []);

  // Load sessions when agent or time window changes
  useEffect(() => {
    if (selectedAgent) {
      loadSessions();
    }
  }, [selectedAgent, hours]);

  const loadAgents = async () => {
    setLoadingAgents(true);
    setError(null);
    try {
      const data = await fetchAgents();
      setAgents(data);
    } catch (err) {
      setError(`Failed to load agents: ${err}`);
    } finally {
      setLoadingAgents(false);
    }
  };

  const loadSessions = async () => {
    if (!selectedAgent) return;

    setLoadingSessions(true);
    setError(null);
    setSessions([]);
    setSelectedSpan(null);
    setSelectedTrace(null);
    try {
      const data = await fetchSessions(selectedAgent, hours);
      setSessions(data);
    } catch (err) {
      setError(`Failed to load sessions: ${err}`);
    } finally {
      setLoadingSessions(false);
    }
  };

  const agentOptions: SelectProps.Option[] = agents.map((agent) => ({
    label: agent.name,
    value: agent.logGroup,
    description: agent.logGroup,
  }));

  const selectedAgentOption =
    agentOptions.find((opt) => opt.value === selectedAgent) || null;

  return (
    <AppLayout
      navigationHide
      toolsHide
      content={
        <SpaceBetween size="l">
          <Container
            header={
              <Header
                variant="h1"
                description="Monitor and analyse AgentCore agent executions"
              >
                AgentCore Observability
              </Header>
            }
          >
            <SpaceBetween size="m">
              {error && (
                <Alert type="error" dismissible onDismiss={() => setError(null)}>
                  {error}
                </Alert>
              )}

              <SpaceBetween size="s" direction="horizontal">
                <div style={{ width: '400px' }}>
                  <Select
                    selectedOption={selectedAgentOption}
                    onChange={({ detail }) => {
                      setSelectedAgent(detail.selectedOption.value || null);
                    }}
                    options={agentOptions}
                    placeholder="Select agent runtime..."
                    statusType={loadingAgents ? 'loading' : 'finished'}
                    loadingText="Loading agents..."
                    empty="No agents found"
                    filteringType="auto"
                  />
                </div>

                <Select
                  selectedOption={selectedTimeWindow}
                  onChange={({ detail }) => {
                    setHours(parseInt(detail.selectedOption.value || '24'));
                  }}
                  options={timeWindowOptions}
                />

                <Button
                  iconName="refresh"
                  onClick={() => {
                    loadAgents();
                    if (selectedAgent) {
                      loadSessions();
                    }
                  }}
                  loading={loadingAgents || loadingSessions}
                >
                  Refresh
                </Button>
              </SpaceBetween>
            </SpaceBetween>
          </Container>

          {selectedAgent && (
            <div style={{ display: 'grid', gridTemplateColumns: '400px 1fr', gap: '16px', minHeight: '600px' }}>
              {/* Left Panel - Tree View */}
              <Container
                header={
                  <Header
                    counter={`(${sessions.reduce((sum, s) => sum + s.traceCount, 0)} traces)`}
                  >
                    Sessions & Traces
                  </Header>
                }
              >
                <TraceTree
                  sessions={sessions}
                  loading={loadingSessions}
                  onSpanSelect={(span, trace) => {
                    setSelectedSpan(span);
                    setSelectedTrace(trace);
                  }}
                />
              </Container>

              {/* Right Panel - Span Details */}
              <Container>
                {selectedSpan && selectedTrace ? (
                  <SpanDetails span={selectedSpan} trace={selectedTrace} />
                ) : (
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      minHeight: '400px',
                      color: '#5f6b7a',
                    }}
                  >
                    Select a span to view details
                  </div>
                )}
              </Container>
            </div>
          )}
        </SpaceBetween>
      }
    />
  );
}
