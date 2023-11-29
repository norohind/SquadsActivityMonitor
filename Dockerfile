FROM python:3.11-slim as builder
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt .
RUN apt update && apt install -y gcc media-types  # media-types for /etc/mime.types for static files
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN useradd --no-create-home --system user
WORKDIR /app
COPY --from=builder /etc/mime.types /etc/mime.types
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

RUN pip install --no-cache /wheels/*
USER user
COPY . .

ENTRYPOINT ["/app/entrypoint.sh"]

