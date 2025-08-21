FROM python:3.9

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    netcat-openbsd \
    gettext && \
    rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt requirements/base.txt requirements/
COPY requirements/production.txt ./requirements/

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements/production.txt
RUN pip install psycopg2-binary

# Copiar el proyecto
COPY . .

# Crear directorios necesarios
RUN mkdir -p /app/staticfiles
RUN mkdir -p /app/mediafiles

# Copiar el entrypoint
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]
