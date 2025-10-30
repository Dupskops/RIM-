"""
Repositorio para gestión de suscripciones en la base de datos.
"""
from typing import Optional, Sequence, List, Any
from datetime import datetime, timezone
from sqlalchemy import select, func, desc, asc, or_
from sqlalchemy.ext.asyncio import AsyncSession

from types import SimpleNamespace
import json

from sqlalchemy import text

from .models import Suscripcion, Plan, EstadoSuscripcion


def _row_to_obj(mapping: dict[str, Any]) -> SimpleNamespace:
    """Convierte un mapping (row) a un objeto ligero con atributos."""
    return SimpleNamespace(**{k: mapping.get(k) for k in mapping.keys()})


class SuscripcionRepository:
    """Repositorio para operaciones CRUD de suscripciones."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    # -- Suscripción (tabla suscripciones_usuario) --
    async def get_by_id(self, suscripcion_id: int) -> Optional[Suscripcion]:
        """Retorna la Suscripcion ORM por id o None."""
        return await self.session.get(Suscripcion, suscripcion_id)

    # -- Planes / transacciones relacionadas a pagos (tabla transacciones) --
    async def get_plan_by_id(self, plan_id: int) -> Optional[Plan]:
        stmt = select(Plan).where(Plan.id == plan_id)
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def create_transaccion(self, data: dict) -> Optional[SimpleNamespace]:
        """Inserta una fila en la tabla `transacciones` y retorna el row (SimpleNamespace).

        Nota: asume que existe una tabla `transacciones` con columnas
        (id, usuario_id, plan_id, monto, status, provider_metadata, created_at, updated_at).
        """
        now = datetime.now(timezone.utc)
        provider_metadata = data.get("provider_metadata") or {}
        sql = text(
            """
            INSERT INTO transacciones(usuario_id, plan_id, monto, status, provider_metadata, created_at)
            VALUES(:usuario_id, :plan_id, :monto, :status, :provider_metadata::jsonb, :created_at)
            RETURNING id, usuario_id, plan_id, monto, status, provider_metadata, created_at, updated_at
            """
        )
        params = {
            "usuario_id": data.get("usuario_id"),
            "plan_id": data.get("plan_id"),
            "monto": data.get("monto"),
            "status": data.get("status"),
            "provider_metadata": json.dumps(provider_metadata),
            "created_at": now,
        }
        result = await self.session.execute(sql, params)
        await self.session.commit()
        row = result.mappings().first()
        return _row_to_obj(row) if row else None

    async def get_transaccion_by_id(self, transaccion_id: int) -> Optional[SimpleNamespace]:
        sql = text("SELECT id, usuario_id, plan_id, monto, status, provider_metadata, created_at, updated_at FROM transacciones WHERE id = :id")
        res = await self.session.execute(sql, {"id": transaccion_id})
        row = res.mappings().first()
        return _row_to_obj(row) if row else None

    async def update_transaccion(self, transaccion_id: int, update_data: dict) -> Optional[SimpleNamespace]:
        # build set clause
        set_parts = []
        sql_params = {"id": transaccion_id}
        for idx, (k, v) in enumerate((update_data or {}).items()):
            param_name = f"p{idx}"
            if k == "provider_metadata":
                set_parts.append(f"{k} = :{param_name}::jsonb")
                sql_params[param_name] = json.dumps(v or {})
            else:
                set_parts.append(f"{k} = :{param_name}")
                sql_params[param_name] = v

        set_parts.append("updated_at = :updated_at")
        sql_params["updated_at"] = datetime.now(timezone.utc)

        sql = text(f"UPDATE transacciones SET {', '.join(set_parts)} WHERE id = :id RETURNING id, usuario_id, plan_id, monto, status, provider_metadata, created_at, updated_at")
        res = await self.session.execute(sql, sql_params)
        await self.session.commit()
        row = res.mappings().first()
        return _row_to_obj(row) if row else None

    async def list_transacciones(self, usuario_id: Optional[int] = None, offset: int = 0, limit: int = 20) -> List[SimpleNamespace]:
        where = ""
        params: dict[str, Any] = {"offset": offset, "limit": limit}
        if usuario_id is not None:
            where = "WHERE usuario_id = :usuario_id"
            params["usuario_id"] = usuario_id

        sql = text(f"SELECT id, usuario_id, plan_id, monto, status, provider_metadata, created_at, updated_at FROM transacciones {where} ORDER BY created_at DESC LIMIT :limit OFFSET :offset")
        res = await self.session.execute(sql, params)
        rows = res.mappings().all()
        return [_row_to_obj(r) for r in rows]

    async def count_transacciones(self, usuario_id: Optional[int] = None) -> int:
        if usuario_id is None:
            sql = text("SELECT COUNT(*) as cnt FROM transacciones")
            res = await self.session.execute(sql)
        else:
            sql = text("SELECT COUNT(*) as cnt FROM transacciones WHERE usuario_id = :usuario_id")
            res = await self.session.execute(sql, {"usuario_id": usuario_id})
        row = res.mappings().first()
        return int(row.get("cnt", 0)) if row else 0

    async def update(self, sus_obj: Suscripcion, update_data: dict) -> Suscripcion:
        """Actualiza una suscripción (ORM instance) y retorna la instancia actualizada."""
        # si nos pasaron un id en vez de objeto, cargar
        if not hasattr(sus_obj, "id"):
            sus_obj = await self.get_by_id(sus_obj)

        for k, v in (update_data or {}).items():
            # mantener nombres tal como los modelos usan
            if hasattr(sus_obj, k):
                setattr(sus_obj, k, v)

        await self.session.flush()
        await self.session.commit()
        return sus_obj

    async def assign_plan_to_user(self, usuario_id: int, plan_id: int, fecha_inicio: Optional[datetime] = None, fecha_fin: Optional[datetime] = None) -> Suscripcion:
        """Asigna un plan al usuario: crea o actualiza la suscripción existente."""
        # Buscar suscripción existente activa para el usuario
        stmt = select(Suscripcion).where(Suscripcion.usuario_id == usuario_id).order_by(desc(Suscripcion.id)).limit(1)
        res = await self.session.execute(stmt)
        existing = res.scalars().first()

        if existing:
            # actualizar
            if plan_id is not None:
                existing.plan_id = plan_id
            if fecha_inicio is not None:
                existing.fecha_inicio = fecha_inicio
            if fecha_fin is not None:
                existing.fecha_fin = fecha_fin
            await self.session.flush()
            await self.session.commit()
            return existing

        # crear nueva suscripción
        sus = Suscripcion(
            usuario_id=usuario_id,
            plan_id=plan_id,
            fecha_inicio=fecha_inicio or datetime.now(timezone.utc),
            fecha_fin=fecha_fin,
            estado_suscripcion=EstadoSuscripcion.ACTIVA,
        )
        self.session.add(sus)
        await self.session.flush()
        await self.session.commit()
        return sus

class PlanesRepository:
    """Repositorio para operaciones CRUD de planes."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_planes(self) -> Sequence[Plan]:
        """Retorna una lista de objetos Plan (ORM)."""
        stmt = select(Plan)
        res = await self.session.execute(stmt)
        return res.scalars().all()
