# UI-04 — resultado primero y formulario bajo demanda

Fecha: 25/10/2026. Responsable: coordinador/frontend, misma sesión. Rama:
`fix/result-first-ui`.

## Escenario

Después de una respuesta, la pantalla debe mostrar el resultado y **Nueva consulta**, no conservar
el formulario debajo. El formulario vacío reaparece únicamente al presionar ese botón. El flujo de
aclaración conserva su formulario específico porque forma parte del resultado en curso.

## RED

Se agregó `test_result_hides_query_form_until_new_query` antes del cambio de producción. El test
envió una consulta y comprobó que no existieran el botón **Consultar** ni el campo «¿Qué querés
saber?» mientras el resultado estaba visible.

```text
AssertionError: todavía existía un botón con label == "Consultar"
1 failed; código 1
```

## GREEN

La UI renderiza el formulario sólo cuando `session_state` no contiene un resultado. Al completar
una llamada guarda resultado, pregunta y contexto y ejecuta un rerun; la siguiente vista contiene
únicamente el resultado. **Nueva consulta** limpia ese estado, incrementa la versión del formulario
y vuelve a ejecutarlo vacío, sin efectuar otra llamada HTTP.

Se actualizaron las pruebas de consultas sucesivas y aclaración para reflejar el contrato visible.
El flujo de error mantiene el formulario para permitir corregir o reintentar la entrada.

Validación final:

```text
pytest: 171 passed, 2 deselected; código 0
ruff check: All checks passed; código 0
ruff format --check: 56 files already formatted; código 0
mypy: Success, 34 source files; código 0
import-linter: 2 contracts kept, 0 broken; código 0
openspec validate 05-frontend-hardening --strict: valid; código 0
```

La revisión fue realizada por la misma sesión; la revisión remota queda en el PR.
