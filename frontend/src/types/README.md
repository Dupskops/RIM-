# Types Module - Tipos del Sistema RIM

Este módulo maneja todos los tipos TypeScript de la aplicación, siguiendo el principio de **Single Source of Truth**.

## 📁 Estructura

```
types/
├── index.ts          # Re-exports y aliases convenientes
└── api.ts            # 🤖 AUTO-GENERADO desde OpenAPI del backend
```

## 🎯 Filosofía: Backend como Source of Truth

El frontend **NO define** tipos de entidades manualmente. En su lugar:

1. ✅ El **backend** expone un schema OpenAPI
2. ✅ **openapi-typescript** genera `api.ts` automáticamente
3. ✅ `index.ts` crea **aliases convenientes** para uso en componentes

### ❌ Antes (Incorrecto)

```typescript
// types/index.ts - ❌ Definiendo tipos manualmente
export interface User {
  id: string;
  email: string;
  nombre: string;
  // ... riesgo de desincronización con el backend
}
```

**Problemas:**
- 🔴 Duplicación de definiciones
- 🔴 Desincronización entre frontend y backend
- 🔴 Mantenimiento manual (propensa a errores)
- 🔴 No hay garantía de que coincidan con el backend

### ✅ Ahora (Correcto)

```typescript
// types/index.ts - ✅ Re-exportando desde api.ts
import type { components } from './api';

export type User = components['schemas']['UsuarioResponse'];
```

**Beneficios:**
- ✅ **Single Source of Truth**: El backend define los tipos
- ✅ **Sincronización automática**: Regenerar api.ts sincroniza todo
- ✅ **Type Safety garantizado**: Los tipos siempre coinciden con el backend
- ✅ **Cero mantenimiento manual**: Los tipos se actualizan solos

## 🔄 Flujo de Trabajo

### 1. Cuando el backend cambia:

```bash
# En el directorio frontend/
npm run generate:types
```

Esto ejecuta:
```bash
npx openapi-typescript http://localhost:8000/api/openapi.json -o src/types/api.ts
```

### 2. Los tipos se actualizan automáticamente

`api.ts` se regenera con los cambios del backend.

### 3. El frontend usa los nuevos tipos

No necesitas cambiar nada manualmente. Los tipos ya están actualizados.

## 📝 Contenido de los Archivos

### `api.ts` (🤖 AUTO-GENERADO)

**NO EDITAR MANUALMENTE**

Contiene:
- `paths`: Todas las rutas del API
- `components['schemas']`: Todos los schemas del backend
- `operations`: Todas las operaciones disponibles

Generado automáticamente con `openapi-typescript`.

### `index.ts` (📝 Mantenimiento Manual)

**Dos responsabilidades:**

#### 1️⃣ Crear aliases convenientes

```typescript
// Alias del backend para uso en frontend
export type User = components['schemas']['UsuarioResponse'];
export type Moto = components['schemas']['MotoResponse'];
```

**¿Por qué?**
- Nombre más corto y familiar
- Consistencia en el frontend
- Fácil de usar en componentes

#### 2️⃣ Definir tipos SOLO de frontend

```typescript
// Este tipo NO existe en el backend
// Es solo para manejo de UI
export interface ChatSession {
  id: string;
  moto_id: string;
  messages: ChatMessage[];
  created_at: string;
}
```

**¿Cuándo agregar tipos aquí?**
- ✅ Tipos para manejo de estado del frontend
- ✅ Tipos para agregación de datos de UI
- ✅ Tipos auxiliares que NO representan entidades del backend

**¿Cuándo NO agregar tipos aquí?**
- ❌ Entidades que ya existen en el backend
- ❌ Respuestas de API
- ❌ Requests al backend

## 🎨 Uso en Componentes

### Importar tipos

```typescript
// ✅ Correcto
import type { User, Moto, AuthResponse } from '@/types';

// ❌ Incorrecto - No importar de api.ts directamente
import type { components } from '@/types/api';
```

### Usar tipos en componentes

```typescript
import type { User, AuthResponse } from '@/types';

const ProfilePage = () => {
  const [user, setUser] = useState<User | null>(null);
  
  const login = async (credentials: LoginRequest): Promise<AuthResponse> => {
    const response = await authService.login(credentials);
    setUser(response.user); // ✅ Type-safe
    return response;
  };
};
```

### Tipos inferidos de operaciones

```typescript
import type { paths } from '@/types';

// Tipo del response de GET /api/usuarios
type GetUsersResponse = paths['/api/usuarios']['get']['responses']['200']['content']['application/json'];
```

## 📊 Comparación

| Aspecto | Manual (❌) | Auto-generado (✅) |
|---------|------------|-------------------|
| **Sincronización** | Manual | Automática |
| **Mantenimiento** | Alto | Cero |
| **Errores** | Propenso | Imposible |
| **Type Safety** | Parcial | Total |
| **Escalabilidad** | Difícil | Excelente |
| **DX** | Pobre | Excelente |

## 🔧 Configuración en package.json

```json
{
  "scripts": {
    "generate:types": "openapi-typescript http://localhost:8000/api/openapi.json -o src/types/api.ts"
  }
}
```

## 📋 Checklist de Tipos

### ✅ Tipos que SÍ van en `index.ts`:

- Aliases convenientes de tipos del backend
- Tipos de estado UI (ChatSession, DashboardStats)
- Tipos de agregación de datos para UI
- Tipos auxiliares del frontend

### ❌ Tipos que NO van en `index.ts`:

- Entidades del backend (User, Moto, etc.) - Usar aliases
- Schemas de request/response - Ya están en api.ts
- Cualquier cosa que el backend ya define

## 🎯 Regla de Oro

> **Si el backend lo define, usa `api.ts`**
>
> **Si es solo para frontend, defínelo en `index.ts`**

## 🔄 Proceso de Actualización

### Cambio en el Backend

```
1. Backend actualiza schema (ej: agregar campo a User)
   ↓
2. Frontend ejecuta: npm run generate:types
   ↓
3. api.ts se regenera con el nuevo campo
   ↓
4. TypeScript detecta el cambio automáticamente
   ↓
5. Los componentes que usan User ahora tienen el nuevo campo
```

### Sin Pasos Manuales ✨

No necesitas:
- ❌ Actualizar types/index.ts manualmente
- ❌ Buscar dónde está definido el tipo
- ❌ Verificar que coincida con el backend
- ❌ Mantener dos definiciones sincronizadas

## 📚 Referencias

- [openapi-typescript](https://github.com/drwpow/openapi-typescript)
- [OpenAPI Specification](https://swagger.io/specification/)
- Backend OpenAPI: `http://localhost:8000/api/openapi.json`
- Backend Swagger UI: `http://localhost:8000/docs`
