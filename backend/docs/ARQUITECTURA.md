# 🏗️ ARQUITECTURA DE RIM-

> Sistema de Moto Inteligente con arquitectura modular por capas, event-driven y diseño orientado a dominios (DDD simplificado).

---

## 📋 Índice

- [🏗️ ARQUITECTURA DE RIM-](#️-arquitectura-de-rim-)
  - [📋 Índice](#-índice)
  - [🎯 Visión General](#-visión-general)
    - [Características clave](#características-clave)
  - [🔑 Principios Arquitectónicos](#-principios-arquitectónicos)
    - [1. **Separation of Concerns**](#1-separation-of-concerns)
    - [2. **Dependency Inversion**](#2-dependency-inversion)
    - [3. **Single Responsibility**](#3-single-responsibility)
    - [4. **Event-Driven Communication**](#4-event-driven-communication)
    - [5. **API First**](#5-api-first)
    - [6. **Permission-Based Access**](#6-permission-based-access)
  - [📁 Estructura de Directorios](#-estructura-de-directorios)

---

## 🎯 Visión General

RIM- utiliza una **arquitectura modular en capas** donde cada módulo representa un dominio de negocio independiente. Los módulos se comunican entre sí mediante un **Event Bus** (arquitectura event-driven) evitando acoplamiento directo.

### Características clave

- **Modularidad**: Cada dominio (auth, motos, sensores, etc.) es independiente
- **Capas**: Separación clara entre presentación, lógica de negocio y datos
- **Event-Driven**: Comunicación asíncrona mediante eventos
- **Middleware de Permisos**: Control de acceso basado en suscripciones
- **WebSocket**: Comunicación bidireccional en tiempo real
- **Escalabilidad**: Fácil agregar nuevos módulos sin afectar existentes

---

## 🔑 Principios Arquitectónicos

### 1. **Separation of Concerns**

Cada capa tiene una responsabilidad única y bien definida.

### 2. **Dependency Inversion**

Las capas superiores no dependen de las inferiores, sino de abstracciones.

### 3. **Single Responsibility**

Cada módulo y clase tiene una única razón para cambiar.

### 4. **Event-Driven Communication**

Módulos desacoplados que se comunican mediante eventos.

### 5. **API First**

Toda funcionalidad expuesta mediante REST API y WebSocket.

### 6. **Permission-Based Access**

Features controladas por middleware según plan de suscripción.

---

## 📁 Estructura de Directorios

```
RIM-\
|-- docker\
|   |-- docker-compose.yml
|   +-- Dockerfile
|-- docs\
|   |-- ARQUITECTURA.md
|   +-- FREEMIUM_PREMIUM.md
|-- scripts\
|   |-- deploy.sh
|   +-- setup_ollama.sh
|-- src\
|   |-- auth\
|   |   |-- __init__.py
|   |   |-- events.py
|   |   |-- models.py
|   |   |-- repositories.py
|   |   |-- routes.py
|   |   |-- schemas.py
|   |   |-- services.py
|   |   |-- use_cases.py
|   |   +-- validators.py
|   |-- chatbot\
|   |   |-- prompts\
|   |   |   |-- diagnostic_prompt.py
|   |   |   |-- explanation_prompt.py
|   |   |   +-- maintenance_prompt.py
|   |   |-- __init__.py
|   |   |-- events.py
|   |   |-- models.py
|   |   |-- repositories.py
|   |   |-- routes.py
|   |   |-- schemas.py
|   |   |-- services.py
|   |   |-- use_cases.py
|   |   |-- validators.py
|   |   +-- websocket.py
|   |-- config\
|   |   |-- __init__.py
|   |   |-- database.py
|   |   |-- dependencies.py
|   |   +-- settings.py
|   |-- fallas\
|   |   |-- __init__.py
|   |   |-- events.py
|   |   |-- models.py
|   |   |-- repositories.py
|   |   |-- routes.py
|   |   |-- schemas.py
|   |   |-- services.py
|   |   |-- use_cases.py
|   |   +-- validators.py
|   |-- integraciones\
|   |   |-- __init__.py
|   |   +-- llm_provider.py
|   |-- mantenimiento\
|   |   |-- __init__.py
|   |   |-- events.py
|   |   |-- models.py
|   |   |-- repositories.py
|   |   |-- routes.py
|   |   |-- schemas.py
|   |   |-- services.py
|   |   |-- use_cases.py
|   |   +-- validators.py
|   |-- ml\
|   |   |-- trained_models\
|   |   |   |-- anomaly_detector.pkl
|   |   |   +-- fault_predictor.h5
|   |   |-- __init__.py
|   |   |-- events.py
|   |   |-- inference.py
|   |   |-- models.py
|   |   |-- repositories.py
|   |   |-- routes.py
|   |   |-- schemas.py
|   |   |-- services.py
|   |   |-- use_cases.py
|   |   +-- validators.py
|   |-- motos\
|   |   |-- __init__.py
|   |   |-- events.py
|   |   |-- models.py
|   |   |-- repositories.py
|   |   |-- routes.py
|   |   |-- schemas.py
|   |   |-- services.py
|   |   |-- use_cases.py
|   |   +-- validators.py
|   |-- notificaciones\
|   |   |-- __init__.py
|   |   |-- events.py
|   |   |-- models.py
|   |   |-- repositories.py
|   |   |-- routes.py
|   |   |-- schemas.py
|   |   |-- services.py
|   |   |-- use_cases.py
|   |   |-- validators.py
|   |   +-- websocket.py
|   |-- sensores\
|   |   |-- __init__.py
|   |   |-- events.py
|   |   |-- models.py
|   |   |-- repositories.py
|   |   |-- routes.py
|   |   |-- schemas.py
|   |   |-- services.py
|   |   |-- simulators.py
|   |   |-- use_cases.py
|   |   |-- validators.py
|   |   +-- websocket.py
|   |-- shared\
|   |   |-- websocket\
|   |   |   |-- __init__.py
|   |   |   |-- auth.py
|   |   |   |-- base_handler.py
|   |   |   |-- connection_manager.py
|   |   |   |-- decorators.py
|   |   |   +-- permissions.py
|   |   |-- __init__.py
|   |   |-- base_models.py
|   |   |-- constants.py
|   |   |-- event_bus.py
|   |   |-- exceptions.py
|   |   |-- middleware.py
|   |   +-- utils.py
|   |-- suscripciones\
|   |   |-- __init__.py
|   |   |-- events.py
|   |   |-- models.py
|   |   |-- repositories.py
|   |   |-- routes.py
|   |   |-- schemas.py
|   |   |-- services.py
|   |   |-- use_cases.py
|   |   +-- validators.py
|   |-- tests\
|   |   |-- test_auth\
|   |   |-- test_chatbot\
|   |   |-- test_fallas\
|   |   |-- test_mantenimiento\
|   |   |-- test_ml\
|   |   |-- test_motos\
|   |   |-- test_notificaciones\
|   |   |-- test_sensores\
|   |   |-- test_usuarios\
|   |   |-- __init__.py
|   |   +-- conftest.py
|   |-- usuarios\
|   |   |-- __init__.py
|   |   |-- events.py
|   |   |-- models.py
|   |   |-- repositories.py
|   |   |-- routes.py
|   |   |-- schemas.py
|   |   |-- services.py
|   |   |-- use_cases.py
|   |   +-- validators.py
|   +-- main.py
|-- venv\
|-- .env
|-- .env.example
|-- README.md
|-- requirements.txt
```
