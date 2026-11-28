# AgroRAG - TP integrador PLN III

Asistente documental verificable sobre riego y estrés hídrico en tomate y lechuga.
Autor y responsable académico: Gustavo Julián Rivas. Fecha del plan: 21/10/2026.

Repositorio independiente: https://github.com/gusjrivas/PLN3_AgroRAG_GJR

**Estado al 24/11/2026.** La demo local con Docker Compose incluye API, Streamlit y Grafana.
El tablero muestra trazas por etapa, latencia, resultados, caché, tokens de entrada y salida y
costo estimado con tarifas configurables. La exposición está preparada para 15 minutos.
[Evidencia de observabilidad](docs/evidence/tdd/OPS-OBS-03.md) · [Prueba de tokens y costo](docs/evidence/tdd/OPS-TOKENS-01.md).

## Arranque rápido con Docker Compose

Desde la raíz del repositorio, con Docker Desktop o Docker Engine, Compose, Python 3.12 y `uv`:

```powershell
uv sync --frozen
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
uv run agro-rag download data/manifest.json
```

Definir `AGRO_READER_KEY` en `.env`. Los comandos de abajo permiten arrancar y explorar fuentes.
Para la demo con respuestas verificadas, seguir el arranque completo con
[Ollama u OpenAI](docs/run-containerized.md#grafana-local-para-la-demo).

```powershell
$compose = @('-f', 'compose.yaml', '-f', 'compose.dev.yaml', '-f', 'compose.observability.yaml')
docker compose @compose --profile admin run --rm --build catalogue-admin
docker compose @compose up --build --wait
```

Abrir [Streamlit](http://127.0.0.1:8501), [Grafana](http://127.0.0.1:3000/d/agrorag-local/agrorag-local)
y [la documentación de la API](http://127.0.0.1:8000/docs). En Grafana, el tablero provisionado
se llama **AgroRAG local**. Si el puerto 8000 está en uso, ejecutar
`$env:AGRO_API_PORT = '18000'` antes de levantar el stack. Para detenerlo y conservar el catálogo,
ejecutar `docker compose @compose stop`.

**Prueba de la demo.** En Streamlit, elegir **Respuesta verificada** y preguntar
«¿Qué recomienda INTA sobre mantener la humedad del suelo durante el crecimiento de la lechuga?».
Abrir la cita y buscar la traza en Grafana. Repetir la consulta con los mismos filtros para ver
el acierto de caché. Los paneles de tokens se actualizan con las llamadas de ambos agentes.
Para calcular el costo, completar las dos tarifas del modelo en USD por millón de tokens.
[Arranque y comprobaciones](docs/run-containerized.md#grafana-local-para-la-demo).

Para usar Python en dos terminales, consultar [el arranque local](docs/run-local.md).

## Evidencia del proyecto

Benchmark histórico: 49 PASS y 11 FAIL de contenido/citas, con 60/60 estados correctos.
E1/E2 y piloto E3 se ejecutaron sobre `dev`; BM25 sigue como default.
La ingesta limpia conserva los 27 IDs del corpus histórico y valida los 60 casos congelados.
Una consulta real con `hybrid_rerank`, GPT-4o y `tiktoken` devolvió una cita verificable de
INTA Lechuga, página 28, en 43,28 s desde el arranque normal de la API.
[Configuración del perfil de demo](docs/run-local.md#perfil-de-demo-con-gpt-4o-y-tiktoken).
La aceptación complementaria del 12/11 cerró con **19 casos conformes y 8 incompletos** según
la rúbrica, revisando tres registros manuales y ejecutando otros 24 por API. El bug #51 está
corregido y su regresión pidió aclaración sin llamadas LLM. Ver [cierre y evidencia](docs/evidence/acceptance-27/README.md).

**Garak ya ejecutado:** API key, Base64 y prompt injection alcanzaron 32 respuestas reales por
familia sin detecciones; las 15 alertas DAN se revisaron como falsos positivos. Se conserva la
evidencia de la candidata `d38814b4`; por instrucción del usuario no se repite el scan para el
siguiente entorno limpio. La promoción formal V2 continúa pendiente. Ver [informe de seguridad](docs/evidence/garak/garak-d38814b4-human-report.md).

**Metadatos docentes:** META-01..04 integradas; curación real, evaluación comparativa y cierre
META-05..07 pendientes. El cierre documental no completa ni archiva esa extensión.
Queda ensayar la exposición, completar las métricas pendientes y confirmar la fecha de Teoría 7.

Engram 3.5.2 está instalado y verificado en el entorno de trabajo remoto; `.engram/config.json` identifica este proyecto. La instalación en la notebook y la activación de los clientes permanecen pendientes. Ver [evidencia](docs/evidence/engram-setup.md). Los ADR son propuestas técnicas; TDD y Python son requisitos expresos del usuario.

## Empezar aquí

**Para ejecutarlo localmente:** seguir [run-local](docs/run-local.md). **La V2 containerizada tiene promoción formal pendiente:** consultar [run-containerized](docs/run-containerized.md). **Para
continuar el desarrollo:** [start-here](docs/start-here.md). Repositorio independiente:
`PLN3_AgroRAG_GJR`.

1. [Plan de ejecución](docs/plan.md): secuencia, dependencias y puertas de salida.
2. [Requisitos y trazabilidad](docs/requirements.md): consigna → cambio → prueba → evidencia.
3. [Arquitectura](docs/architecture.md) y [ADR](docs/adr/README.md).
4. [Protocolo TDD](docs/tdd.md) y [agentes de desarrollo](docs/development-agents.md).
5. [Preparación local y Engram](docs/setup-engram.md).
6. [Cambios OpenSpec](openspec/README.md): estado y evidencia por tarea; algunas listas contienen planificación histórica.

## Stack

Python 3.12, FastAPI y Pydantic v2 en backend, Streamlit en frontend y httpx como cliente HTTP.
El caso de uso orquesta los dos agentes. El RAG usa pdfplumber, BM25, Sentence Transformers,
Pinecone y Cross-Encoder. SQLite conserva el catálogo y la auditoría emite eventos JSON.
pytest, pytest-cov, Hypothesis, Streamlit AppTest y Playwright Python para pruebas; Ruff, mypy e import-linter para calidad. uv y uv.lock fijan dependencias. Docker Compose ensambla API, UI, gateway y jobs explícitos sin cambiar los límites del monolito modular. Ninguna versión de librería del producto se presenta como validada fuera de la evidencia registrada.

OpenSpec 1.14.3 es la versión de tooling seleccionada para validar esta planificación. Engram usa una versión estable registrada al instalar. Son herramientas del desarrollo y quedan fuera del contenedor del producto.

## Alcance

Consultas en español con citas a pasajes exactos, aclaraciones y abstención. Corpus inicial curado de INTA y FAO. Agentes de la aplicación: investigador y verificador con posibilidad de una ronda de corrección. Evaluación contra recuperación base y generación sin verificador.

Fuera del MVP: predicciones con sensores, automatización del riego, CNN/ViT, fine-tuning, búsqueda web libre en ejecución, multiusuario público, Kubernetes y GraphRAG. El sistema explica documentación; no prescribe litros de riego sin evidencia y datos suficientes.

## Estructura objetivo

| Ruta | Responsabilidad |
|---|---|
| `src/agro_rag/domain/` | Entidades, estados, reglas puras |
| `src/agro_rag/application/` | Casos de uso y puertos |
| `src/agro_rag/infrastructure/` | Adaptadores de modelos, índices, catálogo y auditoría |
| `src/agro_rag/api/` | FastAPI, contratos HTTP y autenticación |
| `src/agro_rag/bootstrap/` | Configuración e inyección de dependencias |
| `src/agro_rag_ui/` | Streamlit, estado de pantalla y cliente API |
| `tests/` | unit, contract, integration, architecture, ui, e2e |
| `configs/`, `data/`, `scripts/` | Configuración, corpus/evaluación y operaciones |
| `infra/`, `docs/`, `openspec/` | Ejecución local, decisiones y especificaciones |

Las carpetas de runtime contienen la primera implementación. Algunas capacidades del diseño objetivo continúan pendientes; consultar el runbook y la evidencia por PR.

## Reglas de entrega

TDD obligatorio; ningún test no ejecutado se informa como aprobado. Las evaluaciones con LLM reales se distinguen de pruebas con dobles. La exposición dura 15 minutos; informe PDF y código se entregan a más tardar en Teoría 7. Falta confirmar la fecha calendario de esa clase.

Ver [fuentes](docs/sources.md), [protocolo de evaluación](docs/evaluation.md) y [estado de validación](docs/validation.md).

El material de entrega V3 consta de un informe PDF de 15 páginas y una presentación editable
de 18 diapositivas con su guion. Ver [control previo a la entrega](docs/demo.md#control-previo-a-la-entrega).
Como antecedentes versionados se conservan el [informe del 22/11/2026](output/pdf/agro-rag-report-2026-11-22.pdf),
la [fuente técnica](docs/report.md) y la [presentación de nueve diapositivas](output/presentations/agro-rag-catedra.pptx).
Seguridad Garak: [informe legible](docs/evidence/garak/garak-d38814b4-human-report.md),
[PDF](output/pdf/garak-d38814b4-human-report.pdf) y
[libro de revisión DAN](docs/evidence/workbooks/garak-d38814b4-revision-humana-dan.xlsx).
Exposición: [guion reproducible de 15 minutos](docs/demo.md).
Verificación offline del paquete base: `uv run agro-rag verify-delivery --root .`.
Libros Excel originales de pruebas y revisión: [docs/evidence/workbooks](docs/evidence/workbooks/README.md).

## Ejecutar la base

```bash
uv sync --frozen
uv run uvicorn agro_rag.bootstrap.app:create_app --factory --host 127.0.0.1 --port 8000
```

`GET /health/live` devuelve `{"status":"ok"}`. Pruebas: `uv run pytest --cov`.

**Trazas sin Docker.** Instalar el extra con `uv sync --locked --extra tracing` y habilitar
`AGRO_TRACING_ENABLED=true` para ver trazas en la consola de la API. El overlay de Compose
habilita el envío por OTLP/HTTP a Grafana.
[Instrucciones](docs/run-local.md#trazas-opcionales-para-la-demo-académica).

Descargar e ingerir el corpus piloto: [docs/corpus.md](docs/corpus.md). La selección vigente contiene 27 fragmentos revisados de cinco fuentes institucionales; no equivale a una evaluación científica completa.
