# Engram: instalación operativa parcial

Fecha: 21/10/2026, America/Buenos_Aires. Responsable y revisión: misma sesión de trabajo, sin revisor independiente. Rama: `chore/engram-setup`. Base: `f4e6416b00af331154a2a23f6ff2f838feae8bf9`.

## Resultado verificado

Engram 3.5.2 instalado en `.tools/engram/engram` en la copia Linux x86_64 del entorno remoto de trabajo. Este binario es local, está ignorado por Git y no se transfiere al clonar. La persistencia de ese entorno no equivale a la de la notebook.

Se versiona `.engram/config.json` con `project_name: pln3-agro-rag`. La base de prueba está fuera del repositorio, en `../runtime/agro-engram`, seleccionada con `ENGRAM_DATA_DIR` absoluto. No se activó cloud ni sync. No se modificaron configuraciones globales de clientes.

| Comprobación real | Resultado |
|---|---|
| SHA256 del archivo Linux descargado | Coincide con el digest de la release oficial |
| `engram version` | `engram 3.5.2`, salida 0 |
| `engram init pln3-agro-rag` | Configuración de proyecto creada, salida 0 |
| `engram doctor --json` | 10 checks OK, 0 warnings, 0 errores, salida 0 |
| CLI `save` y `search` en procesos separados | Observación #1 recuperada por token `AGROENGRAM20261022`, salida 0 |
| MCP stdio `initialize` | Servidor `engram`, versión `3.5.2` |
| MCP `mem_current_project` sin override | `pln3-agro-rag`, `project_source: config` |

El chequeo de actualizaciones de la CLI avisó que GitHub tardó demasiado; guardado y búsqueda terminaron correctamente. La observación es una prueba manual de instalación, sin atribución a una sesión de Codex. No se inventaron identificadores de sesión.

## Artefactos fijados

Fuente: [release oficial v3.5.2](https://github.com/Gentleman-Programming/engram/releases/tag/v3.5.2).

| Archivo | SHA256 publicado |
|---|---|
| `engram_3.5.2_linux_amd64.tar.gz` | `106a43ca8f43a27c2c260a6787151c3be6d91c5ed3d5e454e6140527adf92e01` |
| `engram_3.5.2_windows_amd64.zip` | `ba56a36d37b2da85fcb1581bbdbed9ae1ee690e642aab8dbe1e18209bf264afe` |

El artefacto Windows no se ejecutó en este entorno. No se distribuyen binarios ni memorias dentro de Git.

## Activación en la notebook Windows x64

1. Actualizar el clon conservando los cambios locales. Desde la raíz, comprobar que `.engram/config.json` contenga `pln3-agro-rag`.
2. Si ya existe Engram, comprobar su versión y ubicación antes de reemplazarlo. Para una instalación nueva, descargar [el ZIP Windows 3.5.2](https://github.com/Gentleman-Programming/engram/releases/download/v3.5.2/engram_3.5.2_windows_amd64.zip).
3. Comprobar con `Get-FileHash -Algorithm SHA256` que el ZIP coincide con la tabla. Extraer `engram.exe` en `.tools/engram/` del clon. Si Windows rechaza la ejecución, conservar el error y resolverlo con la política del equipo, sin desactivar controles.
4. Desde la raíz, ejecutar:

```powershell
.\.tools\engram\engram.exe version
.\.tools\engram\engram.exe doctor
.\.tools\engram\engram.exe setup codex
```

El setup oficial registra la ruta absoluta y requiere que la CLI `codex` esté disponible para instalar su plugin. Puede modificar la configuración de usuario; conserva entradas ajenas según su documentación. Si devuelve error, no declarar la integración completa. Si se utiliza Claude Code, ejecutar además `.\.tools\engram\engram.exe setup claude-code` con su CLI disponible. No se necesita ejecutar nuevamente `engram init`.

5. Reiniciar el cliente. Confirmar `mem_current_project`, guardar y recuperar una observación de prueba usando la sesión real registrada por el cliente. Repetir tras reinicio. Si se declara integración cruzada, verificar desde el segundo cliente la misma observación y base.

El directorio de datos por defecto será `%USERPROFILE%\.engram`, fuera del clon. Cambiar `ENGRAM_DATA_DIR` sólo de forma consciente y consistente entre clientes. Mover el ejecutable exige repetir el setup para actualizar la ruta registrada.

## Alcance pendiente

No hay CLI Codex ni Claude Code en este entorno. No se ejecutaron sus setups ni se activaron herramientas Engram en esta conversación. La prueba MCP directa verifica transporte y detección del proyecto, pero no el ciclo de sesión de esos clientes.

MEM-01 permanece parcial: falta persistencia tras reinicio del cliente y lectura cruzada. MEM-02 permanece pendiente: el producto todavía no está implementado. `01-engram` no se archiva. El usuario solicitó adelantar la instalación antes de completar `00-foundation`; esto no habilita corpus ni desarrollo sin sus dependencias.

No se añadió código de automatización al producto. Se aplicó la verificación operativa prevista en el diseño del cambio, sin atribuir una fase TDD roja ficticia a la instalación de un binario externo.

Documentación consultada: [instalación](https://github.com/Gentleman-Programming/engram/blob/v3.5.2/docs/INSTALLATION.md) y [setup de agentes](https://github.com/Gentleman-Programming/engram/blob/v3.5.2/docs/AGENT-SETUP.md).
