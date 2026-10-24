# Ejecutar la primera versión local

## Qué funciona

Descarga institucional con hashes fijados, ingesta PDF curada, catálogo SQLite inmutable, búsqueda BM25 con filtro de cultivo, API con clave reader y frontend Streamlit. Dos roles de generación (investigador/verificador) intercambian JSON y admiten una corrección. Ollama se conecta por HTTP sólo si se configura un modelo instalado.

La búsqueda pública sigue siendo un baseline lexical. Existe un adaptador administrativo para
indexar el catálogo con E5 en Pinecone y un adaptador CrossEncoder, pero todavía no están
inyectados en la API. No es la entrega final de la cátedra: faltan integración real aislada,
benchmark bilingüe y activación explícita. No hay Docker Compose aún.

## Preparar

Python 3.12 y uv. Desde el clon actualizado:

```powershell
uv sync --frozen
Copy-Item .env.example .env
```

Si `.env` ya existe, conservarlo y editarlo. Generar una clave local con `uv run python -c "import secrets; print(secrets.token_urlsafe(32))"` y colocarla en `AGRO_READER_KEY` de `.env`. Backend y frontend leen ese archivo, que está ignorado por Git. No enviar la clave a los modelos ni versionarla.

```powershell
uv run agro-rag download data/manifest.json
uv run agro-rag ingest data/manifest.json --output data/processed/catalogue
```

La primera descarga requiere Internet. Hash distinto, redirect inesperado o falta de texto bloquean admisión; no reemplazar hashes automáticamente. Los PDFs y SQLite quedan fuera de Git. La selección piloto actual produce 12 fragmentos de dos fuentes, con página PDF e impresa separadas.

## Dos terminales en la raíz

Backend:

```powershell
uv run uvicorn agro_rag.bootstrap.app:create_app --factory --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
uv run streamlit run src/agro_rag_ui/app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
```

Abrir http://127.0.0.1:8501. En **Explorar fuentes** probar: “¿Cuándo es crítico evitar la falta de agua en tomate?”. Expandir la fuente para ver página, edición y pasaje. No se utiliza un LLM en este modo.

OpenAPI: http://127.0.0.1:8000/docs. Los endpoints de datos requieren header `X-API-Key`. `GET /health/live` verifica sólo el proceso. `GET /health/ready` requiere corpus y modelo disponible. La API no descarga URLs recibidas en consultas.

## Activar generación real

Instalar/iniciar [Ollama](https://docs.ollama.com/) localmente y preparar un modelo que soporte JSON. Configurar `AGRO_MODEL` con su nombre exacto, incluido tag, tal como aparece en `ollama list`. Registrar modelo, digest y hardware antes de evaluar. Reiniciar backend y frontend después de editar `.env`.

Elegir **Respuesta verificada**. El investigador recibe la pregunta y los pasajes; el verificador puede aprobar, pedir revisión, aclarar o abstenerse. Una segunda solicitud de revisión termina en abstención. No se expone razonamiento privado. Se rechazan IDs inventados. El texto final se construye con los claims aprobados, y las citas se resuelven desde el catálogo.

Sin modelo configurado se devuelve 503. Una falla del modelo devuelve 502/504, no una respuesta agronómica. El presupuesto máximo es 12.000 tokens, hasta cuatro llamadas en este flujo y 60 s globales. El recuento se estima conservadoramente si Ollama no devuelve usage. El transporte es cancelable al vencer el deadline; no se realizan reintentos en esta versión. La API admite como máximo dos consultas concurrentes.

Una caída del proveedor de recuperación devuelve `503 RETRIEVAL_UNAVAILABLE`; una respuesta que
viola su contrato devuelve `502 RETRIEVAL_INVALID`. El detalle interno se conserva como causa del
error en el proceso pero no se expone por HTTP. Retrieval síncrono se ejecuta fuera del event loop y
queda incluido en el deadline global de la consulta.

Cada instancia del backend mantiene un LRU de retrieval de hasta 128 claves. Repetir la misma
pregunta normalizada con igual cultivo y corpus evita otra búsqueda y devuelve
`usage.cache_hit=true`. Cambiar cultivo, corpus o reiniciar el proceso produce miss. Los errores del
proveedor nunca se guardan en caché; las respuestas generadas tampoco se cachean.

El modelo no se descargó ni ejecutó en esta entrega. Las pruebas guionadas del flujo no prueban calidad factual de un LLM real. Una cita válida tampoco garantiza que la afirmación sea correcta: falta evaluación semántica y agronómica.

## Credencial local de Pinecone

Esta implementación adapta el patrón docente de
`Teoria1/Codigo/RAG/raglib/config.py` y `raglib/vector_pinecone.py` del commit
`1f4cdbb37f59a049ef9b35c482ccb1de850fbc43`: se conserva el contrato
`PINECONE_API_KEY`, pero la lectura queda centralizada en el bootstrap tipado y la clave se entrega
explícitamente al adaptador. No se copia la creación o limpieza automática de índices al arranque.

El adaptador no se activa al iniciar el backend. El comando administrativo usa prefijos
`query:`/`passage:`, revisión de modelo fijada, un namespace nuevo por versión de corpus y un
manifiesto de identidad. Rechaza sobrescribir namespaces, verifica conteo e IDs antes de publicar
el manifiesto y nunca guarda el texto de los fragmentos en metadata remota.

Instalar el grupo semántico únicamente en el entorno que realizará la indexación:

```powershell
uv sync --frozen --extra semantic
```

Con un índice compatible ya existente, ejecutar:

```powershell
uv run agro-rag index-pinecone
```

Si el índice configurado no existe, el comando falla sin crearlo. La creación serverless requiere
la decisión explícita `--create-index`; usa `PINECONE_INDEX`, `PINECONE_CLOUD` y
`PINECONE_REGION` del entorno. El nombre por defecto corresponde a E5 de 384 dimensiones y no es
compatible con índices de otra dimensión.

```powershell
uv run agro-rag index-pinecone --create-index
```

Para una sesión local, la opción más segura es una variable de proceso: no persiste la clave en un
archivo del proyecto ni en el historial de comandos.

```powershell
$pineconeSecret = Read-Host "PINECONE_API_KEY" -AsSecureString
$env:PINECONE_API_KEY = [Net.NetworkCredential]::new("", $pineconeSecret).Password
Remove-Variable pineconeSecret
```

Ejecutar backend, ingesta o pruebas de integración desde esa misma terminal. Cerrar la terminal
elimina la variable de proceso. No usar `setx`: persiste el secreto en el perfil de Windows.

Como alternativa local, copiar `.env.example` a `.env` y completar `PINECONE_API_KEY`. `.env` y
sus variantes están ignorados por Git, pero siguen siendo texto plano en disco: no sincronizarlos,
adjuntarlos ni copiarlos a tickets. El tipo `SecretStr` evita que el valor aparezca en la
representación de `Settings`; no cifra la variable ni el archivo. En CI o despliegues usar el secret
store de la plataforma e inyectar la misma variable.

## Pruebas

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run lint-imports
uv run pytest --cov --cov-report=term-missing
uv run coverage report --include="src/agro_rag/domain/*,src/agro_rag/application/*" --fail-under=90
uv run playwright install chromium
uv run pytest -m e2e tests/e2e -q
```

La suite normal excluye E2E porque el navegador se instala aparte; CI ejecuta ambos jobs obligatorios. E2E usa un PDF sintético, procesos HTTP reales y Chromium. No consulta proveedores pagos. `uv run pip-audit --local --skip-editable` audita dependencias con acceso a Internet; los hallazgos requieren resolución o excepción justificada explícita.
