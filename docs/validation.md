# Evidencia de Arko 0.1 — 2026-11-03

Alcance: implementación inicial en Windows, Python 3.12.11, Node 24.6.0 y Docker
29.9.2. Criterios fijados antes de implementar en [acceptance.md](acceptance.md).
La validación funcional es ejecutable; no es un estudio comparativo de agentes.

## Ruta ejecutada

Preflight: `./scripts/arch-preflight.ps1` sobre repositorio recién creado; Git,
Python y Node disponibles, cero pruebas preexistentes. Sentrux tomó baseline de
la carpeta vacía. No existía grafo Graphify ni reglas `.sentrux/rules.toml`.

Postflight: `./scripts/arch-postflight.ps1 -Docker`, que ejecuta
`scripts/validate.py --docker` con el Python del entorno del ejemplo. Se necesitó
escalación del sandbox para la red, los temporales Windows y el daemon Docker;
la revisión automática autorizó esas ejecuciones. No se publicaron imágenes; en
esa primera validación no se instaló el plugin. Los contenedores propios se
detuvieron al terminar. La instalación solicitada posteriormente consta abajo.

Registro completo con comandos, salidas, códigos esperados y duración:
`artifacts/validation.json`. El log anterior con
Docker queda en `artifacts/validation-docker.json`. Son evidencia local generada,
no fixtures que redefinan el resultado de las pruebas.

| Criterio | Comprobación realizada | Resultado |
|---|---|---|
| CLI y preservación | 16 pruebas unittest: colisiones, nombres/rutas, frontend posterior, cierre de dependencias, mapa obsoleto, imports, actualizaciones sin escritura y recuperación en proceso nuevo | Pasa |
| Ejemplo | Ruff, mypy estricto sobre app, 11 pruebas Python, OpenAPI actual vs aprobado, tipos TS regenerados a temporal, límites de imports, tsc, 5 pruebas frontend y build Vite | Pasa |
| Base recién creada | init → setup con lock → check solo backend; add-feature → composición explícita → frontend → setup → exportar/aceptar contrato de fixture → check | Pasa |
| Campo priority | 1/5 aceptados; 0/6/fracción/string/bool rechazados; default 3 preserva cliente antiguo; formulario envía valor; cliente tipado serializa JSON y rechaza 422 | Pasa |
| Autorización | propietario 200, otro propietario 404, token ausente/incorrecto 401 y configuración ausente 503; mutación que elimina comprobación de propietario hace fallar test | Pasa |
| Validación rota | mutación ge=1 → ge=0 hace fallar test de frontera | Fallo esperado detectado |
| Arquitectura rota | Python service→FastAPI, core→feature y cross-feature no permitido rechazados; import compartido TS→feature rechazado | Fallo esperado detectado |
| Contrato roto | eliminación de ruta/campo, cambio de tipo, campo requerido nuevo y retirada de seguridad rechazados; consumidor TS con title numérico falla tsc | Fallo esperado detectado |
| Desarrollo local | backend y Vite responden por HTTP; ASGI con excepción inicial hace terminar dev con error | Pasa |
| Docker | imágenes backend/full stack construidas, health 200, index HTML en full stack, uid 10001 | Pasa |
| Skill/paquete | validador oficial quick_validate: Skill is valid; manifiesto/catálogo y ZIP comprobados por package.py | Pasa con límite indicado abajo |

Los fallos de las mutaciones son éxito de detección: el script exige código no
cero y mensajes del comportamiento esperado. No acepta fallos arbitrarios de
instalación o import como regresiones detectadas. `check` no cambia baselines.

## Recuperación y revisión independiente

Un subagente sin historial de implementación recibió AGENTS, skill, tarea y
comando context. Recuperó prioridad 1..5/default 3, compatibilidad con título,
recorrido Python→contrato→React→pruebas y ausencia de permiso de despliegue.
Necesitó leer auth/API para afirmar los códigos de respuesta; el mapa no los prueba.
El proceso Python nuevo también recupera literalmente la nota de tarea en unittest.
No se lanzó otra sesión real de Codex ni se verificó la instalación del plugin en
el cliente durante la primera entrega: la evidencia inicial cubría empaquetado y
ejecución de sus operaciones. La comprobación posterior amplía ese alcance.

### Instalación e identidad solicitadas posteriormente

El 2026-11-03 se comprobó que `arko-local` no estaba registrado. Tras la petición
del usuario se añadieron `author.name` y `interface.developerName` = Joel Gangini,
nombre visible Arko y el favicon PNG de 256 px con fondo negro de
`app/frontend/public/favicon-256.png` del proyecto facilitado por el autor. Copia exacta,
sin transformaciones; procedencia y SHA256 en `plugins/arko/assets/provenance.json`.

Se registró el directorio de Arko con `codex plugin marketplace add` y se ejecutó
`codex plugin add arko@arko-local --json`. La consulta
`codex plugin list --marketplace arko-local --json` devuelve `installed: true`,
`enabled: true`, versión 0.1.0. Caché instalada:
`~/.codex/plugins/cache/arko-local/arko/0.1.0`.
Se comprobaron autor, rutas de icono y hash de la imagen instalada. La CLI de esa
copia instalada recupera `context notes` sin problemas de mapa; resultado local en
`artifacts/context-installed-plugin.json`. No se capturó ni inspeccionó visualmente
el directorio de plugins de la app; un cliente ya abierto puede necesitar recarga.

La revisión detectó imports dinámicos aliasados, updates sin features, enlaces
rotos y supervisión insuficiente del reloader. Se corrigieron y añadieron pruebas.
La inicialización sin locks observada durante una edición concurrente quedó
resuelta; la prueba fresca valida el resultado final. Dos agentes en total:
investigación de fuentes y revisión/recuperación, sin implementación concurrente.
Tiempo/tokens propios de agentes no expuestos; no se atribuye ahorro.

## Sentrux y límites

Ruta MCP: scan → session_start → cambios → rescan → session_end. Sin reglas
locales, por lo que no hay un resultado de check_rules. Gate **no aprobado**:
señal 1.0000 de la carpeta vacía → 0.7247; funciones complejas 0→1; ciclos 0→0.
No se presenta esta comparación como aprobación arquitectónica. Antes de quitar
la copia de la CLI del ejemplo, la señal era 0.5718 con redundancia 0.8264.
Después: 95 archivos, redundancia 0.3854; el principal factor pasa a desigualdad
de tamaños (0.4809). El ejemplo ahora delega a la única implementación del plugin.

La comparación parte de cero código, no de una aplicación previa equivalente.
Permanecen duplicación intencional entre plantilla y ejemplo materializado y un
analizador de dependencias con varias ramas. Se conserva por trazabilidad y
pruebas de comportamiento; no se inventan reglas ni se rebaja el gate para lograr
verde. Antes de ampliar perfiles, revisar este coste con un baseline funcional.
Graphify: no configurado, no se inicializó.

Limitaciones funcionales: identidad local única, datos efímeros, compatibilidad
OpenAPI conservadora e incompleta, imports estáticos sin prueba de dependencias
en runtime, actualización manual propuesta, sin migración entre versiones.
Las bases Docker usan tags versionados, no digest inmutable. Hay un aviso upstream
de deprecación del TestClient con httpx; la ejecución actual pasa, y una actualización
debe evaluar httpx2 con su API y pruebas antes de cambiar el lock.

Las pruebas React usan DOM simulado y fetch controlado; las pruebas HTTP comprueban
servidores reales. No se hizo revisión visual ni captura de pantalla ni prueba de
navegador extremo a extremo. No se ensayó Linux nativo fuera de los contenedores.
No hay afirmaciones de mejora de productividad ni garantía de conservar contexto.

## Reintentos y mantenimiento

La primera descarga falló por el proxy del sandbox; funcionó con ejecución
autorizada. Dos intentos de unittest encontraron denegación de acceso a temporales
Windows; no se cambiaron permisos globales y la ejecución autorizada pasó.
La primera integración fresca reveló clasificación variable de imports en Ruff;
se fijó `known-first-party = ["app"]` en el perfil y se repitió el postflight.
Las últimas repeticiones respondieron a cambios concretos en el cliente y la CLI.
El log registra duraciones por comando; los builds finales reutilizan cache y
sus tiempos no representan una instalación fría ni comparación de productividad.

## Regresión de contexto en consumidores — 2026-11-23

El preflight pasó 16 pruebas. El nuevo caso del CLI generado falló con el mismo
error que los consumidores antes de corregirlo. La prueba verifica que el JSON
conserva las referencias estáticas, el hash y los símbolos de la prueba, y que
`dynamic_import_lines` señala las líneas para revisar.

| Aplicación consumidora | CLI original | Copia corregida |
| --- | --- | --- |
| Aplicación con puertos personalizados | Código 1 por un import dinámico | Código 0, 316 archivos, dos diagnósticos de línea y cero problemas de auditoría |
| Aplicación con validación frontend propia | Código 1 por un import dinámico | Código 0, 143 archivos, un diagnóstico de línea y cero problemas de auditoría |

Cada copia conservó su CLI y su runtime, y ejecutó `context` contra la raíz real
del proyecto. El cambio se integró solo en `arko_lib/context.py` de cada copia.
Ambos resultados coincidieron con los de la CLI de Arko. Se comprobó por hash que
los archivos originales usados en la prueba conservaron su contenido.
Los resultados locales se guardaron en `artifacts/context-consumer-regression.json`.

## Rutas publicables y evaluación de oasdiff — 2026-11-23

La regresión del proyecto generado declara un POST y un GET con parámetro,
verifica ambos con el router montado y luego retira el router manteniendo el
OpenAPI publicado mediante una sobrescritura. Se exige que `check`, `contract`
y `accept-contract` identifiquen ambos métodos y rutas como ausentes de la
aplicación real.

Se ejecutó `oasdiff breaking --fail-on ERR --format json` con el binario oficial
v1.39.0 para Windows, verificado por SHA-256. Los ocho documentos sintéticos
pasaron `oasdiff validate`. [Versión oficial](https://github.com/oasdiff/oasdiff/releases/tag/v1.39.0).

| Cambio OpenAPI 3.1 | Resultado |
| --- | --- |
| Propiedad opcional nueva en una respuesta con `additionalProperties: false` | 0, falso negativo |
| Enum de respuesta `[true]` → `[1]` | 1, detectado |
| POST nuevo en una ruta con GET existente | 0, compatible |
| Propiedad opcional nueva en una respuesta abierta | 0, compatible |

Subir `response-optional-property-added` a error bloqueó tanto la respuesta
cerrada como el control abierto. `oasdiff` queda como candidato de evaluación
hasta contar con una comprobación que distinga ambos casos. Arko conserva su
comparador y sus límites conocidos. El registro local de esta prueba se guardó en
`artifacts/oasdiff-evaluation/results.json`.

## Estabilidad de nombres OpenAPI — 2026-11-23

El caso de regresión exporta OpenAPI desde `app.main:app` antes y después de
montar una segunda funcionalidad con un campo distinto en su modelo. Antes de
la corrección cambió la operación de la primera funcionalidad en los dos casos.

| Caso | Contrato que se conserva | Modelos de la segunda funcionalidad |
| --- | --- | --- |
| Plantillas `line_items` y `line__items` | Operaciones, componentes y referencias de `line_items` | `CreateItem_line__items` e `Item_line__items` |
| Copia del ejemplo Notes con `reminders` | Operaciones, componentes `CreateItem` e `Item` y contrato aprobado de Notes | `CreateItem_reminders` e `Item_reminders` |

La comprobación exige los mismos bytes del baseline en ambos casos. La propuesta
de actualización de Notes indica que deben conservarse los nombres ya aprobados.
Las cachés de herramientas quedan fuera de la generación y del paquete después
de reproducir un fallo de `upgrade` al leer una caché binaria de Ruff.

## Integridad del contrato aprobado — 2026-11-23

La regresión prepara una copia de Notes con su OpenAPI y su registro originales.
Añade un salto de línea a `baseline.json`, que conserva el significado del
documento y cambia su SHA-256. Antes de la corrección pasó `check`. La prueba
exige ahora el fallo por discrepancia con la última aprobación y comprueba que
`check` conserva los dos archivos. La copia vuelve a pasar después de aprobar
explícitamente el OpenAPI verificado.

La suite cubre el registro inicial de un proyecto generado, el registro ausente,
una última entrada inválida y el caso en que solo coincide una aprobación anterior.
La comprobación compara archivos locales. La revisión en control de versiones
establece quién puede cambiar el contrato y su registro conjuntamente.

## Guía de escritorio nativo en Rust — 2026-11-23

El validador oficial de skills aceptó la ficha de Arko. Se verificaron los
metadatos, los enlaces relativos de la skill y la presencia de la guía en el ZIP.
Desde ese paquete se inicializó una aplicación FastAPI con React, se añadió
`notes` y se comprobó su contexto y el hash de la aprobación inicial.

En Windows con Cargo y rustc 1.95.0, se ejecutaron los comandos de formato,
Clippy, pruebas y compilación `release` en un paquete binario mínimo. El
ejecutable produjo la salida esperada. El alcance de esa comprobación fue el
flujo Cargo sin dependencias gráficas.
