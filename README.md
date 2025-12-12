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

**Ejecutar tests (async):**
```bash
python -m apps.cli.cli run-parallel \
  --spec specs/examples/openapi.yaml \
  --endpoint /users \
  --n 20 \
  --concurrency 5
```

## Con Postgres (opcional)

```bash
docker compose up -d postgres
export DATAFUZZ_DATABASE_URL="postgresql://datafuzz:datafuzz@127.0.0.1:5432/datafuzz"
python -c "from storage.db import init_db; init_db()"
```

## Stack

- Python 3.10+
- Typer (CLI)
- httpx (requests)
- SQLAlchemy (persistencia)
- Jinja2 (reportes HTML)
- Prism (mock server)

## TODO

- [ ] Agregar más tipos de mutaciones
- [ ] Soporte para auth (Bearer, API keys)
- [ ] Dashboard web para ver runs históricos
- [ ] Exportar reportes a JSON/CSV

---

Proyecto en fase alpha. Si encontrás bugs o querés sugerir features, abrí un issue.
npx @stoplight/prism-cli mock specs/examples/openapi.yaml -p 4010
```

---

## Uso desde la CLI  

Algunos ejemplos:  

- **Generar payloads:**  
```powershell
python -m apps.cli.cli gen --spec specs/examples/openapi.yaml --endpoint /users --n 10 --base-url http://127.0.0.1:4010
```

- **Ejecutar una petición sincrónica y persistir resultado:**  
```powershell
python -m apps.cli.cli run --spec specs/examples/openapi.yaml --endpoint /users --method post --base-url http://127.0.0.1:4010 --name quick-test
```

- **Ejecutar requests concurrentes:**  
```powershell
python -m apps.cli.cli run-parallel --spec specs/examples/openapi.yaml --endpoint /users --method post --n 20 --concurrency 5 --base-url http://127.0.0.1:4010 --name parallel-test
```

- **Abrir reporte HTML:**  
```powershell
start reports/samples/report.html   # Windows
```

---

## Persistencia: SQLite y Postgres  

- **Por defecto**: SQLite → `sqlite:///datafuzz.db`  
- **Con Postgres (docker-compose)**:  
```powershell
docker compose up -d postgres
$env:DATAFUZZ_DATABASE_URL = "postgresql://datafuzz:datafuzz@127.0.0.1:5432/datafuzz"
python -c "from storage.db import init_db; init_db(); print('DB initialized')"
```

---

## CI con GitHub Actions  
El workflow inicial:  
- Instala Python y Node  
- Levanta Prism  
- Ejecuta `gen` y `run`  
- Publica el reporte como artifact  

*(Se puede ajustar para correr con Postgres o aplicar migraciones en CI).*  

---

## Stack usado  
- **Python**: Typer, httpx, SQLAlchemy, Jinja2, pyyaml, openapi-spec-validator, pytest  
- **Node/npm**: @stoplight/prism-cli (mock server)  
- **Infra**: Docker + Postgres (dev)  
- **CI**: GitHub Actions  

---

👉 Este proyecto todavía está en fase temprana (v0.1). Si te interesa probarlo, romperlo o sugerir mejoras, ¡todo feedback es bienvenido!

##  📫 Contactame: <p align='center'>
  <a href="https://www.linkedin.com/in/florenciaporcel/">
    <img src="https://img.shields.io/badge/linkedin-%230077B5.svg?&style=for-the-badge&logo=linkedin&logoColor=white" />
  </a>&nbsp;&nbsp;
</p>
