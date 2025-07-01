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
export CLOUD_STORAGE_EMULATOR_HOST
export DATABASE_URL
export ENV
export LANGCHAIN_ENDPOINT
export LANGSMITH_TRACING
export LANGSMITH_ENDPOINT
export LANGSMITH_API_KEY
export LANGSMITH_PROJECT
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
	@echo '  CLOUD_STORAGE_EMULATOR_HOST                Cloud Storage Emulator Host'
	@echo '  DATABASE_URL                               Database URL'
	@echo '  LANGCHAIN_ENDPOINT                         LangChain API Endpoint'
	@echo '  LANGSMITH_API_KEY                          LangSmith API Key'
	@echo '  LANGSMITH_ENDPOINT                         LangSmith API Endpoint'
	@echo '  LANGSMITH_PROJECT                          LangSmith Project'
	@echo '  LANGSMITH_TRACING                          LangSmith Tracing'

configure: ## Installs packages using poetry
	poetry install --no-root

docker.up: ## Starts the backend API within the shared network (see infra repository)
	docker compose up --build --pull always

lint: configure ## Runs linter
	poetry run mypy src --explicit-package-bases
	poetry run pre-commit run --all-files --show-diff-on-failure

run: configure ## Runs the backend API locally
	@echo "Running run in $(ENV) environment on port $(PORT)."
	poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port ${PORT}

update: ## Updates poetry packages
	poetry show --outdated
	poetry update
