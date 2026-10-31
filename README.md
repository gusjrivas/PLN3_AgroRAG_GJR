# AgroRAG - TP integrador PLN III

Asistente documental verificable sobre riego y estrés hídrico en tomate y lechuga.
Autor y responsable académico: Gustavo Julián Rivas. Fecha del plan: 21/10/2026.

Repositorio independiente: https://github.com/gusjrivas/PLN3_AgroRAG_GJR

**Estado: V1 local y paquete de entrega técnica implementados. V2 containerizada en ejecución bajo
ADR-015/OpenSpec 07: settings por secret files, imágenes API/UI/gateway no root, Compose local,
catálogo persistente/read-only y overlay productivo endurecido ya tienen evidencia; CI de imágenes,
identidad de release, logs HTTP JSON y rollback validado ya tienen evidencia; supply chain aprobó
en GitHub y las imágenes API/UI/gateway del merge `41ba62f` están publicadas por digest en GHCR.
El runner Garak 0.17.0 aprobó sus contratos offline y fue publicado por digest desde `5a11a29`.
El scan manual autorizado tiene un workflow fail-closed. El smoke de staging también ata
manifiesto, identidad, catálogo y una consulta citada en evidencia sanitizada. El preflight de host
valida digests, identidad OCI, volumen y secretos antes de levantar producción. La candidata
`41ba62f` está desplegada y verificada en el staging local WSL; el scan Garak real sigue abierto.
El benchmark congelado de 60 casos conserva 49 PASS y 11
FAIL de contenido/citas, con 60/60 estados observados correctos. E1/E2 y el piloto mínimo E3 se
ejecutaron sobre `dev`; BM25 permanece como default.**
Engram 3.5.2 está instalado y verificado en el entorno de trabajo remoto; `.engram/config.json` identifica este proyecto. La instalación en la notebook y la activación de los clientes permanecen pendientes. Ver [evidencia](docs/evidence/engram-setup.md). Los ADR son propuestas técnicas; TDD y Python son requisitos expresos del usuario.

## Empezar aquí

**Para ejecutarlo localmente:** seguir [run-local](docs/run-local.md). **La V2 containerizada está
en implementación incremental:** consultar [run-containerized](docs/run-containerized.md). **Para
continuar el desarrollo:** [start-here](docs/start-here.md). Repositorio independiente:
`PLN3_AgroRAG_GJR`.

1. [Plan de ejecución](docs/plan.md): secuencia, dependencias y puertas de salida.
2. [Requisitos y trazabilidad](docs/requirements.md): consigna → cambio → prueba → evidencia.
3. [Arquitectura](docs/architecture.md) y [ADR](docs/adr/README.md).
4. [Protocolo TDD](docs/tdd.md) y [agentes de desarrollo](docs/development-agents.md).
5. [Preparación local y Engram](docs/setup-engram.md).
6. [Cambios OpenSpec](openspec/README.md): todas las tareas funcionales empiezan pendientes.

## Stack propuesto

Python 3.12; FastAPI + Pydantic v2 en backend; Streamlit en frontend Python; httpx como cliente HTTP; LangGraph encapsulado para el flujo de agentes; pdfplumber, BM25, Sentence Transformers, Pinecone y Cross-Encoder para RAG; SQLite para catálogo de evidencias y JSONL para auditoría.
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

Informe técnico: [PDF](output/pdf/agro-rag-report.pdf) y [fuente versionada](docs/report.md).
Exposición: [guion reproducible de 15 minutos](docs/demo.md). Verificación offline:
`uv run agro-rag verify-delivery --root .`.
Libros Excel originales de pruebas y revisión: [docs/evidence/workbooks](docs/evidence/workbooks/README.md).

## Ejecutar la base

```bash
uv sync --frozen
uv run uvicorn agro_rag.bootstrap.app:create_app --factory --host 127.0.0.1 --port 8000
```

`GET /health/live` devuelve `{"status":"ok"}`. Pruebas: `uv run pytest --cov`.

Descargar e ingerir el corpus piloto: [docs/corpus.md](docs/corpus.md). La selección vigente contiene 27 fragmentos revisados de cinco fuentes institucionales; no equivale a una evaluación científica completa.
