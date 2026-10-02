# GAES 3 - Sistema de Gestión de Deserciones SENA

Sistema para gestión, seguimiento y control de casos de deserción (GAES 3), con trazabilidad, auditoría inmutable, FSM, borrado lógico y seguridad por defecto.

## Instalación
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Configuración
Copiar `.env.example` a `.env`

## Ejecutar
```bash
python -m src.main
```

## Verificación Calidad
```bash
ruff check . --fix
ruff format .
mypy src --ignore-missing-imports
pytest -v --cov=src --cov-report=term-missing
```