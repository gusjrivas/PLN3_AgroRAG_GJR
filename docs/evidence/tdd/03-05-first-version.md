# Primera consulta vertical: retrieval, agentes, API y UI

Rama feat/03-query. Responsable y revisión: misma sesión Codex, sin revisor independiente. Base de código: PR #3. Alcance incremental ADR-012, no cierre de todas las etapas 03/04/05.

## Evidencia TDD

- Retrieval: 3 fallos por capacidades ausentes antes de implementar BM25, filtro/cap por fuente, caché por instancia y RRF. Log 03-red.txt. RRF queda preparado y probado para la etapa híbrida, no se usa como si existiera Pinecone.
- Agentes: 11 fallos previos a QueryService. Log 04-red.txt. Los 3 tests de retrieval ya estaban verdes en esa corrida. Se cubren aprobación, revisión acotada, abstención, aclaración, evidencia inventada, tokens y cancelación por deadline.
- Adapter/API: 6 fallos previos al adaptador Ollama/configuración HTTP. Log 04-api-red.txt.
- OpenAPI: fallo real por ausencia de QueryResponse en el schema; se añadieron DTO de respuesta e invariantes. Log 04-schema-red.txt.
- Cantidades: el test de porcentaje convertido a litros detectó una llamada indebida al modelo antes de aclarar; se agregó guardia de contexto para preguntas cuantitativas. Log 04-quantity-red.txt.
- UI: los tests de cliente HTTP se escribieron antes del cliente (2 rojos válidos). El primer harness AppTest tenía además una ruta relativa equivocada; esos 3 fallos no se presentan como RED funcional válido. Se corrigió la ruta absoluta y pasaron. Esta limitación del RED inicial de renderizado queda documentada, sin fabricar evidencia retrospectiva.
- Aclaración UI: después de corregir el harness, un test falló por faltar el segundo formulario (sólo había un textarea). Log 05-clarification-red.txt. Se implementó contexto explícito preservando pregunta original y límite de tres aclaraciones.
- Regresión final: 54 tests aprobados, 1 E2E excluido de la suite rápida, cobertura global 88.72% y core 94% (redondeado). Log 04-05-green.txt. Ruff, mypy e imports correctos.
- E2E: `uv run pytest -m e2e tests/e2e -q`: 1 aprobado, navegador Chromium -> Streamlit -> FastAPI -> PDF sintético. Prueba de regresión, no se le atribuye RED retrospectivo.

## Verificaciones operativas

Auditoría `pip-audit --local --skip-editable`: ninguna vulnerabilidad conocida al ejecutar, antes de incorporar Playwright al grupo de desarrollo; repetir en el gate final.

Se fijó Playwright 1.56.0 después de que la descarga del navegador de 1.64.0 devolviera un ZIP inválido en este entorno. El instalador de 1.56.0 obtuvo Chromium desde su mirror oficial. Es una dependencia de pruebas, no navegador distribuido con el producto. Se conserva el pin para reproducir el smoke; revisar actualización en mantenimiento.

No se cambió el contrato de liveness: sigue indicando sólo proceso. Su regresión sobre readiness pasó de esperar 404 a 401 porque ahora existe el endpoint protegido. No se rebajaron umbrales de cobertura ni se excluyó código para alcanzar las metas.

Smoke adicional con el corpus real: navegador consultó el período crítico del tomate y desplegó dos pasajes de INTA con páginas físicas e impresas. La prueba exploratoria se ejecutó con API y UI locales en el mismo proceso de verificación, sin modelo.

## Riesgos/pendientes

- Falta modelo real instalado y evaluación del investigador/verificador. Prompt injection se reduce mediante separación de datos y ausencia de herramientas de ejecución; no se declara resistencia semántica demostrada con LLM real.
- Falta recuperación semántica/Pinecone, CrossEncoder, búsqueda focalizada del verificador y LangGraph. El flujo inicial es una máquina acotada en Python estándar; mantiene el puerto desacoplado.
- Caché BM25 por snapshot y resultados con métricas de llamadas/tokens/tiempo. `usage.cache_hit` indica caché de respuesta (no implementada, false); falta instrumentación de hits/ahorro de retrieval y audit sink durable.
- Corpus piloto pequeño y sólo pasajes revisados. Falta benchmark anotado de 60 casos, ablations, evaluación y entrega PDF.
- Docker Compose, prueba nativa Windows y la integración Engram de la notebook siguen pendientes.

No hay métricas científicas fabricadas ni simulación presentada como llamada a proveedor real. La etapa permanece abierta y las limitaciones figuran en la UI y el runbook.
