FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# gRPC files are pre-generated, no need to regenerate

EXPOSE 8000 50051
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 & python -m app.grpc.server"]

