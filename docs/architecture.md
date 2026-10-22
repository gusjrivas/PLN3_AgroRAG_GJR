# Arquitectura propuesta

## Objetivo y estilo

Monolito modular de backend con puertos y adaptadores, frontend Python separado por HTTP. Dos procesos locales: FastAPI y Streamlit. Evitar microservicios dentro del RAG. SQLite local mantiene el catálogo versionado; Pinecone almacena vectores. Un único proceso backend inicial simplifica recursos, caché y límites. Engram y OpenSpec pertenecen al plano de desarrollo.

```mermaid
flowchart TD
  U["Usuario"] --> UI["Streamlit"]
  UI --> API["FastAPI: validación y acceso"]
  API --> APP["Caso de uso: consultar"]
  APP --> INV["Agente investigador"]
  INV --> RAG["BM25 + Pinecone + RRF + reranker"]
  RAG --> INV
  INV --> VER["Agente verificador"]
  VER -->|Una corrección como máximo| INV
  VER --> OUT["Respuesta, aclaración o abstención"]
  OUT --> API
```

## Dependencias permitidas

- domain: Python estándar y tipos propios. Entidades inmutables para evidencia y resultado.
- application: domain y Protocols de retrieval, generador, auditoría, reloj y presupuesto.
- infrastructure: implementa esos puertos; encapsula SDKs, LangGraph, almacenamiento y embeddings.
- api: application + DTO Pydantic; obtiene casos de uso desde bootstrap. No lógica agronómica en rutas.
- bootstrap: único lugar que ensambla adaptadores, settings y ciclo de vida de modelos.
- agro_rag_ui: cliente HTTP propio, modelos de vista y Streamlit; no importa agro_rag. El contrato HTTP y sus fixtures se verifican mediante tests, sin compartir lógica de negocio.
- infrastructure nunca importa api/UI; application nunca importa infrastructure. Los contratos se verifican con import-linter o tests de AST; no se resuelven ciclos con imports locales ocultos.

## Ingesta offline

Fuentes admitidas → extracción por página → revisión de tablas → normalización conservadora → chunks → catálogo SQLite + BM25 → embeddings → namespace Pinecone nuevo → verificación de conteos/IDs/textos → activación atómica del manifiesto local.
Una ingesta fallida conserva el corpus activo anterior. Los namespaces no se reutilizan entre versiones. Nada se reindexa durante una consulta. No ejecutar clear_namespace sobre datos activos. corpus_version deriva del manifiesto con hashes, configuración y modelos; no depende sólo del nombre del archivo.

## Consulta y agentes de aplicación

El investigador recibe pregunta/contexto, decide aclarar o buscar, puede reformular hasta dos subconsultas dentro del presupuesto y redacta claims con evidence_ids. El verificador tiene acceso de lectura a pasajes originales y puede llamar a una búsqueda focalizada para contrastar. Emite un resultado estructurado: approve, revise, clarify o abstain, con incidencias breves y evidencia. No guardar razonamiento privado extenso.

La primera revisión puede solicitar corrección; la segunda termina en respuesta aprobada, aclaración o abstención. Máximo dos pasadas de investigación y dos de verificación, seis llamadas LLM totales y cuatro operaciones de búsqueda totales. Los límites de cantidad, tokens y deadline son compartidos por toda la petición, incluidas herramientas y reintentos. Las decisiones son dinámicas; no basta concatenar dos prompts sin permitir corrección.

## Estados y salida

Estados públicos de negocio: answered, needs_clarification, insufficient_evidence. Fallos operativos usan errores HTTP tipados; no se convierten en abstención agronómica ni respuesta exitosa. Toda respuesta answered tiene claims respaldados por evidence_ids existentes y citas direccionables; la verificación semántica se mide, no se presume infalible.

## Ejecución y recursos

Modelos se cargan una vez en startup; cerrar clientes en shutdown. Tareas CPU/SDK síncronos van a workers limitados, sin bloquear el event loop. Límite inicial dos consultas activas, cola explícita inexistente: exceso 429. Reintentos sólo de errores transitorios, máximo uno por operación y dentro del deadline; jitter y reloj reemplazables en tests. Startup no crea o borra índices automáticamente.

Objetivos iniciales a medir, no resultados: p95 caliente ≤30 s en demo local y timeout global 60 s. Presupuesto máximo 12.000 tokens acumulados de entrada y salida por consulta; si un proveedor no devuelve usage, registrar estimación diferenciada. Ajustes pasan por configuración y evaluación en dev.

## Datos y observabilidad

Request ID, corpus_version, commit, prompt_version, modelo, etapas, duración, llamadas, tokens reales/estimados, caché y causa de cierre. No guardar texto completo de preguntas por defecto ni secretos. Citas guardan página física PDF y etiqueta impresa separadas. Caché de retrieval por consulta normalizada, filtros, corpus_version, modelo y parámetros; no cachear errores ni compartir resultados entre corpus distintos.

Ver docs/contracts.md, docs/security.md y ADR-003 a ADR-010.
