################################################################################
# Makefile budget-backend — perintah pengembangan & pengujian.
#
# Gate test (lint + unit) berjalan DALAM Docker via Dockerfile.test.
# Perintah yang sama (`make test`) dipakai di LOKAL maupun di GitHub Actions.
# Tidak ada artefak test (__pycache__, .pytest_cache, dll) yang tertulis
# ke folder project karena source di-COPY ke image, bukan bind-mount.
################################################################################

IMAGE_NAME ?= $(shell basename $(CURDIR))-test
DOCKERFILE  = Dockerfile.test
DOCKER_RUN  = docker run --rm $(IMAGE_NAME)

VENV   := .venv
PYTHON := $(if $(wildcard $(VENV)/bin/python),$(VENV)/bin/python,python3)
PIP    := $(PYTHON) -m pip

.DEFAULT_GOAL := test
.PHONY: build lint unit test clean install run help

## build: bangun image test (Dockerfile.test)
build:
	docker build -f $(DOCKERFILE) -t $(IMAGE_NAME) .

## lint: jalankan ruff check di dalam container
lint: build
	$(DOCKER_RUN) ruff check app tests

## unit: jalankan pytest di dalam container
unit: build
	$(DOCKER_RUN) pytest -q

## test: gate lengkap = lint + unit. Dipakai LOKAL dan CI (identik).
test: lint unit

## clean: hapus image test
clean:
	-docker rmi $(IMAGE_NAME)

## install: pasang dependency ke virtualenv lokal (untuk development)
install:
	$(PIP) install -r requirements.txt -r requirements-dev.txt

## run: jalankan server pengembangan (lokal, via virtualenv)
run:
	$(PYTHON) -m uvicorn app.main:app --reload

## help: tampilkan daftar perintah
help:
	@grep -E '^## ' $(MAKEFILE_LIST) | sed -e 's/## //'
