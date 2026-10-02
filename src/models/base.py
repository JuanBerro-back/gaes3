from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, func, Boolean
from datetime import datetime
class Base(DeclarativeBase): pass
class TimestampMixin:
    fecha_creacion: Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fecha_modificacion: Mapped[datetime|None]=mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
class SoftDeleteMixin:
    activo: Mapped[bool]=mapped_column(Boolean, default=True, nullable=False)
    anulado: Mapped[bool]=mapped_column(Boolean, default=False, nullable=False)
