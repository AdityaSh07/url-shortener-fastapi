# URL Shortener API

A small, production-minded URL shortener built with FastAPI, asynchronous SQLAlchemy, and PostgreSQL. It accepts a destination URL, creates a short code, and redirects requests for that code to the original URL.

The project is designed to be easy to review: Docker Compose starts both the API and PostgreSQL with one command, and FastAPI's interactive documentation is available at `/docs`.

## Features

- Create shortened URLs through `POST /shorten`
- Redirect a short code through `GET /{short_code}`
- Validate submitted destination URLs
- Generate and persist short codes in PostgreSQL
- Handle short-code collisions safely with a database rollback and retry
- Health endpoint at `GET /health`
- Interactive OpenAPI/Swagger documentation at `/docs`
- Docker Compose setup with a PostgreSQL readiness check
- Configurable public `BASE_URL`

## Tech Stack

- **API:** FastAPI
- **Application server:** Uvicorn
- **Database access:** SQLAlchemy async
- **PostgreSQL driver:** asyncpg
- **Database:** PostgreSQL 16
- **Containers:** Docker and Docker Compose

## Architecture

```text
Browser / API client
        |
        | http://localhost:8000
        v
FastAPI container (port 8000)
        |
        | postgresql+asyncpg://...@db:5432/...
        v
PostgreSQL container (internal port 5432)
```

The API port is published to the host as `8000:8000`. PostgreSQL is intentionally not published to the host: the API reaches it over the Compose bridge network using the internal hostname `db` and port `5432`.

## Project Structure

```text
app/
├── api/
│   ├── __init__.py
│   └── routes.py            # Shortening and redirect endpoints
├── core/
│   ├── __init__.py
│   └── config.py            # Application configuration
├── database/
│   ├── __init__.py
│   └── database.py          # Async SQLAlchemy setup
├── models/
│   ├── __init__.py
│   └── url_model.py         # URL database model
├── services/
│   ├── __init__.py
│   └── url_service.py       # URL creation and collision handling
├── templates/
│   └── index.html           # Browser URL-shortening page
├── __init__.py
└── schema.py                # Request and response schemas

main.py                      # FastAPI application entry point
Dockerfile
docker-compose.yml
requirements.txt
.env.example
.dockerignore
.gitignore
README.md
```

## Configuration

Copy the example file before making local configuration changes:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

The relevant settings are:

| Variable | Purpose | Docker value / default |
| --- | --- | --- |
| `POSTGRES_USER` | PostgreSQL user | `postgres` |
| `POSTGRES_PASSWORD` | PostgreSQL password | Development value from `.env` or Compose default |
| `POSTGRES_DB` | PostgreSQL database name | `url_shortener` |
| `DATABASE_URL` | Async SQLAlchemy connection URL | Must use `db:5432` inside Docker |
| `BASE_URL` | Public URL used when returning short links | `http://localhost:8000` |

### Important: Docker host vs. local host

`DATABASE_URL` is environment-specific:

```env
# Docker Compose: the API reaches the database container by service name
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@db:5432/url_shortener

# Local, non-Docker development: the API reaches PostgreSQL on your machine
# DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/url_shortener
```

`BASE_URL` is different: it is the address sent to a browser or API client. For local Docker use, leave it as:

```env
BASE_URL=http://localhost:8000
```

For a real deployment behind a domain, set it to the public address, for example `https://short.example.com`.

> Do not commit `.env` if it contains non-demo credentials. Commit `.env.example` instead.

## Run with Docker Compose (Recommended)

### Prerequisites

- Docker Desktop (or Docker Engine with Docker Compose)

### Start the stack

```bash
docker compose up --build
```

Compose builds the API image, starts PostgreSQL 16, waits for `pg_isready` to report the database healthy, and then starts the API. The API container runs:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Open:

- URL shortener page: <http://localhost:8000/>
- API documentation: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>

To stop the stack:

```bash
docker compose down
```

### Docker notes

- The Compose network uses the `bridge` driver.
- The database health check runs `pg_isready` every five seconds, with a five-second timeout and five retries.
- PostgreSQL has no configured data volume in the current setup. Removing the database container removes its data; this is intentional for a simple, reproducible assessment environment.
- The database is reachable only inside the Compose network at `db:5432`.

## Run Locally Without Docker

### Prerequisites

- Python and the packages in `requirements.txt`
- A running PostgreSQL instance

### Steps

1. Create a PostgreSQL database and user, or use an existing local PostgreSQL user.

   ```sql
   CREATE DATABASE url_shortener;
   ```

2. Create `.env` from `.env.example` and set a **local** database URL:

   ```env
   DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/url_shortener
   BASE_URL=http://localhost:8000
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Start the API:

   ```bash
   uvicorn main:app --reload
   ```

5. Open <http://localhost:8000/>.

## API Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/shorten` | Validates a destination URL and creates a short URL. |
| `GET` | `/{short_code}` | Redirects to the destination associated with the short code. |
| `GET` | `/health` | Confirms that the application is running. |

The precise request schema and response model for `POST /shorten` are available from the running application at `/docs`. This keeps the README aligned with the actual OpenAPI contract rather than duplicating a request-field name here.

> **Swagger UI note:** `GET /{short_code}` redirects to an external destination. CORS is not configured for this project, so Swagger UI is not the appropriate place to verify that redirect. Copy or open the returned `short_url` directly in a browser instead.

## Example Usage

### Use the browser interface

Open <http://localhost:8000/>. The included `index.html` page provides a simple form for entering a destination URL and creating a short URL without using Swagger or a command-line client. Open the generated short URL to verify the redirect.

### Verify the service

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

### Create and use a short URL with Swagger

1. Open <http://localhost:8000/docs>.
2. Expand `POST /shorten`, choose **Try it out**, and submit a valid destination URL using the schema displayed there.
3. The response includes a generated `short_code` and a `short_url`, for example:

   ```json
   {
     "short_code": "adiX7kP2",
     "short_url": "http://localhost:8000/adiX7kP2"
   }
   ```

4. Copy the returned `short_url` and open it directly in a browser. The service redirects the request to the stored destination URL. Do not use Swagger UI to verify this redirect because CORS is not configured.

## Collision Handling

Short-code generation is designed for correctness under collisions:

1. The application generates a candidate code.
2. It attempts to store the code and destination in PostgreSQL.
3. If the database reports a uniqueness collision, the transaction is rolled back.
4. The application generates another candidate and retries.

Using PostgreSQL's uniqueness enforcement as the final authority prevents two records from being created with the same short code, including when requests arrive concurrently.

## Health Check

`GET /health` provides a simple liveness check for local testing, Docker verification, and deployment monitoring.

Docker Compose also checks PostgreSQL readiness before starting the API dependency chain:

```text
pg_isready -U <POSTGRES_USER> -d <POSTGRES_DB>
```

## Production Considerations

This repository configuration is optimized for development and assessment review. A public deployment should additionally consider:

- Use strong, externally managed secrets instead of demo database credentials.
- Add a persistent PostgreSQL volume or use a managed PostgreSQL service.
- Place the API behind a reverse proxy or load balancer with HTTPS/TLS.
- Set `BASE_URL` to the public HTTPS domain; no application code change is required for a domain change.
- Add rate limiting, abuse prevention, monitoring, structured logging, and alerting.
- Consider authentication or usage controls if the service is exposed publicly.
- Apply container hardening and pin images to immutable versions or digests as appropriate.
- Decide whether `/docs` should remain public or be restricted in a production environment.

## Future Improvements

- Custom aliases for short URLs
- Link expiration and deletion
- Click analytics
- User accounts and ownership of links
- Rate limiting and abuse reporting
- Automated tests and CI
- Database migrations
- Persistent storage and backup strategy

## Reviewer Quick Start

```bash
docker compose up --build
```

### Test the application

1. Open **<http://localhost:8000/>** in a browser.
2. Enter a destination URL in the URL-shortener form and submit it.
3. Open the generated short URL directly in the browser to confirm it redirects to the destination.

For the API contract and to test URL creation through the API interface, use <http://localhost:8000/docs>. Test redirects from the generated browser link rather than Swagger UI.
