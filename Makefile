# Include .env file if it exists
ifneq (,$(wildcard ./.env))
    include .env
    export $(shell sed 's/=.*//' .env)
endif

.PHONY: run-loader run-generate-init test-env help

# Example target using environment variables
run-loader:
	python3 loader.py

run-generate-init:
	python3 generate_data.py init

# Print variables to verify they are loaded
test-env:
	@echo "Loaded variables from .env:"
	@env | grep -E '^($(shell sed 's/=.*//' .env | tr '\n' '|' | sed 's/|$$//'))'