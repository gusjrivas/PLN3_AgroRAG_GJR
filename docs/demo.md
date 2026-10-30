# Guion reproducible de demo - 15 minutos

Commit, corpus, modelo, hardware y fecha se anotan antes de comenzar. Usar el stack local preparado
según `docs/run-local.md`. No mostrar `.env`, consolas con secretos ni paneles de proveedor.

## 00:00 a 02:00 - problema y corpus

- Explicar que AgroRAG responde sobre riego y estrés hídrico en tomate/lechuga con evidencia.
- Mostrar `data/manifest.json`: cinco fuentes, hashes, páginas seleccionadas y derechos.
- Aclarar que hay 27 evidencias piloto y que el sistema no automatiza riego.
- Criterio de éxito: el público distingue corpus, pasaje y respuesta generada.

## 02:00 a 05:00 - arquitectura y reutilización

- Mostrar el diagrama de `docs/architecture.md` y las capas domain/application/infrastructure/API/UI.
- Explicar investigador, verificador, una revisión máxima y estados públicos.
- Señalar la adaptación del ejemplo docente: BM25, E5/Pinecone, RRF y reranker con identidad fuerte.
- Criterio de éxito: queda claro que la UI sólo consume HTTP y que startup no crea índices.

## 05:00 a 09:00 - demo funcional

1. Verificar backend: abrir `http://127.0.0.1:8000/health/live`; debe devolver `status=ok`.
2. Abrir `http://127.0.0.1:8501` y entrar en **Explorar fuentes**.
3. Consultar: "¿Cuándo es crítico evitar la falta de agua en tomate?".
4. Expandir la cita y mostrar título, edición, página física/impresa y pasaje.
5. Si OpenAI u Ollama está configurado, cambiar a **Respuesta verificada** y repetir la pregunta.
6. Mostrar un pedido ambiguo: "¿Cuánto riego aplico?"; debe pedir datos o abstenerse, no inventar litros.

Criterio de éxito: se observa evidencia resoluble y un estado de negocio explícito. Si el modelo no
está disponible, mostrar el error real y continuar con el modo lexical.

## 09:00 a 13:00 - evaluación, costo y resultado negativo

- Presentar el protocolo 60 casos, split 30/30, familias aisladas y denominadores separados.
- Mostrar E1 sobre los 18 casos respondibles de `dev`: hybrid RRF logró Recall@20 0,9722 con p95
  215,98 ms; el reranker mejoró el orden pero alcanzó p95 47,01 s sólo en retrieval.
- Mostrar E2: 18/18 estados correctos en ambas variantes, USD 0,289792 y revisión humana de los
  pares con 12 PASS y 6 FAIL.
- Explicar que el dictamen único por par no demuestra una mejora causal del verificador.
- Mostrar E3 como piloto mínimo: una consulta, tres repeticiones frías/calientes y 156 ms menos de
  mediana sin ahorro de tokens.

Criterio de éxito: nadie interpreta los fixtures o el smoke como evaluación científica final.

## 13:00 a 15:00 - conclusiones y límites

- Resumir: corpus trazable, API/UI, agentes acotados, citas, seguridad, caché y auditoría.
- Enumerar límites: `test` cerrado, E3 no generalizable, metadatos incompletos en la planilla y
  revisión final del diff/PDF pendiente.
- Declarar asistencia de IA y responsabilidad humana.
- Cerrar con la decisión principal: no activar una mejora aparente sin calidad y latencia validadas.

## Preparación técnica

Backend:

```powershell
uv run uvicorn agro_rag.bootstrap.app:create_app --factory --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
uv run streamlit run src/agro_rag_ui/app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
```

Smoke previo:

```powershell
uv run pytest -q
uv run python scripts/build_report.py
```

## Contingencia

- Tener el PDF y capturas de una ejecución previa identificadas como respaldo, no como ejecución viva.
- Si el proveedor generativo falla, mostrar el error tipado y usar exploración lexical.
- Si Pinecone falla, no cambiar configuración en vivo: la demo pública usa BM25.
- Si la red externa falla, el corpus ya ingerido permite la demo local.
- No usar respuestas fixture sin rotularlas ni borrar un fallo para favorecer la presentación.
