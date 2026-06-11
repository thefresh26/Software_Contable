#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py loaddata apps/contabilidad/fixtures/puc_colombia.json || true
python manage.py cargar_datos_prueba || true
