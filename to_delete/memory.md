Two patterns for tool loading
Pattern 1 — Small catalog (what we're doing now)


list_tools → load all N tools into agent context → agent picks directly
The agent sees all tools upfront. x_amz_bedrock_agentcore_search is just another tool in the list that the agent may or may not use.

Pattern 2 — Large catalog (search-first)


agent only has x_amz_bedrock_agentcore_search registered
  → agent calls it with natural language query
  → gateway's vector store returns ranked relevant tool definitions
  → agent then calls the specific tools it discovered
Instead of loading 1000 tools into the LLM context (which causes hallucinations and slow reasoning), the agent is only registered with the search tool. It discovers tools on-demand via semantic search, keeping the context window small.

Why pagination matters for large catalogs
The paginated list_tools example in the docs is for the alternative approach — enumerate everything once at startup. But x_amz_bedrock_agentcore_search replaces that for large catalogs entirely.

Implication for our stack
With only ~4 tools total across both gateways, we're correctly using Pattern 1 — load everything upfront. The x_amz_bedrock_agentcore_search being present is fine but won't be meaningfully exercised. It only becomes the critical tool when a gateway has tens or hundreds of targets, where fitting all tool descriptions into the LLM context window becomes a real problem.

x_amz_bedrock_agentcore_search — Summary
What it is: A built-in semantic search tool that AgentCore Gateway automatically injects into every gateway's MCP tool list. It's backed by a vector store scoped to that specific gateway.

How agents use it: Intended for large tool catalogs. Instead of loading all tools upfront, an agent can call x_amz_bedrock_agentcore_search with a natural-language query to discover which tools are relevant, then call those tools. This keeps the agent's context smaller when there are dozens or hundreds of tools.

Why we got a duplicate: We connect to two gateways simultaneously (JWT + IAM). Both inject their own x_amz_bedrock_agentcore_search tool. The strands registry rejected the second registration with a ValueError.

The fix: Deduplicate during tool list construction, keeping the JWT gateway's version:


_seen_tool_names: set[str] = set()
tools = []
for tool in jwt_client.list_tools_sync() + iam_client.list_tools_sync():
    if tool.tool_name not in _seen_tool_names:
        _seen_tool_names.add(tool.tool_name)
        tools.append(tool)
Trade-off accepted: The IAM gateway's calculator tools won't be semantically searchable via the deduplicated tool. This is acceptable because:

Our total catalog is tiny (~4 tools) — semantic search isn't meaningfully used anyway
No AWS documentation mandates "one gateway per agent"; multi-gateway is a valid pattern
Each gateway's search tool only covers its own vector store — there's no cross-gateway search regardless