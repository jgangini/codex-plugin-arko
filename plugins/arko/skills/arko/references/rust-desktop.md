# Aplicaciones de escritorio nativas con Rust

Fuentes verificadas el 23 de noviembre de 2026.

Usa esta guía para una aplicación de escritorio cuya lógica y cuya interfaz
se escriban en Rust. Aplica el estándar de Arko para definir funcionalidades,
límites del código, decisiones y pruebas. Usa Cargo para crear, compilar y
verificar el proyecto.

## Elegir la interfaz

| Necesidad | Punto de partida |
| --- | --- |
| Una aplicación con formularios y flujos de usuario cuyo estado conviene modelar con mensajes | **Iced**. Empieza con un ejemplo oficial que se parezca a la funcionalidad y consulta la documentación de la versión fijada en el proyecto. [Libro de Iced](https://book.iced.rs/) · [Ejemplos de Iced](https://github.com/iced-rs/iced/tree/98bd48fe011efc0ec5819fee0fa7673a7169ff11/examples) |
| Un inspector, editor o herramienta interactiva cuya interfaz encaja con el modo inmediato | **egui con eframe**. Usa la plantilla upstream para revisar el punto de entrada y el ciclo de vida nativos. Mide el costo de dibujar vistas grandes antes de diseñarlas completas. [eframe](https://docs.rs/eframe/latest/eframe/) · [Plantilla upstream](https://github.com/emilk/eframe_template/tree/f108546a2b9f2fc6a82543ceae1625a3893305cb) · [Rendimiento en egui](https://github.com/emilk/egui/blob/main/README.md#cpu-usage) |

Si el proyecto ya depende de una interfaz React, Tauri permite aprovecharla con
un núcleo Rust y un WebView. Incluye esa opción en la comparación cuando la
reutilización de la interfaz sea un requisito. [Modelo de procesos de Tauri](https://v2.tauri.app/concept/process-model/)

Antes de adaptar archivos de un ejemplo, usa la revisión que corresponda a las
versiones elegidas y conserva la atribución y los avisos de su licencia. Iced
declara MIT. La plantilla de eframe declara MIT o Apache-2.0 y la revisión
enlazada requiere Rust 1.95. [Licencia de Iced](https://github.com/iced-rs/iced/blob/98bd48fe011efc0ec5819fee0fa7673a7169ff11/LICENSE) · [Manifiesto de la plantilla eframe](https://github.com/emilk/eframe_template/blob/f108546a2b9f2fc6a82543ceae1625a3893305cb/Cargo.toml)

## Crear y mantener el proyecto

1. **Define una funcionalidad completa.** Identifica los sistemas objetivo y
   describe una acción real con su resultado y su error principal. Si el
   proyecto es nuevo, usa `cargo new --bin mi-app` o parte del ejemplo upstream
   elegido. En uno existente, revisa `Cargo.toml`, `Cargo.lock`, el archivo de
   toolchain, los scripts de CI y las reglas del proyecto. [Cargo new](https://doc.rust-lang.org/cargo/commands/cargo-new.html)
2. **Organiza la funcionalidad en un solo crate al empezar.** Deja el punto de
   entrada a cargo del arranque. Coloca la lógica y sus pruebas en módulos por
   funcionalidad y mantén allí tipos y errores independientes de Iced o egui.
   Usa un workspace cuando el proyecto necesite varios paquetes, por ejemplo
   para compartir el mismo núcleo entre el escritorio y una CLI. [Cargo Workspaces](https://doc.rust-lang.org/cargo/reference/workspaces.html)
3. **Mantén la ventana receptiva.** Ejecuta lectura de archivos, red y cálculos
   largos fuera del hilo de interfaz. Devuelve progreso, resultados o errores
   que la interfaz pueda presentar. Para vistas grandes, procesa y dibuja lo
   que el usuario necesita en pantalla. Mide arranque, memoria y latencia de
   la acción representativa con una compilación `release`, en el mismo equipo
   y con los mismos datos al comparar alternativas. [Perfiles de Cargo](https://doc.rust-lang.org/cargo/reference/profiles.html)
4. **Prueba los límites reales.** Prueba el núcleo sin abrir la ventana y
   comprueba el flujo desde el binario en el sistema objetivo, incluidos foco,
   navegación por teclado y errores relevantes para la funcionalidad. Los tipos
   y errores de Rust definen los límites internos. Usa OpenAPI cuando la
   aplicación tenga una API HTTP que deba generar o verificar con un contrato.

## Verificación con Cargo

Registra la versión de Rust y los componentes requeridos en
`rust-toolchain.toml` cuando el proyecto necesite fijarlos. Si declaras una
versión mínima con `rust-version`, inclúyela en la validación prevista. Genera
el `Cargo.lock` al seleccionar las dependencias y consérvalo en control de
versiones para la aplicación. [Selección del toolchain](https://rust-lang.github.io/rustup/overrides.html) · [Versión mínima de Rust](https://doc.rust-lang.org/cargo/reference/rust-version.html)

Con el lockfile disponible, ejecuta desde la raíz. En un workspace, aplica
`--workspace` a Clippy, pruebas y compilación cuando quieras verificar todos
los paquetes de ese workspace.

```sh
cargo fmt --all -- --check
cargo clippy --locked --all-targets -- -D warnings
cargo test --locked
cargo build --locked --release
```

Integra estas comprobaciones en los scripts y CI que el proyecto ya usa.
Arranca el binario de distribución en cada plataforma comprometida y deja
evidencia del flujo probado, la versión de la herramienta y los límites
pendientes. Si el usuario necesita un instalador, valida también su instalación
y arranque en el sistema objetivo. [Clippy en CI](https://doc.rust-lang.org/clippy/continuous_integration/index.html) · [Plataformas de Rust](https://doc.rust-lang.org/rustc/platform-support.html)
