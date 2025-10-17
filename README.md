# Datafuzz-ai — v0.1

## Resumen  
**Datafuzz-ai** nació como un experimento personal para automatizar pruebas rápidas a partir de especificaciones OpenAPI. La idea: generar payloads válidos e inválidos, correrlos contra un mock o servicio real, medir latencias/estatus y guardar los resultados para luego analizarlos en un reporte.  

Esta primera versión (v0.1) incluye:  
- Parser OpenAPI básico (openapi-spec-validator + pyyaml).  
- Generador de payloads (válidos + mutaciones inválidas como `enum` fuera de rango, `missing required`, strings largos, unicode, etc.).  
- Runners HTTP: sincrónico y asíncrono (concurrency con httpx).  
- Persistencia con SQLAlchemy (modelos `Run` / `Result`). Por defecto SQLite, opcional Postgres vía env var y `docker-compose`.  
- Reporting: HTML (Jinja2) + JSON.  
- CLI con Typer: `gen`, `run`, `run-parallel`, `report`.  
- Tests unitarios y de integración con pytest + workflow inicial de GitHub Actions.  

---

## Estructura del repo  
Algunos archivos relevantes:  

```
apps/cli/cli.py               → CLI principal (Typer)
apps/runner/http_runner.py    → runner sincrónico
apps/runner/async_runner.py   → runner asíncrono (concurrency)
core/parser.py                 → parser OpenAPI básico
engines/contract/generator.py → generador de payloads y mutaciones
storage/db.py                  → session maker (usa DATAFUZZ_DATABASE_URL)
storage/models.py              → modelos SQLAlchemy: Run, Result
apps/reporting/renderers/html.py → renderer con Jinja2
specs/examples/openapi.yaml    → spec de ejemplo
tests/unit/                    → tests unitarios y de persistencia/paralelo
```

---

## Requisitos previos  
- Python 3.10+  
- pip  
- Node.js + npm (para `npx @stoplight/prism-cli` → mock server)  
- Docker & docker-compose (opcional, para Postgres en dev)  
- En Windows: PowerShell o WSL / Git Bash  

---

## Instalación rápida  

1. Clonar repo y entrar a la carpeta raíz:  
```powershell
git clone <url>
cd datafuzz-ai
```

2. Crear y activar entorno virtual:  
```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1    # PowerShell
# o en Linux/Mac:
# source .venv/bin/activate
```

3. Instalar dependencias:  
```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

*(Si usás Postgres, `psycopg2-binary` ya viene en `requirements.txt`.)*  

---

## Ejecutar tests  
```powershell
pytest -q
```

---

## Mock server con Prism  
Para correr un mock local:  
```powershell
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
