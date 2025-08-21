#!/bin/bash

# Esperar a que la base de datos esté disponible
if [ "$DATABASE" = "postgres" ]
then
    echo "Esperando a postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL iniciado"
fi

# Aplicar migraciones
python manage.py migrate

# Iniciar Gunicorn
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
