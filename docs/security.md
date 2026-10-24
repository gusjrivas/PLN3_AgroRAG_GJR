# Seguridad y robustez proporcionadas al alcance

## Modelo de uso

Demo local, un usuario, backend y UI publicados sólo en 127.0.0.1. Dos claves de rol reader/admin almacenadas en entorno o secret store local; la UI sólo posee reader en su servidor. Sin pretensión de multiusuario público ni exposición a Internet. CORS restringido si se habilita. Ingesta administrativa mediante CLI local.

## Riesgos y controles comprobables

| Riesgo | Control | Prueba |
|---|---|---|
| Instrucciones en PDF o pregunta | Contexto marcado como datos, herramientas allowlist, sin shell/web libre, contratos de salida | Documento fixture que ordena ignorar reglas no activa herramientas extra ni filtra secretos |
| Cita inventada | Resolver cada evidence_id en catálogo de la versión activa y construir cita en backend | ID desconocido se rechaza; cita cruzada entre corpus se rechaza |
| JSON válido pero afirmación falsa | Verificador sobre pasaje original + evaluación humana independiente | Casos con número/unidad alterados y afirmación sin soporte |
| Filtración de claves | Secretos fuera de prompts/logs/UI, redacción de errores y configuración mínima | Clave centinela ausente en logs y respuestas |
| Traversal o acceso a archivos arbitrarios | Cliente sólo envía evidence_id; catálogo resuelve rutas controladas | ../../ no accede a archivos; 404/422 |
| SSRF/ingesta arbitraria | Sin fetch de URL solicitado por usuario; admisión local curada | URL en consulta se trata como texto |
| Consumo descontrolado | Límite de input, concurrencia, llamadas, tokens, deadline y reintentos | Proveedor lento/fallido no supera presupuesto |
| XSS en UI | Render seguro sin unsafe_allow_html; links sólo desde catálogo validado | Texto HTML se muestra como datos |
| Sesiones mezcladas | Estado Streamlit aislado por sesión; caché no contiene datos de otra consulta contextual | Dos sesiones con contextos diferentes |

Las regex de sanitización no constituyen una defensa completa contra prompt injection. El verificador LLM tampoco garantiza veracidad. Medir errores residuales y abstenciones; no anunciar seguridad perfecta.

## Auditoría

Eventos estructurados con request_id, etapa, decisión breve, corpus_version y uso. Sin credenciales, prompts completos ni razonamiento privado. Rotación local configurable y política de retención inicial 7 días para logs de operación; artefactos científicos seleccionados se conservan con datos revisados y hashes. Separar errores operativos de rechazo por falta de evidencia.

El evento implementado tiene esquema cerrado: resultado/decisión, revisiones, duración, llamadas,
tokens, estimación y cache hit. No contiene pregunta, contexto, evidencia, URLs ni mensajes de
excepción. Los errores tempranos registran contadores en cero y un tipo allowlisted; no se infiere
uso parcial que no pudo medirse. La rotación/retención del proceso anfitrión sigue siendo una tarea
operacional de despliegue local, no una garantía del adaptador.
