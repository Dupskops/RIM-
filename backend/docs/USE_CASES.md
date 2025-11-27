[//]: # (Archivo formateado automáticamente)

# Casos de uso

Este documento resume los casos de uso principales por módulo del backend.

---

## 🔐 auth (Autenticación)

Responsable de verificar la identidad del usuario y gestionar sesiones.

- Registrar usuario
  - Input: email, contraseña
  - Acciones: hashear la contraseña y crear el registro en `usuarios`.

- Enviar email de verificación
  - Generar token en `email_verification_tokens` y enviar por email.

- Verificar email
  - Validar token y actualizar `usuarios.email_verificado`.

- Inicio de sesión (Login)
  - Validar credenciales. Emitir tokens: `access_token` y `refresh_token`.

- Refrescar sesión
  - Recibir `refresh_token` válido y emitir un nuevo `access_token`.

- Cerrar sesión (Logout)
  - Revocar el `refresh_token` de la sesión.

- Reseteo de contraseña
  - Solicitar: generar `password_reset_tokens` y enviar por email.
  - Confirmar: validar token y permitir establecer nueva contraseña.

---

## 👤 usuarios (Gestión de perfil)

Gestión de datos de usuario después de autenticación.

- Obtener perfil
  - Endpoint: `GET /usuarios/me` (ejemplo)
  - Devuelve: nombre, email, teléfono, etc.

- Actualizar perfil
  - Permitir cambios en nombre, apellidos, teléfono.

- Eliminar cuenta
  - Soft delete: marcar `deleted_at`.

- (Admin) Listar usuarios
  - Endpoint: `GET /admin/usuarios` (ejemplo)

- (Admin) Gestionar usuario
  - Activar/desactivar, cambiar rol.

---

## 💳 suscripciones (Freemium y Pagos)

Gestión de planes y acceso según suscripción.

- Listar planes
  - Endpoint: `GET /planes` — muestra Free, Premium y características.

- Crear suscripción (Checkout) — MVP: pagos simulados (sin pasarela)
  - Endpoint: `POST /suscripciones/checkout` — inicia un flujo de pago dentro del sistema (simulado por el backend del MVP).
  - Comportamiento: el endpoint crea una entidad `Transaccion` en estado `pending` y devuelve un token/URL interna que el cliente puede usar para completar el pago simulado.
- Webhook de pago (interno)
  - Endpoint: `POST /webhooks/payments` — punto de entrada para notificaciones de pago. En el MVP (sin pasarela externa) este endpoint recibe el `payment_token` devuelto por `checkout` para simular la notificación del proveedor.
  - Payload esperado (mínimo): `{ "payment_token": "<token>", "transaccion_id": <id>, "metadata": { ... } }`.
  - Regla de simulación (convenio MVP): el backend interpreta el valor del `payment_token` para decidir el resultado del cobro:
    - token `'0'` → pago exitoso (status `success`)
    - token `'1'` → fallo de pago (status `failed`)
  - Acciones: validar payload, actualizar la `Transaccion` (status, provider_metadata), en caso de `success` actualizar `suscripciones_usuario` (estado, `fecha_fin`) y emitir `suscripcion.actualizada`.

- Cancelar suscripción
  - Endpoint: `PATCH /suscripciones/{id}/cancel` — soporta `mode=immediate|end_of_period`.
  - Comportamiento: marcar `estado_suscripcion` y/o ajustar `fecha_fin` según la política.

- Verificar acceso (Middleware)
  - Middleware global consulta `suscripciones_usuario` y `plan_caracteristicas` para permitir/denegar endpoints premium (ej. `chatbot`).

- (Admin) Asignar plan
  - Endpoint: `POST /admin/suscripciones/assign` — permite a un admin asignar manualmente un plan a un usuario (útil para tests y administración).

- Historial de transacciones
  - Endpoint: `GET /usuarios/{id}/transacciones` — lista transacciones para auditoría.

- Reintentos y periodo de gracia
  - Flujos: cuando un pago falla, la suscripción pasa a `PENDIENTE_PAGO`; un job de reintentos puede intentar cobrar de nuevo. Tras X fallos, pasar a `CANCELADA`.

- Reportes y admin
  - Endpoint: `GET /admin/suscripciones` — filtrar por estado, plan, fallas de pago.
  - Métricas: churn, MRR, tasa de fallos.

Nota: en el MVP los pagos son simulados por el backend (no existe integración con pasarela). Se recomienda implementar modelos mínimos `Transaccion` y `WebhookLog` para auditoría y facilitar pruebas.

---

## 🏍️ motos (Gestión del gemelo digital)

Mantiene el estado de salud de la moto y publica eventos cuando hay cambios.

- CRUD de motos
  - Crear/Editar/Mostrar/Eliminar una moto asociada a un usuario.

- Actualizar estado (interno)
  - Escucha evento `frame_recibido`, aplica `reglas_estado` y actualiza `estado_actual` (Estados: Excelente, Bueno, Atención, Crítico).

- Publicar cambio de estado (interno)
  - Si el estado cambia, publicar eventos como `estado_cambiado` o `estado_critico_detectado`.

- Obtener estado actual (API)
  - Endpoint: `GET /motos/{id}/estado-actual` — consumido por la UI 3D.

- Obtener diagnóstico general (API)
  - Endpoint para widget "Diagnóstico" que calcula estado general.

---

## 📡 sensores (Ingesta de datos)

Puerta de entrada de datos desde el simulador o dispositivos.

- Ingestar frame (API)
  - Endpoint: `POST /api/ingest/frame` — recibe paquete de datos.

- Validar datos
  - Reglas básicas (ej. RPM no puede ser negativo cuando corresponde).

- Guardar historial
  - Persistir datos crudos en `historial_lecturas`.

- Publicar evento (interno)
  - Publicar `frame_recibido` en el event bus para consumidores (`motos`, `ml`, etc.).

- Gestión de viajes (interno)
  - Detectar inicio/fin de viaje (velocidad > 0 / velocidad == 0) y crear/actualizar `viajes`.

- Obtener último viaje (API)
  - Endpoint: `GET /motos/{id}/ultimo-viaje`.

---

## 🔧 mantenimiento (Mantenimiento predictivo)

Se encarga del desgaste a largo plazo y servicios programados.

- Calcular estado de servicio (interno)
  - Escucha `frame_recibido`, revisa `kilometraje_actual` y fecha, actualiza `estado_actual` del componente "Servicio de Motor".

- Registrar servicio (API)
  - Registro manual de mantenimiento (e.g. "Cambio de aceite"), resetea contadores relacionados.

- Obtener predicciones (API)
  - Endpoint: `GET /motos/{id}/predicciones` — consulta `predicciones_ml`.

---

## ⚠️ fallas (Diagnóstico de fallas)

Detecta y documenta fallas cuando el sistema reporta estados críticos.

- Generar diagnóstico (interno)
  - Consumir `estado_critico_detectado` del módulo `motos`.

- Consultar LLM (interno)
  - Llamar al módulo `integraciones` (LLM) para generar explicación de la falla.

- Guardar diagnóstico (interno)
  - Persistir en `insights_llm` con prioridad (`Alta` o `Media`).

- Obtener historial de fallas (API)
  - Endpoint: `GET /motos/{id}/historial`.

---

## 🧠 ml (Machine Learning)

Consumo de datos para detección de anomalías y predicción de desgaste.

- Detección de anomalías (interno)
  - Escuchar `frame_recibido`, comparar contra patrones aprendidos y publicar `anomalia_detectada`.

- Predicción de desgaste (interno)
  - Alimentar modelos predictivos (p. ej. `fault_predictor.h5`) con los frames.

- Guardar predicción (interno)
  - Persistir resultados en `predicciones_ml` (ej. "pastillas de freno fallarán en 850 km").

---

## 💬 chatbot (IA interactiva)

Interfaz conversacional entre el usuario y el sistema.

- Iniciar sesión de chat
  - Crear registro en `chat_sesiones`.

- Enviar mensaje (API/WebSocket)
  - Guardar mensaje del usuario en `chat_historial` (rol: `USUARIO`).

- Generar respuesta (interno)
  - Construir prompt con historial y contexto de la moto; llamar a `integraciones` (LLM).

- Devolver respuesta (WebSocket)
  - Guardar respuesta en `chat_historial` (rol: `LLM`) y enviar por WebSocket.

- Obtener historial de chat (API)
  - Cargar mensajes de sesiones anteriores.

---

## 🔔 notificaciones (Alertas)

Consumidor de eventos responsable de alertar al usuario por distintos canales.

- Escuchar eventos críticos
  - Eventos: `estado_critico_detectado`, `servicio_vencido`, `anomalia_detectada`, etc.

- Crear notificación
  - Guardar en `notificaciones` con metadatos.

- Enviar notificación (interno)
  - Enviar por WebSocket, Email u otros canales según severidad.

- Listar notificaciones (API)
  - Permite al usuario ver su historial de alertas.

- Marcar como leída (API)
  - Actualizar estado `leida` de la notificación.
