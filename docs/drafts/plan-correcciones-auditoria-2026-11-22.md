# Plan de correcciones de la auditoría (22/11/2026)

Borrador de trabajo para retomar desde VS Code. Camino ODD: un commit pequeño por ítem, con
RED/GREEN cuando cambie comportamiento y los comandos registrados en el PR.

## Contexto para retomar

- Auditoría sobre `main` en `e98e6ab`: ruff, ruff format, mypy strict e import-linter sin errores.
- `pytest --cov`: 344 pasan, 3 omitidos, cobertura global 87,06 % (umbral 85 %) y 96 % en
  domain/application (umbral 90 %).
- Sin secretos en el árbol ni `.env` en el historial. Workflows con acciones fijadas por SHA.
- No verificado: e2e (Playwright), `integration_live`, `openspec validate`, build de imágenes y Garak.
- Rama de trabajo: `claude/keen-cray-q65p1j`.

## Traspaso a Codex (estado al 23/11/2026)

- Rama de trabajo: `claude/cobertura-c2-c3` (sale de `claude/keen-cray-q65p1j`). No tocar `main`:
  todo llega por PR y el merge lo decide el responsable.
- PR abierto: https://github.com/gusjrivas/PLN3_AgroRAG_GJR/pull/60 (listo para revisión).
  Su CI de GitHub Actions aún no se había ejecutado al escribir esto; revisar antes de seguir.
- Leer primero `AGENTS.md` (orden de lectura, camino ODD, límites técnicos) y este archivo.
- Hechos: H2 (CVE OpenTelemetry), C2 (cobertura) y C3 (CI). Pendientes: C1, C4 y C5.
- Orden sugerido: 1) confirmar CI verde del PR #60; 2) C4; 3) C5; 4) C1 cuando se decida cómo
  escanear imágenes (hace falta Docker y un escáner; el CI usa `trivy-action`).
- Reglas: un commit pequeño por ítem, test primero cuando cambie comportamiento, sin secretos,
  sin push a `main`, sin force-push. Registrar comandos y resultados en el PR.
- Dos decisiones siguen siendo del responsable: C1 (dónde escanear) y C5.2 (regla `Teoria*`).

## Hecho

- **H2. CVE-2026-126360 en OpenTelemetry.** `opentelemetry-sdk` pasó de 1.45.1 a 1.45.2 en
  `pyproject.toml` y `uv.lock`. `pip-audit` sobre el lock con el extra `tracing` pasó de 1 a 0
  vulnerabilidades y los 4 tests de tracing pasan. Nota en `docs/evidence/tdd/OPS-TRACE-01.md`.

## Antes de empezar

```bash
git fetch origin && git checkout claude/keen-cray-q65p1j && git pull
uv sync --frozen --python 3.12
```

## C1. Excepciones de vulnerabilidades vencidas (prioridad alta)

Archivos: `configs/security/vulnerability-exceptions.json`,
`configs/security/garak-runner-vulnerability-exceptions.json`, `scripts/check_vulnerability_policy.py`.

Las 7 excepciones vencieron el 2026-11-15 (CVE-2026-116587, -78669, -111943, -78667, -97031,
-78661 en gateway y CVE-2026-104851 en garak-runner). El commit `30dbaf0` corrigió sólo
CVE-2026-78661 (x/net).

1. Verificar: construir la imagen del gateway y escanearla con el escáner de `containers.yml`.
2. Quitar las excepciones cuyo CVE ya no aparece (empezando por CVE-2026-78661).
3. Renovar las que sigan abiertas (30 días) y actualizar `risk` y `tracking`; "MR #30" parece obsoleto.
4. Comprobar: `uv run pytest tests/unit/test_vulnerability_policy.py -q`.
5. Si cambia la política y no sólo las fechas, reclasificar como SDD.

Hecho cuando: el check de política pasa con `--today` igual a la fecha actual.

## C2. Cobertura de infraestructura (prioridad media) — HECHO en PR #60

Resultado: tokenizer 100 %, pinecone 96 %, bootstrap/app 96 %; global 87 % → 92 % con la CI nueva.

Un commit por módulo; sin llamadas a LLM ni descarga de modelos; test rojo primero.

| Módulo | Cobertura | Qué cubrir |
|---|---|---|
| `infrastructure/tokenizer.py` | 69 % | líneas 35 y 37-42 |
| `infrastructure/pinecone.py` | 77 % | líneas 96-104, 400-405, 451-454 |
| `bootstrap/app.py` | 77 % | líneas 87-95 y 137-148 |
| `infrastructure/tracing.py` | 0 % | ver C3 |

Hecho cuando: sube la cobertura global sin excluir código.

## C3. Cobertura de tracing en CI (prioridad media) — HECHO en PR #60

Archivo: `.github/workflows/ci.yml`. El paso "Verify optional tracing contract" no suma al informe.
Recomendado: agregar `--cov --cov-append` a ese paso y generar el informe después. Si hay duda sobre
el umbral, preguntar antes de tocarlo.

## C4. Documentación desfasada (prioridad baja)

1. Documentar cómo reproducir el contador `tiktoken` del perfil de la demo (README, línea 15) y
   verificar el procedimiento corriéndolo.
2. Revisar `openspec/changes/0[0-5]*/tasks.md` y `07`/`08`: marcar sólo lo que tenga evidencia en
   `docs/evidence/tdd/`; el resto, anotar "omitida" o "histórica".
3. Comprobar con `npx --yes @fission-ai/openspec@1.14.3 validate --all --strict`.

## C5. Higiene menor (prioridad baja)

1. Deprecación de `starlette.testclient` con `httpx`: valorar `httpx2` o fijar versión.
2. `AGENTS.md` exige preservar `Teoria*`, pero no existe ningún archivo con ese nombre. Decidir si
   la regla sigue vigente.

## Comprobación tras cada cambio

```bash
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run lint-imports
uv run pytest --cov --cov-report=term-missing
uv run coverage report --include='src/agro_rag/domain/*,src/agro_rag/application/*' --fail-under=90
```

## Decisiones pendientes del responsable

- C1: ¿se escanea la imagen desde VS Code (hace falta Docker) o desde CI?
- C5.2: estado de la regla `Teoria*`.
