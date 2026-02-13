FROM python:3.10-slim-bookworm

# 1. Install dependency sistem + Deno secara global (Sesuai saran Fin & Adifagos)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    ca-certificates \
    unzip \
 && curl -fsSL https://deno.land/x/install/install.sh | sh -s -- -d /usr/local/bin \
 && rm -rf /var/lib/apt/lists/*

# 2. Atur Environment Path agar Deno & Node terdeteksi semua user
ENV PATH="/usr/local/bin:/usr/bin:/bin:$PATH"

# 3. Berikan izin eksekusi eksplisit (Sesuai saran Fin)
RUN chmod +x /usr/local/bin/deno /usr/bin/ffmpeg

WORKDIR /app

# 4. Setup User & Cache
RUN useradd -m koyeb
ENV YTDLP_CACHE_DIR=/app/yt_cache
ENV YTDLP_JS_RUNTIME=deno

# 5. Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --upgrade yt-dlp-ejs==0.4.0

# 6. Copy project & Pindahkan kepemilikan ke user koyeb (Sesuai saran Fin)
COPY . .
RUN chown -R koyeb:koyeb /app && \
    mkdir -p $YTDLP_CACHE_DIR && \
    chown -R koyeb:koyeb $YTDLP_CACHE_DIR && \
    chmod -R 755 $YTDLP_CACHE_DIR

# 7. Pre-cache solver (dijalankan sebelum switch user untuk memastikan berhasil)
RUN yt-dlp --cache-dir $YTDLP_CACHE_DIR \
    --extractor-args "youtube:js_runtime=deno" \
    --version

USER koyeb

# Port fleksibel (cloud friendly)
EXPOSE 8000
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT:-8000} app:app --timeout 120"]
