# Videoflix Backend

This is the backend for a Netflix clone, featuring user authentication and a video streaming API. Built with Django, PostgreSQL, and Redis, it provides a robust foundation for video streaming and user management.

---

## 🚀 Getting Started

### Prerequisites

Ensure the following tools are installed on your system:

- **Docker** (version 20.10 or higher) & **Docker Compose** (version 1.29 or higher)
- **Git** (version 2.30 or higher)

### Installation

1. **Clone the repository:**
   git clone https://github.com/your-username/videoflix-backend.git
   cd your videoflix folder

2. **Configure environment variables:**
   - Copy the template file: `cp .env.template .env`
   - Edit the `.env` file and replace the placeholder values with secure, unique secrets and credentials.

   **⚠️ Important:** The `SECRET_KEY` is critical for security. Generate a new one by running:
   docker compose exec web python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

   Example `.env` file content:
   # Example .env content
   DJANGO_SUPERUSER_USERNAME=admin
   DJANGO_SUPERUSER_PASSWORD=adminpassword
   DJANGO_SUPERUSER_EMAIL=admin@example.com

   SECRET_KEY=replace-with-your-django-secret-key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   CSRF_TRUSTED_ORIGINS=http://localhost:4200,http://127.0.0.1:4200

   DB_NAME=your_database_name
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password
   DB_HOST=db
   DB_PORT=5432

   REDIS_HOST=redis
   REDIS_LOCATION=redis://redis:6379/1
   REDIS_PORT=6379
   REDIS_DB=0

   EMAIL_HOST=mailhog
   EMAIL_PORT=1025
   EMAIL_HOST_USER=
   EMAIL_HOST_PASSWORD=
   EMAIL_USE_TLS=False
   EMAIL_USE_SSL=False
   DEFAULT_FROM_EMAIL=your-project@example.com

3. **Start the application:**
   docker compose up --build -d
   This builds the Docker images and starts the containers in the background.

4. **Run database migrations:**
   docker compose exec web python manage.py migrate

5. **(Optional) Create a superuser:**
   docker compose exec web python manage.py createsuperuser

6. **(Optional) Collect static files:**
   docker compose exec web python manage.py collectstatic

---

## 🔑 API Endpoints

All API endpoints are accessible via `http://localhost:8000/api/`.

### Authentication

| `Method` | `Endpoint` | `Description` |
|----------|------------|---------------|
| `POST` | `/register/` | User registration |
| `GET` | `/activate/<uidb64>/<token>/` | Account activation |
| `POST` | `/login/` | Logs in the user and sets JWT cookies |
| `POST` | `/logout/` | Logs out the user by deleting JWT cookies |
| `POST` | `/token/refresh/` | Refreshes the access token (cookie-based) |
| `POST` | `/password_reset/` | Initiates a password reset |
| `POST` | `/password_confirm/<uidb64>/<token>/` | Sets a new password |

### Video

| `Method` | `Endpoint` | `Description` |
|----------|------------|---------------|
| `GET` | `/video/` | Lists all available videos |
| `GET` | `/video/<movie_id>/<resolution>/index.m3u8` | HLS master playlist for a specific video |
| `GET` | `/video/<movie_id>/<resolution>/<segment>/` | Single HLS video segment |

**Note:** The video endpoints require a valid JWT access token, which is handled via cookies after login.

---

## 📝 Usage Examples

Here are some `cURL` examples to interact with the API.

### Authentication

* **Register User:**
   curl -X POST http://localhost:8000/api/register/ \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "password": "supersecure123", "confirmed_password": "supersecure123"}'

* **Login & Save Cookies:**
   curl -X POST http://localhost:8000/api/login/ \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "password": "supersecure123"}' \
     -c cookies.txt

* **Refresh Token:**
   curl -X POST http://localhost:8000/api/token/refresh/ \
     -b cookies.txt -c cookies.txt

### Video

* **Fetch Video List:**
   curl -X GET http://localhost:8000/api/video/ \
     -b cookies.txt

---

## 🛠️ Testing

For a smoother testing experience, we recommend using a tool like **Postman** or **Insomnia**. The authentication flow with cookies is straightforward to test with these tools.

* **Authentication Flow:**
    1. **Register:** `POST /api/register/`
    2. **Activate:** Follow the link from the email (e.g., in MailHog at `http://localhost:8025`).
    3. **Login:** `POST /api/login/` to receive cookies.
    4. **Token Refresh:** `POST /api/token/refresh/` to refresh the session.
    5. **Fetch Video:** `GET /api/video/` with the cookies attached.
    6. **Logout:** `POST /api/logout/` to end the session.

---

## 🛑 Stopping Containers

To stop and remove all containers, volumes, and networks created by `docker compose`, run:
   docker compose down -v --remove-orphans

---

## 📂 Project Structure & Notes

- `.env` file: Used to store sensitive information and is ignored by Git.
- `.gitignore`: Contains a list of files and folders that should not be committed to the repository, including `.env`, `media/`, and `*.sqlite3`.
- `requirements.txt`: Lists all Python dependencies for the project.
- **DEBUG**: The `DEBUG` setting should be `True` for development and `False` in production.

---

## 🛠️ Tech Stack

- **Django**: Web framework for the backend.
- **PostgreSQL**: Database for persistent storage.
- **Redis**: Caching and session management.
- **Docker**: Containerization for consistent deployment.
- **MailHog**: Local email testing server (accessible at `http://localhost:8025`).

---

## 📜 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## 🔧 Troubleshooting

- **Docker fails to start**: Check for port conflicts (e.g., ports 8000, 5432, 6379, or 8025).
- **Database connection errors**: Verify `DB_HOST`, `DB_USER`, and `DB_PASSWORD` in the `.env` file.
- **Email not received**: Ensure MailHog is running and accessible at `http://localhost:8025`.