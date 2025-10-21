# 🔄 Migración de Servicios a API_ENDPOINTS

## ✅ Servicios Migrados

- [x] `auth.service.ts`
- [x] `motos.service.ts`

## 🚧 Servicios Pendientes de Migrar

- [ ] `sensores.service.ts`
- [ ] `fallas.service.ts`
- [ ] `mantenimiento.service.ts`
- [ ] `ml.service.ts`
- [ ] `chatbot.service.ts`
- [ ] `notificaciones.service.ts`

---

## 📝 Plantilla de Migración

### Antes

```typescript
import apiClient from '@/config/api-client';

export const serviceName = {
  async getAll() {
    const { data } = await apiClient.get('/endpoint');
    return data;
  },
  
  async getById(id: string) {
    const { data } = await apiClient.get(`/endpoint/${id}`);
    return data;
  },
};
```

### Después

```typescript
import apiClient from '@/config/api-client';
import { API_ENDPOINTS } from '@/config/api-endpoints';

export const serviceName = {
  async getAll() {
    const { data } = await apiClient.get(API_ENDPOINTS.MODULE.BASE);
    return data;
  },
  
  async getById(id: string) {
    const { data } = await apiClient.get(API_ENDPOINTS.MODULE.BY_ID(id));
    return data;
  },
};
```

---

## 🎯 Ejemplos por Módulo

### 📡 sensores.service.ts

```typescript
// ❌ Antes
await apiClient.get('/sensores');
await apiClient.get('/sensores/lecturas');
await apiClient.post('/sensores/simular');

// ✅ Después
await apiClient.get(API_ENDPOINTS.SENSORES.BASE);
await apiClient.get(API_ENDPOINTS.SENSORES.LECTURAS);
await apiClient.post(API_ENDPOINTS.SENSORES.BASE);
```

### ⚠️ fallas.service.ts

```typescript
// ❌ Antes
await apiClient.get('/fallas');
await apiClient.get(`/fallas/${id}`);
await apiClient.get(`/fallas/moto/${motoId}`);
await apiClient.post(`/fallas/${id}/diagnosticar`);
await apiClient.post(`/fallas/${id}/resolver`);

// ✅ Después
await apiClient.get(API_ENDPOINTS.FALLAS.BASE);
await apiClient.get(API_ENDPOINTS.FALLAS.BY_ID(id));
await apiClient.get(API_ENDPOINTS.FALLAS.BY_MOTO(motoId));
await apiClient.post(API_ENDPOINTS.FALLAS.DIAGNOSTICAR(id));
await apiClient.post(API_ENDPOINTS.FALLAS.RESOLVER(id));
```

### 🔧 mantenimiento.service.ts

```typescript
// ❌ Antes
await apiClient.get('/mantenimiento');
await apiClient.get(`/mantenimiento/${id}`);
await apiClient.get(`/mantenimiento/moto/${motoId}`);
await apiClient.post(`/mantenimiento/${id}/iniciar`);
await apiClient.post(`/mantenimiento/${id}/completar`);

// ✅ Después
await apiClient.get(API_ENDPOINTS.MANTENIMIENTO.BASE);
await apiClient.get(API_ENDPOINTS.MANTENIMIENTO.BY_ID(id));
await apiClient.get(API_ENDPOINTS.MANTENIMIENTO.BY_MOTO(motoId));
await apiClient.post(API_ENDPOINTS.MANTENIMIENTO.INICIAR(id));
await apiClient.post(API_ENDPOINTS.MANTENIMIENTO.COMPLETAR(id));
```

### 🤖 ml.service.ts

```typescript
// ❌ Antes
await apiClient.post('/ml/predict/fault');
await apiClient.post('/ml/predict/anomaly');
await apiClient.get(`/ml/predictions/moto/${motoId}`);
await apiClient.get('/ml/predictions/criticas');
await apiClient.get('/ml/statistics');

// ✅ Después
await apiClient.post(API_ENDPOINTS.ML.PREDICT_FAULT);
await apiClient.post(API_ENDPOINTS.ML.PREDICT_ANOMALY);
await apiClient.get(API_ENDPOINTS.ML.BY_MOTO(motoId));
await apiClient.get(API_ENDPOINTS.ML.CRITICAS);
await apiClient.get(API_ENDPOINTS.ML.STATISTICS);
```

### 💬 chatbot.service.ts

```typescript
// ❌ Antes
await apiClient.post('/chatbot/chat');
await apiClient.post('/chatbot/chat-stream');
await apiClient.get(`/chatbot/${conversationId}`);
await apiClient.get(`/chatbot/usuario/${userId}`);
await apiClient.get(`/chatbot/${conversationId}/history`);

// ✅ Después
await apiClient.post(API_ENDPOINTS.CHATBOT.CHAT);
await apiClient.post(API_ENDPOINTS.CHATBOT.CHAT_STREAM);
await apiClient.get(API_ENDPOINTS.CHATBOT.BY_ID(conversationId));
await apiClient.get(API_ENDPOINTS.CHATBOT.BY_USUARIO(userId));
await apiClient.get(API_ENDPOINTS.CHATBOT.HISTORY(conversationId));
```

### 🔔 notificaciones.service.ts

```typescript
// ❌ Antes
await apiClient.get('/notificaciones');
await apiClient.post('/notificaciones/masiva');
await apiClient.get(`/notificaciones/${id}`);
await apiClient.post('/notificaciones/leer');
await apiClient.get('/notificaciones/stats');

// ✅ Después
await apiClient.get(API_ENDPOINTS.NOTIFICACIONES.BASE);
await apiClient.post(API_ENDPOINTS.NOTIFICACIONES.MASIVA);
await apiClient.get(API_ENDPOINTS.NOTIFICACIONES.BY_ID(id));
await apiClient.post(API_ENDPOINTS.NOTIFICACIONES.LEER);
await apiClient.get(API_ENDPOINTS.NOTIFICACIONES.STATS);
```

---

## 🔍 Comando de Búsqueda y Reemplazo

Para cada servicio, buscar patrones y reemplazar:

### Patrón 1: Endpoints sin parámetros

```
Buscar: '/endpoint'
Reemplazar: API_ENDPOINTS.MODULE.CONSTANT
```

### Patrón 2: Endpoints con template literals

```
Buscar: `/endpoint/${id}`
Reemplazar: API_ENDPOINTS.MODULE.BY_ID(id)
```

### Patrón 3: Concatenación de strings

```
Buscar: '/endpoint/' + id
Reemplazar: API_ENDPOINTS.MODULE.BY_ID(id)
```

---

## ✅ Checklist de Migración

Para cada servicio:

1. [ ] Agregar import: `import { API_ENDPOINTS } from '@/config/api-endpoints';`
2. [ ] Reemplazar endpoints simples (sin params)
3. [ ] Reemplazar endpoints con parámetros
4. [ ] Verificar que no haya URLs hardcodeadas
5. [ ] Probar que todo funcione
6. [ ] Actualizar tests si existen

---

## 🎨 Beneficios Visuales

### Antes (difícil de mantener)

```typescript
// Archivo 1
await apiClient.get('/motos/123');

// Archivo 2
await apiClient.get('/motos/' + id);

// Archivo 3
await apiClient.get(`/motos/${motoId}`);

// 3 formas diferentes de hacer lo mismo ❌
```

### Después (consistente)

```typescript
// Archivo 1
await apiClient.get(API_ENDPOINTS.MOTOS.BY_ID('123'));

// Archivo 2
await apiClient.get(API_ENDPOINTS.MOTOS.BY_ID(id));

// Archivo 3
await apiClient.get(API_ENDPOINTS.MOTOS.BY_ID(motoId));

// Una sola forma estándar ✅
```

---

## 📊 Progreso

```
Migración de Servicios
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
███████░░░░░░░░░░░░░░░░░░░░░░░░░░░ 25%

✅ auth.service.ts       (migrado)
✅ motos.service.ts      (migrado)
🚧 sensores.service.ts   (pendiente)
🚧 fallas.service.ts     (pendiente)
🚧 mantenimiento.service.ts (pendiente)
🚧 ml.service.ts         (pendiente)
🚧 chatbot.service.ts    (pendiente)
🚧 notificaciones.service.ts (pendiente)
```

---

**🚀 ¿Quieres que migre los servicios restantes automáticamente?**
