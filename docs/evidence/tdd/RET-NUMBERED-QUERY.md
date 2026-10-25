# RET-NUMBERED-QUERY — consulta numerada en respuesta verificada

Fecha: 25/10/2026. Responsable: coordinador/RAG, misma sesión. Rama:
`fix/corpus-runtime-sync`.

## Incidente observable

La pregunta pegada desde la lista como «2. ¿Qué métodos de riego pueden utilizarse en lechuga?»
devolvía `insufficient_evidence`. La misma consulta sin numeración sí recuperaba el pasaje que
enumera riego gravitacional por pulso, aspersión y goteo.

El número inicial se convertía en un término BM25. Con `BM25Plus` alteraba el orden y, debido al
límite de cuatro pasajes y diversidad por fuente, desplazaba fuera del contexto la evidencia
directa. OpenAI recibió sólo pasajes generales y se abstuvo correctamente con una llamada.

## RED

Se agregó `test_leading_list_number_does_not_change_query_terms` antes de modificar producción:

```text
assert tokens("2. " + question) == tokens(question)
AssertionError: el resultado izquierdo contenía el término adicional "2"
1 failed; código 1
```

La reproducción real devolvió HTTP 200 con `status=insufficient_evidence`, decisión `abstain` y
`llm_calls=1`.

## GREEN

La tokenización elimina únicamente una numeración de lista de hasta tres dígitos seguida por `.` o
`)` al principio de la consulta. No elimina números internos, porcentajes ni cantidades
agronómicas.

El test focal pasó. En el catálogo real, la consulta numerada volvió a recuperar
`INTA-LECHUGA-2022`, sección «Lechuga: exceso de agua y sistemas de riego». Después de reiniciar
backend y UI, la misma consulta real produjo:

```text
status=answered
verification.decision=approve
llm_calls=2
cita=INTA-LECHUGA-2022 / Lechuga: exceso de agua y sistemas de riego
```

La respuesta aprobada enumeró goteo, aspersión y riego gravitacional por pulso. La llamada real a
OpenAI tuvo consumo; los tests automatizados permanecen offline.
