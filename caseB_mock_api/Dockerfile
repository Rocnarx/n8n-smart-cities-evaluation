FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

ENV MIN_DELAY_MS=0
ENV MAX_DELAY_MS=0
ENV FAIL_RATE=0
ENV PORT=8002

EXPOSE 8002
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8002}"]
