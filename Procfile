web: daphne portfolio_backend.asgi:application --port $PORT --bind 0.0.0.0
release: python manage.py migrate && python manage.py collectstatic --noinput