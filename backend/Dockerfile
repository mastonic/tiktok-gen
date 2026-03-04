FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

# The command is overridden in docker-compose.yml
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
