FROM public.ecr.aws/docker/library/python:3.12-slim
WORKDIR /app

COPY . .

RUN python -m pip install --no-cache-dir -r requirements.txt

ENV AWS_REGION=ap-southeast-2
ENV AWS_DEFAULT_REGION=ap-southeast-2
ENV DOCKER_CONTAINER=1
ENV PYTHONUNBUFFERED=1

RUN useradd -m -u 1000 bedrock_agentcore
USER bedrock_agentcore

EXPOSE 8080

CMD ["python", "server.py"]
