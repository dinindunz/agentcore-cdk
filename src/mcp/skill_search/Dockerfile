FROM public.ecr.aws/lambda/python:3.12

# Copy shared utilities
COPY common/ ${LAMBDA_TASK_ROOT}/common/

# Copy skill search service
COPY mcp/skill_search/main.py ${LAMBDA_TASK_ROOT}

CMD ["main.handler"]
