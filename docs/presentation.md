# Presentación para la cátedra

Versión: 13/11/2026. Nueve diapositivas y guion de 15 minutos en `docs/demo.md`.

## 1. AgroRAG

00:00–00:30. Presentar autor y problema. Fuente: docs/report.md, secciones 1 y 2.

## 2. Un corpus acotado y trazable

00:30–02:00. Explicar las cinco fuentes y distinguir fragmentos de casos de prueba. Fuente: data/manifest.json y docs/report.md §2.

## 3. Una interfaz HTTP y dos roles de agente

02:00–03:30. Recorrer la arquitectura. La UI no importa agentes, modelos ni índices. Fuente: docs/architecture.md y docs/report.md §3.

## 4. Recuperación medible y límites explícitos

03:30–05:00. Reuso docente y decisiones propias. Distinguir capacidad semántica y default público. Fuente: docs/report.md §3–4; ADR-013/016.

## 5. Demo: fuente, respuesta y aclaración

05:00–09:00. Abrir app local. Primero Explorar fuentes, luego Respuesta verificada. No mostrar secretos. Fuente: docs/demo.md; docs/evidence/acceptance-27/README.md.

## 6. Evaluación: el ranking no decide el producto

09:00–11:00. Protocolo 60 casos, split agrupado 30/30. E1/E2 se limitaron a dev. E2: 18 pares, dictamen único por par, no efecto causal. E3: una consulta, seis corridas, 156 ms menos de mediana sin ahorro de tokens. Fuentes: docs/report.md §5–6; docs/evidence/tdd/EVA-02-budgeted-live.md.

## 7. Una cita válida no garantiza completitud

11:00–12:00. No sumar esta campaña al benchmark de 60. Tres registros manuales revisados, 24 casos por API y repetición P02. Revisión por la misma sesión asistente. Fuentes: docs/evidence/acceptance-27/README.md y pruebas-27-revisadas.xlsx.

## 8. Garak: cobertura ejecutada y revisada

12:00–13:00. Candidata d38814b4. No afirmar seguridad universal ni aprobación de versiones posteriores. DAN: 15 falsos positivos revisados por Gus Rivas. Fuentes: docs/evidence/garak/garak-d38814b4-human-report.md y d38814b4-targeted-recovery.json.

## 9. Conclusiones y siguiente paso

13:00–15:00. Declarar asistencia de IA y responsabilidad humana. Cierre documental con limitaciones, no producto perfecto. META-05..07 y promoción V2 pendientes. El entorno limpio se hace después, sin repetir Garak por instrucción del usuario. Ensayo y fecha/modalidad aún por confirmar. Fuentes: docs/report.md §11–13; docs/delivery.md.

Archivos: `output/presentations/agro-rag-catedra.pptx` y `output/pdf/agro-rag-catedra.pdf`.
Las diapositivas son editables y sus notas conservan tiempos y fuentes. No se abrió PowerPoint.
