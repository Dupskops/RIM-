# Schemas

Documento resumen de los esquemas (Pydantic / OpenAPI) usados por el backend.

---

## 🔐 auth (Autenticación)

### TokenSchema (Salida)

Lo que se devuelve al usuario tras un login exitoso.

- `access_token`: str
- `refresh_token`: str
- `token_type`: str (default: `"bearer"`)

### UserRegisterSchema (Entrada)

Body de `POST /auth/register`.

- `email`: EmailStr
- `password`: str (validación de longitud)
- `nombre`: str

### UserLoginSchema (Entrada)

Body de `POST /auth/login`.

- `email`: EmailStr
- `password`: str

### PasswordResetRequestSchema (Entrada)

Body de `POST /auth/request-reset`.

- `email`: EmailStr

### PasswordResetConfirmSchema (Entrada)

Body de `POST /auth/confirm-reset`.

- `token`: str
- `new_password`: str

---

## 👤 usuarios (Gestión de Perfil)

### UserReadSchema (Salida)

Vista pública de un usuario. Importante: no incluye `password_hash`.

- `id`: int
- `email`: EmailStr
- `nombre`: str
- `apellido`: str (opcional)
- `telefono`: str (opcional)
- `rol`: str
- `email_verificado`: bool

### UserUpdateSchema (Entrada)

Body de `PATCH /usuarios/me`. Todos los campos son opcionales.

- `nombre`: str (opcional)
- `apellido`: str (opcional)
- `telefono`: str (opcional)

---

## 💳 suscripciones (Freemium y Pagos)

### CaracteristicaReadSchema (Salida)

Describe una característica incluida en un plan.

- `clave_funcion`: str
- `descripcion`: str

### PlanReadSchema (Salida)

Para `GET /planes` (página de precios).

- `id`: int
- `nombre_plan`: str
- `precio`: Decimal (usa Python's Decimal en el modelo; al serializar a JSON se recomienda enviar como string o number con cuidado)
- `periodo_facturacion`: str
- `caracteristicas`: list[CaracteristicaReadSchema]

### SuscripcionUsuarioReadSchema (Salida)

Para `GET /usuarios/me/suscripcion`.

- `plan`: PlanReadSchema
- `estado_suscripcion`: str
- `fecha_fin`: datetime (opcional)
- `suscripcion_id`: int
- `fecha_inicio`: datetime

### TransaccionCreateResponse (Salida)

Respuesta devuelta por `POST /suscripciones/checkout`.

- `transaccion_id`: int
- `payment_token`: str  (valor que el cliente usará/mostrará; en MVP '0' = success, '1' = failed)

### TransaccionReadSchema (Salida)

Representación de una transacción / intento de cobro.

- `transaccion_id`: int
- `usuario_id`: int (opcional)
- `plan_id`: int (opcional)
- `monto`: Decimal
- `status`: str (Enum: `pending`, `success`, `failed`)
- `provider_metadata`: object (opcional)
- `created_at`: datetime

### PaymentNotificationSchema (Entrada)

Payload mínimo esperado por `POST /webhooks/payments` (webhook/confirmación de pago).

- `transaccion_id`: int
- `payment_token`: str
- `metadata`: object (opcional)

Nota: en el MVP la convención simple es: `payment_token == '0'` => pago exitoso; `payment_token == '1'` => pago fallido. El webhook es la fuente de verdad que actualiza `Transaccion` y `suscripciones_usuario`.

---

### CheckoutCreateRequest (Entrada)

Body de `POST /suscripciones/checkout` — datos que envía el cliente para iniciar el flujo de pago.

- `usuario_id`: int
- `plan_id`: int
- `monto`: Decimal (opcional) — si se omite, usar `Plan.precio`.
- `payment_method`: str (opcional)
- `metadata`: object (opcional)

### SuscripcionCancelRequest (Entrada)

Body de `PATCH /suscripciones/{id}/cancel`.

- `mode`: str (Enum: `immediate` | `end_of_period`)
- `reason`: str (opcional)

### AdminAssignSubscriptionRequest (Entrada)

Body de `POST /admin/suscripciones/assign`.

- `usuario_id`: int
- `plan_id`: int
- `fecha_inicio`: datetime (opcional)
- `fecha_fin`: datetime (opcional)

### TransaccionListResponse (Salida)

Respuesta para listados de transacciones (`GET /usuarios/{id}/transacciones`).

- `items`: list[TransaccionReadSchema]
- `total`: int
- `page`: int
- `per_page`: int

## 📡 sensores (Ingesta de Datos)

### LecturaSensorSchema (Sub-esquema)

Usado dentro del body de ingesta.

- `parametro`: str (ej: `"rpm"`, `"temp_motor"`)
- `valor`: float

### FrameIngestaSchema (Entrada)

Schema principal para `POST /api/ingest/frame`.

- `moto_id`: int
- `timestamp`: datetime
- `lecturas`: list[LecturaSensorSchema]

---

## 🏍️ motos (Gestión del Gemelo Digital)

### MotoCreateSchema (Entrada)

Body de `POST /motos`.

- `vin`: str
- `modelo`: str
- `ano`: int
- `placa`: str (opcional)
- `kilometraje_actual`: float (opcional, default: 0)

### MotoReadSchema (Salida)

Para `GET /motos/{id}`.

- `moto_id`: int
- `usuario_id`: int
- `vin`: str
- `modelo`: str
- `ano`: int
- `placa`: str (opcional)
- `kilometraje_actual`: float

### EstadoComponenteSchema (Salida)

Sub-esquema para la respuesta del estado.

- `componente_id`: int
- `nombre`: str
- `mesh_id_3d`: str
- `estado`: str (Enum: `EXCELENTE`, `BUENO`, ...)
- `ultimo_valor`: float

### DiagnosticoGeneralSchema (Salida)

Para `GET /motos/{id}/diagnostico` (widget).

- `estado_general`: str (Enum: `EXCELENTE`, `BUENO`, ...)
- `partes_afectadas`: list[EstadoComponenteSchema]
- `fecha`: datetime

### ViajeReadSchema (Salida)

Para `GET /motos/{id}/ultimo-viaje` (widget).

- `viaje_id`: int
- `distancia_km`: float
- `velocidad_media_kmh`: float
- `timestamp_fin`: datetime

---

## 🔧 mantenimiento (Mantenimiento Predictivo)

### PrediccionReadSchema (Salida)

Para `GET /motos/{id}/predicciones`.

- `prediccion_id`: int
- `componente_id`: int
- `mensaje_prediccion`: str
- `km_predichos`: int
- `timestamp`: datetime

### MantenimientoCreateSchema (Entrada)

Body de `POST /motos/{id}/mantenimiento` (registrar un servicio).

- `tipo_servicio`: str (ej: `"Cambio de aceite"`)
- `fecha`: date
- `kilometraje`: float

---

## ⚠️ fallas (Diagnóstico de Fallas)

### InsightReadSchema (Salida)

Para `GET /motos/{id}/historial` (widget).

- `insight_id`: int
- `resumen_generado`: str
- `prioridad`: str (Enum: `BAJA`, `MEDIA`, `ALTA`)
- `timestamp`: datetime

---

## 💬 chatbot (IA Interactiva)

### ChatSesionCreateSchema (Entrada)

Para `POST /chat/sesiones`.

- `moto_id`: int (opcional)
- `titulo`: str (opcional)

### ChatSesionReadSchema (Salida)

Para `GET /chat/sesiones`.

- `sesion_id`: int
- `usuario_id`: int
- `moto_id`: int (opcional)
- `titulo`: str

### ChatMensajeCreateSchema (Entrada)

Para `POST /chat/sesiones/{id}/mensajes`.

- `mensaje`: str

### ChatMensajeReadSchema (Salida)

Para `GET /chat/sesiones/{id}/mensajes` y la respuesta del WebSocket.

- `mensaje_id`: int
- `sesion_id`: int
- `rol`: str (Enum: `USUARIO`, `LLM`)
- `mensaje`: str
- `timestamp`: datetime

---

## 🔔 notificaciones (Alertas)

### NotificacionReadSchema (Salida)

Para `GET /notificaciones`.

- `notificacion_id`: int
- `mensaje`: str
- `canal`: str
- `leida`: bool
- `timestamp`: datetime

### NotificacionUpdateSchema (Entrada)

Para `PATCH /notificaciones/{id}`.

- `leida`: bool
