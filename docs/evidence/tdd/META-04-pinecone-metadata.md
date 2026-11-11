# META-04 — metadata Pinecone e identidad remota

Fecha: 2026-11-09. Rama: `feat/meta-04-pinecone-metadata`.
Base: `471aa420a696b68c64addca429f2613a82d9ebde`. Issue: #47.
Responsable: agente META-04, coordinado por Gustavo Julián Rivas.

## Alcance y caracterización

Se modificaron el adaptador Pinecone, la composición runtime, sus pruebas unitarias y esta
evidencia. No se editaron API, caso de uso, política local, corpus, tests live ni fuentes `Teoria*`.
La implementación y todas las verificaciones fueron offline, con dobles locales y sin
credenciales, red, namespaces remotos ni modelos descargados.

La caracterización inicial de `tests/unit/test_pinecone.py` alcanzó 12 pruebas correctas y un error
de entorno: pytest no podía crear su directorio temporal global fuera del workspace autorizado.
Las ejecuciones posteriores fijaron un `--basetemp` controlado y desactivaron sólo el cache de
pytest; no se cambió comportamiento del producto.

Antes del cambio, `PineconeVectorRanker.rank` aceptaba `str | None`, aplicaba identidad y cultivo,
y `index_catalogue` guardaba sólo `kind`, `evidence_id`, `corpus_version` y cultivo opcional. El
manifiesto ya se publicaba después de verificar todos los IDs; esa garantía se conservó.

## RED

Se escribieron primero escenarios observables para:

- consumir `RetrievalFilters` sin romper el argumento legacy de cultivo;
- empujar etapa y región de forma conservadora, preservando evidencia general o sin ese campo;
- incluir en cada vector sólo identidad y metadata curada admitida;
- excluir explícitamente texto completo, texto original, URLs, páginas, secciones, offsets y título;
- mantener la garantía existente de que una verificación parcial no publica manifiesto.

```text
python -m pytest tests/unit/test_pinecone.py::test_vector_ranker_uses_safe_structured_context_filters tests/unit/test_pinecone.py::test_index_payload_contains_safe_metadata_without_text tests/unit/test_pinecone.py::test_partial_metadata_index_does_not_publish_manifest -q --basetemp C:\Repo\PLN3_AgroRAG_GJR\.tmp-meta04-red -p no:cacheprovider
# exit 1: 2 failed, 1 passed
```

Los dos fallos esperados mostraron que el objeto `RetrievalFilters` era tratado como si fuese el
valor de `crop` y que el payload todavía no contenía metadata contextual. El caso de manifiesto ya
pasaba y se registró como caracterización; no se fabricó una fase roja para comportamiento
preexistente.

## GREEN

El adaptador normaliza `FilterInput`, por lo que conserva `str | None` y acepta el contrato
estructurado. Toda consulta remota exige `kind=chunk` y la versión de corpus. Cultivo sigue siendo
estricto pero permite evidencia sin cultivo. Para etapa y región, el prefiltro admite:

1. coincidencia explícita;
2. `applicability=general`;
3. ausencia del campo contextual.

Esto evita que Pinecone descarte evidencia general o desconocida. Es deliberadamente
conservador: la política en application y el catálogo local siguen siendo la autoridad para
clasificar y excluir incompatibles.

El payload de chunks ahora contiene identidad, `crop`, `source_type`, `growth_stages`,
`applicable_regions` y `applicability`, todos derivados del dominio validado. Las secuencias se
serializan como listas de strings y los campos vacíos no se publican. Nunca se agrega texto, URL,
ruta local ni datos de página/sección. El payload y orden del manifiesto no cambiaron.

```text
$env:PYTHONPATH='C:\Users\gusta\AppData\Local\Temp\PLN3_AgroRAG_GJR_meta04\src'; python -m pytest tests/unit/test_pinecone.py -q --basetemp C:\Repo\PLN3_AgroRAG_GJR\.tmp-meta04-green-local -p no:cacheprovider
# exit 0: 14 passed
```

`PYTHONPATH` apunta al worktree porque la virtualenv compartida tiene un editable instalado hacia
el worktree raíz; sin esta asignación pytest importaría esa copia y no la rama META-04.

## Corrección de revisión: integración runtime

La revisión independiente detectó que `_CropOnlyVectorRanker` seguía reduciendo el contrato
estructurado a cultivo durante la composición real. Se amplió explícitamente el alcance de
META-04 al bootstrap y su prueba runtime. Primero se cambió el escenario observable para exigir
que cultivo, etapa y región lleguen a Pinecone:

```text
python -m pytest tests/unit/test_retrieval_runtime.py::test_hybrid_runtime_delivers_complete_filters_to_pinecone_and_closes_resources -q -p no:cacheprovider
# exit 1: 1 failed
```

El fallo mostró un filtro remoto con identidad y cultivo, pero sin `growth_stages` ni
`applicable_regions`. Luego se eliminó `_CropOnlyVectorRanker` y se entregó directamente el
`PineconeVectorRanker`, que ya implementa `FilterInput`. El mismo comando terminó con `1 passed`.
La regresión focal combinada quedó así:

```text
python -m pytest tests/unit/test_pinecone.py tests/unit/test_retrieval_runtime.py -q --basetemp C:\Repo\PLN3_AgroRAG_GJR\.tmp-meta04-review-focal -p no:cacheprovider
# exit 0: 21 passed
```

## REFACTOR y regresión

No se alteraron batching, namespace fresco, dimensión, orden de upserts, verificación de IDs,
sentinela del manifiesto ni validación de identidad. La firma usa el alias compartido
`FilterInput`; no duplica la política local.

```text
python -m pytest tests/unit -q --basetemp C:\Repo\PLN3_AgroRAG_GJR\.tmp-meta04-unit -p no:cacheprovider
# exit 0: 214 passed, 1 skipped

python -m pytest -q --basetemp C:\Repo\PLN3_AgroRAG_GJR\.tmp-meta04-full -p no:cacheprovider
# exit 0: 330 passed, 1 skipped, 3 deselected, 1 warning

python -m pytest -q --basetemp C:\Repo\PLN3_AgroRAG_GJR\.tmp-meta04-review-full -p no:cacheprovider
# exit 0 tras la corrección: 330 passed, 1 skipped, 3 deselected, 1 warning
```

El skip conocido corresponde a bits POSIX del runner Garak en Windows. La advertencia conocida es
la deprecación externa de Starlette TestClient/httpx. Los tres casos deseleccionados son e2e/live
por la configuración offline del proyecto.

Controles finales:

- `python -m ruff check` sobre los cuatro archivos Python de propiedad:
  exit 0;
- `python -m ruff format --check` sobre los mismos cuatro archivos:
  exit 0, 4 archivos ya formateados;
- `python -m mypy src`: exit 0, 38 archivos sin issues;
- `lint-imports`: exit 0, 2 contratos conservados;
- `npx --yes @fission-ai/openspec@latest validate 08-metadata-aware-retrieval --strict`:
  exit 0, cambio válido;
- `git diff --check`: exit 0.

## Estado de entrega

- Sin commit ni push, por instrucción del coordinador.
- La revisión independiente detectó el bloqueo de integración runtime; quedó corregido con RED y
  GREEN reales y la re-revisión independiente aprobó el corte sin hallazgos funcionales.
- El puente temporal de cultivo fue eliminado: el runtime entrega el objeto estructurado completo
  al adaptador compatible.
- No se ejecutó el escenario LIVE opcional ni se creó, modificó o consultó ningún índice real.
