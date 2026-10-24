# RET-CORPUS-SYNC — catálogo, Pinecone y runtime ampliados

Fecha: 24/10/2026. Responsable: coordinador/RAG, misma sesión. Rama:
`fix/corpus-runtime-sync`. No se imprimieron ni versionaron credenciales.

## Estado sincronizado

- Catálogo local: versión
  `e9929440f552b1c7be1349118a1ee98c6cdba41fbd2e2ce05343247c918dfb7d`, 27 evidencias y
  cinco fuentes.
- Pinecone: índice `pln3-agrorag-e5-384`, namespace inmutable
  `corpus-e9929440f552b1c7`, E5 multilingüe revisión fijada, dimensión 384.
- Namespace: 27 vectores de evidencia y un manifiesto publicado después de verificar los IDs.
- Generación: OpenAI `gpt-4o`, seleccionado explícitamente por el `.env` local.

Los PDF, el catálogo SQLite, `.env` y los modelos descargados permanecen fuera de Git.

## RED

Con el namespace nuevo, el smoke real falló antes de consultar Pinecone porque
`retrieval-dev-draft.jsonl` todavía declaraba la versión anterior:

```text
ValueError: Caso inválido o de otro corpus
1 failed; código 1
```

Después de migrar cada etiqueta a su pasaje equivalente, el smoke top 5 mostró una diferencia
observable: `dev-002` quedó en posición 9 y `dev-007` en posición 17. La nueva fuente de lechuga
aportó además un pasaje directamente relevante para `dev-002`, incorporado al borrador sin cambiar
su estado `pending_human`.

La suite offline detectó por diseño que el hash congelado del dataset había cambiado:

```text
test_frozen_dev_dataset_has_expected_bytes: failed
esperado: bfe832f33b8683f0680953bba2b215c3e981b05867c30f29a8a7f30d1807d34f
obtenido: 037b27219c3772f4d4ff3381860d11ddb43799f2b85762686994590d0b8c8933
```

## GREEN

Se actualizó la versión y los IDs por correspondencia de fuente, página, sección y texto. El hash
nuevo quedó fijado y el smoke real usa el objetivo preregistrado Recall@20, sin presentar los qrels
pendientes como evaluación científica:

```text
pytest -m integration_live tests/integration_live/test_pinecone_live.py
1 passed in 29.42s; código 0
```

El flujo local se inició en `127.0.0.1:8010` y `127.0.0.1:8501` con una clave reader aleatoria sólo
en memoria. La verificación real devolvió liveness 200, readiness 200 y catálogo 200 con 27
evidencias. La pregunta «¿Qué sistemas de riego se utilizan en lechuga?» produjo HTTP 200,
`answered`, decisión `approve`, dos llamadas y una cita a `INTA-LECHUGA-2022`, sección
«Lechuga: exceso de agua y sistemas de riego». Esta llamada fue real y tuvo consumo del proveedor;
las pruebas offline no llaman servicios externos.

Validación final:

```text
pytest: 169 passed, 2 deselected; código 0
ruff check: All checks passed; código 0
ruff format --check: 56 files already formatted; código 0
mypy: Success, 34 source files; código 0
import-linter: 2 contracts kept, 0 broken; código 0
openspec validate 03-retrieval --strict: valid; código 0
```

## Limitaciones

La API pública continúa usando BM25 de acuerdo con ADR-013; Pinecone queda indexado y validado como
adaptador experimental, no activado silenciosamente. Los ocho qrels siguen pendientes de revisión
humana y las métricas históricas del corpus de 12 evidencias no se trasladan al corpus ampliado.
