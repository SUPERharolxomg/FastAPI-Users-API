# FastAPI Users API
 
A production-ready RESTful API for user management built with FastAPI, SQLAlchemy, and PostgreSQL. Containerized with Docker for easy deployment.
 
## Features
 
- Full CRUD operations for user management
- Soft delete (logical deletion) instead of permanent removal
- Password hashing with bcrypt via Passlib
- Input validation with Pydantic schemas
- PostgreSQL with connection pooling and health checks
- Docker Compose setup (API + Database)
- Database isolated from external access
- Non-root container user for security
- Auto-generated Swagger documentation at `/docs`
- Health check endpoint for monitoring
## Tech Stack
 
| Layer | Technology |
|-------|-----------|
| Framework | FastAPI |
| ORM | SQLAlchemy |
| Validation | Pydantic |
| Database | PostgreSQL 15 |
| Security | Passlib + bcrypt |
| Container | Docker + Docker Compose |
| Server | Uvicorn |
 
## Project Structure
 
```
fastapi-users-api/
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI app initialization, CORS, lifespan
│   ├── database.py            # PostgreSQL connection, session management
│   ├── models/
│   │   └── user.py            # SQLAlchemy User model
│   ├── schemas/
│   │   └── user.py            # Pydantic schemas (Create, Update, Response)
│   ├── routes/
│   │   └── user.py            # CRUD endpoints
│   ├── utils/
│   │   └── security.py        # Password hashing and verification
│   └── tests/
│       └── test_user.py       # pytest test suite
├── migrations/                # Alembic (database migrations)
├── Dockerfile
├── docker-compose.yml
├── .env
├── .dockerignore
├── .gitignore
├── requirements.txt
└── README.md
```
 
## Getting Started
 
### Prerequisites
 
- Docker and Docker Compose installed
- Git
### Installation
 
```bash
# Clone the repository
git clone https://github.com/SUPERharolxomg/fastapi-users-api.git
cd fastapi-users-api
 
# Create your environment file
cp .env.example .env
 
# Start the containers
docker-compose up --build
```
 
The API will be available at `http://localhost:8000`
 
Swagger docs at `http://localhost:8000/docs`
 
### Environment Variables
 
Create a `.env` file in the root directory:
 
```env
POSTGRES_USER=admin
POSTGRES_PASSWORD=S3cur3P4ss!
POSTGRES_DB=users_db
SECRET_KEY=your_secret_key_here
```
 
## API Endpoints
 
| Method | Endpoint | Description | Status Code |
|--------|----------|-------------|-------------|
| GET | `/` | Health check | 200 |
| POST | `/users/` | Create a new user | 201 |
| GET | `/users/` | List active users (paginated) | 200 |
| GET | `/users/{id}` | Get user by ID | 200 |
| PATCH | `/users/{id}` | Partial update | 200 |
| DELETE | `/users/{id}` | Soft delete (deactivate) | 204 |
 
## Usage Examples
 
### Create a user
 
```bash
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Harold Garces",
    "email": "harold@example.com",
    "password": "Segura123!"
  }'
```
 
Response `201 Created`:
```json
{
  "id": 1,
  "name": "Harold Garces",
  "email": "harold@example.com",
  "is_active": true,
  "created_at": "2026-08-10T15:30:00Z",
  "updated_at": "2026-08-10T15:30:00Z"
}
```
 
### List active users
 
```bash
curl http://localhost:8000/users/?skip=0&limit=10
```
 
### Update a user
 
```bash
curl -X PATCH http://localhost:8000/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Harold David Garces"}'
```
 
### Soft delete a user
 
```bash
curl -X DELETE http://localhost:8000/users/1
```
 
## Design Decisions
 
**Soft Delete:** Users are never permanently removed. The `is_active` flag is set to `False`, preserving data integrity and enabling recovery. All GET queries filter by `is_active=True`.
 
**Password Security:** Passwords are hashed using bcrypt with automatic salt generation. The password field is excluded from all API responses.
 
**Connection Pooling:** SQLAlchemy is configured with `pool_size=10`, `max_overflow=20`, and `pool_pre_ping=True` for production-grade database connection management.
 
**Database Isolation:** PostgreSQL has no exposed ports in Docker Compose. It is only accessible within the internal Docker network, reducing the attack surface.
 
**Non-root Container:** The API runs under a dedicated `appuser` with no root privileges, following container security best practices.
 
**PATCH over PUT:** The update endpoint uses PATCH for partial updates, only modifying the fields sent in the request body via `model_dump(exclude_unset=True)`.
 
## Testing Strategy
 
Tests are organized in three categories:
 
**Happy Path:** Successful creation (201), retrieval (200), listing with pagination, partial update with `updated_at` verification, and soft delete (204).
 
**Error Cases:** Duplicate email (409 Conflict), non-existent user (404), inactive user returns 404, invalid payload (422 Unprocessable Entity).
 
**Edge Cases:** Invalid email format rejection, short password rejection, non-editable field injection via PATCH (email, created_at), and soft-deleted users excluded from listings.
 
### Running Tests
 
```bash
# Inside the container
docker-compose exec api pytest tests/ -v --cov=app
 
# Locally
pytest tests/ -v --cov=app
```
 
## Roadmap
 
- [ ] JWT authentication with login/logout
- [ ] Role-based access control (admin, user)
- [ ] Alembic migrations setup
- [ ] Rate limiting
- [ ] Logging with structured output
- [ ] CI/CD pipeline with GitHub Actions
## Author
 
**Harold David Garces Casas**
- [LinkedIn](https://www.linkedin.com/in/harold-david-garces-casas-003813264)
- [GitHub](https://github.com/SUPERharolxomg)
## License
 
This project is licensed under the MIT License.
