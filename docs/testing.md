# Pruebas y validación de Arko

## Comprobar un proyecto generado

En el proyecto creado con Arko, ejecuta `python tools/arko.py check --root .` con el entorno preparado. Revisa el resultado antes de aprobar una modificación del contrato. El [tutorial](tutorial.md) muestra cómo llegar a este punto.

## Comprobar el plugin y Notes

Desde la raíz de Arko, prepara el entorno de [Notes](../examples/notes/docs/repository-map.md) antes de validar. Usa Python 3.12 o 3.13, uv y Node.js 22.12 o posterior. La validación necesita libres los puertos locales 8000 y 5173.

```powershell
python examples/notes/tools/arko.py setup --root examples/notes
./scripts/arch-postflight.ps1
```

La validación comprueba el generador, la API, el contrato, los tipos y el frontend de Notes. Para incluir la construcción y la prueba básica de las imágenes, ejecuta `./scripts/arch-postflight.ps1 -Docker` con Docker disponible.

[Script de validación](../scripts/validate.py) · [Criterios de aceptación](acceptance.md) · [Historial de validación](validation.md)
