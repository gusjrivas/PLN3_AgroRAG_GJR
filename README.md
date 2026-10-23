# AgroRAG - TP integrador PLN III

Asistente documental verificable sobre riego y estrés hídrico en tomate y lechuga.
Autor y responsable académico: Gustavo Julián Rivas. Fecha del plan: 21/10/2026.

Repositorio independiente: https://github.com/gusjrivas/PLN3_AgroRAG_GJR

**Estado: primera versión local implementada: corpus piloto, búsqueda, API, interfaz y flujo investigador/verificador. El adaptador administrativo Pinecone/E5 y el reranker están implementados, pero la API pública conserva el baseline lexical hasta completar integración real y benchmark.**
Engram 3.5.2 está instalado y verificado en el entorno de trabajo remoto; `.engram/config.json` identifica este proyecto. La instalación en la notebook y la activación de los clientes permanecen pendientes. Ver [evidencia](docs/evidence/engram-setup.md). Los ADR son propuestas técnicas; TDD y Python son requisitos expresos del usuario.

## Empezar aquí

**Para ejecutarlo:** seguir [run-local](docs/run-local.md). **Para continuar el desarrollo:** [start-here](docs/start-here.md). Repositorio independiente: `PLN3_AgroRAG_GJR`.

1. [Plan de ejecución](docs/plan.md): secuencia, dependencias y puertas de salida.
2. [Requisitos y trazabilidad](docs/requirements.md): consigna → cambio → prueba → evidencia.
3. [Arquitectura](docs/architecture.md) y [ADR](docs/adr/README.md).
4. [Protocolo TDD](docs/tdd.md) y [agentes de desarrollo](docs/development-agents.md).
5. [Preparación local y Engram](docs/setup-engram.md).
6. [Cambios OpenSpec](openspec/README.md): todas las tareas funcionales empiezan pendientes.

## Stack propuesto

Python 3.12; FastAPI + Pydantic v2 en backend; Streamlit en frontend Python; httpx como cliente HTTP; LangGraph encapsulado para el flujo de agentes; pdfplumber, BM25, Sentence Transformers, Pinecone y Cross-Encoder para RAG; SQLite para catálogo de evidencias y JSONL para auditoría.
pytest, pytest-cov, Hypothesis, Streamlit AppTest y Playwright Python para pruebas; Ruff, mypy e import-linter para calidad. uv y uv.lock para resolver/fijar dependencias durante el primer cambio. Docker Compose para dos procesos locales. Ninguna versión de librería del producto se presenta como ya validada.

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

## Ejecutar la base

```bash
uv sync --frozen
uv run uvicorn agro_rag.bootstrap.app:create_app --factory --host 127.0.0.1 --port 8000
```

`GET /health/live` devuelve `{"status":"ok"}`. Pruebas: `uv run pytest --cov`.

Descargar e ingerir el corpus piloto: [docs/corpus.md](docs/corpus.md). La primera selección contiene 12 fragmentos revisados; no equivale a una evaluación científica completa.
