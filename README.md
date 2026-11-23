# Arko 0.1

Plugin de Codex para crear y mantener aplicaciones Python por funcionalidades,
con React/TypeScript opcional. Incluye skill, CLI propia, plantillas, contratos,
mapas comprobables y ejemplo de aceptación. No instala un runtime de agentes LLM.

Autor: **Joel Gangini**. El icono reutiliza un favicon con fondo negro entregado
por el autor y conserva su imagen original.

Se eligió **FastAPI + React/Vite** para permitir empezar solo con backend y añadir
una UI mediante OpenAPI. [Comparación, fuentes y licencias](plugins/arko/skills/arko/references/research.md).
El estándar común está separado del perfil técnico; no se impone estética ni
pantallas de producto. El formulario de notas existe solo en el ejemplo.

## Escritorio con Rust

Para proyectos con lógica e interfaz nativas, pide «usa Arko para crear una
aplicación de escritorio nativa en Rust». La [guía de escritorio](plugins/arko/skills/arko/references/rust-desktop.md)
ayuda a elegir Iced o egui, organizar la lógica y verificar el proyecto con Cargo.
La generación automatizada de Arko se describe en el flujo FastAPI siguiente.

## Empezar

Requisitos: Python 3.12+, uv, Node >=22.12 para React; Docker para construir imágenes.
Desde este repositorio (PowerShell; `python` debe ser un intérprete real):

```powershell
python plugins/arko/skills/arko/scripts/arko.py init ../mi-app
python ../mi-app/tools/arko.py setup --root ../mi-app
python ../mi-app/tools/arko.py check --root ../mi-app
python ../mi-app/tools/arko.py dev --root ../mi-app
```

Añadir una funcionalidad y React más tarde:

```powershell
python ../mi-app/tools/arko.py add-feature notes --root ../mi-app
python ../mi-app/tools/arko.py frontend --root ../mi-app
```

Montar `create_router(Store())` de la funcionalidad en `backend/app/main.py` antes
del montaje estático. Componer el componente desde App.tsx según el producto.
Cuando la API esté lista para publicarse, declarar los métodos y rutas en
`features.<nombre>.public_routes` de `.arko/project.json`. Por ejemplo,
`["POST /api/notes", "GET /api/notes/{item_id}"]`. `check`, `contract` y
`accept-contract` verifican estas operaciones desde la aplicación FastAPI real
y su OpenAPI. `check` también protege las operaciones del contrato aprobado, incluso
en proyectos sin `public_routes`. El listado sirve para declarar operaciones
antes de su primera aprobación.
Luego `setup`, `contract`, revisar el diff, `accept-contract --reason "..."` y
`check`. La composición es explícita; añadir archivos no modifica rutas en secreto.
Para varias funcionalidades, aliasar `create_router` y `Store` al importarlos.
Los modelos nuevos publican nombres OpenAPI que incluyen la funcionalidad, como
`CreateItem_notes` e `Item_notes`. Al actualizar la plantilla para futuras
funcionalidades, conservar los nombres incluidos en los contratos ya aprobados.

## Ejemplo reproducible

Consulta el [mapa del repositorio de Notes](examples/notes/docs/repository-map.md)
para ubicar sus reglas y decisiones.

```powershell
python examples/notes/tools/arko.py setup --root examples/notes
python examples/notes/tools/arko.py check --root examples/notes
python examples/notes/tools/arko.py context notes --root examples/notes
$env:ARKO_API_TOKEN = python -c "import secrets; print(secrets.token_urlsafe(32))"
python examples/notes/tools/arko.py dev --root examples/notes
```

Abrir http://127.0.0.1:5173 e introducir el token local en el formulario. Obtenerlo
desde la variable local del shell; no guardarlo en código ni en VITE_*. El token
solo vive en memoria del componente. API/docs: http://127.0.0.1:8000/docs.
Ctrl+C termina ambos procesos. Reiniciar `dev` después de cambios Python; Vite
mantiene su actualización habitual. El almacén en memoria se pierde al reiniciar.

```powershell
python examples/notes/tools/arko.py docker --root examples/notes --tag arko-notes:local
docker run --rm -p 127.0.0.1:8000:8000 -e ARKO_API_TOKEN arko-notes:local
```

La imagen full stack sirve el frontend en http://127.0.0.1:8000. Backend-only usa
Dockerfile; con React usa Dockerfile.web. No se publica ninguna imagen. Las bases
Docker tienen etiquetas de versión, no digest inmutable: fijar digest por plataforma
es un paso pendiente para reproducibilidad binaria y política de actualizaciones.

## Instalar en Codex

Paquete fuente: `plugins/arko`. `python scripts/package.py` genera el ZIP en
`artifacts/` con la versión declarada en `plugins/arko/plugin.json`. El catálogo
del repo está en `.agents/plugins/marketplace.json`. Registrar desde el cliente:

```powershell
codex plugin marketplace add (Get-Location).Path
codex plugin add arko@arko-local
codex plugin list --marketplace arko-local --json
```

Estos comandos están disponibles en la CLI local comprobada. En clientes sin
`plugin add`, abrir el directorio de plugins, elegir **Arko local** e instalar Arko.
Si el cliente ya estaba abierto, reiniciar o abrir una sesión nueva para cargarlo.
Crear el ZIP o el catálogo por sí solo no registra ni instala el plugin.
La [documentación oficial](https://developers.openai.com/plugins/build/plugins)
distingue marketplace local, instalación y publicación. Pedir «usa Arko para
inicializar una aplicación»; la skill ejecuta la CLI empaquetada. No existen
comandos nativos `codex arko` ni slash commands de Arko.

## Operaciones y mantenimiento

`init`, `add-feature`, `frontend`, `context`, `map`, `setup`, `contract`,
`accept-contract`, `check`, `dev`, `docker`, `upgrade`.
Consultar `--help` y [el workflow](plugins/arko/skills/arko/references/workflow.md).

`context` devuelve archivos actuales, símbolos/imports Python, hashes, dependencias,
consumidores declarados y estado pendiente. Si una prueba en `backend/tests` usa
imports dinámicos, su entrada conserva los imports estáticos y añade las líneas
que requieren revisión en `dynamic_import_lines`. La auditoría de límites del
código de aplicación sigue rechazando los imports dinámicos. `check`
detecta mapas obsoletos; `map` los actualiza solo por petición explícita.
`upgrade` muestra diffs y personalizaciones, sin escribir. No hay migraciones entre
versiones todavía. Para adoptar una corrección del estándar en un proyecto
existente, integrar los cambios de su CLI, conservar las personalizaciones y
ejecutar `check` contra el contrato aprobado. Corregir los hallazgos en el código
o revisar expresamente el cambio de contrato antes de aceptarlo. El ejemplo bajo
tools delega a la CLI del plugin en este repositorio; conservar ambas carpetas
juntas. Las aplicaciones generadas con
`init` sí incluyen su propia CLI y plantillas, y funcionan fuera de este repositorio.
El generador instala `AGENTS.md` desde `templates/base/agent-instructions.md`.

`check` compara los bytes de `contracts/baseline.json` con el SHA-256 de la
última aprobación en `contracts/acceptance.json`. Si difieren, recuperar el
archivo aprobado o revisar el OpenAPI actual y ejecutar `accept-contract` con
un motivo. `init` registra la aprobación inicial. Las plantillas preservan los
bytes del contrato en Git para que el hash sea estable entre plataformas.

Validación de desarrollo: `./scripts/arch-preflight.ps1`, cambios y
`./scripts/arch-postflight.ps1`. La ruta unificada usa `scripts/validate.py`;
`--docker` incluye build y smoke tests. [Criterios](docs/acceptance.md),
[evidencia y límites](docs/validation.md). No se mide productividad comparativa.

Pendiente para producción: identidad multiusuario real, almacenamiento durable,
TLS/límites operativos según despliegue y política de compatibilidad ampliada.
El guardia de contratos no implementa toda la semántica OpenAPI y el análisis de
dependencias no demuestra todas las relaciones en runtime. No se garantiza que
notas e índices conserven por sí solos todo el contexto de una sesión.
