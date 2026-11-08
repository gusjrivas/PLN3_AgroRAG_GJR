# META-01 — contrato de metadata de corpus

Fecha: 2026-11-07. Rama: `feat/meta-01-corpus-contract`. Base registrada: `eb9122d`.
HEAD al iniciar: `5f4f0bce52a64398cf7903253293da66e479b6a8`. Issue: #40. PR draft: #41.

## Alcance y decisión conservadora

Se ampliaron exclusivamente el modelo inmutable `Evidence`, los modelos de admisión del corpus y
las pruebas de integración de corpus. `source_type`, etapas, regiones y aplicabilidad usan los
vocabularios de ADR-016/OpenSpec. Las listas se conservan ordenadas y rechazan duplicados.

Para no inferir metadata ni obligar a curar `data/manifest.json` dentro de META-01, la ausencia de
`source_type` se representa como `None`, etapas/regiones ausentes como tuplas vacías y
`applicability` como `unknown`. Esto mantiene compatible el manifiesto real actual sin asignarle una
clasificación no respaldada. La curación real corresponde a META-05.

META-01 sólo comprueba que una región declarada en el manifiesto pertenezca al vocabulario
autorizado. No puede demostrar que esa declaración tenga respaldo documental ni distinguir por sí
solo una región inferida: esa verificación es un control humano y trazable de META-05.

## Caracterización

Comando:

```text
python -m pytest tests/integration/test_corpus.py -q
```

Resultado previo a los tests nuevos: exit code `0`, `17 passed in 11.13s`.

## RED

Se escribieron primero los escenarios `META-01-propagacion`, `META-01-rechazo` y `META-01-version`.

Comando:

```text
python -m pytest tests/integration/test_corpus.py -q -k "metadata_is_propagated or uncontrolled_or_unsupported or metadata_change_creates"
```

Resultado: exit code `1`, `2 failed, 5 passed, 16 deselected in 2.07s`.

Fallas funcionales observadas:

- `test_metadata_is_propagated_to_evidence`: Pydantic informó cuatro `extra_forbidden` porque el
  contrato todavía no admitía `source_type`, `growth_stages`, `applicable_regions` ni
  `applicability`.
- `test_metadata_change_creates_new_version_without_activation_on_failure`: `Evidence` no tenía
  `source_type` (`AttributeError`).

Las cinco variantes de rechazo ya pasaban en RED por la política heredada `extra="forbid"`: el
sistema rechazaba cualquier campo nuevo, válido o inválido. No se fabrica una fase roja para ese
comportamiento existente. El cambio agrega aceptación controlada y mantiene el rechazo específico,
incluido el diagnóstico por campo, duplicados y preservación del puntero activo.

## GREEN

Comando focalizado, sin red ni modelos:

```text
python -m pytest tests/integration/test_corpus.py -q -k "metadata_is_propagated or uncontrolled_or_unsupported or metadata_change_creates"
```

Resultado: exit code `0`, `7 passed, 16 deselected in 1.27s`.

La versión continúa derivándose del `manifest.model_dump()` serializado de forma determinista y el
`evidence_id` incluye esa versión. Por eso un cambio de metadata crea versión e IDs nuevos sin
cambiar PDF o chunking. La validación del manifiesto ocurre antes de crear o reemplazar
`active.json`. La lectura desde SQLite reconvierte arrays JSON a tuplas para preservar la igualdad e
inmutabilidad de `Evidence`.

## REFACTOR y regresión

```text
python -m pytest tests/integration/test_corpus.py -q
```

Exit code `0`: `23 passed in 4.79s`.

```text
python -m pytest tests/integration/test_catalogue_backup.py tests/unit/test_retrieval.py tests/unit/test_retrieval_runtime.py tests/contract/test_query_api.py -q
```

Exit code `0`: `30 passed, 1 warning in 5.87s`. La advertencia es una deprecación externa existente
de Starlette TestClient/httpx.

```text
python -m ruff check src/agro_rag/domain/evidence.py src/agro_rag/infrastructure/corpus.py tests/integration/test_corpus.py
```

Exit code `0`: `All checks passed!`.

```text
python -m mypy src/agro_rag/domain/evidence.py src/agro_rag/infrastructure/corpus.py
```

Exit code `0`: `Success: no issues found in 2 source files`.

```text
.venv\Scripts\lint-imports.exe
```

Exit code `0`: 2 contratos conservados, 0 rotos (`71 files`, `197 dependencies`). `uv` no estaba
disponible en `PATH`, por lo que se ejecutó el binario instalado del entorno virtual.

## Correcciones de revisión independiente

La revisión independiente detectó dos bloqueantes: `Evidence.__post_init__` convertía secuencias a
tuplas sin validar valores runtime, y un snapshot nuevo se activaba sin relectura completa. Se
agregaron pruebas antes de corregir ambos comportamientos.

RED propio de esta sesión:

```text
python -m pytest tests/integration/test_corpus.py -q -k "snapshot_metadata_is_validated or new_snapshot_is_verified"
```

Exit code `1`: `9 failed, 23 deselected in 2.64s`. Ocho casos demostraron que payloads SQLite con
valores fuera de vocabulario, duplicados o strings en lugar de secuencias eran aceptados. El noveno
demostró que una falla controlada de verificación posterior a escritura no era invocada antes de
activar.

GREEN propio de esta sesión, mismo comando: exit code `0`,
`9 passed, 23 deselected in 1.79s`. El dominio ahora valida scalars y secuencias al construir
`Evidence`, acepta listas JSON válidas y las convierte a tuplas, y rechaza strings sin convertirlos
en tuplas de caracteres. `build_catalogue` relee y compara el snapshot completo antes de escribir
`active.json`; un target inválido puede quedar como archivo no activo para diagnóstico.

Regresión propia posterior a las correcciones:

```text
python -m pytest tests/integration/test_corpus.py -q
```

Exit code `0`: `32 passed in 6.33s`.

```text
python -m pytest tests/integration/test_catalogue_backup.py tests/unit/test_retrieval.py tests/unit/test_retrieval_runtime.py tests/contract/test_query_api.py -q
```

Exit code `0`: `30 passed, 1 warning in 6.01s`.

Ruff, mypy e import-linter se repitieron en esta sesión con exit code `0`: Ruff sin hallazgos, mypy
sin issues en los dos archivos fuente y 2 contratos de importación conservados de 2.

Validación OpenSpec estricta propia:

```text
npx --yes @fission-ai/openspec@latest validate 08-metadata-aware-retrieval --strict
```

Exit code `0`: `Change '08-metadata-aware-retrieval' is valid`.

El coordinador repitió la suite completa después de las correcciones: exit code `0`, `313 passed, 1
skipped, 3 deselected, 1 warning in 36.48s`. También repitió Ruff y mypy sobre todo `src`/`tests`,
import-linter, OpenSpec estricto y `git diff --check`; todos terminaron con exit code `0`.

## Estado de entrega y revisión

- Commit funcional: `2ec2dbc` (`feat: add curated corpus metadata contract`).
- Revisión del diff: auto-revisión completada; una revisión independiente encontró los dos
  bloqueantes anteriores y fueron corregidos. El mismo revisor independiente confirmó después que
  no quedan bloqueantes y repitió corpus, suites afectadas, Ruff, mypy, import-linter, OpenSpec y
  `git diff --check` con resultado satisfactorio.
- Limitaciones: no se modificó ni curó el manifiesto real, no se reindexó Pinecone y no se ejecutó
  ninguna prueba live, red, LLM o modelo. El vocabulario regional inicial sólo admite
  `ar-mendoza-oasis-norte`; ampliarlo requiere actualizar el contrato autorizado.
- Riesgo de integración: consumidores API que serializan `Evidence` mediante `asdict` expondrán los
  cuatro campos aditivos. META-03 debe revisar y fijar ese contrato; no se editó API en META-01.
