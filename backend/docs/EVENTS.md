# Eventos del sistema

Este documento lista los eventos emitidos y consumidos por cada módulo del backend.

---

## 📦 usuarios y auth (Usuarios y Autenticación)

### Eventos emitidos (produce) — usuarios

- `usuario.creado`

  Se emite cuando un nuevo usuario completa el registro.

  Payload:

  ```json
  { "usuario_id": 123, "email": "user@example.com" }
  ```

- `usuario.password_reseteado`

  Se emite cuando el usuario confirma un cambio de contraseña.

  Payload:

  ```json
  { "usuario_id": 123 }
  ```

### Eventos escuchados (consume) — usuarios

- (Ninguno) — Este módulo es principalmente reactivo a las llamadas API.

---

## 💳 suscripciones (Freemium y Pagos)

### Eventos emitidos (produce) — suscripciones

- `transaccion.creada`

  Se emite cuando se inicia un checkout y el sistema crea una `Transaccion` en estado `pending`.

  Payload (ejemplo):

  ```json
  {
    "transaccion_id": 456,
    "usuario_id": 123,
    "plan_id": 2,
    "monto": "49.99",
    "status": "pending",
    "created_at": "2025-10-30T12:00:00Z"
  }
  ```

- `transaccion.actualizada`

  Se emite cuando el estado de una `Transaccion` cambia (por ejemplo, tras procesar el `payment_token` en el webhook).

  Payload (ejemplo):

  ```json
  {
    "transaccion_id": 456,
    "status": "success",
    "provider_metadata": { "provider": "simulator", "token": "0" },
    "updated_at": "2025-10-30T12:00:05Z"
  }
  ```

- `suscripcion.actualizada`

  Se emite cuando la suscripción de un usuario cambia (ej. activación tras pago, cancelación, cambio de plan).

  Nota: cuando la actualización es consecuencia de un cobro exitoso, incluir `transaccion_id` para trazar la operación.

  Payload (ejemplo):

  ```json
  {
    "suscripcion_id": 987,
    "usuario_id": 123,
    "plan_anterior": "Free",
    "plan_nuevo": "Premium",
    "fecha_inicio": "2025-10-30T12:34:56Z",
    "fecha_fin": null,
    "transaccion_id": 456
  }
  ```

### Eventos escuchados (consume) — suscripciones

- `usuario.creado` — Para crear automáticamente una suscripción `Free` por defecto en `suscripciones_usuario`.

- `transaccion.actualizada` — Opcional: algunos consumidores pueden reaccionar a cambios de transacción (por ejemplo, para métricas o auditoría). El webhook interno que procesa `payment_token` es el responsable de actualizar la `Transaccion` y luego emitir `transaccion.actualizada`.

---

## 📡 sensores (Ingesta de datos y viajes)

### Eventos emitidos (produce) — sensores

- `frame.recibido`

  El "latido" del sistema. Se emite cada vez que el simulador envía un paquete de datos.

  Payload (ejemplo):

  ```json
  {
    "moto_id": 1,
    "timestamp": "...",
    "lecturas": [ { "parametro": "rpm", "valor": 1450 }, { "parametro": "temp_motor", "valor": 85 } ]
  }
  ```

- `viaje.iniciado`

  Se emite cuando el sistema detecta que la moto empieza a moverse.

  Payload:

  ```json
  { "moto_id": 1, "viaje_id": 42 }
  ```

- `viaje.finalizado`

  Se emite cuando el viaje termina.

  Payload:

  ```json
  { "moto_id": 1, "viaje_id": 42, "distancia_km": 15.2, "velocidad_media": 45.1 }
  ```

### Eventos escuchados (consume) — sensores

- (Ninguno) — Es la fuente principal de eventos, iniciado por la llamada API `POST /api/ingest/frame`.

---

## 🏍️ motos (Gestión del gemelo digital)

### Eventos emitidos (produce) — motos

- `estado.cambiado`

  Se emite cada vez que la lógica de 4 estados cambia el estado de un componente.

  Payload:

  ```json
  { "moto_id": 1, "componente_id": 5, "estado_anterior": "Bueno", "estado_nuevo": "Atencion" }
  ```

- `estado.critico_detectado`

  Evento de alta prioridad para alertas inmediatas.

  Payload:

  ```json
  { "moto_id": 1, "componente_id": 2, "estado_nuevo": "Critico", "valor": 105.0 }
  ```

- `servicio.vencido`

  Se emite cuando la lógica de mantenimiento pasa a `Critico`.

  Payload:

  ```json
  { "moto_id": 1, "componente_id": 1, "mensaje": "Servicio de 10.000km vencido" }
  ```

### Eventos escuchados (consume) — motos

- `frame.recibido` — Disparador principal; usado para ejecutar la lógica de 4 estados y actualizar `estado_actual`.

---

## 🧠 ml (Machine Learning)

### Eventos emitidos (produce) — ml

- `anomalia.detectada`

  Se emite cuando el modelo detecta un comportamiento anómalo (p. ej. temperatura subiendo muy rápido).

  Payload:

  ```json
  { "moto_id": 1, "anomalia": "Incremento anómalo de T° del motor detectado" }
  ```

- `prediccion.generada`

  Se emite cuando el modelo de predicción genera y persiste un resultado.

  Payload:

  ```json
  { "moto_id": 1, "componente_id": 8, "mensaje": "Desgaste de pastillas de freno en 850km" }
  ```

### Eventos escuchados (consume) — ml

- `frame.recibido` — Disparador principal; alimenta los modelos de inferencia.

---

## ⚠️ fallas (Diagnóstico de Fallas - LLM)

### Eventos emitidos (produce) — fallas

- `diagnostico.generado`

  Se emite después de que el LLM genera el resumen y se guarda en `insights_llm`.

  Payload:

  ```json
  { "moto_id": 1, "insight_id": 77 }
  ```

### Eventos escuchados (consume) — fallas

- `estado.critico_detectado` — Disparador principal para iniciar la llamada al LLM.
- `anomalia.detectada` — (Opcional) también puede disparar una llamada al LLM para explicar la anomalía.

---

## 🔧 mantenimiento (Mantenimiento predictivo)

### Eventos emitidos (produce) — mantenimiento

- `mantenimiento.registrado`

  Se emite cuando el usuario registra un servicio manualmente.

  Payload:

  ```json
  { "moto_id": 1, "tipo": "Cambio de aceite" }
  ```

### Eventos escuchados (consume) — mantenimiento

- `servicio.vencido` — Para crear una tarea de mantenimiento visible para el usuario.
- `prediccion.generada` — Para crear una tarea de mantenimiento sugerida (ej. "Agendar cambio de pastillas").

---

## 🔔 notificaciones (Alertas)

### Eventos emitidos (produce) — notificaciones

- (Ninguno) — Es un "sumidero" (sink) de eventos; su trabajo es consumir eventos y enviarlos fuera del sistema (Email, Push, WebSocket).

### Eventos escuchados (consume) — notificaciones

- `usuario.creado` — Para enviar un email de bienvenida.
- `suscripcion.actualizada` — Para enviar confirmación de pago/cambio de plan.
- `estado.critico_detectado` — Disparador clave para notificaciones PUSH urgentes.
- `servicio.vencido` — Para enviar recordatorios por email/push.
- `anomalia.detectada` — Para enviar una notificación de "Atención".
- `diagnostico.generado` — Para notificar que hay un nuevo reporte de diagnóstico listo.
- `viaje.finalizado` — (Opcional) para enviar un resumen del viaje.

---

## 💬 chatbot (IA interactiva)

### Eventos emitidos (produce) — chatbot

- (Opcional) `chat.respuesta_generada` — Podría emitirse para que `notificaciones` lo envíe por WebSocket.

### Eventos escuchados (consume) — chatbot

- (Ninguno) — Módulo reactivo a llamadas API y WebSockets del usuario.
