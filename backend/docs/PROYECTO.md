# 🏍️ RIM - Sistema Inteligente de Moto con IA

> **Ecosistema completo de moto inteligente** que integra sensores IoT, inteligencia artificial predictiva, chatbot en lenguaje natural y visualización 3D interactiva para diagnóstico, mantenimiento preventivo y optimización de rendimiento de motocicletas.

---

## 📋 Índice

- [Descripción General](#-descripción-general)
- [Objetivos del Proyecto](#-objetivos-del-proyecto)
- [Componentes Principales](#-componentes-principales)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Modelo de Negocio](#-modelo-de-negocio)
- [Stack Tecnológico](#-stack-tecnológico)
- [Funcionalidades Clave](#-funcionalidades-clave)
- [Flujo de Datos](#-flujo-de-datos)
- [Casos de Uso](#-casos-de-uso)
- [Diferenciadores](#-diferenciadores)
- [Roadmap](#-roadmap)

---

## 🎯 Descripción General

**RIM** es un sistema integral que transforma motocicletas convencionales en **motos inteligentes** mediante la integración de:

- **Sensores IoT** en tiempo real (temperatura, vibración, presión, batería, GPS)
- **IA de Edge** embebida en la moto para detección de anomalías local
- **Machine Learning en la nube** para mantenimiento predictivo avanzado
- **Chatbot con LLM local (Ollama)** para diagnóstico en lenguaje natural
- **Gemelo Digital 3D** para visualización interactiva del estado de la moto
- **Sistema de notificaciones** en tiempo real vía WebSocket

El sistema opera bajo un **modelo Freemium** donde las funciones básicas vienen incluidas con la moto nueva, y las funcionalidades avanzadas (IA predictiva, modos de conducción, asistencia remota) se desbloquean mediante suscripción Premium.

---

## 🎯 Objetivos del Proyecto

### Objetivo Principal

Crear un **ecosistema completo** que permita a los usuarios:

1. Monitorear el estado de su moto en tiempo real
2. Predecir fallos antes de que ocurran
3. Recibir recomendaciones de mantenimiento personalizadas
4. Optimizar el rendimiento y eficiencia de combustible
5. Mejorar la seguridad del piloto

### Objetivos Específicos

- ✅ **Reducir costos de mantenimiento** mediante detección temprana de fallos
- ✅ **Aumentar la vida útil** de componentes críticos
- ✅ **Mejorar la experiencia del usuario** con interfaz natural (chat)
- ✅ **Generar ingresos recurrentes** mediante suscripciones Premium
- ✅ **Diferenciación competitiva** para fabricantes de motos (KTM, Honda, etc.)

---

## 🧩 Componentes Principales

### 1. 🏍️ **La Moto (Hardware + Sensores)**

Sensores instalados en puntos críticos:

- **Motor**: Temperatura, vibraciones, RPM
- **Sistema eléctrico**: Voltaje batería, ciclos de carga
- **Frenos**: Presión hidráulica, desgaste de pastillas
- **Neumáticos**: PSI, temperatura
- **Navegación**: GPS, acelerómetro (detección de caídas)

**Microcontrolador**: ESP32 / Raspberry Pi / ECU personalizada

### 2. 🤖 **IA Embebida (Edge AI)**

- Modelos **TensorFlow Lite** corriendo localmente en la moto
- **No depende de internet** para funciones críticas
- Detección de anomalías en tiempo real
- Optimización de modos de conducción (Eco, Sport, Off-road)

### 3. ☁️ **Backend (API + ML Pipeline)**

- **FastAPI** con arquitectura modular por capas
- **PostgreSQL** para datos estructurados
- **Redis** para caché y WebSocket pub/sub
- **Machine Learning** para análisis histórico y predicciones avanzadas
- **Ollama (LLM local)** para chatbot sin dependencias de APIs externas

### 4. 💬 **Chatbot con IA**

- **LLM local (Llama 3.1 8B)** vía Ollama
- Consultas en lenguaje natural: *"¿Cómo está mi batería?"*
- Explicación de predicciones: *"En 30 km hay riesgo de sobrecalentamiento"*
- Recomendaciones personalizadas de mantenimiento
- Interfaz WebSocket para respuestas en tiempo real

### 5. 🌐 **Web App + Modelo 3D**

- **React + Three.js** para visualización 3D interactiva
- Modelo 3D de la moto con **fallos resaltados visualmente**
- Dashboard con métricas en tiempo real
- Historial de mantenimiento y predicciones
- **Simulador QR** para demo sin hardware físico

### 6. 🔔 **Sistema de Notificaciones**

- **WebSocket** para alertas en tiempo real
- Notificaciones push a móvil (futuro)
- Diferentes niveles de severidad (info, advertencia, crítico)
- Integración con eventos del sistema

---

## 🏗️ Arquitectura del Sistema

### Arquitectura de Software

```
Arquitectura en Capas por Módulos

src/
├── auth/              # Autenticación JWT
├── usuarios/          # Gestión de usuarios
├── motos/             # Registro de motocicletas
├── sensores/          # Lecturas de sensores + simulador MVP
├── fallas/            # Detección y registro de fallos
├── ml/                # Machine Learning predictivo
├── chatbot/           # Chatbot con Ollama + WebSocket
├── notificaciones/    # Alertas en tiempo real
├── mantenimiento/     # Historial y programación
├── suscripciones/     # Gestión Freemium/Premium
├── shared/            # Código compartido (event bus, websocket)
└── integraciones/     # Ollama LLM provider

Cada módulo tiene:
├── models.py          # Entidades de base de datos
├── schemas.py         # DTOs (Pydantic)
├── repositories.py    # Acceso a datos (CRUD)
├── services.py        # Lógica de negocio
├── use_cases.py       # Orquestación entre servicios
├── routes.py          # Endpoints FastAPI
├── validators.py      # Reglas de negocio
├── events.py          # Eventos del dominio
└── websocket.py       # Handlers WebSocket (si aplica)
```

### Flujo de Comunicación

```
┌─────────────────┐
│   Sensores IoT  │  → Datos en tiempo real
└────────┬────────┘
         │
         ↓ (MQTT/HTTP)
┌─────────────────┐
│  Edge AI (Moto) │  → Detección local
└────────┬────────┘
         │
         ↓ (REST API)
┌─────────────────┐
│  Backend FastAPI│
│  ├─ Sensores    │  → Almacena lecturas
│  ├─ Fallas      │  → Analiza anomalías
│  ├─ ML          │  → Predicciones avanzadas
│  └─ Chatbot     │  → Responde consultas
└────────┬────────┘
         │
         ├→ Event Bus → Notificaciones
         ├→ WebSocket → Frontend en tiempo real
         └→ Ollama    → LLM local
         
         ↓
┌─────────────────┐
│   Frontend      │
│  ├─ Web (React) │  → Dashboard + 3D
│  ├─ Mobile      │  → App nativa (futuro)
│  └─ Chat UI     │  → Interfaz conversacional
└─────────────────┘
```

---

## 💰 Modelo de Negocio

### 🆓 **Plan Freemium** (Incluido con moto nueva)

**Objetivo**: Atraer usuarios y generar confianza

| Feature | Descripción |
|---------|-------------|
| **Alertas básicas** | Mantenimiento rutinario (aceite, batería, llantas) |
| **Historial de servicios** | Registro automático de mantenimientos |
| **Diagnóstico general** | Sensores estándar en tiempo real |
| **Geolocalización básica** | Ubicación de la moto en caso de pérdida |
| **Chatbot básico** | Consultas simples sobre el estado |
| **Conectividad estándar** | Acceso a datos esenciales vía app |

---

### 💎 **Plan Premium** ($9.99/mes o $99.99/año)

**Objetivo**: Personalización y control avanzado

| Feature | Descripción |
|---------|-------------|
| **Modos de manejo** | Configuración urbano/sport/off-road |
| **Diagnóstico predictivo IA** | Detección temprana con recomendaciones |
| **Actualizaciones OTA** | Mejoras de rendimiento remotas |
| **Asistencia remota 24/7** | Conexión con talleres y soporte técnico |
| **Integración wearables** | Alertas en smartwatch/casco inteligente |
| **Reportes avanzados** | Eficiencia, desgaste, estilo de conducción |
| **Chatbot avanzado** | Respuestas detalladas y contextuales |

**Estrategia de Conversión**:

- 🎁 Trial gratuito de 7 días
- 📊 Analytics de features más deseadas
- 🔔 Notificaciones educativas cuando se bloquean features
- 💰 Descuentos por primer mes

---

## 🛠️ Stack Tecnológico

### Backend

- **FastAPI** - Framework web moderno y rápido
- **Python 3.11+** - Lenguaje principal
- **SQLAlchemy** - ORM para base de datos
- **PostgreSQL** - Base de datos relacional
- **Redis** - Caché y pub/sub para WebSocket
- **Alembic** - Migraciones de base de datos

### Machine Learning

- **TensorFlow / PyTorch** - Entrenamiento de modelos
- **TensorFlow Lite** - Modelos embebidos (Edge AI)
- **scikit-learn** - Algoritmos clásicos
- **pandas / numpy** - Procesamiento de datos

### LLM (Chatbot)

- **Ollama** - Servidor LLM local
- **Llama 3.1 8B** - Modelo principal (puede cambiarse a Mistral, Phi, etc.)
- **httpx** - Cliente HTTP asíncrono para Ollama

### Frontend

- **React** - Framework UI
- **Three.js** - Visualización 3D
- **WebSocket** - Comunicación en tiempo real
- **Recharts / D3.js** - Gráficos y visualizaciones

### DevOps

- **Docker & Docker Compose** - Contenedorización
- **GitHub Actions** - CI/CD (futuro)
- **Nginx** - Reverse proxy (producción)

---

## ⚡ Funcionalidades Clave

### 🔍 **Detección de Anomalías**

- **Umbral estático**: Alertas cuando sensores exceden rangos normales
- **Análisis de tendencias**: Detecta cambios bruscos en lecturas
- **ML predictivo**: Predice fallos hasta 30 días antes

### 🤖 **Chatbot Inteligente**

**Consultas soportadas**:

- *"¿Cómo está mi moto?"* → Reporte completo del estado
- *"¿Por qué está caliente el motor?"* → Explicación técnica simplificada
- *"¿Cuándo debo cambiar el aceite?"* → Recomendaciones basadas en uso
- *"¿Qué significa este error?"* → Interpretación de códigos de falla

**Tecnología**:

- LLM local (Ollama) con prompts especializados
- Contexto enriquecido con datos reales de sensores
- Streaming de respuestas vía WebSocket

### 📊 **Visualización 3D**

- Modelo 3D interactivo de la moto
- Componentes resaltados según estado (verde/amarillo/rojo)
- Click en parte → Ver detalles y métricas
- Animaciones para fallos detectados

### 🔔 **Notificaciones en Tiempo Real**

- **WebSocket** para alertas instantáneas
- Niveles de severidad (info, warning, critical)
- Personalización por usuario
- Historial de notificaciones

### 📈 **Reportes y Analytics**

- Gráficos de evolución de sensores
- Comparativas de eficiencia
- Predicciones futuras visualizadas
- Exportación de datos (CSV, PDF)

---

## 🔄 Flujo de Datos

### Ciclo Completo de una Lectura de Sensor

```
1. Sensor mide temperatura del motor: 92°C
   ↓
2. Microcontrolador (ESP32) envía dato vía WiFi
   ↓
3. API recibe: POST /api/sensores/reading
   ↓
4. SensorService detecta anomalía (> 90°C)
   ↓
5. Publica evento: SensorAnomalyDetectedEvent
   ↓
6. FallaService escucha evento y crea registro de falla
   ↓
7. NotificacionService envía alerta vía WebSocket
   ↓
8. Frontend muestra: "⚠️ Motor sobrecalentado - 92°C"
   ↓
9. MLService analiza tendencia y predice: "Riesgo alto en 20km"
   ↓
10. Usuario pregunta en chat: "¿Por qué está caliente?"
    ↓
11. ChatService con Ollama genera explicación contextual
    ↓
12. Usuario recibe recomendación: "Detén y revisa refrigerante"
```

---

## 💡 Casos de Uso

### 1. **Autodiagnóstico en Tiempo Real**

**Escenario**: Piloto nota vibración extraña

- Moto detecta vibraciones anómalas (sensor)
- Sistema crea alerta en panel 3D (suspensión en rojo)
- Chatbot explica: *"Vibraciones elevadas detectadas. Posible desgaste en rodamientos."*
- Recomendación: *"Visita taller en próximos 100km"*

### 2. **Mantenimiento Predictivo**

**Escenario**: Batería envejeciendo

- ML analiza patrones de carga: voltaje decreciente
- Predice fallo en 15 días
- Usuario recibe: *"Tu batería muestra signos de desgaste. Reemplazar en 2 semanas."*
- Se agenda mantenimiento preventivo

### 3. **Optimización de Conducción** (Premium)

**Escenario**: Usuario en ciudad consume mucho combustible

- Sistema detecta conducción agresiva (aceleraciones bruscas)
- Sugiere activar modo "Eco"
- Ajusta mapeo de motor automáticamente
- Resultado: 15% menos consumo

### 4. **Seguridad Post-Accidente**

**Escenario**: Moto detecta caída (acelerómetro)

- Envía ubicación GPS a contactos de emergencia
- Notifica a servicios de asistencia
- Registra datos del incidente (velocidad, hora, condiciones)

---

## 🌟 Diferenciadores

| Característica | RIM | Competencia Típica |
|----------------|-----|-------------------|
| **IA en la moto** | ✅ Edge AI local | ❌ Solo telemetría |
| **LLM local** | ✅ Ollama (privado) | ❌ APIs externas/caras |
| **Gemelo digital 3D** | ✅ Interactivo | ⚠️ Dashboards planos |
| **Chatbot contextual** | ✅ Con datos reales | ❌ FAQs estáticas |
| **ML predictivo** | ✅ Con retroalimentación | ⚠️ Alertas reactivas |
| **Modelo Freemium** | ✅ Incluido con moto | ❌ Todo de pago |
| **Offline-first** | ✅ Edge AI funciona sin red | ❌ Requiere internet |

---

## 🗺️ Roadmap

### **Fase 1: MVP Demo** ✅ (Actual)

- [x] Arquitectura backend modular
- [x] Simulador de sensores (datos sintéticos)
- [x] Chatbot con Ollama local
- [x] API REST completa
- [x] WebSocket para tiempo real
- [x] Sistema de suscripciones Freemium/Premium
- [ ] Frontend básico con visualización 3D
- [ ] QR code para demo con datos simulados

### **Fase 2: Prototipo con Hardware** 🚧

- [ ] Integración ESP32 + sensores físicos
- [ ] MQTT para comunicación IoT
- [ ] Adaptadores para APIs de sensores reales
- [ ] Pruebas en moto real (banco de pruebas)
- [ ] App móvil nativa (React Native)

### **Fase 3: ML en Producción** 📊

- [ ] Recolección de datos reales (1000+ horas de conducción)
- [ ] Entrenamiento de modelos con datos históricos
- [ ] Exportar modelos a TensorFlow Lite
- [ ] Deploy de Edge AI en motos
- [ ] Sistema de feedback para mejorar predicciones

### **Fase 4: Escalamiento** 🚀

- [ ] OTA updates de modelos ML
- [ ] Integración con talleres KTM/Honda/Yamaha
- [ ] Marketplace de plugins de terceros
- [ ] Integración con seguros (descuentos por buen manejo)
- [ ] API pública para developers
- [ ] Soporte multi-marca de motos

### **Fase 5: Features Avanzadas** 🌐

- [ ] Integración con wearables (smartwatch, casco)
- [ ] Comunidad de pilotos (social features)
- [ ] Gamificación (logros, rankings)
- [ ] Asistente de voz (manos libres)
- [ ] Realidad aumentada (AR) para diagnóstico

---

## 📊 KPIs Esperados

### Técnicos

- **Latencia de detección**: < 2 segundos desde sensor a alerta
- **Precisión de predicciones**: > 85% en detección temprana
- **Uptime del sistema**: > 99.5%
- **Tiempo de respuesta chatbot**: < 3 segundos

### Negocio

- **Tasa de conversión Freemium → Premium**: > 5%
- **Churn rate**: < 5% mensual
- **NPS (Net Promoter Score)**: > 50
- **Reducción de costos de mantenimiento**: 20-30%

### Usuario

- **Usuarios activos diarios**: > 70%
- **Consultas al chatbot por usuario/mes**: > 10
- **Satisfacción con predicciones**: > 4.5/5

---

## 🎓 Aprendizajes Clave del Proyecto

### Técnicos

- Arquitectura modular escalable con FastAPI
- Integración de LLM local sin dependencias externas
- Event-driven architecture para desacoplamiento
- WebSocket para comunicación bidireccional en tiempo real
- Edge AI con TensorFlow Lite

### Negocio

- Modelo Freemium bien diseñado genera confianza
- Features premium deben tener valor claro y medible
- Analytics de conversión son críticos para iterar
- Educación del usuario > paywalls agresivos

### Producto

- Chatbot mejora drásticamente UX vs dashboards complejos
- Visualización 3D hace comprensible lo técnico
- Notificaciones contextuales > alertas genéricas
- Predicción > Reacción

---

## 🤝 Contribuciones

Este proyecto está diseñado para ser modular y extensible. Áreas de contribución:

- 🤖 **Nuevos modelos ML** para diferentes tipos de fallos
- 💬 **Mejora de prompts** del chatbot
- 🎨 **Diseño UI/UX** del frontend
- 📱 **App móvil** nativa
- 🔌 **Integraciones** con nuevos sensores o plataformas IoT
- 🌍 **Localización** (i18n) a múltiples idiomas

---

## 📄 Licencia

[Definir licencia según el caso: MIT, Apache 2.0, Propietaria, etc.]

---

## 📞 Contacto

- **Equipo**: [Nombres del equipo]
- **Email**: [email@proyecto.com]
- **Demo**: [link-a-demo]
- **Documentación**: [link-a-docs]

---

## 🙏 Agradecimientos

- **Ollama** por hacer LLMs accesibles localmente
- **FastAPI** por el framework excelente
- **Three.js** por la visualización 3D
- **Comunidad Open Source** por las herramientas increíbles

---

<div align="center">
  
**Construido con ❤️ para hacer las motos más inteligentes, seguras y eficientes**

🏍️ **RIM - Ride Intelligently, Maintain Predictively**

</div>
