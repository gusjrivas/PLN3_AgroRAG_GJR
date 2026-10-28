# Plan de inicio y ejecución

## Estado al 28/10/2026

La primera versión local y el paquete técnico están implementados: corpus curado de 27 fragmentos,
API/UI, investigador/verificador, caché, auditoría redactada, proveedores Ollama/OpenAI opcionales,
adaptadores E5/Pinecone/reranker, contratos de evaluación, informe PDF y guion de demo. La suite
rápida tiene evidencia vigente y el verificador offline reconoce los ocho artefactos de entrega.

Corte activo: `feat/semantic-runtime-activation`, responsable coordinador/RAG, misma sesión.
Propiedad: ensamblado de retrieval en bootstrap, tokenizer, configuración, pruebas y documentación de
03. El runtime permite seleccionar `bm25`, `vector`, `hybrid` o `hybrid_rerank`; los modos semánticos
fallan antes de servir si faltan secreto, identidad compatible o tokenizer fijado. BM25 continúa como
default: no se presenta el smoke de ocho qrels `pending_human` como evaluación definitiva ni se activa
silenciosamente un fallback.

Siguiente puerta académica: revisión humana del benchmark, ejecución E1/E2/E3 y actualización del
informe con resultados definitivos. Después corresponde ensayo final de 15 minutos, confirmación de
modalidad/fecha y envío a ambos docentes sólo con autorización del usuario. La secuencia original de
abajo queda como mapa de dependencias, no como estado de implementación.

## Decisión de organización

Usar el repositorio independiente creado por el usuario: https://github.com/gusjrivas/PLN3_AgroRAG_GJR. `src`, `tests`, `docs` y `openspec` pertenecen a su raíz; las carpetas runtime se crean durante 00-foundation. `gusjrivas/PLN3_GJR` se conserva exclusivamente como referencia docente de lectura, sin copiar su historial ni modificarlo. La primera carga contiene planificación. Las ramas funcionales parten del commit documental de main.

## Secuencia y puertas de salida

| Etapa / cambio | Responsable de desarrollo | Dependencias | Entrega / puerta de salida | Esfuerzo orientativo |
|---|---|---|---|---|
| 00-foundation | Coordinador + backend | Plan revisado | Python fijado, paquete, uv.lock, CI, test de salud en TDD, reglas de importación | 8-12 h |
| 01-engram | Coordinador | 00 | Integración local probada, memoria recuperada tras reinicio, proyecto correcto | 2-4 h |
| 02-corpus | RAG/datos | 00, 01 | Fuentes admitidas, hashes, páginas y tablas verificadas, manifiesto reproducible | 10-14 h |
| 03-retrieval | RAG/datos | 02 | Baselines y RAG híbrido medibles, reranker español, índice versionado | 12-18 h |
| 04-agents-backend | Backend/agentes | 03 | Dos agentes, ciclo acotado, API y citas verificables, tests de fallos | 14-20 h |
| 05-frontend-hardening | Frontend + revisor | 04 | UI Python, auth, pruebas AppTest/E2E, caché, logs y límites | 12-18 h |
| 06-evaluation-delivery | Evaluación + coordinador | 05 | Benchmark congelado, resultados reales, informe PDF y demo reproducible | 14-20 h |

Total orientativo: 72-106 horas de trabajo efectivo, no calendario comprometido. Añadir margen si la extracción de tablas o la inferencia en CPU no alcanza el objetivo. Confirmar fecha de Teoría 7 al iniciar. Ajustar alcance antes de omitir TDD o evaluación.

## Primera sesión: resultado concreto

- Clonar el nuevo repositorio en C:\Repo\PLN3_AgroRAG_GJR siguiendo docs/start-here.md. Si ya existe una copia, verificar origin y preservar cambios locales antes de actualizar. No reinicializar Git.
- Revisar alcance, contratos y ADR. Registrar aceptación técnica por integración del PR; no atribuir aprobación a la cátedra.
- Iniciar sólo 00-foundation: test rojo del endpoint de salud, implementación mínima, refactor y CI.
- Registrar Python, SO, recursos reales y versiones. Resolver e inmovilizar dependencias del producto en uv.lock.
- Luego 01-engram: instalación estable en el mismo entorno que ejecuta los agentes, configuración y prueba de recuperación.
- Cerrar con una nota de estado que permita retomar. No comenzar simultáneamente corpus, UI y agentes.

## Trabajo paralelo posterior

Después de fijar los contratos de 04, frontend puede avanzar contra respuestas fixture mientras backend completa integración. Evaluación puede preparar el conjunto anotado tras 02; no mirar ni optimizar sobre test. Un coordinador es dueño de contratos, lockfile, configuración y merges. Cada PR representa una tarea o corte vertical, no una carpeta entera sin validación.

## Bloqueos reales y resolución

| Riesgo | Acción / criterio |
|---|---|
| Guía INTA no descargable | Usar documentos verificables ya identificados; registrar cobertura faltante |
| Permisos de redistribución no claros | Manifestar origen y procedimiento de obtención, no subir PDF a Git |
| BGE reranker demasiado lento | Benchmark en CPU; cambiar por candidato multilingüe documentado mediante ADR, repetir evaluación |
| Sin credenciales Pinecone/LLM | Avanzar pruebas offline; integración real permanece pendiente y no se declara terminada |
| Engram incompatible | Diagnosticar y registrar bloqueo local; continuar con specs/Git, sin inventar memoria persistente |
| Fecha de entrega cercana | Reducir cantidad de documentos y funciones accesorias; mantener agentes, TDD, citas y evaluación |

## Definition of Ready

Cada tarea tiene escenario, contrato, archivos, dependencia, prueba inicial y responsable. Toda decisión pendiente que afecte su comportamiento se resuelve antes del código; las decisiones irrelevantes para esa tarea no la bloquean.
