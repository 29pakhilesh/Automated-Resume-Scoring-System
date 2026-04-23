# Resume Scoring System — monorepo layout
#
#   backend/              FastAPI application (import app from here; cwd for `make dev`)
#   backend/requirements.txt
#   backend/data/         SQLite + HF cache roots (see .gitignore)
#   Resumes are processed in memory only (not written under backend/).
#   frontend/             Vite + React (source)
#   frontend/dist/        production bundle — path wired in backend/app/paths.py (FRONTEND_DIST)
#   .env                  optional repo-root env (loaded via backend/app/paths.py)
#
#   make install-all && make build
#   make dev
#
# Split UI hot reload (Vite proxies /api; default target port is 8000 — see frontend/vite.config.ts):
#   make dev-api & make dev-ui
#
# Avoid `make -j` for install-all (venv creation and npm ci can race).

SHELL         := /bin/bash
.SHELLFLAGS   := -eu -o pipefail -c
.DEFAULT_GOAL := help
.DELETE_ON_ERROR:

.PHONY: help install install-frontend install-all build dev dev-api dev-ui \
	backend frontend run clean clean-node clean-dist benchmark-hf-resume benchmark-kaggle-jobsphere

# --- Repo paths ---
BACKEND  ?= backend
FRONTEND ?= frontend
REQ       := $(BACKEND)/requirements.txt
DIST      := $(FRONTEND)/dist

# --- Python ---
PYTHON  ?= python3
VENV    ?= .venv
PIP          := $(VENV)/bin/pip
UVICORN      := $(VENV)/bin/uvicorn
UVICORN_ABS  := $(abspath $(UVICORN))

# --- Server ---
HOST ?= 127.0.0.1
PORT ?= 8000

# --- Node ---
NPM ?= npm
FRONTEND_VITE := $(FRONTEND)/node_modules/.bin/vite

help:
	@echo "Resume Scoring System"
	@echo ""
	@echo "Layout:  $(BACKEND)/ (API)   $(FRONTEND)/ (UI source)   $(DIST)/ (UI build output)"
	@echo ""
	@echo "Setup"
	@echo "  make install              $(PYTHON) venv + pip install -r $(REQ)"
	@echo "  make install-frontend     npm ci in $(FRONTEND)/"
	@echo "  make install-all          install + install-frontend"
	@echo ""
	@echo "Build"
	@echo "  make build                Vite → $(DIST)/ (served by FastAPI when present)"
	@echo ""
	@echo "Run"
	@echo "  make benchmark-hf-resume       HF 0xnbk resume–ATS vs generic JD ($(BACKEND)/benchmark_hf_resume_ats.py)"
	@echo "  make benchmark-kaggle-jobsphere Kaggle Jobsphere .docx vs generic JD ($(BACKEND)/benchmark_kaggle_jobsphere.py)"
	@echo "  make dev                  cd $(BACKEND) && uvicorn app.main:app --reload"
	@echo "  make dev-api              same as make dev"
	@echo "  make dev-ui               Vite dev server in $(FRONTEND)/ (pair with dev-api)"
	@echo "  make backend / frontend / run   aliases for make dev"
	@echo ""
	@echo "  App:  http://$(HOST):$(PORT)/     Docs: http://$(HOST):$(PORT)/docs"
	@echo ""
	@echo "Clean"
	@echo "  make clean-node           rm -rf $(FRONTEND)/node_modules"
	@echo "  make clean-dist           rm -rf $(DIST)/"
	@echo "  make clean                clean-node + clean-dist"
	@echo ""
	@echo "Overrides: PYTHON=$(PYTHON) HOST=$(HOST) PORT=$(PORT) VENV=$(VENV) BACKEND=$(BACKEND) FRONTEND=$(FRONTEND) NPM=$(NPM)"

# --- Python ---

$(UVICORN):
	@test -n "$$(command -v $(PYTHON) 2>/dev/null)" || { echo "Missing $(PYTHON) on PATH"; exit 1; }
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r $(REQ)

install: $(UVICORN)

# --- Frontend ---

$(FRONTEND_VITE): $(FRONTEND)/package.json $(FRONTEND)/package-lock.json
	@test -n "$$(command -v $(NPM) 2>/dev/null)" || { echo "Missing $(NPM) on PATH (install Node.js)"; exit 1; }
	cd $(FRONTEND) && $(NPM) ci

install-frontend: $(FRONTEND_VITE)

install-all: install install-frontend

build: $(FRONTEND_VITE)
	cd $(FRONTEND) && $(NPM) run build

# --- Run (cwd must be $(BACKEND) so package app is importable as app) ---

dev dev-api backend frontend run: $(UVICORN)
	cd $(BACKEND) && $(UVICORN_ABS) app.main:app --reload --host $(HOST) --port $(PORT)

dev-ui: $(FRONTEND_VITE)
	cd $(FRONTEND) && $(NPM) run dev

benchmark-hf-resume: $(UVICORN)
	cd $(BACKEND) && $(abspath $(VENV))/bin/python benchmark_hf_resume_ats.py --split validation --limit 200

benchmark-kaggle-jobsphere: $(UVICORN)
	cd $(BACKEND) && $(abspath $(VENV))/bin/python benchmark_kaggle_jobsphere.py --limit 30

# --- Clean ---

clean-node:
	rm -rf $(FRONTEND)/node_modules

clean-dist:
	rm -rf $(DIST)

clean: clean-node clean-dist
