# Crear una primera API con Arko

En este recorrido generas una aplicación FastAPI sin interfaz web, compruebas el contrato y verificas que responde en local. Necesitas Python 3.12 o 3.13, uv y una carpeta de destino vacía.

Desde la raíz del repositorio de Arko:

```powershell
python plugins/arko/skills/arko/scripts/arko.py init ../mi-app
python ../mi-app/tools/arko.py setup --root ../mi-app
python ../mi-app/tools/arko.py check --root ../mi-app
python ../mi-app/tools/arko.py dev --root ../mi-app
```

Con el servidor activo, abre `http://127.0.0.1:8000/api/health`. La respuesta esperada es `{"status":"ok"}`. En `http://127.0.0.1:8000/docs` puedes inspeccionar el contrato inicial. Usa **Ctrl+C** para detener el proceso.

Si quieres una interfaz web, agrega React cuando hayas definido las operaciones de tu API. Para escritorio nativo, consulta la [guía de Rust](../plugins/arko/skills/arko/references/rust-desktop.md).

[Cómo se genera el proyecto](architecture.md) · [Cómo se valida](testing.md) · [Flujo de mantenimiento](../plugins/arko/skills/arko/references/workflow.md)
