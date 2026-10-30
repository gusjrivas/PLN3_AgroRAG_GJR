# Ejecutar AgroRAG V2 con contenedores

Estado: implementación incremental. Este runbook documenta sólo capacidades verificadas; Compose,
gateway productivo, catálogo administrativo, rollback y garak se completan en fases posteriores del
cambio OpenSpec 07.

## Requisitos

- Docker Engine con BuildKit.
- Docker Compose Plugin para las fases siguientes.
- No se necesita Python ni uv del proyecto para construir o ejecutar las imágenes.

## Construir imágenes

Las bases Python 3.12 y uv están fijadas por digest. El builder instala desde `uv.lock` y los
targets finales comparten un virtualenv no editable, sin dependencias de desarrollo.

```powershell
docker build --target api --build-arg APP_VERSION=0.2.0 --build-arg VCS_REF=<commit> -t agrorag-api:<commit> .
docker build --target ui --build-arg APP_VERSION=0.2.0 --build-arg VCS_REF=<commit> -t agrorag-ui:<commit> .
```

No pasar claves mediante `--build-arg`. `.dockerignore` excluye `.env*`, Git, entornos, tests,
outputs, corpus local y libros de evidencia. Las imágenes ejecutan como UID/GID `10001:10001`.

## Smoke de imagen

API sin catálogo/modelo sigue exponiendo sólo liveness; readiness permanece cerrada:

```powershell
docker run --rm -p 127.0.0.1:18000:8000 agrorag-api:<commit>
```

En otra terminal, `http://127.0.0.1:18000/health/live` debe devolver `{"status":"ok"}`. Para UI:

```powershell
docker run --rm -p 127.0.0.1:18501:8501 agrorag-ui:<commit>
```

`http://127.0.0.1:18501/_stcore/health` debe responder 200. Sin reader key, la pantalla muestra la
advertencia segura y no consulta API.

## Secretos en runtime

Los despliegues usarán archivos montados y una única variable por secreto:

- `AGRO_READER_KEY_FILE=/run/secrets/reader_key` en API y UI.
- `OPENAI_API_KEY_FILE=/run/secrets/openai_api_key` sólo en API cuando se seleccione OpenAI.
- `PINECONE_API_KEY_FILE=/run/secrets/pinecone_api_key` sólo en los perfiles que lo necesiten.

Definir a la vez el valor directo y `*_FILE`, o montar un archivo ausente/vacío, bloquea startup.
La imagen no contiene secretos, catálogo, certificados ni configuración productiva.

## Limitaciones todavía abiertas

- Aún no hay archivos Compose ni volumen de catálogo en este corte.
- El scan Docker Scout local requiere autenticación y no se consideró ejecutado; el gate de CI debe
  usar un scanner no interactivo y registrar hallazgos/excepciones.
- Estas imágenes contienen el perfil BM25 base. El job semántico/administrativo se define de forma
  separada para no incorporar dependencias pesadas al runtime API/UI.
