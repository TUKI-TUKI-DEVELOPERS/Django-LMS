#!/bin/bash

# Esperar a que PostgreSQL esté disponible
echo "Esperando a PostgreSQL..."
while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
    sleep 0.1
done
echo "PostgreSQL iniciado"

# Aplicar migraciones
python manage.py migrate

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Iniciar Gunicorn
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
