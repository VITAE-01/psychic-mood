FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# create non-root user
RUN useradd -m appuser

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

WORKDIR /app/frontend

RUN mkdir -p /app/frontend/static
RUN mkdir -p /app/data
RUN chown -R appuser:appuser /app

RUN python manage.py collectstatic --noinput

USER appuser

EXPOSE 8000

CMD ["gunicorn", "web.wsgi:application", "--bind", "0.0.0.0:8000"]