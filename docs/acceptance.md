# Arko 0.1 — requisitos y aceptación

Fuente: solicitud del usuario del 2026-11-03; estado: alcance de v0.1.
Esta es la fuente de requisitos; README explica operación y research.md fundamenta decisiones.

Un solo perfil FastAPI + React/TypeScript opcional. Python 3.12+, Node 22.12+,
uv, npm y Docker para distribución. Sin pantallas de producto en la base.
El estándar común no depende del framework. No se implementan agentes de negocio,
proveedores LLM, persistencia de datos ni un segundo framework.

El 2026-11-23 se amplió la skill con una [guía de referencia para escritorio nativo en Rust](../plugins/arko/skills/arko/references/rust-desktop.md).
La skill identifica ese caso, remite a ejemplos upstream y usa Cargo para
inicializar y verificar el proyecto. FastAPI con React opcional es el perfil
de generación automatizada de la CLI.

Antes de implementar se fijan estos criterios observables:

1. Inicializar un directorio vacío; rechazar colisiones y rutas fuera del destino.
   Poder añadir React después conservando todos los archivos personalizados.
2. Añadir una funcionalidad y localizar API, servicio, contratos, consumidor,
   componente y pruebas, además de dependencias y consumidores declarados.
   Detectar archivos ausentes, nuevos archivos no registrados e imports prohibidos.
3. Ejemplo `notes`: campo `priority` opcional (1..5) desde Pydantic a tipos
   generados y formulario React. Aceptar 1 y 5; rechazar 0 y 6; conservar título.
4. Autorización: propietario puede leer; otro usuario recibe 404; ausencia o
   credencial inválida no permiten acceso. Una mutación que elimine la comprobación
   de propietario debe hacer fallar la prueba de regresión.
5. Una lectura independiente sin historial debe recuperar tarea pendiente,
   fuentes, estado, siguiente paso y comprobaciones desde el repositorio.
6. Mutaciones controladas deben hacer fallar comprobaciones de arquitectura,
   contrato incompatible y mapa obsoleto. No actualizar baselines durante `check`.
   El SHA-256 de los bytes de `contracts/baseline.json` debe coincidir con la
   última aprobación de `contracts/acceptance.json`. `check` falla cuando el
   registro falta, es inválido o el hash difiere. `init` registra el contrato inicial.
   Al añadir una funcionalidad con modelos distintos, la primera conserva sus
   componentes OpenAPI, referencias y baseline, incluido el ejemplo Notes.
7. Verificación unificada: pruebas Python, lint y tipos, contrato actual vs aprobado,
   tipos TS actualizados, límites de dependencias, pruebas React y build frontend.
   Las rutas declaradas en `public_routes` deben aparecer como operaciones montadas
   en la aplicación FastAPI real y en el OpenAPI exportado. Un OpenAPI personalizado
   no puede ocultar un router ausente. `check` verifica también las operaciones del
   contrato aprobado, aun sin declaraciones. Una retirada puede exportarse para
   revisión y solo reemplaza el contrato aprobado con `accept-contract`.
   En el comparador, una propiedad nueva de una respuesta cerrada y los cambios
   de tipo entre booleanos y números requieren revisión. Un método nuevo en una
   ruta existente puede agregarse conservando las operaciones previas.
8. `dev` coordina procesos y propaga fallos; `docker` construye imagen backend o
   full stack sin secretos y como usuario no privilegiado. Probar build y HTTP si
   el daemon está disponible; declarar el bloqueo si no lo está.
9. Actualización: versión y hashes iniciales registrados; propuesta de diff sin
   sobrescribir personalizaciones. Aplicación manual revisable en v0.1.
10. Entregar paquete, ejemplo, instrucciones y evidencia real. No atribuir mejoras
    de productividad ni conservación garantizada de contexto a una prueba piloto.

Medición: comandos, resultado, duración y reintentos cuando se registren. Tokens
solo si la plataforma los ofrece. Pruebas automatizadas no equivalen a un estudio
comparativo de agentes ni a una sesión nueva real de Codex.
