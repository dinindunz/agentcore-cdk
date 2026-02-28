# ==============================================================================
# Convenience Targets
# ==============================================================================

# Infrastructure tests
all-infrastructure-tests: test-infrastructure

# Manual tests
skill-tests: skill-issue-heat-map skill-portfolio-summary skill-repo-comparison skill-repo-hotness skill-trending-topic
iam-tests: iam-list-tools iam-search-tools iam-mcp-tests
jwt-tests: jwt-list-tools jwt-search-tools jwt-mcp-tests
all-manual-tests: skill-tests iam-tests jwt-tests

# All tests (infrastructure + manual)
all-tests: all-infrastructure-tests all-manual-tests
