# README.md

# Videoflix Backend

This is the backend for a Netflix clone, including authentication and video API.

## Requirements

- Docker & Docker Compose installed
- Python 3.x (only for local tests without Docker)
- Git

## Setup

1. Clone the repository:

git clone <your-repo-url>
cd videoflix

2. Build and start Docker containers:

docker compose build
docker compose up -d

3. Apply migrations:

docker compose exec web python manage.py migrate

4. Optional: Create a superuser:

docker compose exec web python manage.py createsuperuser

5. Prepare media and static files (if needed):

docker compose exec web python manage.py collectstatic

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

## Testing / API Usage

- Use Postman or Insomnia to call the endpoints.
- Cookies are used for login/refresh – HTTP-only.

### Example Postman Flow

1. **Register** → `/api/register/` → Email + Password  
2. **Activate** → Link from email (MailHog)  
3. **Login** → `/api/login/` → Receive cookies (`access_token` & `refresh_token`)  
4. **Token Refresh** → `/api/token/refresh/` → Renew access token  
5. **Fetch Video** → `/api/video/` → Use JWT in cookie  
6. **Logout** → `/api/logout/` → Cookies deleted  

## Stopping the Containers

docker compose down

## Notes

- `media/` folder is ignored (not pushed to Git)  
- `requirements.txt` contains all Python dependencies  
- Use a `.env` file for sensitive data (e.g., email settings)  
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
