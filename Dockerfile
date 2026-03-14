FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1 \
    APP_PORT=9097 \
    SESSION_BACKEND=redis

EXPOSE 9097

CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:9097", "app:app"]
