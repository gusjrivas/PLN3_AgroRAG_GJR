# Cierre de aceptación complementaria: 27 casos

Ejecución: 12/11/2026 (America/Buenos_Aires). Cierre documental: 13/11/2026.
Base local: `3ec244544ad908ea396e7f3a99532e61710e7b26`, posterior a la integración del bug #51.
Responsable académico: Gustavo Julián Rivas. Ejecución/revisión asistida: misma sesión Codex;
no hubo segundo revisor independiente. Esta campaña se cierra con limitaciones, sin corregir
código ni declarar que todos los casos aprobaron.

## Método y resultado

- Tres respuestas fueron registradas manualmente por el usuario. Se conservan texto, cita y fecha.
- P04-P27 se ejecutaron por HTTP contra la API local real, con BM25 y OpenAI `gpt-4o`.
- P02 se repitió por API para revisar la cita no registrada en el libro manual.
- P01-P26 se seleccionaron sólo de `dev`; P27 reproduce el bug #51. No es un benchmark nuevo.
- Corpus: `e9929440f552b1c7be1349118a1ee98c6cdba41fbd2e2ce05343247c918dfb7d` (27 fragmentos).
- Resultado agregado: **19 conformes, 8 incompletos, 0 pendientes y 0 bloqueados**.
- Los 24 casos nuevos devolvieron el estado esperado; las citas resolvieron al catálogo con
  fuente, página y extracto coincidentes. Se revisó el soporte y la completitud por separado.
- P27 pidió aclaración con `llm_calls=0`: la regresión del bug #51 aprobó.
- No se ejercitaron controles del navegador. Esta evidencia valida API y contenido, no una nueva
  campaña E2E visual ni calidad agronómica certificada.

## Omisiones frente al criterio original

| Caso | Información requerida que falta |
|---|---|
| P01 | Efecto adverso de temperaturas superiores a 30 °C. |
| P03 | Surco, inundación y riego localizado, además de los tres métodos mencionados. |
| P07 | Precaución desde floración hasta maduración, además del cuajado. |
| P09 | Simultaneidad de evaporación y transpiración. |
| P10 | Diferenciar evaporación del suelo de transpiración vegetal. |
| P11 | Explicar que los estomas son aberturas en las hojas. |
| P16 | Distinguir contenido de humedad de energía de retención y sus instrumentos. |
| P17 | Reducción potencial del rendimiento del 10 % a 1,4 dS/m. |

Estos son incumplimientos de completitud de la rúbrica, no ocho datos falsos ni ocho fallos de
seguridad. Algunos detalles son complementarios a la pregunta breve. No se cambió el criterio
después de observar la respuesta. P01/P03 habían sido marcados «Pasó» por el usuario: el libro
revisado conserva sus respuestas y explica el cambio a «Falló».

## Uso observado

| Ejecución | Llamadas LLM | Tokens entrada | Tokens salida |
|---|---:|---:|---:|
| P04-P27 | 34 | 64202 | 1931 |
| Repetición P02 | 2 | 4065 | 111 |
| Total nuevo | 36 | 68267 | 2042 |

No se calculó gasto monetario sin verificar tarifa. No se sumó el consumo de las tres pruebas
manuales porque no quedó registrado. La evidencia incluye request IDs, estados y citas, sin
credenciales ni cabeceras de autenticación.

## Artefactos

- `pruebas-27-revisadas.xlsx`: registro final, respuestas, citas y observaciones.
- `ejecucion-real-24.json`: respuestas y controles de integridad de P04-P27.
- `revision-P02.json`: repetición puntual de P02.
- `manifest.json`: SHA-256 y tamaño de los tres artefactos.

La validación de fórmulas dio 27/19/8/0/0/100 %; no se encontraron errores de fórmula. El XLSX
se reabrió como ZIP válido y conserva los dos desplegables y las respuestas manuales originales.
No se fabricó una fase RED: éste es un cierre de evaluación y documentación, no una corrección
de comportamiento. Las mejoras quedan documentadas para trabajo posterior.
