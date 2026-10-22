# Frontend Python y experiencia de uso

Streamlit como cliente de FastAPI, con httpx y timeout explícito. UI no carga modelos ni consulta Pinecone. Cliente HTTP inyectable mediante factory para tests AppTest. Estado separado por sesión, sin variables globales mutables para preguntas/respuestas.

## Pantalla y comportamiento

Consulta en español, selector opcional tomate/lechuga, contexto opcional. Botón Consultar dispara una única llamada por envío; reruns no repiten inferencia. Mostrar estado de espera, deshabilitar reenvío y asociar respuesta a su pregunta, descartando resultados de solicitud anterior si cambia el identificador activo.

Estados: bienvenida, validación, procesando, answered, needs_clarification, insufficient_evidence y error operativo. Aclaraciones conservan pregunta/contexto y piden sólo lo faltante; la nueva llamada usa clarification_context explícito. No inventar estado backend ni usar una conversación global.

Respuesta muestra texto, limitaciones y citas expandibles con pasaje exacto, título, edición, página física y página impresa cuando exista. Enlace externo sólo al origen autorizado del catálogo. Panel técnico plegable para latencia/tokens/versión; detalles de implementación no ocupan el flujo principal. UI no confunde sin evidencia con API caída.

## Calidad de frontend

Etiquetas visibles, navegación por teclado, contraste suficiente, mensajes comprensibles, texto seleccionable y diseño usable en notebook. Pruebas AppTest primero para estados, referencias y no duplicación. Playwright Python para recorrido real browser/API y revisión de teclado. No usar HTML inseguro para mostrar documentos. No exponer claves en campos del cliente ni logs.

La calidad visual se verifica además manualmente, porque AppTest valida comportamiento y no toda la accesibilidad ni layout. Registrar capturas de evidencia en entrega final con datos del corpus público.
