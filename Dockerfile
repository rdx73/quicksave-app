FROM python:3.10-slim-bookworm

# Install dependency sistem + NodeJS official
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    ca-certificates \
    gnupg \
 && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get install -y nodejs \
 && rm -rf /var/lib/apt/lists/*

# Pastikan node terbaca
RUN node -v && which node

WORKDIR /app

# User non-root
RUN useradd -m koyeb
ENV YTDLP_CACHE_DIR=/app/yt_cache
ENV PATH="/usr/bin:/usr/local/bin:$PATH"

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-cache solver yt-dlp (hindari JS challenge fail)
RUN mkdir -p $YTDLP_CACHE_DIR && \
    yt-dlp --cache-dir $YTDLP_CACHE_DIR \
    --extractor-args "youtube:js_runtime=node" \
    --version

# Copy project
COPY . .
RUN chown -R koyeb:koyeb /app && chmod -R 755 $YTDLP_CACHE_DIR

USER koyeb

# Port fleksibel (cloud friendly)
EXPOSE 8000
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT:-8000} app:app --timeout 120"]