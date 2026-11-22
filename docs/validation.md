# Validación documental

## Estado de cierre al 13/11/2026

La revisión complementaria está cerrada en [acceptance-27](evidence/acceptance-27/README.md):
19 casos conformes y 8 incompletos; 24 consultas nuevas por API, tres registros manuales
revisados y repetición de P02. No se presenta esta revisión asistida como evaluación humana
independiente ni se agregan sus casos a los 60 del benchmark histórico.

La cobertura de Garak se completó según su [informe final](evidence/garak/garak-d38814b4-human-report.md).
No se ejecutará de nuevo en el siguiente entorno limpio. Sigue pendiente la promoción formal V2.
La reproducción limpia de la versión actual se hará después del cierre documental, sin atribuirle
los resultados de un checkout anterior. META-05..07 continúan pendientes.

## Validación inicial histórica

Fecha: 21/10/2026 (America/Buenos_Aires).

## Ejecutado

- OpenSpec 1.14.3: `openspec validate --all --strict`, desde la raíz PLN3_AgroRAG_GJR. Resultado: 7 cambios aprobados, 0 fallidos; código de salida 0.
- Comprobación de enlaces Markdown locales y balance de bloques de código: sin referencias rotas ni bloques desbalanceados.
- Lectura JSON de candidatos de corpus: válida.
- IDs de requisitos y escenarios: sin duplicados; 22 requisitos de implementación y 48 escenarios.
- Tareas OpenSpec: todas pendientes; no se marcó implementación inexistente como completada.
- Revisión de independencia: estructura en raíz, repositorio fuente usado sólo por referencias. La publicación se dirige exclusivamente a PLN3_AgroRAG_GJR; el repositorio docente permanece sin modificaciones.

## Contenido

11 ADR propuestos, 7 cambios OpenSpec completos (propuesta, diseño, especificación, tareas y plan de pruebas), arquitectura, contratos, plan TDD, trazabilidad de consigna, memoria de desarrollo, corpus, frontend, seguridad, evaluación y entrega.

## Límites

Esta sección registra la validación inicial de planificación y formato. El avance posterior de Engram se registra en [engram-setup](evidence/engram-setup.md). No se ejecutaron tests de backend/frontend porque todavía no existen. No se instalaron Engram ni dependencias del producto en la notebook. No se descargó/indexó el corpus del TP ni se generaron métricas científicas. El usuario creó el repositorio remoto independiente; su existencia y estado vacío se verificaron antes de preparar la carga.

La carga inicial adapta la guía de inicio para clonar el nuevo repositorio. La publicación se verifica contra los objetos Git remotos después del commit. No se atribuye aprobación académica a esta revisión técnica.

El manifiesto del paquete documental inicial se conserva como histórico en `docs/evidence/planning-package-manifest.json`; sus hashes corresponden a aquella entrega, no al código evolutivo actual.
