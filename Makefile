# Makefile

.PHONY: all build up down logs test clean

all: build

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

test:
	pytest tests/

clean:
	docker-compose down --volumes --remove-orphans
	rm -rf reports/samples/*
	rm -rf __pycache__

run-mock:
\tnpx @stoplight/prism-cli mock specs/examples/openapi.yaml -p 4010

gen:
\tpython -m apps.cli.cli gen --spec specs/examples/openapi.yaml --endpoint /users --n 50 --base-url http://localhost:4010

report:
\tpython - <<'PY'\nfrom apps.reporting.renderers.html import render_latest\nrender_latest()\nPY
