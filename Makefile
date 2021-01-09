#!make
.EXPORT_ALL_VARIABLES:

# Global variables
PYTHONPATH = $(PWD)
SHELL=/bin/bash
pyver = "3.8.0"
include .env

# Targets
activate: install
	@echo --- ACTIVATING PYTHON VENV ---
	@poetry shell

install:
	@echo --- INSTALLING ---
	@python -V
	@printf "${pyver}\n`python -V | cut -d" " -f2`" | sort -V | head -n1 | grep -q ${pyver} || echo "You need Python ${pyver} or newer"
	@poetry --version || pip3 install poetry
	@poetry install $$INSARGS

run: install
	@echo --- RUNNING FASTAPI ---
	@poetry run python3 src/main.py

test: install
	@printf "Is TESTMODE on? %s \n" "$(TESTMODE)"
	@echo --- RUN TESTING ---
	@poetry run pytest $$TESTARG