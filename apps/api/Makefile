TEST_PATH ?= .

# Override ENV to "test" only for the "test" target
ifneq ($(filter $(MAKECMDGOALS),test test.coverage),)
	ENV := test
endif

# Load specific dotenv files based on precedence
-include src/config/.env
-include src/config/.env.$(ENV)
-include src/config/.env.$(ENV).local

# Exported variables will be visible in external scripts
export GCS_EMULATOR_HOST
export DATABASE_URL
export ENV
export GCP_PROJECT_ID
export GCS_BUCKET_NAME
export GEMINI_API_KEY
export LANGCHAIN_ENDPOINT
export LANGSMITH_API_KEY
export LANGSMITH_ENDPOINT
export LANGSMITH_PROJECT
export LANGSMITH_TRACING
export OPENAI_API_KEY
export PORT

default: help

help: ## Show this help message.
	@echo 'BookWith API'
	@echo
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m\033[0m\n"} /^[$$()% a-zA-Z_.-]+:.*?##/ { printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo
	@echo 'Common environment variables:'
	@echo
	@echo '  OPENAI_API_KEY                             OpenAI API Key'
	@echo '  ENV                                        sets the environment. .env.${ENV} and .env.${ENV}.local will be automatically loaded.'
	@echo '  PORT                                       Run server on the specified port'
	@echo '  GCS_EMULATOR_HOST                Cloud Storage Emulator Host'
	@echo '  DATABASE_URL                               Database URL'
	@echo '  LANGCHAIN_ENDPOINT                         LangChain API Endpoint'
	@echo '  LANGSMITH_API_KEY                          LangSmith API Key'
	@echo '  LANGSMITH_ENDPOINT                         LangSmith API Endpoint'
	@echo '  LANGSMITH_PROJECT                          LangSmith Project'
	@echo '  LANGSMITH_TRACING                          LangSmith Tracing'

configure: ## Installs packages using poetry
	poetry install --no-root

docker.up: ## Starts the backend API within the shared network (see infra repository)
	# Weaviate 匿名アクセスは dev のみ。本番派生時に変数を引きずらないよう Makefile 側で局所付与する。
	WEAVIATE_ANON_ACCESS=true docker compose up --build --pull always

lint: configure ## Runs linter
	poetry run mypy src --explicit-package-bases
	poetry run pre-commit run --all-files --show-diff-on-failure

lint.fix: configure ## Auto-fix lint errors (ruff)
	poetry run ruff check --fix --unsafe-fixes src tests
	poetry run ruff format src tests

## レビュー文書 04_infra_supply_chain.md の 4.4 に従い、既定は loopback バインド。
## 公衆 Wi-Fi で意図せず LAN 公開される事故（CORS は別防御で塞がれているが多層防御）を防ぐ。
HOST ?= 127.0.0.1

run: configure ## Runs the backend API locally (loopback only)
	@echo "Running run in $(ENV) environment on port $(PORT) (host=$(HOST))."
	poetry run uvicorn src.main:app --reload --host $(HOST) --port ${PORT}

run.lan: configure ## Runs the backend API on all interfaces (LAN). Use with care on trusted networks only.
	@echo "[warn] Binding to 0.0.0.0 — only use on trusted networks."
	poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port ${PORT}

update: ## Updates poetry packages
	poetry show --outdated
	poetry update

test: configure ## Runs pytest
	poetry run pytest $(TEST_PATH)

migrate: configure ## Apply Alembic migrations
	poetry run alembic upgrade head

migrate.gen: configure ## Generate a new Alembic migration (use MSG="describe change")
	poetry run alembic revision --autogenerate -m "$(MSG)"

secret-scan: ## Scan git history for leaked secrets (gitleaks + grep)
	bash $(CURDIR)/../../scripts/check-history-leaks.sh

audit: configure ## Run pip-audit for known CVEs
	poetry run pip-audit --strict --vulnerability-service osv || \
		echo "::warning::pip-audit reported vulnerabilities. Review the output above."
