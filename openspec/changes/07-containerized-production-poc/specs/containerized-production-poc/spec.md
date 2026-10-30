# PoC productiva containerizada

## ADDED Requirements

### Requirement: CFG-V2 Configuración container-safe
API y UI MUST resolver configuración externa y secretos montados sin filtrar contenido ni romper la
configuración local existente.

#### Scenario: CFG-V2-secret-file
- **GIVEN** sólo se configura una variable `*_FILE` legible con un valor no vacío.
- **WHEN** se construyen los settings.
- **THEN** el valor se usa y no aparece en `repr`, logs ni errores.

#### Scenario: CFG-V2-secret-conflict
- **GIVEN** valor directo y `*_FILE`, o archivo ausente/vacío.
- **WHEN** se construyen los settings.
- **THEN** falla cerrado con un error sanitizado.

#### Scenario: CFG-V2-local-compatible
- **GIVEN** configuración V1 por entorno o `.env` y rutas/URLs locales.
- **WHEN** se inicia API o UI.
- **THEN** conserva precedencia y comportamiento; una URL interna `http://api:8000` también es válida.

### Requirement: IMG-V2 Imágenes reproducibles y mínimas
La release MUST construir targets API/UI desde `uv.lock`, sin secretos ni dependencias de desarrollo
en runtime, y ejecutar con identidad no root.

#### Scenario: IMG-V2-build
- **GIVEN** checkout limpio sin `.env` ni catálogo privado.
- **WHEN** BuildKit construye los artefactos API/UI/gateway.
- **THEN** instala el wheel bloqueado, API/UI/gateway comparten versión y revisión OCI, y los
  entrypoints exec-form arrancan sin descargar modelos.

#### Scenario: IMG-V2-content
- **GIVEN** imágenes finales.
- **WHEN** se inspeccionan filesystem, usuario y paquetes.
- **THEN** no contienen `.git`, `.env`, tests, output, toolchain o dev deps no justificadas.

### Requirement: CMP-V2 Stack Compose preserva comportamiento
Compose MUST iniciar API/UI saludables, mantener el límite HTTP y conservar todo comportamiento V1.

#### Scenario: CMP-V2-e2e
- **GIVEN** catálogo fixture y proveedores offline.
- **WHEN** se levanta base+dev desde un host con sólo Docker.
- **THEN** UI consulta API por DNS interno y los contratos existentes siguen aprobando.

#### Scenario: DAT-V2-persistence
- **GIVEN** catálogo publicado por el job administrativo.
- **WHEN** API/UI se recrean.
- **THEN** el catálogo persiste, API no puede escribirlo y startup no lo reconstruye.

### Requirement: SEC-V2 Perfil productivo endurecido
El overlay productivo MUST minimizar exposición, privilegios, secretos y estado mutable.

#### Scenario: SEC-V2-exposure
- **GIVEN** configuración productiva renderizada.
- **WHEN** se inspeccionan puertos, redes, mounts y permisos.
- **THEN** sólo gateway publica puertos y cada servicio recibe únicamente sus secretos/volúmenes.

#### Scenario: OPS-V2-rollback
- **GIVEN** release y catálogo previos respaldados.
- **WHEN** falla la candidata.
- **THEN** el runbook restaura digest+manifiesto y prueba salud sin borrar el volumen activo.

#### Scenario: OPS-V2-release-observability
- **GIVEN** una imagen construida con versión, commit y referencia inmutable.
- **WHEN** la API atiende health o tráfico funcional.
- **THEN** expone identidad de release/catálogo y emite eventos JSON correlacionables sin query,
  credenciales, cuerpo ni secretos.

### Requirement: CI-V2 Supply chain verificable
CI MUST probar una release candidate una vez, conservar SBOM/scan y publicar exactamente las mismas
imágenes mediante referencias inmutables.

#### Scenario: CI-V2-supply-chain
- **GIVEN** un commit o tag semver candidato.
- **WHEN** el workflow construye API/UI/gateway.
- **THEN** E2E, SBOM y scan operan sobre esos tags; CRITICAL/secretos bloquean, HIGH sólo admite una
  excepción completa/no vencida, y la publicación produce SHA, digest y manifiesto sin `latest` ni
  rebuild.

### Requirement: REL-V2 Staging verifica la candidata publicada
Staging MUST demostrar que ejecuta los mismos digests aprobados y que el comportamiento observable
continúa disponible por el gateway, sin conservar entradas ni salidas sensibles en la evidencia.

#### Scenario: REL-V2-clean-host-preflight
- **GIVEN** un host Linux limpio, imágenes candidatas descargadas por digest, secretos montados y un
  catálogo externo restaurado.
- **WHEN** se valida el host antes de levantar la candidata.
- **THEN** falla cerrado ante Engine/Compose no disponible, tag mutable, commit/usuario de imagen
  divergente, volumen ausente, permisos laxos o Compose inválido; al aprobar emite inventario
  sanitizado de ambiente, recursos, tiempos y digests sin imprimir secretos.

#### Scenario: REL-V2-staging-smoke
- **GIVEN** un manifiesto publicado por un run exitoso y esos digests desplegados en staging.
- **WHEN** se verifica la candidata por el gateway autenticado.
- **THEN** identidad, commit, imagen API y catálogo coinciden con el manifiesto, una consulta
  sintética produce respuesta citada y la evidencia no conserva pregunta, respuesta ni secretos.

### Requirement: GARAK-V2 Evaluación adversarial trazable
La release candidate MUST superar una política garak versionada sobre el gateway desplegado, sin
presentar el resultado como garantía o certificación.

#### Scenario: GARAK-V2-gate
- **GIVEN** reporte versionado con metadatos por probe/detector.
- **WHEN** se evalúa la política.
- **THEN** bloquea hallazgos críticos/altos confirmados o regresiones fuera de tolerancia y registra
  excepciones con responsable/vencimiento.

#### Scenario: GARAK-V2-confidentiality
- **GIVEN** scan con identidad/datos sintéticos.
- **WHEN** CI conserva evidencia.
- **THEN** el JSONL crudo queda restringido, el resumen es sanitizado y ninguna credencial aparece.
