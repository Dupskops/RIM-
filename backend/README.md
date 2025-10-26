# Backend - RIM-

Este es el servicio backend del proyecto **RIM-**, desarrollado con **FastAPI**.

## 🚀 Requisitos

- Python 3.10 o superior
- Git
- Virtualenv (incluido en Python desde 3.3 con `venv`)

## 🔧 Instalación y Configuración

1. Clonar el repositorio:

```bash
git clone https://github.com/Dupskops/RIM-.git
cd RIM-/backend
```

2. Crear un entorno virtual (dependiendo del SO):

- En Windows || PowerShell:

```bash
python -m venv venv

venv\Scripts\Activate.ps1
```

- En macOS/Linux || Bash:

```bash
python -m venv venv

source venv/bin/activate
```

3. Instalar las dependencias:

```bash
python -m pip install -r requirements.txt
```

4. Copiar el env y colocar la url correcta de la bd

```bash
cp .env.example .env
```

## 🚀 Ejecutar el servidor

```bash
fastapi dev main.py

# O usando uvicorn directamente
uvicorn main:app --reload
```

El backend quedará disponible en:

```cpp
http://localhost:8000
```
