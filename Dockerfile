# Multi-stage build for production efficiency
FROM python:3.12-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.12-slim
WORKDIR /app

# Copy only the installed packages and code
COPY --from=builder /root/.local /root/.local

# Environment setup
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=.
ENV LANG=C.UTF-8
ENV PYTHONIOENCODING=utf-8

# Browser runtime for rendering Webook seat charts into Telegram images.
# Playwright's --with-deps currently asks Debian trixie for removed legacy font packages,
# so install the exact Chromium runtime libraries first.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libglib2.0-0 libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 \
        libcups2 libdrm2 libatspi2.0-0 libx11-6 libxcomposite1 libxdamage1 \
        libxext6 libxfixes3 libxrandr2 libgbm1 libxcb1 libxkbcommon0 \
        libpango-1.0-0 libcairo2 libasound2t64 fonts-unifont fonts-liberation \
    && rm -rf /var/lib/apt/lists/* \
    && python -m playwright install chromium

COPY . .

COPY clean_py.py /tmp/clean_py.py
RUN python /tmp/clean_py.py && rm /tmp/clean_py.py

# Expose API and Metrics ports
EXPOSE 8000
EXPOSE 8001

CMD ["python", "main.py"]
