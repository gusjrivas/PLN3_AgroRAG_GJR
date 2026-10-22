# Estado actual y próxima sesión

La base y el corpus ya se implementaron. Para ejecutar la primera versión, seguir [run-local](run-local.md). Revisar PR #4 y su CI antes de continuar; no repetir bootstrap ni reemplazar archivos del clon.

Próximas tareas: configurar y probar un modelo real; ampliar corpus revisado; integrar recuperación semántica/reranker; benchmark. Conservar TDD y dependencias por PR. Las instrucciones iniciales debajo son el plan histórico y no deben ejecutarse de nuevo sobre la versión actual.

# Primera sesión de desarrollo

## Resultado esperado

Repositorio independiente organizado, entorno reproducible y primera funcionalidad mínima desarrollada con TDD. Luego integrar Engram y probar memoria persistente. La planificación ya contiene arquitectura, ADR y cambios SDD; no hace falta generarlos otra vez.

## Preparación del repositorio nuevo

1. Clonar el repositorio independiente desde `C:\Repo` si la carpeta destino todavía no existe:

   ```powershell
   git clone https://github.com/gusjrivas/PLN3_AgroRAG_GJR.git
   cd PLN3_AgroRAG_GJR
   ```

2. Si ya existe una copia local, verificar `git remote -v` y `git status --short`; preservar cambios locales y actualizar sin reset/clean. No volver a ejecutar git init ni copiar .git del repositorio docente.
3. Abrir `C:\Repo\PLN3_AgroRAG_GJR` en VS Code y comprobar que se cargue AGENTS.md.
4. Leer esta planificación y crear la rama `feat/00-foundation` desde main actualizado. La aplicación todavía no existe; evitar comandos de arranque supuestos.
5. Ejecutar la primera etapa con TDD y luego la integración local de Engram. La existencia del repositorio no completa el entorno ni las pruebas de 00-foundation.

## Encargo inicial para Codex o Claude Code

Leer README.md, AGENTS.md, docs/requirements.md, docs/architecture.md, docs/tdd.md y los ADR-001/003/008. Ejecutar únicamente openspec/changes/00-foundation con TDD estricto. Respetar dependencias y alcance. Crear Python 3.12, pyproject.toml/uv.lock, estructura modular y CI. Empezar por un test de salud que falle por funcionalidad ausente, luego implementar lo mínimo y refactorizar. Registrar comandos y resultados reales. No implementar corpus/RAG/agentes/UI todavía. No modificar el repositorio docente ni instalar software global sin revisar instalaciones existentes. Al cerrar, resumir archivos, verificaciones y bloqueos.

## Encargo siguiente

Con 00 integrado, aplicar 01-engram según docs/setup-engram.md. Configurar sólo los clientes utilizados y verificar recuperación tras reinicio. Guardar primeras memorias con referencias a ADR y requisitos. Continuar con 02-corpus cuando corresponda. No habilitar sync/cloud por defecto.

## Regla de avance

Una etapa se cierra por comportamiento probado y evidencia, no por haber escrito documentos ni porque el agente dice terminado. Mantener tareas abiertas cuando falten credenciales o integración real.
