FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
    libgl1 cmake build-essential curl unzip \
    && rm -rf /var/lib/apt/lists/*

# Pre-descargar buffalo_s en el build (evita problemas de DNS en runtime)
RUN mkdir -p /root/.insightface/models/buffalo_s && \
    cd /tmp && \
    curl -L -o buffalo_s.zip \
      https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_s.zip && \
    unzip buffalo_s.zip -d /root/.insightface/models/buffalo_s && \
    rm buffalo_s.zip

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Script de arranque con DNS fix
RUN printf '#!/bin/bash\necho "nameserver 8.8.8.8" > /etc/resolv.conf\necho "nameserver 8.8.4.4" >> /etc/resolv.conf\necho "nameserver 1.1.1.1" >> /etc/resolv.conf\nexec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}\n' > /start.sh && \
    chmod +x /start.sh

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/api/health || exit 1

CMD ["/start.sh"]
