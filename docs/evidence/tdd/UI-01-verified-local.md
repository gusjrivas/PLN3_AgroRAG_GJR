# Evidencia TDD: respuesta verificada local

Fecha: 24/10/2026. Responsable y revisor disponible: misma sesión Codex; revisión humana
pendiente. Rama: `fix/ui-repeat-guidance` (ampliación del PR #15).

## Diagnóstico

El 503 era correcto: `AGRO_MODEL` estaba vacío y no existía un servidor Ollama. Pinecone recupera
vectores pero no reemplaza al modelo generativo. Además, otro proyecto Docker ocupaba
`0.0.0.0:8000`; AgroRAG se levantó en `127.0.0.1:8010` y la UI conservó el puerto 8501.

Con Ollama y `qwen2.5:3b`, readiness pasó, pero una primera ejecución agotó el deadline de 60 s y
otra devolvió un borrador inconsistente. La salida no se aceptó ni se mostró como respuesta.

## RED

Las pruebas focalizadas de esquema estricto y mensajes accionables terminaron con exit code 1:
`5 failed`. Una prueba adicional de la inconsistencia `needs_clarification` con claims respaldados
también falló con `UpstreamError` antes de llegar al verificador. El contrato real de error usa
`error` en la raíz; la prueba corregida falló `3 failed` hasta que el cliente reconoció esa forma.

## GREEN

- Ollama recibe un JSON Schema cerrado y específico para investigador/verificador.
- Una aclaración vacía con claims no se aprueba: se reclasifica como borrador y pasa por la
  validación de IDs y por el verificador. Sin claims sigue siendo error operativo.
- El cliente traduce sólo códigos conocidos a mensajes útiles; nunca muestra el cuerpo arbitrario
  del proveedor.

Suite afectada inicial: exit code 0, `35 passed in 3.91s`.

## Prueba real

Se instaló el contenedor oficial `ollama/ollama` ligado sólo a localhost y un volumen persistente.
`qwen2.5:1.5b` completó dentro del límite una consulta autenticada real:

```text
READY=ready
QUERY_STATUS=answered
CITATIONS=2
ANSWER_PRESENT=True
```

No se imprimieron ni copiaron claves al contenedor. `.env` permanece ignorado por Git. El modelo
local es evidencia de integración operativa, no una evaluación agronómica ni científica.

## REFACTOR y cierre

- Suite completa final: exit code 0, `152 passed, 2 deselected in 10.91s`.
- Ruff check/formato: exit code 0, 143 archivos formateados.
- mypy: exit code 0, 32 archivos sin errores.
- import-linter: exit code 0, 2 contratos mantenidos.
- OpenSpec `05-frontend-hardening` estricto: válido.
- La suite inicialmente alcanzó el modelo real porque un helper construía `Settings` parciales y
  heredaba `.env`; se fijó `model=""` explícitamente en ese cliente contractual offline.

Commit y CI se registran al actualizar el PR #15.
