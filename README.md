<h1 align="center">Arko</h1>

<p align="center">
  <img src="docs/assets/arko-cover.png" width="960" alt="Ilustración de un servicio modular, un contrato OpenAPI y una interfaz web opcional, con una guía de escritorio separada.">
</p>

<p align="center"><em>Crea una API en FastAPI y añade React cuando lo necesites.</em></p>

<p align="center">
  <a href="plugins/arko/plugin.json"><img src="https://img.shields.io/badge/Plugin-0.1.1-165D63?style=flat-square" alt="Versión del plugin 0.1.1"></a>
  <a href="#instalar-en-codex"><img src="https://img.shields.io/badge/Codex-Plugin_local-303640?style=flat-square" alt="Plugin local de Codex"></a>
  <a href="docs/tutorial.md"><img src="https://img.shields.io/badge/Python-3.12%20%2F%203.13-215C8D?style=flat-square&amp;logo=python&amp;logoColor=white" alt="Requiere Python 3.12 o 3.13"></a>
</p>

<p align="center"><strong>Tecnologías</strong></p>

<p align="center">
  <a href="docs/architecture.md"><img src="https://img.shields.io/badge/FastAPI-0E695D?style=flat-square&amp;logo=fastapi&amp;logoColor=white" alt="FastAPI"></a>
  <a href="docs/architecture.md"><img src="https://img.shields.io/badge/OpenAPI-456326?style=flat-square&amp;logo=openapiinitiative&amp;logoColor=white" alt="OpenAPI"></a>
  <a href="docs/architecture.md"><img src="https://img.shields.io/badge/React-Opcional-195F72?style=flat-square&amp;logo=react&amp;logoColor=white" alt="React opcional"></a>
  <a href="plugins/arko/skills/arko/references/rust-desktop.md"><img src="https://img.shields.io/badge/Rust-Gu%C3%ADa_de_escritorio-8B4B2E?style=flat-square&amp;logo=rust&amp;logoColor=white" alt="Rust, guía de escritorio"></a>
</p>

<p align="center">
  <a href="#instalar-en-codex">Instalar</a> ·
  <a href="docs/tutorial.md">Crear la primera API</a> ·
  <a href="docs/architecture.md">Arquitectura</a> ·
  <a href="docs/testing.md">Pruebas</a>
</p>

## Qué puedes hacer

| Punto de partida | Qué ofrece Arko |
| --- | --- |
| **API o servicio en Python** | Genera una base FastAPI organizada por funcionalidades con un contrato OpenAPI y comprobaciones locales. |
| **Aplicación web** | Añade un frontend React y TypeScript durante la creación o cuando el backend esté listo. |
| **Escritorio en Rust** | Orienta la elección de Iced o egui, la organización de la lógica y la validación con Cargo. [Guía de escritorio](plugins/arko/skills/arko/references/rust-desktop.md) |

## Instalar en Codex

Desde la carpeta del repositorio, en un cliente con gestión de plugins por CLI:

```powershell
codex plugin marketplace add (Get-Location).Path
codex plugin add arko@arko-local
```

Abre un chat de Codex en tu espacio de trabajo y pide «Usa Arko para crear una API». Para probar la CLI por tu cuenta, sigue el [tutorial](docs/tutorial.md). Necesitas Python 3.12 o 3.13 y uv. Para React, necesitas Node.js 22.12 o posterior.

## Documentación

- [Arquitectura](docs/architecture.md) para entender qué genera Arko y cómo comprueba el contrato.
- [Pruebas y validación](docs/testing.md) para comprobar el generador y la aplicación de ejemplo.
- [Ejemplo Notes](examples/notes/docs/repository-map.md) para explorar una funcionalidad con backend y frontend.
- [Flujo de mantenimiento](plugins/arko/skills/arko/references/workflow.md) para añadir funcionalidades, renovar el contrato y revisar actualizaciones.

Arko es un proyecto de Joel Gangini.
