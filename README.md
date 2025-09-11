# Videoflix Backend Setup Script (README as bash)

echo "Starting Videoflix backend setup..."

# 🚀 Clone the repository
git clone https://github.com/NoAltF4Dan/Videoflix_backend.git videoflix-backend
cd videoflix-backend

# 📝 Copy environment template
cp .env.template .env

# 🔑 Generate a secure Django SECRET_KEY and insert into .env
SECRET_KEY=$(docker compose run --rm web python -c \
"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
sed -i '' "s/SECRET_KEY=changeme/SECRET_KEY=$SECRET_KEY/" .env

# ⚠️ Example .env placeholders for other values
cat >> .env <<'EOF'
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=changeme
DJANGO_SUPERUSER_EMAIL=admin@example.com

DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:4200,http://127.0.0.1:4200

DB_NAME=videoflix
DB_USER=videouser
DB_PASSWORD=changeme
DB_HOST=db
DB_PORT=5432

REDIS_HOST=redis
REDIS_LOCATION=redis://redis:6379/1
REDIS_PORT=6379
REDIS_DB=0

EMAIL_HOST=mailhog
EMAIL_PORT=1025
EMAIL_HOST_USER=changeme
EMAIL_HOST_PASSWORD=changeme
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=default@example.com
EOF

# 🚀 Build and start containers
docker compose up --build -d

# 📦 Run database migrations
docker compose exec web python manage.py migrate

# 👤 Create a superuser (optional)
docker compose exec web python manage.py createsuperuser

# 🎨 Collect static files (optional)
docker compose exec web python manage.py collectstatic --noinput

# ✅ API is now available at:
#   http://localhost:8000/api/
#   MailHog UI: http://localhost:8025

# -------------------------
# 🔑 Example API requests
# -------------------------

# Register a user
curl -X POST http://localhost:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "supersecure123", "confirmed_password": "supersecure123"}'

# Login and save cookies
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "supersecure123"}' \
  -c cookies.txt

# Refresh token
curl -X POST http://localhost:8000/api/token/refresh/ \
  -b cookies.txt -c cookies.txt

# Fetch video list
curl -X GET http://localhost:8000/api/video/ -b cookies.txt

# -------------------------
# 🛑 Stop and clean up
# -------------------------
docker compose down -v --remove-orphans