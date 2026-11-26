FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OPENLEGAL_HTTP_HOST=0.0.0.0 \
    OPENLEGAL_HTTP_PORT=8765 \
    OPENLEGAL_PROFILE=router

RUN useradd --create-home --shell /usr/sbin/nologin --uid 10001 openlegal

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir . \
    && mkdir -p /home/openlegal/.openlegal \
    && chown -R openlegal:openlegal /home/openlegal /app

USER openlegal

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/health', timeout=3)"]

CMD ["openlegal-mcp-http", "--host", "0.0.0.0", "--port", "8765"]
