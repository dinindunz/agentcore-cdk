FROM public.ecr.aws/docker/library/python:3.12-slim
WORKDIR /app

# Copy shared utilities
COPY common/ /app/common/

# Copy agent service
COPY agent/ /app/

RUN pip install --no-cache-dir .

ENV DOCKER_CONTAINER=1
ENV PYTHONUNBUFFERED=1

RUN useradd -m -u 1000 bedrock_agentcore
USER bedrock_agentcore

EXPOSE 8080

CMD ["opentelemetry-instrument", "python", "-m", "main"]
