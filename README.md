# README.md

# Videoflix Backend

This is the backend for a Netflix clone, including authentication and video API.

## Requirements

- Docker & Docker Compose installed
- Python 3.x (only for local tests without Docker)
- Git

## Setup

1. Clone the repository:

```bash
git clone <your-repo-url>
cd videoflix
```

2. Build and start Docker containers:

```bash
docker compose build
docker compose up -d
```

3. Apply migrations:

```bash
docker compose exec web python manage.py migrate
```

4. Optional: Create a superuser:

```bash
docker compose exec web python manage.py createsuperuser
```

5. Prepare media and static files (if needed):

```bash
docker compose exec web python manage.py collectstatic
```

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | `/api/register/` | User registration |
| GET    | `/api/activate/<uidb64>/<token>/` | Account activation |
| POST   | `/api/login/` | Login, returns JWT cookies |
| POST   | `/api/logout/` | Logout, deletes JWT cookies |
| POST   | `/api/token/refresh/` | Refresh access token (cookie-based) |
| POST   | `/api/password_reset/` | Reset password |
| POST   | `/api/password_confirm/<uidb64>/<token>/` | Set new password |

### Video

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/api/video/` | List all videos |
| GET    | `/api/video/<movie_id>/<resolution>/index.m3u8` | HLS master playlist for a video |
| GET    | `/api/video/<movie_id>/<resolution>/<segment>/` | Single HLS video segment |

**Note:** JWT access token is required for video endpoints.

## Example Requests

### Register User (cURL)

```bash
curl -X POST http://localhost:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "supersecure123", "confirmed_password": "supersecure123"}'
```

### Login (cURL)

```bash
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "supersecure123"}' \
  -c cookies.txt
```

### Refresh Token (cURL)

```bash
curl -X POST http://localhost:8000/api/token/refresh/ \
  -b cookies.txt -c cookies.txt
```

### Logout (cURL)

```bash
curl -X POST http://localhost:8000/api/logout/ \
  -b cookies.txt
```

### Fetch Video List (cURL)

```bash
curl -X GET http://localhost:8000/api/video/ \
  -b cookies.txt
```

### Fetch HLS Manifest (cURL)

```bash
curl -X GET http://localhost:8000/api/video/1/720p/index.m3u8 \
  -b cookies.txt
```

### Fetch HLS Video Segment (cURL)

```bash
curl -X GET http://localhost:8000/api/video/1/720p/000.ts \
  -b cookies.txt
```

## Testing / API Usage

- Use Postman or Insomnia to call the endpoints.
- Cookies are used for login/refresh – HTTP-only.
- Example Test Flow:
  1. Register → `/api/register/`
  2. Activate → Link from email (MailHog)
  3. Login → `/api/login/` → receive cookies
  4. Token Refresh → `/api/token/refresh/`
  5. Fetch Video → `/api/video/` → JWT in cookie
  6. Logout → `/api/logout/`

### Example Postman Tests

- **Auth Tests**
  - Login sets `access_token` and `refresh_token` cookies.
  - Logout blacklists refresh token and clears cookies.
- **Video Tests**
  - Fetch video list → status 200/404/403
  - Fetch HLS manifest → status 200/404/403/301
  - Fetch video segment → status 200/404/403/301

## Stop Containers

```bash
docker compose down
```

## Notes

- `media/` folder is ignored (not pushed to Git)
- `requirements.txt` contains all Python dependencies
- Use `.env` file for sensitive data (e.g., email settings)
- Debug mode: `DEBUG = True` in `settings.py` for development, `DEBUG = False` for production

# .gitignore

*.pyc
*.pyo
*.mo
__pycache__/
.env
media/
*.sqlite3
*.log
.DS_Store
.vscode/
.idea/
node_modules/
dist/
docker-compose.override.yml

# .dockerignore

*.pyc
*.pyo
*.mo
__pycache__/
.env
.git/
media/
*.sqlite3
*.log
.DS_Store
.vscode/
.idea/
node_modules/
dist/
docker-compose.override.yml

# requirements.txt

Django>=5.2
djangorestframework>=3.16
djangorestframework-simplejwt>=5.5
psycopg2-binary>=2.9
django-cors-headers>=4.0
