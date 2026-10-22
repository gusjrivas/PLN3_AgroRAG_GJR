# TDD: contratos de recuperación

Fecha: 22/10/2026. Responsable/revisor: misma sesión, sin revisión independiente. Rama: feat/03-retrieval-contracts. Base main: `14caec653611fdbec94dc9c50aab396d87b996ac`.

## Escenarios y ciclo

RET-01: cuatro modos con scores por etapa, fallo vector explícito. RET-02-incompatible: corpus/modelo/revisión/dimensión diferentes, incluso con dimensión igual. RET-03: cap por PDF, IDs inválidos y cultivo, presupuesto del contexto serializado sin cortar pasajes. No se acredita RET-02-e5 ni funcionamiento real de Pinecone/reranker/tokenizer.

1. RED antes de crear el módulo y el método rank: `uv run pytest tests/unit/test_retrieval_pipeline.py -q`, salida 1, 25 fallos por import/capacidades ausentes. Log [03-pipeline-red.txt](03-pipeline-red.txt).
2. GREEN: `uv run pytest tests/unit/test_retrieval_pipeline.py tests/unit/test_retrieval.py -q`, salida 0, 28 aprobadas. Log [03-pipeline-green.txt](03-pipeline-green.txt).
3. Refactor: formato, imports y anotación explícita de proveedores opcionales. Se corrigieron un orden de imports y un error mypy antes de continuar.
4. Hardening: se añadieron 13 verificaciones de regresión sobre validaciones ya implementadas, sin atribuirles un RED previo. Una nueva prueba de error del tokenizer falló antes de corregirlo: 1 fallo, 38 aprobadas, salida 1. Log [03-pipeline-hardening-red.txt](03-pipeline-hardening-red.txt). Se envolvió la falla con RetrievalUnavailable sin detalles del proveedor.
5. GREEN final: `uv run pytest --cov --cov-report=term-missing`, salida 0, **95 aprobadas**, 1 E2E excluida por diseño; **91,17% global**, **97% core** redondeado. Módulo nuevo: 100% de líneas/ramas medidas, sin que cobertura equivalga a calidad de modelos. Log [03-pipeline-final-green.txt](03-pipeline-final-green.txt).

Ruff check/format, mypy (23 archivos), import-linter (2 contratos) y diff --check aprobados localmente. E2E y validación OpenSpec son gates de CI antes de integrar. Sin nuevas dependencias ni cambios de lockfile. El merge está condicionado a los tres jobs remotos; ver checks del PR para sus resultados definitivos.

## Corpus y alcance operacional

Se comprobaron nuevamente los SHA256 de los dos PDFs ya descargados. INTA: `b46eed913543dabc8b4bc3e00b4ce1ec8d8deb2b0810516e426c769181c7d5b7`. FAO: `bba2b84e839336453556ebe8422dc862f10831deda1a8ab46bfd3a9092d8665a`. El corpus activo conserva versión `a85bec55032f5adea8675749c0cafa71be5ed61664535f93cdf4da9a981a9313` y 12 fragmentos. No se duplicaron descargas ni se publicaron PDFs en Git.

Engram CLI se consultó con proyecto pln3-agro-rag y base local previa. Sólo contenía la prueba de persistencia; se confirmó estado con Git. No se atribuye integración de sesión al cliente ni memoria compartida con Windows.

## Límites y siguiente puerta

Los tests de ranking vectorial/reranking usan dobles. El contador de tests cuenta caracteres como sustituto determinista; no es un tokenizer real. El nuevo pipeline no se inyecta todavía en API/UI. El baseline lexical conserva la interfaz vigente y la generación real sigue pendiente. ADR-013 enumera las condiciones para activarlo. No archivar 03 ni afirmar que el TP está terminado.
