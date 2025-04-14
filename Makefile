# Makefile for AoE2HD Parsing App

# 🛠️ DEV TASKS (Native)
dev: pg-start run

pg-start:
	@echo "🚀 Ensuring local PostgreSQL is running via Homebrew..."
	@brew services start postgresql@14 || true

run:
	@echo "🚀 Launching FastAPI locally with .env.dev ..."
	@ENV_FILE=.env.dev ./run_local.sh

pg-shell:
	psql -U aoe2user -d aoe2db

pg-reset:
	@echo "♻️ Dropping + recreating local DB..."
	dropdb aoe2db --if-exists -U aoe2user
	createdb aoe2db -U aoe2user

pg-stop:
	@echo "🛑 Stopping local PostgreSQL..."
	@brew services stop postgresql@14

# 🐳 DEV TASKS (Docker)
dev-up:
	@echo "🟢 Starting Docker DB/PGAdmin only..."
	docker compose up db pgadmin -d

dev-down:
	@echo "🛑 Stopping Docker Dev Environment..."
	docker compose down -v

dev-reset:
	@echo "♻️ Resetting Docker Dev DB..."
	docker compose down -v && docker compose up db pgadmin -d

# 🚀 PROD TASKS
prod-up:
	@echo "🚀 Starting Production Docker Environment..."
	docker compose -f docker-compose.prod.yml up -d --build

prod-down:
	@echo "🛑 Stopping Production..."
	docker compose -f docker-compose.prod.yml down -v

prod-rebuild:
	@echo "♻️ Rebuilding Production Environment..."
	docker compose -f docker-compose.prod.yml down -v
	docker system prune -af --volumes
	docker compose -f docker-compose.prod.yml up -d --build

# 🔍 UTILITIES
logs:
	docker compose logs -f

ps:
	docker compose ps

prune:
	docker system prune -af --volumes

frontend:
	cd ../aoe2hd-frontend && npm run dev

all:
	@echo "🚀 Launching FastAPI and Frontend..."
	(ENV_FILE=.env.dev ./run_local.sh &) && \
	cd ../aoe2hd-frontend && npm run dev

frontend-tab:
	osascript -e 'tell app "Terminal" to do script "cd ~/projects/aoe2hd-frontend && npm run dev"'

backend-tab:
	osascript -e 'tell app "Terminal" to do script "cd ~/projects/aoe2hd-parsing && ENV_FILE=.env.dev ./run_local.sh"'

