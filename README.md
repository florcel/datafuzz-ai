# datafuzz-ai

Herramienta para testear APIs automáticamente usando specs OpenAPI.

## Por qué esto existe

Me cansé de probar endpoints manualmente, así que armé esto para:
- Generar payloads válidos e inválidos desde un OpenAPI spec
- Mandarlos contra un mock o API real
- Ver qué rompe y qué anda

## Setup rápido

```bash
# 1. Clonar e instalar
git clone <url>
cd datafuzz-ai
python -m venv .venv
source .venv/bin/activate  # en Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Levantar mock para pruebas
npx @stoplight/prism-cli mock specs/examples/openapi.yaml -p 4010

# 3. Probar
python -m apps.cli.cli gen --spec specs/examples/openapi.yaml --endpoint /users --n 10
```

## Comandos útiles

**Generar payloads:**
```bash
python -m apps.cli.cli gen \
  --spec specs/examples/openapi.yaml \
  --endpoint /users \
  --n 10
```

**Ejecutar tests (sync):**
```bash
python -m apps.cli.cli run \
  --spec specs/examples/openapi.yaml \
  --endpoint /users \
  --method post \
  --name "mi-test"
```

**Ejecutar tests (async, paralelo):**
```bash
python -m apps.cli.cli run-parallel \
  --spec specs/examples/openapi.yaml \
  --endpoint /users \
  --n 20 \
  --concurrency 5
```

## Persistencia

Por defecto usa SQLite (`datafuzz.db`). Para Postgres:

```bash
docker compose up -d postgres
export DATAFUZZ_DATABASE_URL="postgresql://datafuzz:datafuzz@127.0.0.1:5432/datafuzz"
python -c "from storage.db import init_db; init_db()"
```

## Stack

- **Python 3.10+** con Typer, httpx, SQLAlchemy, Jinja2
- **OpenAPI Spec Validator** para validar specs
- **Prism** como mock server (opcional)
- **PostgreSQL** para persistencia (opcional)

## TODO

- [ ] Más tipos de mutaciones (format violations, boundary testing)
- [ ] Autenticación (Bearer, API keys, OAuth)
- [ ] Dashboard web para histórico de runs
- [ ] Exportar a JSON/CSV

---

**v0.1 alpha** — Feedback y PRs bienvenidas 🚀
