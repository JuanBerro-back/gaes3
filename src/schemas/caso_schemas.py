from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class AprendizBase(BaseModel):
    tipo_documento: str = "CC"
    numero_documento: str
    nombres: str
    apellidos: str
    email: str
    telefono: str
    ficha: str
    programa: str
    jornada: str = "Diurna"

class AprendizCreate(AprendizBase):
    pass

class AprendizResponse(AprendizBase):
    id: int
    activo: bool
    fecha_creacion: datetime

    class Config:
        from_attributes = True

class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    email: str
    rol: str
    telefono: Optional[str] = None

    class Config:
        from_attributes = True

class ActuacionCreate(BaseModel):
    tipo: str
    resultado: str
    observaciones: str
    proxima_accion: Optional[str] = None
    usuario_nombre: Optional[str] = "Juan David Berroterán"

class ActuacionResponse(BaseModel):
    id: int
    caso_id: int
    tipo: str
    resultado: str
    observaciones: str
    proxima_accion: Optional[str] = None
    fecha_actuacion: datetime
    usuario: Optional[UsuarioResponse] = None

    class Config:
        from_attributes = True

class CompromisoCreate(BaseModel):
    descripcion: str
    responsable: str = "Aprendiz"
    fecha_limite: datetime

class CompromisoResponse(BaseModel):
    id: int
    caso_id: int
    descripcion: str
    responsable: str
    fecha_limite: datetime
    estado: str
    fecha_cumplimiento: Optional[datetime] = None

    class Config:
        from_attributes = True

class AuditoriaResponse(BaseModel):
    id: int
    usuario_nombre: str
    accion: str
    detalle: str
    estado_anterior: Optional[str] = None
    estado_nuevo: Optional[str] = None
    fecha: datetime

    class Config:
        from_attributes = True

class CasoCreate(BaseModel):
    aprendiz_id: int
    motivo_desercion: str
    descripcion_inicial: Optional[str] = None
    asignado_a_id: Optional[int] = None

class CasoResponse(BaseModel):
    id: int
    numero_caso: str
    aprendiz: AprendizResponse
    motivo_desercion: str
    estado: str
    asignado_a: Optional[UsuarioResponse] = None
    tipo_cierre: Optional[str] = None
    dias_sin_actuacion: int
    fecha_creacion: datetime
    total_actuaciones: int = 0
    total_compromisos: int = 0

    class Config:
        from_attributes = True

class CasoDetailResponse(BaseModel):
    id: int
    numero_caso: str
    aprendiz: AprendizResponse
    motivo_desercion: str
    descripcion_inicial: Optional[str] = None
    estado: str
    asignado_a: Optional[UsuarioResponse] = None
    tipo_cierre: Optional[str] = None
    justificacion_cierre: Optional[str] = None
    fecha_cierre: Optional[datetime] = None
    dias_sin_actuacion: int
    fecha_creacion: datetime
    actuaciones: List[ActuacionResponse] = []
    compromisos: List[CompromisoResponse] = []
    auditorias: List[AuditoriaResponse] = []
    transiciones_permitidas: List[str] = []

    class Config:
        from_attributes = True

class TransicionRequest(BaseModel):
    nuevo_estado: str
    justificacion: Optional[str] = None
    usuario_nombre: str = "Juan David Berroterán"
    tipo_cierre: Optional[str] = None
    asignado_a_id: Optional[int] = None
