# Makefile budget-backend — perintah pengembangan & pengujian.
#
# Menggunakan virtualenv lokal di .venv jika tersedia, jika tidak fallback
# ke `python -m`. Jalankan `make test` untuk menjalankan seluruh unit test.

VENV := .venv
PYTHON := $(if $(wildcard $(VENV)/bin/python),$(VENV)/bin/python,python3)
PIP := $(PYTHON) -m pip

.PHONY: help install test lint run clean

help: ## Tampilkan daftar perintah
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

install: ## Pasang dependency runtime + dev
	$(PIP) install -r requirements.txt -r requirements-dev.txt

test: ## Jalankan seluruh unit test (pytest)
	$(PYTHON) -m pytest -q

lint: ## Periksa gaya kode dengan ruff
	$(PYTHON) -m ruff check app tests

run: ## Jalankan server pengembangan
	$(PYTHON) -m uvicorn app.main:app --reload

clean: ## Hapus cache pytest & ruff
	rm -rf .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
