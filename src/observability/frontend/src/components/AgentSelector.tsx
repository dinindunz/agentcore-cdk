import { Select, SelectProps } from '@cloudscape-design/components';
import { Agent } from '../types/models';

interface AgentSelectorProps {
  agents: Agent[];
  selectedAgent: string | null;
  onChange: (logGroup: string | null) => void;
  loading?: boolean;
}

export default function AgentSelector({
  agents,
  selectedAgent,
  onChange,
  loading = false,
}: AgentSelectorProps) {
  const options: SelectProps.Option[] = agents.map((agent) => ({
    label: agent.name,
    value: agent.logGroup,
    description: agent.logGroup,
  }));

  const selectedOption =
    options.find((opt) => opt.value === selectedAgent) || null;

  return (
    <Select
      selectedOption={selectedOption}
      onChange={({ detail }) => {
        onChange(detail.selectedOption.value || null);
      }}
      options={options}
      placeholder="Select agent runtime..."
      statusType={loading ? 'loading' : 'finished'}
      loadingText="Loading agents..."
      empty="No agents found"
      filteringType="auto"
    />
  );
}
