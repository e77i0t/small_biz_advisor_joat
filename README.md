# Small Business Communication Automation Platform

## Project Overview
This platform automates small business communications using an event-driven microservices architecture. It ingests SMS/calls, groups them into conversations, categorizes them with AI, detects spam, and automates responses. Each service is independently deployable and communicates via RabbitMQ events.

## Development Environment
All development and testing is done using Docker containers. Do not run code directly on your local machine.

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Visual Studio Code](https://code.visualstudio.com/) with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

### Getting Started
1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd small_biz_advisor
   ```
2. **Open in VS Code:**
   - Open the project folder in VS Code.
   - When prompted, reopen in the Dev Container, or use the Command Palette: `Dev Containers: Reopen in Container`.
3. **Start the development environment:**
   - The Dev Container will automatically build and start all services using `docker-compose.dev.yml`.
   - All services, RabbitMQ, Postgres, and Redis will be available.
4. **Accessing Services:**
   - Each service API is exposed on ports 8001-8008 (see `docker-compose.dev.yml`).
   - RabbitMQ Management UI: [http://localhost:15672](http://localhost:15672) (user: dev, pass: dev123)
   - Postgres: `localhost:5432` (user: dev, pass: dev123, db: comms_platform)
   - Redis: `localhost:6379`

### Environment Variables
- Each service has a `.env` file in its directory with required environment variables.
- Update API keys and secrets as needed for your environment.

### Running Tests
- Run tests for a service using Docker Compose, e.g.:
  ```bash
  docker-compose -f docker-compose.dev.yml run --rm twilio-monitor pytest
  ```
- Replace `twilio-monitor` with the desired service name.

### Adding Dependencies
- Add Python dependencies to the relevant `requirements.txt` in the service directory.
- Rebuild the service container:
  ```bash
  docker-compose -f docker-compose.dev.yml build <service-name>
  ```

## Architecture Principles
- Event-driven microservices
- API-first design with OpenAPI
- Type safety with Pydantic
- Shared contracts in `shared/`
- Dockerized development

---
For more details, see the project documentation and code comments.
