TEST_PATH ?= .

# Override ENV to "test" only for the "test" target
ifneq ($(filter $(MAKECMDGOALS),test test.coverage),)
	ENV := test
endif

# Load specific dotenv files based on precedence
-include config/.env
-include config/.env.$(ENV)
-include config/.env.$(ENV).local

# Exported variables will be visible in external scripts
export DROPBOX_CLIENT_ID
export DROPBOX_CLIENT_SECRET
export OPENAI_API_KEY

default: help

help: ## Show this help message.
	@echo 'BookWith API'
	@echo
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m\033[0m\n"} /^[$$()% a-zA-Z_.-]+:.*?##/ { printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo
	@echo 'Common environment variables:'
	@echo
	@echo '  DROPBOX_CLIENT_ID                          Dropbox Client ID'
	@echo '  DROPBOX_CLIENT_SECRET                      Dropbox Client Secret'
	@echo '  OPENAI_API_KEY                             OpenAI API Key'
	@echo '  ENV                                        sets the environment. .env.${ENV} and .env.${ENV}.local will be automatically loaded.'
	@echo '  PORT                                       Run server on the specified port'

configure: ## Installs packages using poetry
	poetry install --no-root

docker.up: ## Starts the backend API within the shared network (see infra repository)
	docker compose up --build --pull always

lint: ## Runs linter
	poetry run mypy src --explicit-package-bases
	pre-commit run --all-files --show-diff-on-failure

run: configure ## Runs the backend API locally
	@echo "Running run in $(ENV) environment on port $(PORT)."
	poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port ${PORT}

update: ## Updates poetry packages
	poetry show --outdated
	poetry update
