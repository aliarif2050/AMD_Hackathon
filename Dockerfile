FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements-image.txt .
RUN pip install --no-cache-dir -r requirements-image.txt

COPY app ./app

CMD ["python", "-m", "app.main"]
