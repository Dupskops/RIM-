# 🎯 MATRIZ DE FEATURES: FREEMIUM VS PREMIUM

## Matriz de features

| Feature                                   |  Freemium  |   Premium   |
| ----------------------------------------- | :--------: | :---------: |
| Alertas básicas (aceite, batería)         |     ✅     |     ✅     |
| Historial de servicios                    |     ✅     |     ✅     |
| Diagnóstico general (sensores estándar)   |     ✅     |     ✅     |
| Geolocalización básica                    |     ✅     |     ✅     |
| Chatbot básico (respuestas limitadas)     |     ✅     |     ✅     |
| Modos de manejo (urbano, sport, off-road) |     ❌     |     ✅     |
| Diagnóstico predictivo (IA)               |     ❌     |     ✅     |
| Actualizaciones OTA                       |     ❌     |     ✅     |
| Asistencia remota 24/7                    |     ❌     |     ✅     |
| Integración con wearables                 |     ❌     |     ✅     |
| Reportes avanzados                        |     ❌     |     ✅     |
| Chatbot avanzado (respuestas detalladas)  |     ❌     |     ✅     |

---

## Ejemplo: proteger endpoints

Ejemplo rápido para mostrar la diferencia entre una ruta accesible por todo usuario (freemium) y una ruta que requiere plan premium.

```python
# ❌ FREEMIUM: Respuesta básica
@router.get("/diagnostico-basico")
async def diagnostico_basico(moto_id: str):
   """Todos pueden acceder"""
   return {"temperatura": 75, "status": "normal"}
```

```python
# ✅ PREMIUM: Respuesta avanzada con IA
@router.get("/diagnostico-predictivo")
@require_premium(Feature.DIAGNOSTICO_PREDICTIVO_AVANZADO_IA)
async def diagnostico_predictivo(moto_id: str):
   """Solo usuarios premium"""
   return {
      "prediccion_falla": "Sobrecalentamiento en 30km",
      "probabilidad": 0.85,
      "recomendacion": "Revisar sistema de refrigeración"
   }
```

---

## 🎮 Sistema de Simulación de Pagos (MVP)

Para el MVP **NO se integran pasarelas reales**, pero se simula el flujo completo de manera realista.

### Arquitectura de Simulación

```
┌──────────────────┐
│  Frontend (UI)   │
│  "Pagar Premium" │
└────────┬─────────┘
         │ POST /api/suscripciones/simulate-payment
         ↓
┌──────────────────┐
│  Backend API     │
│  Simula webhook  │ → Genera "transacción" simulada
└────────┬─────────┘
         │ Publica evento
         ↓
┌──────────────────┐
│   Event Bus      │ → UpgradeToPremiumEvent
└────────┬─────────┘
         │
         ├→ Actualiza DB (suscripciones)
         ├→ Notificación al usuario
         └→ Analytics (conversión)
```

### Endpoints de Simulación

```python
# suscripciones/routes.py

@router.post("/simulate-payment")
async def simulate_payment(
    payload: SimulatePaymentRequest,
    usuario_id: str = Depends(get_current_user_id)
):
    """
    Simula un pago exitoso sin pasarela real.
    Válido solo para MVP/Demo.
    """
    transaccion = {
        "transaction_id": f"SIM_{uuid4()}",
        "amount": payload.amount,
        "plan": payload.plan,
        "timestamp": datetime.utcnow(),
        "status": "success",
        "payment_method": "SIMULATED"
    }
    
    # Procesar igual que webhook real
    await subscription_service.upgrade_to_premium(
        usuario_id=usuario_id,
        transaction=transaccion
    )
    
    return {
        "success": True,
        "message": "Upgrade a Premium completado (simulado)",
        "transaction": transaccion
    }

@router.post("/admin/force-plan-change")
@require_admin  # Solo para demos/testing
async def force_plan_change(
    usuario_id: str,
    nuevo_plan: str,
    admin_token: str = Header(...)
):
    """
    Endpoint de administración para cambiar plan manualmente.
    Útil para demos en vivo.
    """
    await subscription_service.change_plan(
        usuario_id=usuario_id,
        nuevo_plan=nuevo_plan,
        reason="admin_override"
    )
    
    return {"success": True, "new_plan": nuevo_plan}
```

---

## Flujo de upgrade Freemium → Premium (MVP)

1. Usuario con moto nueva → Freemium automático
2. Usuario ve funciones premium bloqueadas
3. Usuario hace clic en "Upgrade a Premium"
4. **Simulador de pago** muestra interfaz realista con opciones:
   - ✅ Simular pago exitoso (inmediato)
   - ❌ Simular pago fallido (para testing)
   - ⏱️ Simular pago pendiente (procesamiento)
5. Backend recibe webhook simulado
6. Usuario obtiene acceso inmediato a features premium
7. **Notificación push**: "¡Bienvenido a Premium! 🎉"

---

## 🎨 Panel de Simulación (Frontend)

### Interfaz de Upgrade

```jsx
// SimulatedPaymentModal.jsx
function PaymentSimulator({ onSuccess }) {
  const [loading, setLoading] = useState(false);
  
  const handleSimulatedPayment = async (scenario) => {
    setLoading(true);
    
    const response = await fetch('/api/suscripciones/simulate-payment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        plan: 'premium',
        amount: 9.99,
        scenario: scenario  // 'success', 'failed', 'pending'
      })
    });
    
    if (response.ok) {
      toast.success('¡Ahora eres Premium! 🎉');
      onSuccess();
    }
    
    setLoading(false);
  };
  
  return (
    <div className="payment-simulator">
      <h3>Simulador de Pago (MVP Demo)</h3>
      <p>Selecciona un escenario de prueba:</p>
      
      <button onClick={() => handleSimulatedPayment('success')}>
        ✅ Simular Pago Exitoso
      </button>
      
      <button onClick={() => handleSimulatedPayment('failed')}>
        ❌ Simular Pago Fallido
      </button>
      
      <button onClick={() => handleSimulatedPayment('pending')}>
        ⏱️ Simular Pago Pendiente
      </button>
      
      <small>* Esto es un simulador para demostración</small>
    </div>
  );
}
```

---

## 📊 Estados de Suscripción

### Ciclo de Vida de una Suscripción

```plaintext
┌─────────────┐
│  CREADA     │  → Usuario registrado con Freemium
└──────┬──────┘
       │
       ↓ (upgrade simulado)
┌─────────────┐
│   ACTIVA    │  → Premium funcionando
│  (Premium)  │
└──────┬──────┘
       │
       ├→ (cancelación) → CANCELADA
       ├→ (falta pago)  → SUSPENDIDA
       └→ (downgrade)   → ACTIVA (Freemium)
```

### Estados en Base de Datos

```python
# suscripciones/models.py

class EstadoSuscripcion(str, Enum):
    ACTIVA = "activa"          # Usuario puede usar el plan
    CANCELADA = "cancelada"    # Usuario canceló voluntariamente
    SUSPENDIDA = "suspendida"  # Falta de pago (en caso real)
    TRIAL = "trial"            # Prueba gratuita de 7 días
    EXPIRADA = "expirada"      # Trial terminó sin conversión

class Suscripcion(Base):
    __tablename__ = "suscripciones"
    
    id = Column(UUID, primary_key=True)
    usuario_id = Column(UUID, ForeignKey("usuarios.id"))
    plan_id = Column(UUID, ForeignKey("planes.id"))
    estado = Column(Enum(EstadoSuscripcion), default=EstadoSuscripcion.ACTIVA)
    fecha_inicio = Column(DateTime, default=datetime.utcnow)
    fecha_fin = Column(DateTime, nullable=True)  # Para trials
    fecha_cancelacion = Column(DateTime, nullable=True)
    es_trial = Column(Boolean, default=False)
    metadata = Column(JSON, default={})  # Info adicional
```

---

## 🔌 Endpoints Completos

### Gestión de Suscripciones

```python
# suscripciones/routes.py

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

router = APIRouter(prefix="/api/suscripciones", tags=["Suscripciones"])

# ============================================
# ENDPOINTS PÚBLICOS (Usuario autenticado)
# ============================================

@router.get("/mi-plan")
async def get_mi_plan(
    usuario_id: str = Depends(get_current_user_id),
    service: SubscriptionService = Depends()
):
    """Obtiene el plan actual del usuario."""
    suscripcion = await service.get_suscripcion_activa(usuario_id)
    return {
        "plan": suscripcion.plan.nombre,
        "estado": suscripcion.estado,
        "es_trial": suscripcion.es_trial,
        "dias_restantes": calcular_dias_restantes(suscripcion),
        "features_disponibles": suscripcion.plan.features
    }

@router.post("/simulate-payment")
async def simulate_payment(
    payload: SimulatePaymentRequest,
    usuario_id: str = Depends(get_current_user_id),
    service: SubscriptionService = Depends()
):
    """
    Simula un pago exitoso para upgrade a Premium.
    Solo para MVP - no procesa pago real.
    """
    if payload.scenario == "failed":
        raise HTTPException(status_code=400, detail="Pago simulado fallido")
    
    if payload.scenario == "pending":
        # Simular procesamiento asíncrono
        await service.create_pending_payment(usuario_id, payload.plan)
        return {"status": "pending", "message": "Pago en procesamiento"}
    
    # Escenario exitoso
    transaccion = {
        "transaction_id": f"SIM_{uuid4().hex[:8]}",
        "amount": payload.amount,
        "plan": payload.plan,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "success",
        "payment_method": "SIMULATED"
    }
    
    suscripcion = await service.upgrade_to_premium(
        usuario_id=usuario_id,
        transaction=transaccion
    )
    
    return {
        "success": True,
        "message": "¡Bienvenido a Premium!",
        "suscripcion": suscripcion,
        "transaction": transaccion
    }

@router.post("/activar-trial")
async def activar_trial(
    usuario_id: str = Depends(get_current_user_id),
    service: SubscriptionService = Depends()
):
    """Activa prueba gratuita de 7 días de Premium."""
    suscripcion = await service.activate_trial(usuario_id, dias=7)
    
    return {
        "success": True,
        "message": "Trial de 7 días activado",
        "fecha_expiracion": suscripcion.fecha_fin,
        "features_desbloqueadas": ["diagnostico_predictivo", "modos_manejo", "reportes_avanzados"]
    }

@router.post("/cancelar")
async def cancelar_suscripcion(
    motivo: Optional[str] = None,
    usuario_id: str = Depends(get_current_user_id),
    service: SubscriptionService = Depends()
):
    """Cancela la suscripción Premium (downgrade a Freemium)."""
    suscripcion = await service.cancel_subscription(
        usuario_id=usuario_id,
        motivo=motivo or "usuario_solicito_cancelacion"
    )
    
    return {
        "success": True,
        "message": "Suscripción cancelada. Volverás a Freemium.",
        "fecha_cancelacion": suscripcion.fecha_cancelacion,
        "nuevo_plan": "freemium"
    }

@router.post("/reactivar")
async def reactivar_premium(
    usuario_id: str = Depends(get_current_user_id),
    service: SubscriptionService = Depends()
):
    """Reactiva una suscripción Premium cancelada."""
    # Simula nuevo "pago"
    transaccion = {
        "transaction_id": f"REACTIVE_{uuid4().hex[:8]}",
        "type": "reactivation",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    suscripcion = await service.reactivate_premium(
        usuario_id=usuario_id,
        transaction=transaccion
    )
    
    return {
        "success": True,
        "message": "¡Bienvenido de vuelta a Premium!",
        "suscripcion": suscripcion
    }

# ============================================
# ENDPOINTS ADMINISTRATIVOS (Solo para demo)
# ============================================

@router.post("/admin/force-upgrade")
async def admin_force_upgrade(
    usuario_id: str,
    plan: str,
    admin_key: str = Header(...),
    service: SubscriptionService = Depends()
):
    """
    Endpoint de administración para cambiar plan forzadamente.
    Útil para demos en vivo o testing.
    """
    if admin_key != settings.ADMIN_SECRET_KEY:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    await service.force_plan_change(
        usuario_id=usuario_id,
        nuevo_plan=plan,
        reason="admin_demo"
    )
    
    return {
        "success": True,
        "message": f"Usuario {usuario_id} ahora es {plan}"
    }

@router.get("/admin/estadisticas")
async def admin_estadisticas(
    admin_key: str = Header(...),
    service: SubscriptionService = Depends()
):
    """Estadísticas de conversión para el demo."""
    if admin_key != settings.ADMIN_SECRET_KEY:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    stats = await service.get_conversion_stats()
    
    return {
        "total_usuarios": stats["total"],
        "freemium": stats["freemium"],
        "premium": stats["premium"],
        "trial_activo": stats["trial"],
        "tasa_conversion": f"{stats['conversion_rate']:.2%}",
        "cancelaciones": stats["cancelled"]
    }
```

---

## 🧪 Casos de Prueba para MVP

### Escenario 1: Usuario Nuevo

```gherkin
Dado que un usuario se registra en el sistema
Cuando completa el registro
Entonces se le asigna automáticamente el plan Freemium
Y puede acceder a features básicas
Y ve opciones para upgrade a Premium
```

**Comandos de prueba:**

```bash
# 1. Registrar usuario
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "piloto@test.com",
    "password": "SecurePass123",
    "nombre": "Juan Piloto"
  }'

# 2. Verificar plan asignado
curl http://localhost:8000/api/suscripciones/mi-plan \
  -H "Authorization: Bearer {token}"

# Respuesta esperada:
{
  "plan": "freemium",
  "estado": "activa",
  "es_trial": false,
  "features_disponibles": [
    "alertas_basicas",
    "historial_servicios",
    "diagnostico_general"
  ]
}
```

---

### Escenario 2: Activar Trial Premium

```gherkin
Dado que un usuario Freemium quiere probar Premium
Cuando activa el trial de 7 días
Entonces obtiene acceso a todas las features Premium
Y el sistema marca la fecha de expiración
Y recibe notificaciones antes de que expire
```

**Comandos de prueba:**

```bash
# Activar trial
curl -X POST http://localhost:8000/api/suscripciones/activar-trial \
  -H "Authorization: Bearer {token}"

# Respuesta:
{
  "success": true,
  "message": "Trial de 7 días activado",
  "fecha_expiracion": "2025-10-13T10:00:00Z",
  "features_desbloqueadas": [
    "diagnostico_predictivo",
    "modos_manejo",
    "reportes_avanzados"
  ]
}

# Intentar acceder a feature Premium
curl http://localhost:8000/api/ml/diagnostico-predictivo?moto_id=123 \
  -H "Authorization: Bearer {token}"

# ✅ Ahora funciona (antes daba 403 Forbidden)
```

---

### Escenario 3: Upgrade a Premium (Simulado)

```gherkin
Dado que un usuario quiere convertir a Premium de pago
Cuando simula un pago exitoso
Entonces su suscripción se actualiza a Premium
Y obtiene acceso permanente a features avanzadas
Y recibe confirmación por email/notificación
```

**Comandos de prueba:**

```bash
# Simular pago exitoso
curl -X POST http://localhost:8000/api/suscripciones/simulate-payment \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "plan": "premium",
    "amount": 9.99,
    "scenario": "success"
  }'

# Respuesta:
{
  "success": true,
  "message": "¡Bienvenido a Premium!",
  "transaction": {
    "transaction_id": "SIM_a3f8b2c1",
    "amount": 9.99,
    "status": "success",
    "payment_method": "SIMULATED"
  },
  "suscripcion": {
    "plan": "premium",
    "estado": "activa",
    "es_trial": false
  }
}
```

---

### Escenario 4: Cancelación de Premium

```gherkin
Dado que un usuario Premium quiere cancelar
Cuando solicita la cancelación
Entonces vuelve al plan Freemium
Y pierde acceso a features Premium inmediatamente
Y se registra la fecha y motivo de cancelación
```

**Comandos de prueba:**

```bash
# Cancelar suscripción
curl -X POST http://localhost:8000/api/suscripciones/cancelar \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "motivo": "Costo muy alto"
  }'

# Respuesta:
{
  "success": true,
  "message": "Suscripción cancelada. Volverás a Freemium.",
  "fecha_cancelacion": "2025-10-06T15:30:00Z",
  "nuevo_plan": "freemium"
}

# Intentar acceder a feature Premium
curl http://localhost:8000/api/ml/diagnostico-predictivo?moto_id=123 \
  -H "Authorization: Bearer {token}"

# ❌ Respuesta: 403 Forbidden
{
  "detail": "Esta función requiere plan Premium",
  "upgrade_url": "/planes/premium"
}
```

---

### Escenario 5: Admin Panel (Para Demos)

```gherkin
Dado que necesito demostrar el sistema en vivo
Cuando uso el panel de administración
Entonces puedo cambiar planes manualmente sin simulación de pago
Y ver estadísticas de conversión en tiempo real
```

**Comandos de prueba:**

```bash
# Forzar upgrade (útil para demos rápidas)
curl -X POST http://localhost:8000/api/suscripciones/admin/force-upgrade \
  -H "admin-key: {ADMIN_SECRET}" \
  -H "Content-Type: application/json" \
  -d '{
    "usuario_id": "uuid-del-usuario",
    "plan": "premium"
  }'

# Ver estadísticas
curl http://localhost:8000/api/suscripciones/admin/estadisticas \
  -H "admin-key: {ADMIN_SECRET}"

# Respuesta:
{
  "total_usuarios": 150,
  "freemium": 120,
  "premium": 25,
  "trial_activo": 5,
  "tasa_conversion": "16.67%",
  "cancelaciones": 3
}
```

---

## Ejemplo: chatbot con límites

Freemium (respuesta corta y limitada):

```text
Usuario: "¿Cómo está mi moto?"
Bot: "Tu moto está normal. Temperatura: 75°C"
```

Premium (respuesta enriquecida con detalles y análisis predictivo):

```text
Usuario: "¿Cómo está mi moto?"
Bot: """
Tu moto KTM 390 Adventure está en buen estado general:

🌡️ Temperatura motor: 75°C (óptima)
🔋 Batería: 12.8V (excelente)
🛞 Presión llantas: 32 PSI (correcto)
⚙️ Vibraciones: 2.1g (normal)

📊 Análisis predictivo:
- Sin fallas detectadas
- Próximo mantenimiento: 500km
- Eficiencia combustible: 95%

💡 Recomendación: Todo perfecto para tu viaje.
"""
```

---

## Eventos de suscripción

Archivo: `suscripciones/events.py` (ejemplos de eventos usados por el event bus)

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SuscripcionCreadaEvent:
   usuario_id: str
   plan: str
   timestamp: datetime

@dataclass
class UpgradeToPremiumEvent:
   usuario_id: str
   plan_anterior: str
   timestamp: datetime

@dataclass
class SuscripcionCanceladaEvent:
   usuario_id: str
   motivo: str
   timestamp: datetime
```

Integración con otros módulos (ejemplo):

```python
event_bus.subscribe(
   UpgradeToPremiumEvent,
   lambda e: analytics_service.track_conversion(e)
)
```

---

## Migración: script inicial

Script SQL para crear los planes y asignar Freemium a usuarios existentes.

```sql
-- Crear planes iniciales
INSERT INTO planes (nombre, descripcion, precio_mensual, precio_anual, features) VALUES
  ('freemium', 'Plan gratuito', 0, 0, '["alertas_basicas", "diagnostico_general"]'),
  ('premium', 'Plan completo', 9.99, 99.99, '["todas_las_features"]');

-- Asignar freemium a usuarios existentes
INSERT INTO suscripciones (usuario_id, plan_id, estado, fecha_inicio)
SELECT id, 1, 'activa', NOW() FROM usuarios;
```

---

## Flujo completo de usuario

1. Compra moto (ej. KTM nueva)
2. Activa cuenta → Freemium automático ✅
3. Usa features básicas (diagnóstico general, alertas)
4. Intenta acceder a "Diagnóstico Predictivo Avanzado IA" → 🔒 Bloqueado
5. Ve mensaje: "Desbloquea con Premium - 7 días gratis"
6. Activa trial → 7 días Premium ✅
7. Usa features avanzadas
8. Día 5: Notificación "Quedan 2 días de trial"
9. Convierte a Premium de pago → $9.99/mes ✅

---

## ✅ Checklist de Implementación

### Backend

- [ ] **Modelos de BD**:
  - [ ] Tabla `planes` con features en JSON
  - [ ] Tabla `suscripciones` con estados y fechas
  - [ ] Tabla `transacciones_simuladas` para auditoría

- [ ] **Endpoints funcionales**:
  - [ ] `GET /api/suscripciones/mi-plan`
  - [ ] `POST /api/suscripciones/simulate-payment`
  - [ ] `POST /api/suscripciones/activar-trial`
  - [ ] `POST /api/suscripciones/cancelar`
  - [ ] `POST /api/suscripciones/reactivar`
  - [ ] `POST /api/suscripciones/admin/force-upgrade`

- [ ] **Middleware de protección**:
  - [ ] Decorador `@require_premium` funcional
  - [ ] Manejo de excepciones con mensajes claros
  - [ ] Cache de permisos en Redis

- [ ] **Event Bus**:
  - [ ] Eventos de suscripción (creada, upgrade, cancelada)
  - [ ] Listeners en módulos relevantes
  - [ ] Notificaciones automáticas

### Frontend

- [ ] **Componentes UI**:
  - [ ] Modal de upgrade con simulador de pago
  - [ ] Badge de plan actual en navbar
  - [ ] Paywall para features Premium
  - [ ] Panel de gestión de suscripción

- [ ] **Flujos implementados**:
  - [ ] Registro → Freemium automático
  - [ ] Activación de trial desde UI
  - [ ] Upgrade simulado con feedback visual
  - [ ] Cancelación con confirmación

### Testing

- [ ] **Tests unitarios**:
  - [ ] `test_subscription_service.py`
  - [ ] `test_require_premium_decorator.py`
  - [ ] `test_payment_simulation.py`

- [ ] **Tests de integración**:
  - [ ] Flujo completo Freemium → Trial → Premium
  - [ ] Cancelación y downgrade
  - [ ] Validación de permisos por endpoint

- [ ] **Casos de prueba manuales**:
  - [ ] Demo en vivo con admin panel
  - [ ] Simulación de diferentes escenarios de pago

---

## 📦 Schemas y DTOs

```python
# suscripciones/schemas.py

from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime

class PlanSchema(BaseModel):
    id: str
    nombre: str  # "freemium" | "premium"
    descripcion: str
    precio_mensual: float
    precio_anual: float
    features: List[str]
    
    class Config:
        from_attributes = True

class SuscripcionSchema(BaseModel):
    id: str
    usuario_id: str
    plan: PlanSchema
    estado: str  # "activa" | "cancelada" | "trial" | "expirada"
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    fecha_cancelacion: Optional[datetime] = None
    es_trial: bool = False
    dias_restantes: Optional[int] = None
    
    class Config:
        from_attributes = True

class SimulatePaymentRequest(BaseModel):
    plan: str  # "premium"
    amount: float
    scenario: str = "success"  # "success" | "failed" | "pending"
    
    @validator("scenario")
    def validate_scenario(cls, v):
        allowed = ["success", "failed", "pending"]
        if v not in allowed:
            raise ValueError(f"Scenario debe ser uno de: {allowed}")
        return v

class CancelSubscriptionRequest(BaseModel):
    motivo: Optional[str] = None

class ForceUpgradeRequest(BaseModel):
    usuario_id: str
    plan: str
    reason: Optional[str] = "admin_override"
```

---

## 🔐 Middleware de Protección

```python
# shared/middleware.py

from functools import wraps
from fastapi import HTTPException, Depends
from typing import Callable
from enum import Enum

class Feature(str, Enum):
    """Features que pueden estar bloqueadas por plan."""
    ALERTAS_BASICAS = "alertas_basicas"
    DIAGNOSTICO_GENERAL = "diagnostico_general"
    HISTORIAL_SERVICIOS = "historial_servicios"
    
    # Premium only
    MODOS_MANEJO = "modos_manejo"
    DIAGNOSTICO_PREDICTIVO = "diagnostico_predictivo"
    REPORTES_AVANZADOS = "reportes_avanzados"
    ACTUALIZACIONES_OTA = "actualizaciones_ota"
    ASISTENCIA_REMOTA = "asistencia_remota"
    INTEGRACION_WEARABLES = "integracion_wearables"

def require_premium(feature: Feature):
    """
    Decorador para proteger endpoints que requieren Premium.
    
    Uso:
        @router.get("/diagnostico-predictivo")
        @require_premium(Feature.DIAGNOSTICO_PREDICTIVO)
        async def diagnostico_predictivo(...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Obtener usuario actual
            usuario_id = kwargs.get("usuario_id") or kwargs.get("current_user_id")
            
            if not usuario_id:
                raise HTTPException(
                    status_code=401,
                    detail="Autenticación requerida"
                )
            
            # Verificar suscripción (con caché Redis)
            subscription_service = kwargs.get("subscription_service")
            if not subscription_service:
                from src.suscripciones.services import SubscriptionService
                subscription_service = SubscriptionService()
            
            tiene_acceso = await subscription_service.has_feature_access(
                usuario_id=usuario_id,
                feature=feature
            )
            
            if not tiene_acceso:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "premium_required",
                        "message": f"La función '{feature.value}' requiere plan Premium",
                        "upgrade_url": "/planes/premium",
                        "trial_available": await subscription_service.can_activate_trial(usuario_id)
                    }
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

# Ejemplo de uso en un endpoint
from fastapi import APIRouter

router = APIRouter()

@router.get("/diagnostico-basico")
async def diagnostico_basico(moto_id: str):
    """✅ Accesible para todos (Freemium)"""
    return {
        "temperatura": 75,
        "bateria": 12.5,
        "status": "normal"
    }

@router.get("/diagnostico-predictivo")
@require_premium(Feature.DIAGNOSTICO_PREDICTIVO)
async def diagnostico_predictivo(
    moto_id: str,
    usuario_id: str = Depends(get_current_user_id)
):
    """🔒 Solo Premium"""
    return {
        "prediccion_falla": "Sobrecalentamiento en 30km",
        "probabilidad": 0.85,
        "recomendacion": "Revisar sistema de refrigeración",
        "analisis_ml": {...}  # Datos avanzados de IA
    }
```

---

## 🎯 Consideraciones para el MVP

### ✅ Lo que SÍ incluimos

1. **Simulación realista**: El flujo de pago se ve y funciona como real
2. **Estados completos**: Activa, trial, cancelada, etc.
3. **Event-driven**: Eventos de suscripción integrados con notificaciones
4. **Admin panel**: Para demos en vivo sin fricciones
5. **Validación de permisos**: Middleware robusto que funciona como en producción
6. **Casos de prueba**: Documentados y ejecutables

### ❌ Lo que NO incluimos (pero queda preparado)

1. **Pasarela real**: No Stripe/PayPal/MercadoPago
2. **Webhooks reales**: Solo simulados
3. **Renovación automática**: No hay cargos recurrentes
4. **Facturación**: No se generan facturas
5. **Reembolsos**: No aplicable sin pagos reales

### 🔄 Migración futura a producción

Cuando el MVP esté validado y se requiera producción real:

```python
# Reemplazar:
await simulate_payment(...)

# Por:
await stripe.create_payment_intent(...)
```

El resto del sistema **NO requiere cambios** porque está diseñado de forma agnóstica al método de pago.

---

## 📚 Referencias

- [Documentación FastAPI Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)
- [Patterns de Event-Driven Architecture](https://martinfowler.com/articles/201701-event-driven.html)
- [Freemium Best Practices](https://www.productplan.com/glossary/freemium/)
