# Evaluación y entrega académica reproducibles

## ADDED Requirements

### Requirement: EVA-01 Benchmark congelado
El benchmark MUST contener 60 casos revisados con split agrupado 30 dev/30 test y evidencia fuente; parámetros SHALL seleccionarse sólo con dev.

#### Scenario: EVA-01-split
- **GIVEN** casos y paráfrasis anotados.
- **WHEN** se valida benchmark.
- **THEN** no hay familia cruzada entre splits ni IDs sin evidencia; manifiesto tiene hash.

#### Scenario: EVA-01-sin-soporte
- **GIVEN** caso sin relevantes.
- **WHEN** se calcula evaluación.
- **THEN** se excluye del promedio IR respondible y se incluye en métricas de abstención con denominador explícito.

### Requirement: EVA-02 Métricas y ablaciones reales
La evaluación MUST separar recuperación, generación, agentes y operación, y distinguir ejecuciones reales de dobles de prueba.

#### Scenario: EVA-02-comparacion
- **GIVEN** config congelada y proveedores reales.
- **WHEN** se ejecutan E1/E2/E3.
- **THEN** se guardan resultados por pregunta, errores, versiones, tokens y p50/p95 con revisión humana.

#### Scenario: EVA-02-negativo
- **GIVEN** verificador empeora calidad o costo.
- **WHEN** se redacta conclusión.
- **THEN** se informa el resultado completo sin seleccionar sólo casos favorables.

#### Scenario: EVA-02-estabilidad
- **GIVEN** un subconjunto y una cantidad explícita de repeticiones autorizadas.
- **WHEN** se ejecuta la evaluación live.
- **THEN** cada fila registra su repetición y el resumen informa conteos de estado, estabilidad y
  pass rate por consulta sin ocultar errores operativos.

### Requirement: DEL-01 Entrega preproductiva
La entrega MUST incluir código reproducible, informe PDF y demo de 15 minutos con limitaciones y atribución de asistencia de IA.

#### Scenario: DEL-01-reproduccion
- **GIVEN** checkout limpio y guía final.
- **WHEN** un evaluador sigue pasos documentados.
- **THEN** puede instalar, probar, configurar y ejecutar con requisitos explícitos.

#### Scenario: DEL-01-informe
- **GIVEN** resultados congelados.
- **WHEN** se exporta PDF y ensaya demo.
- **THEN** incluye objetivo, arquitectura, implementación, métricas, resultados, conclusiones y planificación humana si es grupal.
