# Preparación local: repositorio, OpenSpec y Engram

Estado: procedimiento preparado, no ejecutado sobre `C:\Repo\PLN3_AgroRAG_GJR` ni sobre las configuraciones locales del usuario.

## 1. Checkout seguro

Seguir docs/start-here.md para clonar el repositorio independiente ya creado por el usuario. Si el destino ya tiene Git, revisar `git status --short`, `git branch --show-current` y su origin antes de escribir. Preservar cambios previos con commit o worktree; no reset/clean. No reutilizar el Git del material docente. Abrir `C:\Repo\PLN3_AgroRAG_GJR` como carpeta de trabajo del agente. Verificar que sus instrucciones AGENTS.md se carguen.

Si se elige WSL, ejecutar Python, uv, OpenSpec, Engram y agentes en ese entorno de forma consistente. No mezclar dos bases Engram independientes Windows/WSL creyendo que comparten memoria. Confirmar ubicación y proyecto en cada cliente.

## 2. Tooling OpenSpec

Se selecciona OpenSpec 1.14.3, con Node >=20.19.0 según metadata del paquete consultada. Registrar `node --version` y `npm --version`. Node sólo se usa para tooling; producto backend/UI es Python.

```powershell
npm install -g @fission-ai/openspec@1.14.3
openspec --version
```

Desde la raíz del nuevo repositorio, antes de inicializar revisar si ya hay integración OpenSpec del cliente. Si falta:

```powershell
openspec init --tools codex,claude
```

Revisar el diff y preservar los archivos de planificación existentes; no usar --force. Esto genera integraciones locales para asistentes, no implementa el producto. Después:

```powershell
openspec list
openspec validate --all --strict
openspec status --change 00-foundation
```

Aplicar sólo el cambio activo y sus tareas habilitadas. No archivar cambios por tener sus cuatro documentos completos: el código y sus pruebas deben existir.

## 3. Engram estable

Consultar releases oficiales e instalar binario estable para SO/arquitectura siguiendo docs/INSTALLATION.md. Registrar versión exacta y checksum del binario usado; no fijar una versión supuesta a partir del README de main. Si ya existe instalación, inspeccionar antes de modificarla. No reemplazar una base existente ni cambiar configuraciones de otros proyectos.

```powershell
engram version
engram doctor
engram setup codex
engram setup claude-code
```

Ejecutar sólo los setup de clientes realmente utilizados; reiniciarlos tras una configuración exitosa. Engram documenta MCP stdio para uso local habitual, sin Docker requerido. No habilitar cloud ni sync en este TP inicial.

Crear o revisar `.engram/config.json` con `{"project_name":"pln3-agro-rag"}` durante 01. El directorio .engram/config.json identifica proyecto y puede versionarse; la base SQLite de memoria y sus backups quedan fuera de Git. Verificar la resolución efectiva, no asumirla.

Para Codex, comprobar compatibilidad del core y registro real de sesión según documentación oficial. Si el cliente exige `capabilities.runtime_session_resolution`, resolver incompatibilidad actualizando/reiniciando explícitamente el runtime adecuado. No desactivar controles ni inventar session_id para forzar escritura.

## 4. Prueba de aceptación de memoria

Desde el agente: confirmar proyecto; guardar una observación inocua con token único y referencia al ADR-002; recuperarla; reiniciar sesión y recuperar de nuevo. Si se usan dos clientes, repetir lectura desde el segundo y registrar ambos entornos. Verificar que una búsqueda normal no mezcle memorias de otro proyecto. La misma máquina no garantiza la misma base.

Registrar pasos, versiones y evidencia en docs/evidence/engram-setup.md; no dar el setup por terminado sólo porque el comando terminó sin error. La app debe funcionar con Engram apagado. `scope: personal` no es una barrera de privacidad ni excluye sincronización: no almacenar datos personales/secretos ni activar sync automático.

## 5. Resultado esperado de inicio

Repo preparado, CI inicial verde bajo TDD, tooling registrado, memoria local probada y primer handoff. Recién entonces comenzar corpus. El procedimiento se aplica en la notebook; este paquete no instala software remotamente allí.

Fuentes: https://github.com/Gentleman-Programming/engram/blob/main/docs/INSTALLATION.md ; https://github.com/Gentleman-Programming/engram/blob/main/docs/AGENT-SETUP.md ; https://github.com/Gentleman-Programming/engram/blob/main/docs/TEAM-USAGE.md ; https://github.com/Fission-AI/OpenSpec/blob/main/docs/cli.md
