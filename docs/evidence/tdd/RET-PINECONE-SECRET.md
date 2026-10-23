# TDD: credencial local de Pinecone

Fecha: 22/10/2026. Responsable/revisor: misma sesión, sin revisión independiente. Rama:
`fix/pinecone-secret-config`. Base main:
`21d124f775d1731f7e0bff3f82233a0932c72553`.
Commit de implementación verificado: `e1a5921b03cfb4b906f0f3bf73a881c0db992508`.

## Fuente y alcance

Se revisó como base docente `Teoria1/Codigo/RAG` de `PLN3_GJR` en el commit fijado
`1f4cdbb37f59a049ef9b35c482ccb1de850fbc43`. En particular:

- `raglib/config.py` carga el `.env` del proyecto;
- `raglib/vector_pinecone.py::PineconeSearcher.__post_init__` obtiene
  `PINECONE_API_KEY` del entorno o de un parámetro y la entrega al cliente;
- los scripts de construcción y demo instancian ese adaptador.

Este corte conserva el nombre de variable y adapta la lectura al bootstrap con
`pydantic-settings` y `SecretStr`. No activa Pinecone, no carga modelos, no crea índices y no copia
`clear_namespace`; esas operaciones siguen pendientes del corte de adaptadores reales de ADR-013.

## Revisión de exposición

No existía `.env` en este repositorio ni una variable Pinecone en el proceso. `.env`, `.env.*` y
variantes locales están cubiertos por `.gitignore`, con excepción deliberada de `.env.example`.
La búsqueda del patrón `pcsk_` y de asignaciones no vacías a `PINECONE_API_KEY` no encontró
secretos en archivos versionados ni commits. La revisión imprimió únicamente nombres de variables
y rutas, nunca valores. El repositorio docente tampoco tenía `.env`; su README contiene sólo un
placeholder.

## Ciclo TDD

1. Intentos de entorno no acreditados como RED: `python -m pytest ...` falló porque el Python
   global no tenía pytest; `uv` no estaba instalado. Se instaló `uv` y se ejecutó `uv sync
   --frozen`, que creó `.venv` con Python 3.12 y el lock vigente.
2. RED funcional: `.venv\Scripts\python.exe -m pytest tests/unit/test_settings.py -q`, salida 1,
   tres fallos porque `Settings` no tenía `pinecone_api_key`.
3. GREEN: se añadió el campo opcional `SecretStr`, alias `PINECONE_API_KEY`, redacción y
   `env_ignore_empty=True`. La suite afectada final incluyó cuatro escenarios: entorno de proceso,
   `.env`, precedencia del proceso y valor vacío.
4. REFACTOR/regresión: `.venv\Scripts\python.exe -m pytest tests/unit
   tests/contract/test_query_api.py -q`, salida 0, 67 aprobadas y una advertencia de deprecación
   ajena al cambio.

## Controles finales

- `ruff check .`: salida 0.
- `ruff format --check .`: salida 0, 111 archivos formateados.
- `mypy`: salida 0, 23 archivos sin incidencias.
- `lint-imports`: salida 0, dos contratos conservados.
- `git diff --check`: salida 0.
- `npx --yes @fission-ai/openspec@latest validate 03-retrieval --strict`: salida 0.

Se intentó además `pytest tests/unit/test_settings.py tests/contract/test_health.py
tests/contract/test_query_api.py -q`: 14 pruebas pasaron y el test de liveness falló antes de
crear el cliente porque su monkeypatch global de `socket.connect` intercepta el `socketpair` que
AnyIO necesita en Windows. Es un problema preexistente del test/harness y no sustituye ni invalida
el GREEN específico; queda explícito y no se informa la suite completa como aprobada.

## Riesgos restantes

`SecretStr` evita exposición accidental en representaciones, pero no cifra memoria ni `.env`.
Para desarrollo local se recomienda una variable del proceso creada sin escribir la clave en el
historial. El secret store de la plataforma será obligatorio fuera del entorno local. No había una
clave real disponible para migrar o rotar. La integración real de Pinecone y sus pruebas
`integration_live` permanecen pendientes.
