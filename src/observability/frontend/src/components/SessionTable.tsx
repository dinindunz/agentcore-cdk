import {
  Table,
  Box,
  Header,
  Link,
} from '@cloudscape-design/components';
import { Session } from '../types/models';
import { useNavigate } from 'react-router-dom';

interface SessionTableProps {
  sessions: Session[];
  loading?: boolean;
}

export default function SessionTable({
  sessions,
  loading = false,
}: SessionTableProps) {
  const navigate = useNavigate();

  const formatDateTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleString('en-AU', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Flatten sessions to show traces
  const items = sessions.flatMap((session) =>
    session.traces.map((trace) => ({
      sessionId: session.sessionId,
      actorId: session.actorId,
      traceId: trace.traceId,
      startTime: trace.startTime,
      duration: trace.durationMs,
      llmCalls: trace.totalLlmCalls,
      toolCalls: trace.totalToolCalls,
      tokens: trace.totalInputTokens + trace.totalOutputTokens,
      userInput: trace.userInput,
    }))
  );

  return (
    <Table
      columnDefinitions={[
        {
          id: 'traceId',
          header: 'Trace ID',
          cell: (item) => (
            <Link onFollow={() => navigate(`/trace/${item.traceId}`)}>
              {item.traceId.substring(0, 16)}...
            </Link>
          ),
          sortingField: 'traceId',
        },
        {
          id: 'sessionId',
          header: 'Session ID',
          cell: (item) => item.sessionId.substring(0, 16) + '...',
          sortingField: 'sessionId',
        },
        {
          id: 'actorId',
          header: 'Actor ID',
          cell: (item) => item.actorId,
          sortingField: 'actorId',
        },
        {
          id: 'startTime',
          header: 'Time',
          cell: (item) => formatDateTime(item.startTime),
          sortingField: 'startTime',
        },
        {
          id: 'duration',
          header: 'Duration (ms)',
          cell: (item) => item.duration.toFixed(2),
          sortingField: 'duration',
        },
        {
          id: 'llmCalls',
          header: 'LLM Calls',
          cell: (item) => item.llmCalls,
          sortingField: 'llmCalls',
        },
        {
          id: 'toolCalls',
          header: 'Tool Calls',
          cell: (item) => item.toolCalls,
          sortingField: 'toolCalls',
        },
        {
          id: 'tokens',
          header: 'Tokens',
          cell: (item) => item.tokens.toLocaleString(),
          sortingField: 'tokens',
        },
        {
          id: 'userInput',
          header: 'User Input',
          cell: (item) =>
            item.userInput
              ? item.userInput.substring(0, 50) +
                (item.userInput.length > 50 ? '...' : '')
              : '-',
        },
      ]}
      items={items}
      loading={loading}
      loadingText="Loading traces..."
      empty={
        <Box textAlign="center" color="inherit">
          <b>No traces</b>
          <Box padding={{ bottom: 's' }} variant="p" color="inherit">
            No traces found for the selected time window.
          </Box>
        </Box>
      }
      header={
        <Header counter={`(${items.length})`}>
          Traces
        </Header>
      }
      sortingDescending
      variant="embedded"
    />
  );
}
