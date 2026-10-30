# Tasks: Evaluación y entrega académica reproducibles

Responsable: Evaluador y coordinador. Dependencias: 05-frontend-hardening; anotación iniciada tras
02. Implementación y cierre técnico verificados.

## 1. Preparación

- [x] 1.1 Leer ADR aplicables, fijar archivos de propiedad y comprobar dependencias para EVA-01.
- [x] 1.2 Preparar fixtures/contratos EVA-01 sin servicios pagos; la anotación y las métricas de calidad requieren revisión/ejecución real.

## 2. Implementación mediante TDD

- [x] 2.1.1 RED: escribir y ejecutar pruebas de los escenarios de EVA-01; guardar fallo funcional esperado.
- [x] 2.1.2 GREEN: implementar mínimo comportamiento automatizable de EVA-01 y ejecutar las mismas pruebas.
- [x] 2.1.3 REFACTOR: validar diseño, suite afectada/typing/imports y registrar evidencia del contrato EVA-01.
- [x] 2.1.4 Preparar y validar un paquete de 60 casos `pending_human`, sin promoción implícita.
- [x] 2.1.5 Revisar humanamente preguntas, referencias, claims, páginas e IDs; congelar el benchmark
  final sólo cuando las 60 filas sean `reviewed`.
- [x] 2.2.1 RED: escribir y ejecutar pruebas del contrato de reporte EVA-02; guardar fallo funcional esperado.
- [x] 2.2.2 GREEN: implementar comparación pareada, procedencia y persistencia completa de EVA-02.
- [x] 2.2.3 REFACTOR: mejorar diseño, ejecutar suite afectada/typing/imports y registrar evidencia del contrato EVA-02.
- [x] 2.2.4 Ejecutar E1/E2/E3 con benchmark humano congelado y proveedores reales; revisar soporte y publicar resultados completos, incluidos los negativos.
  E1 y E2 se completaron en `dev` respondible; E3 mínimo usó tres repeticiones frías/calientes
  sobre una consulta. La revisión humana de los 18 pares obtuvo 12 PASS y 6 FAIL. E3 no se
  generaliza más allá de esa consulta y el dictamen por par no estima un efecto causal separado.
- [x] 2.2.5 Implementar repetición y resumen de estabilidad con pruebas offline; la nueva corrida
  live queda pendiente de autorización de costo.
- [x] 2.3.1 Definir verificación observable de DEL-01; generador PDF y verificador comenzaron con prueba RED.
- [x] 2.3.2 Generar, renderizar e inspeccionar el PDF; validar offline comandos, secciones, guion y hashes.
- [x] 2.3.3 Revisar los escenarios DEL-01 y registrar benchmark, evaluación, modalidad y fecha aún pendientes.

## 3. Cierre

- [x] 3.1 Ejecutar tests offline/integración local y checks estáticos; los proveedores reales y qrels humanos siguen separados.
- [x] 3.2 Actualizar documentación, trazabilidad, informe y handoff; enlazar evidencia y commit.
- [x] 3.3 Revisión del diff por revisor disponible, registrar autor y riesgos; integrar cuando Definition of Done esté satisfecha.
  Revisión realizada por la misma sesión coordinadora al no disponer de un revisor distinto. Suite
  afectada, Ruff, mypy contractual, OpenSpec, verificador offline y PDF aprobaron. Riesgos abiertos:
  `test` cerrado, E3 de una consulta y dictamen E2 por par. La deuda de typing de
  `build_report.py` quedó resuelta en `DEL-02-release-closeout.md`.
- [x] 3.4 Archivar el cambio y promover deltas a specs después de verificar implementación real.
