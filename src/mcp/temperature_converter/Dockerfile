FROM public.ecr.aws/lambda/python:3.12

# Copy shared utilities
COPY common/ ${LAMBDA_TASK_ROOT}/common/

# Copy temperature converter service
COPY mcp/temperature_converter/main.py ${LAMBDA_TASK_ROOT}

CMD ["main.handler"]
