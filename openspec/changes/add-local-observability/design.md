## Contrato compartido

El adaptador manual conserva los spans `POST /v1/query`, `retrieval`, `researcher` y `verifier`. `AGRO_TRACING_ENABLED=true` habilita la instrumentación. Sin `AGRO_OTLP_ENDPOINT` exporta a consola y con un origen HTTP explícito exporta mediante OTLP/HTTP. Los proveedores tienen ciclo de vida por instancia de API.

| Instrumento | Unidad | Atributos |
| --- | --- | --- |
| `agro_rag.query.requests` | conteo | `http.response.status_code` |
| `agro_rag.query.duration` | segundos | `http.response.status_code` |
| `agro_rag.query.outcomes` | conteo | `outcome` del conjunto cerrado de auditoría |
| `agro_rag.retrieval.cache.lookups` | conteo | `cache.result` con valores `hit` o `miss` |

El middleware registra HTTP, el evento de auditoría aporta sólo el resultado y el punto de lookup aporta la métrica de caché. Las dos últimas señales se enlazan mediante un puerto acotado al contexto de consulta. Los conteos de caché incluyen los lookups efectivamente iniciados aunque falle una búsqueda posterior. Los instrumentos excluyen texto, cabeceras, credenciales e identificadores de consulta.

## Despliegue y verificación

El overlay local conecta API y Collector a través de Compose y publica Grafana en loopback. El tablero se provisiona desde archivos versionados. El exportador usa una cola de trazas y recolección periódica de métricas. La verificación cubre consola heredada, opt-in, payload OTLP, ausencia de datos sensibles, caída y recuperación del Collector, arranque desde Compose y recorrido desde Streamlit.

La implementación corre en `feat/observability-grafana`, sobre `d0111a3`, en una sola sesión. El coordinador verifica el diff, TDD, dependencias y las pruebas del stack. El merge a main requiere verificación completa y CI verde.
