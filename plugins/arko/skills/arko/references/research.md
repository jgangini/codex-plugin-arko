# Fundamento y decisiones — 2026-11-03

Estado: investigación para Arko 0.1, no garantía de vigencia futura. No se copió
código de los tres repositorios de referencia. Dependencias instaladas conservan
sus avisos en sus paquetes y quedan fijadas por lockfiles.

## Fuentes frente a decisiones de Arko

| Fuente | Hallazgo de la fuente | Decisión de Arko |
|---|---|---|
| [OpenAI, Harness engineering, 2026-02-11](https://openai.com/index/harness-engineering/) | Describe AGENTS.md como mapa, conocimiento versionado, límites comprobables y planes dentro del repositorio; experiencia interna. | Instrucciones breves, ADR y estado pendiente, límites ejecutables. Sus cifras no prueban productividad de Arko. |
| [Anthropic, 2025-09-29](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents) | Recuperación progresiva, referencias y notas persistentes; compactar puede perder detalles y explorar tiene coste. | Recuperar según la tarea y ampliar cuando haya incertidumbre. Sin cuota de archivos/tokens ni memoria garantizada. |
| [Vercel, 2026-01-27](https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals) | En una evaluación de APIs Next.js 16, el índice en AGENTS.md superó las condiciones de skills ensayadas. | Mapa siempre accesible y skill para operaciones. El resultado no generaliza a Python ni prueba que una skill siempre sea inferior. |

## Referencias de repositorios

GitHub API/README/licencias/CI inspeccionados el 2026-11-03. Upstream tests no ejecutados.

| Revisión | Alcance/compatibilidad/estado | Licencia |
|---|---|---|
| [openai/skills `49f948f`](https://github.com/openai/skills/tree/49f948faa9258a0c61caceaf225e179651397431) | Catálogo, no arquitectura. README declara deprecated y remite openai/plugins; no archivado. HEAD 2026-06-24, pushed_at 2026-10-28. No usar instalación histórica como contrato actual. | No licencia raíz única detectada; revisar por skill. skill-creator tiene Apache-2.0. |
| [vercel-labs/agent-skills `1a2c79d`](https://github.com/vercel-labs/agent-skills/tree/1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62) | React/Next.js, diseño y despliegue; complementa frontend, no exige Next/Vercel. HEAD 2026-10-27, no archivado, CI de React. | README y React skill declaran MIT; no LICENSE raíz identificado y API raíz devuelve null. Resolver aviso antes de copiar código sustancial. |
| [litestar-org/litestar-skills `150bdbe`](https://github.com/litestar-org/litestar-skills/tree/150bdbebadf79022bd0440e6f3ddcfde22b74f4e) | v0.11.0 early access, 20 skills, Codex CLI >=0.125.0; HEAD 2026-10-20, pushed_at 2026-11-02, CI y pruebas de hooks. No slash commands propios en Codex. | MIT explícita, Cody Fincher/contribuidores 2026. No se importan hooks/políticas. |

`pushed_at` puede referirse a otra rama; no certifica una release. Licencias y
estado requieren volver a verificarse antes de incorporar código futuro.

## Elección de perfil

| Criterio | FastAPI + React | Litestar + React SPA | Litestar + Inertia/React |
|---|---|---|---|
| Responsabilidad | HTTP separa dominio Python y UI | Separación equivalente con handlers/controllers/DTO | Servidor decide rutas/páginas; React presenta props |
| Navegación | Router → esquema/servicio → cliente TS → componente/prueba | Similar; explicitar DI y DTO | Incluir nombre de página, middleware, sesión y redirects |
| Contrato | Pydantic/OpenAPI → TS | OpenAPI, generación con litestar-vite | Props/rutas/protocolo de navegación; API pública es otra decisión |
| Local | Coordinador pequeño de uvicorn/Vite, proxy API | litestar-vite integra procesos/HMR/recursos/tipos | Integración real, con semántica de navegación y errores |
| Checks | Tipos, comportamiento, deriva/compatibilidad HTTP | Equivalentes + configuración de integración | Añadir visitas iniciales/Inertia, props, redirects y CSRF si sesiones |
| Mantenimiento | Dos procesos explícitos, backend independiente | Coordinar versiones Python/npm del plugin | Adecuado si navegación dirigida por servidor es requisito |

Se elige FastAPI por el inicio backend-only y frontera reutilizable con clientes
futuros. No por novedad, popularidad, menos archivos ni supuesta superioridad del
monorepo. Litestar es una alternativa viable; Inertia responde a otra decisión de
navegación y añade semántica innecesaria para este alcance inicial.

Fuentes primarias: [FastAPI routers](https://fastapi.tiangolo.com/tutorial/bigger-applications/),
[SDKs](https://fastapi.tiangolo.com/advanced/generate-clients/),
[Litestar routing](https://docs.litestar.dev/2/usage/routing/overview.html),
[DTO](https://docs.litestar.dev/2/usage/dto/0-basic-use.html),
[Litestar Vite](https://litestar-org.github.io/litestar-vite/usage/vite.html),
[modos](https://litestar-org.github.io/litestar-vite/usage/modes.html),
[Inertia validation](https://inertiajs.com/docs/v3/the-basics/validation).
Inertia usa redirecciones/errores compartidos en su flujo usual, no simplemente
capturar el JSON 422 de un cliente API.

## Capacidades nativas y dependencias

[El formato actual de plugins](https://developers.openai.com/plugins/build/plugins)
admite plugin.json portable, descubrimiento de skills y marketplaces locales.
Arko utiliza ese formato sin hooks, servidor MCP ni comandos Codex inventados.
La instalación/carga en una sesión nueva debe verificarse separadamente de validar
el JSON. La CLI propia es Python estándar; no añade dependencias al host.

[openapi-typescript](https://openapi-ts.dev/introduction) admite OpenAPI 3.0/3.1
y genera tipos sin runtime; [openapi-fetch](https://openapi-ts.dev/openapi-fetch/)
consume esos tipos con fetch. Ambos se usan como API pública de biblioteca, no se
copian internals. Evitan mantener un generador TS casero. TypeScript ya instalado
se reutiliza para analizar imports del frontend. AST de Python para el backend.
No índice persistente: el mapa se contrasta con archivos actuales y contiene hashes.

Limitación: las comprobaciones de dependencias son reglas del perfil y detección
estática, no un sandbox. Reflection, alias no convencionales, red, eventos y
consumidores externos requieren exploración y pruebas adicionales. La comparación
de contratos es conservadora sobre estructura, no prueba formal de sustituibilidad.
