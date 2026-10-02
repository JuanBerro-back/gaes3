from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Text, ForeignKey, DateTime, func, Boolean
from datetime import datetime
from typing import List, Optional
from src.models.base import Base, TimestampMixin, SoftDeleteMixin
from src.core.enums import (
    EstadoCasoEnum, TipoActuacionEnum, ResultadoActuacionEnum,
    EstadoCompromisoEnum, TipoCierreEnum, RolCodigoEnum, AccionAuditoriaEnum
)

class Usuario(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[str] = mapped_column(String(30), default=RolCodigoEnum.GAES_APOYO.value, nullable=False)
    telefono: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    casos_asignados: Mapped[List["Caso"]] = relationship("Caso", back_populates="asignado_a")
    actuaciones: Mapped[List["Actuacion"]] = relationship("Actuacion", back_populates="usuario")

class Aprendiz(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "aprendices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tipo_documento: Mapped[str] = mapped_column(String(10), default="CC", nullable=False)
    numero_documento: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    nombres: Mapped[str] = mapped_column(String(80), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=False)
    telefono: Mapped[str] = mapped_column(String(20), nullable=False)
    ficha: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    programa: Mapped[str] = mapped_column(String(150), nullable=False)
    jornada: Mapped[str] = mapped_column(String(30), default="Diurna", nullable=False)

    casos: Mapped[List["Caso"]] = relationship("Caso", back_populates="aprendiz")

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}"

class Caso(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "casos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    numero_caso: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    aprendiz_id: Mapped[int] = mapped_column(Integer, ForeignKey("aprendices.id"), nullable=False)
    motivo_desercion: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion_inicial: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(40), default=EstadoCasoEnum.REGISTRADO.value, nullable=False, index=True)
    asignado_a_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=True)
    
    tipo_cierre: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    justificacion_cierre: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fecha_cierre: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    dias_sin_actuacion: Mapped[int] = mapped_column(Integer, default=0)

    aprendiz: Mapped["Aprendiz"] = relationship("Aprendiz", back_populates="casos")
    asignado_a: Mapped[Optional["Usuario"]] = relationship("Usuario", back_populates="casos_asignados")
    actuaciones: Mapped[List["Actuacion"]] = relationship("Actuacion", back_populates="caso", cascade="all, delete-orphan", order_by="Actuacion.fecha_actuacion.desc()")
    compromisos: Mapped[List["Compromiso"]] = relationship("Compromiso", back_populates="caso", cascade="all, delete-orphan", order_by="Compromiso.fecha_limite.asc()")
    auditorias: Mapped[List["Auditoria"]] = relationship("Auditoria", back_populates="caso", cascade="all, delete-orphan", order_by="Auditoria.fecha.desc()")

class Actuacion(Base, TimestampMixin):
    __tablename__ = "actuaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    caso_id: Mapped[int] = mapped_column(Integer, ForeignKey("casos.id"), nullable=False)
    usuario_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=True)
    tipo: Mapped[str] = mapped_column(String(40), default=TipoActuacionEnum.LLAMADA.value, nullable=False)
    resultado: Mapped[str] = mapped_column(String(40), default=ResultadoActuacionEnum.CONTACTADO.value, nullable=False)
    observaciones: Mapped[str] = mapped_column(Text, nullable=False)
    proxima_accion: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    fecha_actuacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)

    caso: Mapped["Caso"] = relationship("Caso", back_populates="actuaciones")
    usuario: Mapped[Optional["Usuario"]] = relationship("Usuario", back_populates="actuaciones")

class Compromiso(Base, TimestampMixin):
    __tablename__ = "compromisos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    caso_id: Mapped[int] = mapped_column(Integer, ForeignKey("casos.id"), nullable=False)
    descripcion: Mapped[str] = mapped_column(String(250), nullable=False)
    responsable: Mapped[str] = mapped_column(String(80), default="Aprendiz", nullable=False)
    fecha_limite: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    estado: Mapped[str] = mapped_column(String(30), default=EstadoCompromisoEnum.PENDIENTE.value, nullable=False)
    fecha_cumplimiento: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    caso: Mapped["Caso"] = relationship("Caso", back_populates="compromisos")

class Auditoria(Base):
    __tablename__ = "auditorias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    caso_id: Mapped[int] = mapped_column(Integer, ForeignKey("casos.id"), nullable=False)
    usuario_nombre: Mapped[str] = mapped_column(String(100), default="Sistema GAES", nullable=False)
    accion: Mapped[str] = mapped_column(String(50), nullable=False)
    detalle: Mapped[str] = mapped_column(Text, nullable=False)
    estado_anterior: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    estado_nuevo: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    caso: Mapped["Caso"] = relationship("Caso", back_populates="auditorias")
