# Ejecutar la primera versión local

## Qué funciona

Descarga institucional con hashes fijados, ingesta PDF curada, catálogo SQLite inmutable, búsqueda BM25 con filtro de cultivo, API con clave reader y frontend Streamlit. Dos roles de generación (investigador/verificador) intercambian JSON y admiten una corrección. OpenAI u Ollama se conectan por HTTP sólo cuando se configura el proveedor correspondiente.

La búsqueda pública usa BM25 por defecto. El runtime permite activar explícitamente vector,
hybrid o hybrid_rerank sobre el namespace E5/Pinecone ya indexado, con identidad verificada,
tokenizer fijado y CrossEncoder opcional. No se degrada silenciosamente a BM25. El default no cambia
porque faltan qrels humanos, E1/E2/E3 y resolver la latencia observada del reranker. No hay Docker
Compose aún; no es un requisito de la cátedra.

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

La primera descarga requiere Internet. Hash distinto, redirect inesperado o falta de texto bloquean admisión; no reemplazar hashes automáticamente. Los PDFs y SQLite quedan fuera de Git. La selección piloto actual produce 27 fragmentos de cinco fuentes institucionales, con página PDF e impresa separadas.

## Dos terminales en la raíz

Backend:

```powershell
uv run uvicorn agro_rag.bootstrap.app:create_app --factory --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
uv run streamlit run src/agro_rag_ui/app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
```

Abrir http://127.0.0.1:8501. En **Explorar fuentes** probar: “¿Cuándo es crítico evitar la falta de agua en tomate?”. Este modo devuelve fragmentos, no una respuesta redactada. Expandir la fuente para ver página, edición y pasaje. Después de un resultado, usar **Nueva consulta** para descartarlo y mostrar un formulario vacío. No se utiliza un LLM en este modo.

OpenAPI: http://127.0.0.1:8000/docs. Los endpoints de datos requieren header `X-API-Key`. `GET /health/live` verifica sólo el proceso. `GET /health/ready` requiere corpus y modelo disponible. La API no descarga URLs recibidas en consultas.

## Activar generación real

### Opción OpenAI (sin modelo local)

Crear una API key en la plataforma de OpenAI y guardarla únicamente en `.env`, que está ignorado
por Git. No usar la clave de una cuenta de ChatGPT: la API se autentica y factura por separado.

```dotenv
AGRO_MODEL_PROVIDER=openai
OPENAI_API_KEY=valor-secreto
AGRO_OPENAI_MODEL=gpt-4o
```

El backend usa Responses API con Structured Outputs y `store=false`; investigador y verificador
reciben la pregunta, el contexto y los pasajes recuperados. La UI nunca recibe la API key. Reiniciar
backend y frontend después de cambiar el proveedor. `GET /health/ready` valida credencial y acceso
al modelo sin generar texto. La prueba automática usa transporte simulado: una prueba real requiere
una key, acceso al modelo y puede generar costo.

### Opción Ollama (local)

Instalar/iniciar [Ollama](https://docs.ollama.com/) localmente y preparar un modelo que soporte JSON. Configurar `AGRO_MODEL` con su nombre exacto, incluido tag, tal como aparece en `ollama list`. Registrar modelo, digest y hardware antes de evaluar. Reiniciar backend y frontend después de editar `.env`.

Alternativa local probada con Docker y CPU:

```powershell
docker run -d --name agrorag-ollama -p 127.0.0.1:11434:11434 -v agrorag-ollama:/root/.ollama ollama/ollama
docker exec agrorag-ollama ollama pull qwen2.5:1.5b
```

En ese caso usar `AGRO_MODEL=qwen2.5:1.5b`. El modelo de 3B superó el deadline total de 60 s en
el equipo de prueba sólo CPU; no se recomienda allí. Si otro servicio ya ocupa el puerto 8000,
iniciar FastAPI en otro puerto, por ejemplo 8010, y establecer
`AGRO_API_URL=http://127.0.0.1:8010` en el proceso del frontend.

Elegir **Respuesta verificada**. El investigador recibe la pregunta y los pasajes; el verificador puede aprobar, pedir revisión, aclarar o abstenerse. Una segunda solicitud de revisión termina en abstención. No se expone razonamiento privado. Se rechazan IDs inventados. El texto final se construye con los claims aprobados, y las citas se resuelven desde el catálogo.

Al completar la consulta, el resultado verificado reemplaza al formulario y muestra una
confirmación visible de OpenAI, seguida de la respuesta, sus fuentes y **Nueva consulta**. El
formulario vacío reaparece sólo después de presionar ese botón.

Sin modelo configurado se devuelve 503. Una falla del modelo devuelve 502/504, no una respuesta agronómica. El presupuesto máximo es 12.000 tokens, hasta cuatro llamadas en este flujo y 60 s globales. El recuento se estima conservadoramente si Ollama no devuelve usage. El transporte es cancelable al vencer el deadline; no se realizan reintentos en esta versión. La API admite como máximo dos consultas concurrentes.

Una caída del proveedor de recuperación devuelve `503 RETRIEVAL_UNAVAILABLE`; una respuesta que
viola su contrato devuelve `502 RETRIEVAL_INVALID`. El detalle interno se conserva como causa del
error en el proceso pero no se expone por HTTP. Retrieval síncrono se ejecuta fuera del event loop y
queda incluido en el deadline global de la consulta.

Cada instancia del backend mantiene un LRU de retrieval de hasta 128 claves. Repetir la misma
pregunta normalizada con igual cultivo y corpus evita otra búsqueda y devuelve
`usage.cache_hit=true`. Cambiar cultivo, corpus o reiniciar el proceso produce miss. Los errores del
proveedor nunca se guardan en caché; las respuestas generadas tampoco se cachean.

Las consultas configuradas por bootstrap emiten un evento JSON al logger `agro_rag.audit`. El
evento contiene sólo identificadores operativos, resultado, decisión, duración, uso y cache hit. No
incluye pregunta, contexto, evidencia, prompt ni detalle de excepción. La configuración de logging
del proceso anfitrión determina destino, rotación y retención.

El corte inicial no descargaba ni ejecutaba modelos. Después se documentaron un smoke local real con
Ollama `qwen2.5:1.5b` y una respuesta visible con OpenAI; esas ejecuciones comprueban integración,
no calidad factual. Las pruebas guionadas tampoco sustituyen la evaluación: una cita válida no
garantiza que la afirmación sea correcta y aún falta evaluación semántica y agronómica.

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

## Activar retrieval semántico de forma explícita

Primero ejecutar la indexación administrativa anterior y conservar el namespace publicado. Los
modelos y tokenizer deben existir en caché local cuando se mantiene el default seguro
`AGRO_SEMANTIC_LOCAL_FILES_ONLY=true`; el servidor no descarga pesos durante startup.

Configurar en `.env`:

```dotenv
AGRO_RETRIEVAL_MODE=hybrid
PINECONE_NAMESPACE=corpus-<version-activa>
AGRO_RETRIEVAL_TOKENIZER_MODEL=<tokenizer-exacto-del-generador>
AGRO_RETRIEVAL_TOKENIZER_REVISION=<revision-inmutable>
AGRO_SEMANTIC_LOCAL_FILES_ONLY=true
```

Los valores permitidos son `bm25`, `vector`, `hybrid` y `hybrid_rerank`. Este último también carga
el reranker configurado. Para cualquier modo semántico, startup falla si falta la credencial, el
tokenizer o si el manifiesto remoto no coincide exactamente en corpus, embedding, revisión y
dimensión. Eso es intencional: no se presenta un resultado lexical como híbrido.

El tokenizer debe corresponder al modelo generador efectivo. Para Ollama, usar el tokenizer de la
misma familia/revisión del modelo instalado; para un proveedor cuyo tokenizer exacto no pueda
fijarse localmente, mantener BM25 hasta incorporar un contador compatible. La API publica el modo
activo en `/v1/corpus` y `<modo>_preview` en `/v1/preview/search`.

Esta activación permite una corrida controlada, pero no sustituye la revisión humana de qrels ni
autoriza declarar mejora científica. Después de cambiar el modo, repetir E1/E2/E3 con manifiesto,
hardware y versiones registrados.

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

### Checklist manual y recorrido Playwright del benchmark

Generar el PDF rellenable de 60 casos (campos de tester, Pass, Fail, resultado y observaciones):

```powershell
uv run python scripts/build_benchmark_checklist.py
```

El archivo queda en `output/pdf/agro-rag-benchmark-checklist.pdf`. Para automatizar el recorrido
contra una UI ya levantada, instalar Chromium una sola vez y ejecutar primero un caso de humo:

```powershell
uv run playwright install chromium
uv run python scripts/run_benchmark_playwright.py --url http://127.0.0.1:8501 --limit 1
```

Para repetir regresiones concretas sin ejecutar todo el benchmark, usar `--query-id` una o más
veces; el runner preserva el orden original y falla ante un ID desconocido:

```powershell
uv run python scripts/run_benchmark_playwright.py --query-id dev-r-005 --query-id test-r-006
```

Quitar `--limit 1` para recorrer los 60 casos. Cada consulta usa el proveedor configurado y puede
tener costo y latencia reales. El resultado incremental se guarda en
`output/evaluation/benchmark-live-results.jsonl`, incluso si un caso falla. Playwright compara el
estado visible (`answered`, `needs_clarification` o `insufficient_evidence`); la corrección del
contenido, los claims y las citas se valida manualmente en el PDF.

## Verificar la entrega

Regenerar el informe y comprobar offline que el paquete contiene runbook, manifiesto, guion,
fuente y PDF, con hashes imprimibles y sin leer `.env`:

```powershell
uv run python scripts/build_report.py
uv run agro-rag verify-delivery --root .
```

El comando no instala dependencias, descarga corpus ni llama proveedores. Los resultados
científicos definitivos siguen sujetos al benchmark humano y a las ejecuciones reales E1/E2/E3.
