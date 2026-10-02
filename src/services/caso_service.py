from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from src.models.entities import Usuario, Aprendiz, Caso, Actuacion, Compromiso, Auditoria
from src.core.enums import (
    EstadoCasoEnum, TipoActuacionEnum, ResultadoActuacionEnum,
    EstadoCompromisoEnum, TipoCierreEnum, RolCodigoEnum, AccionAuditoriaEnum
)
from src.core.exceptions import (
    TransicionEstadoNoPermitida, EvidenciasMinimasRequeridas, JustificacionRequeridaError
)
from src.core.security import hash_password

TRANSICIONES_PERMITIDAS = {
    EstadoCasoEnum.REGISTRADO.value: [EstadoCasoEnum.ASIGNADO.value, EstadoCasoEnum.ANULADO.value],
    EstadoCasoEnum.ASIGNADO.value: [EstadoCasoEnum.EN_INVESTIGACION.value, EstadoCasoEnum.ANULADO.value],
    EstadoCasoEnum.EN_INVESTIGACION.value: [EstadoCasoEnum.EN_SEGUIMIENTO.value, EstadoCasoEnum.PROPUESTO_CIERRE.value, EstadoCasoEnum.ANULADO.value],
    EstadoCasoEnum.EN_SEGUIMIENTO.value: [EstadoCasoEnum.PROPUESTO_CIERRE.value, EstadoCasoEnum.EN_INVESTIGACION.value],
    EstadoCasoEnum.PROPUESTO_CIERRE.value: [EstadoCasoEnum.CERRADO.value, EstadoCasoEnum.EN_SEGUIMIENTO.value],
    EstadoCasoEnum.CERRADO.value: [EstadoCasoEnum.REABIERTO.value],
    EstadoCasoEnum.REABIERTO.value: [EstadoCasoEnum.EN_INVESTIGACION.value],
    EstadoCasoEnum.ANULADO.value: []
}

class CasoService:
    @staticmethod
    def generar_numero_caso(db: Session) -> str:
        count = db.query(func.count(Caso.id)).scalar() or 0
        return f"DES-{count + 1:06d}"

    @staticmethod
    def crear_caso(db: Session, aprendiz_id: int, motivo: str, descripcion: Optional[str] = None, asignado_a_id: Optional[int] = None, usuario_creador: str = "Instructor") -> Caso:
        aprendiz = db.query(Aprendiz).filter(Aprendiz.id == aprendiz_id).first()
        if not aprendiz:
            raise ValueError("Aprendiz no encontrado")
        
        num_caso = CasoService.generar_numero_caso(db)
        caso = Caso(
            numero_caso=num_caso,
            aprendiz_id=aprendiz_id,
            motivo_desercion=motivo,
            descripcion_inicial=descripcion,
            asignado_a_id=asignado_a_id,
            estado=EstadoCasoEnum.REGISTRADO.value if not asignado_a_id else EstadoCasoEnum.ASIGNADO.value,
            dias_sin_actuacion=0
        )
        db.add(caso)
        db.flush()

        # Auditoria inicial
        aud = Auditoria(
            caso_id=caso.id,
            usuario_nombre=usuario_creador,
            accion=AccionAuditoriaEnum.CREAR.value,
            detalle=f"Registro inicial de caso {caso.numero_caso} para el aprendiz {aprendiz.nombres} {aprendiz.apellidos} (Ficha: {aprendiz.ficha}). Motivo: {motivo}",
            estado_anterior=None,
            estado_nuevo=caso.estado
        )
        db.add(aud)
        db.commit()
        db.refresh(caso)
        return caso

    @staticmethod
    def transicionar_estado(db: Session, caso_id: int, nuevo_estado: str, justificacion: Optional[str] = None, usuario_nombre: str = "Juan David Berroterán", tipo_cierre: Optional[str] = None, asignado_a_id: Optional[int] = None) -> Caso:
        caso = db.query(Caso).filter(Caso.id == caso_id).first()
        if not caso:
            raise ValueError("Caso no encontrado")

        estado_actual = caso.estado
        permitidos = TRANSICIONES_PERMITIDAS.get(estado_actual, [])

        if nuevo_estado not in permitidos:
            raise TransicionEstadoNoPermitida(f"Transición no válida de {estado_actual} a {nuevo_estado}. Permitidas: {permitidos}")

        # Validaciones de negocio
        if nuevo_estado in [EstadoCasoEnum.PROPUESTO_CIERRE.value, EstadoCasoEnum.CERRADO.value]:
            num_actuaciones = db.query(func.count(Actuacion.id)).filter(Actuacion.caso_id == caso_id).scalar() or 0
            if num_actuaciones < 1:
                raise EvidenciasMinimasRequeridas("Se requiere registrar al menos una actuación de contacto antes de proponer o ejecutar el cierre del caso.")

        if nuevo_estado == EstadoCasoEnum.CERRADO.value:
            if not tipo_cierre:
                tipo_cierre = TipoCierreEnum.DESERCION_CONFIRMADA.value
            caso.tipo_cierre = tipo_cierre
            caso.justificacion_cierre = justificacion or "Cierre administrativo aprobado."
            caso.fecha_cierre = datetime.now(timezone.utc)

        if nuevo_estado == EstadoCasoEnum.REABIERTO.value:
            if not justificacion:
                raise JustificacionRequeridaError("La reapertura requiere justificación formal.")
            caso.fecha_cierre = None
            caso.tipo_cierre = None

        if asignado_a_id:
            caso.asignado_a_id = asignado_a_id

        caso.estado = nuevo_estado
        caso.dias_sin_actuacion = 0

        # Auditoria
        aud = Auditoria(
            caso_id=caso.id,
            usuario_nombre=usuario_nombre,
            accion=AccionAuditoriaEnum.CAMBIAR_ESTADO.value,
            detalle=f"Cambio de estado: {estado_actual} -> {nuevo_estado}. " + (f"Justificación: {justificacion}" if justificacion else ""),
            estado_anterior=estado_actual,
            estado_nuevo=nuevo_estado
        )
        db.add(aud)
        db.commit()
        db.refresh(caso)
        return caso

    @staticmethod
    def agregar_actuacion(db: Session, caso_id: int, tipo: str, resultado: str, observaciones: str, proxima_accion: Optional[str] = None, usuario_id: Optional[int] = None, usuario_nombre: str = "Juan David Berroterán") -> Actuacion:
        caso = db.query(Caso).filter(Caso.id == caso_id).first()
        if not caso:
            raise ValueError("Caso no encontrado")

        act = Actuacion(
            caso_id=caso_id,
            usuario_id=usuario_id,
            tipo=tipo,
            resultado=resultado,
            observaciones=observaciones,
            proxima_accion=proxima_accion,
            fecha_actuacion=datetime.now(timezone.utc)
        )
        db.add(act)
        caso.dias_sin_actuacion = 0

        # Si el caso estaba solo en ASIGNADO, pasar automáticamente a EN_INVESTIGACION o EN_SEGUIMIENTO
        if caso.estado in [EstadoCasoEnum.ASIGNADO.value, EstadoCasoEnum.REGISTRADO.value]:
            caso.estado = EstadoCasoEnum.EN_INVESTIGACION.value

        aud = Auditoria(
            caso_id=caso_id,
            usuario_nombre=usuario_nombre,
            accion=AccionAuditoriaEnum.ADJUNTAR.value,
            detalle=f"Nueva actuación registrada: {tipo} ({resultado}). {observaciones[:80]}...",
            estado_anterior=caso.estado,
            estado_nuevo=caso.estado
        )
        db.add(aud)
        db.commit()
        db.refresh(act)
        return act

    @staticmethod
    def agregar_compromiso(db: Session, caso_id: int, descripcion: str, responsable: str, fecha_limite: datetime, usuario_nombre: str = "Juan David Berroterán") -> Compromiso:
        caso = db.query(Caso).filter(Caso.id == caso_id).first()
        if not caso:
            raise ValueError("Caso no encontrado")

        comp = Compromiso(
            caso_id=caso_id,
            descripcion=descripcion,
            responsable=responsable,
            fecha_limite=fecha_limite,
            estado=EstadoCompromisoEnum.PENDIENTE.value
        )
        db.add(comp)
        
        aud = Auditoria(
            caso_id=caso_id,
            usuario_nombre=usuario_nombre,
            accion=AccionAuditoriaEnum.ACTUALIZAR.value,
            detalle=f"Compromiso adquirido: '{descripcion}' con plazo hasta {fecha_limite.strftime('%Y-%m-%d')}",
            estado_anterior=caso.estado,
            estado_nuevo=caso.estado
        )
        db.add(aud)
        db.commit()
        db.refresh(comp)
        return comp

    @staticmethod
    def actualizar_compromiso(db: Session, compromiso_id: int, nuevo_estado: str, usuario_nombre: str = "Juan David Berroterán") -> Compromiso:
        comp = db.query(Compromiso).filter(Compromiso.id == compromiso_id).first()
        if not comp:
            raise ValueError("Compromiso no encontrado")

        comp.estado = nuevo_estado
        if nuevo_estado == EstadoCompromisoEnum.CUMPLIDO.value:
            comp.fecha_cumplimiento = datetime.now(timezone.utc)

        db.commit()
        db.refresh(comp)
        return comp

    @staticmethod
    def seed_data_si_vacio(db: Session):
        if db.query(func.count(Usuario.id)).scalar() > 0:
            return

        # 1. Usuarios Staff SENA
        u1 = Usuario(nombre="Juan David Berroterán", email="juan.berroteran@sena.edu.co", password_hash=hash_password("admin123"), rol=RolCodigoEnum.LIDER_GAES.value, telefono="3102345678")
        u2 = Usuario(nombre="Andrea Rojas Peña", email="andrea.rojas@sena.edu.co", password_hash=hash_password("sena123"), rol=RolCodigoEnum.GAES_APOYO.value, telefono="3159876543")
        u3 = Usuario(nombre="Ing. Fernando Castro", email="fcastro@sena.edu.co", password_hash=hash_password("sena123"), rol=RolCodigoEnum.INSTRUCTOR.value, telefono="3001234987")
        u4 = Usuario(nombre="Psic. Patricia Silva", email="patricia.silva@sena.edu.co", password_hash=hash_password("sena123"), rol=RolCodigoEnum.BIENESTAR.value, telefono="3125556677")
        db.add_all([u1, u2, u3, u4])
        db.flush()

        # 2. Aprendices
        aprendices_datos = [
            ("CC", "1020304050", "Sebastián", "Gómez Montoya", "sebastian.gomez@misena.edu.co", "3112233445", "2670192", "Análisis y Desarrollo de Software (ADSO)", "Diurna"),
            ("TI", "1098765432", "Valeria", "Duque Cárdenas", "valeria.duque@misena.edu.co", "3154433221", "2670192", "Análisis y Desarrollo de Software (ADSO)", "Diurna"),
            ("CC", "1032456789", "Mateo", "López Herrera", "mateo.lopez@misena.edu.co", "3127788990", "2558190", "Gestión Empresarial", "Nocturna"),
            ("CC", "1045678901", "Daniela", "Torres Quintero", "daniela.torres@misena.edu.co", "3186655443", "2712903", "Animación Digital y 3D", "Mixta"),
            ("CC", "1012345678", "Juan Camilo", "Ramírez Ortiz", "juan.ramirez@misena.edu.co", "3109988776", "2629104", "Mantenimiento de Equipos de Cómputo", "Diurna"),
            ("CC", "1078901234", "Camila", "Morales Suárez", "camila.morales@misena.edu.co", "3201122334", "2670192", "Análisis y Desarrollo de Software (ADSO)", "Diurna"),
            ("CC", "1089012345", "Alejandro", "Vargas Benítez", "alejandro.vargas@misena.edu.co", "3178899001", "2558190", "Gestión Empresarial", "Virtual"),
            ("TI", "1065432109", "Sofía", "Castillo Pérez", "sofia.castillo@misena.edu.co", "3145566778", "2712903", "Animación Digital y 3D", "Diurna")
        ]

        aprendices_objs = []
        for tdoc, ndoc, nom, ape, em, tel, fic, prog, jor in aprendices_datos:
            ap = Aprendiz(tipo_documento=tdoc, numero_documento=ndoc, nombres=nom, apellidos=ape, email=em, telefono=tel, ficha=fic, programa=prog, jornada=jor)
            aprendices_objs.append(ap)
            db.add(ap)
        db.flush()

        # 3. Casos representativos en diferentes estados
        # Caso 1: En Seguimiento con compromisos
        c1 = Caso(
            numero_caso="DES-000001",
            aprendiz_id=aprendices_objs[0].id,
            motivo_desercion="Dificultades de conectividad y equipo de cómputo para continuar formación.",
            descripcion_inicial="El aprendiz no asiste desde hace 2 semanas a las sesiones de programación web.",
            estado=EstadoCasoEnum.EN_SEGUIMIENTO.value,
            asignado_a_id=u2.id,
            dias_sin_actuacion=2
        )
        db.add(c1)
        db.flush()

        # Actuaciones caso 1
        db.add(Actuacion(
            caso_id=c1.id, usuario_id=u2.id, tipo=TipoActuacionEnum.LLAMADA.value, resultado=ResultadoActuacionEnum.CONTACTADO.value,
            observaciones="Se contacta al aprendiz. Manifiesta que su laptop se dañó y no cuenta con recursos inmediatos para repararla. Tiene alta motivación para continuar.",
            proxima_accion="Gestionar préstamo de equipo de cómputo en sala de sistemas del centro.",
            fecha_actuacion=datetime.now(timezone.utc) - timedelta(days=5)
        ))
        db.add(Actuacion(
            caso_id=c1.id, usuario_id=u2.id, tipo=TipoActuacionEnum.REUNION.value, resultado=ResultadoActuacionEnum.ACUERDO_ALCANZADO.value,
            observaciones="Reunión con Bienestar al Aprendiz. Se le asigna turno en los laboratorios de cómputo de 2:00 a 6:00 pm de lunes a viernes.",
            proxima_accion="Verificar asistencia a las clases de la semana siguiente.",
            fecha_actuacion=datetime.now(timezone.utc) - timedelta(days=2)
        ))
        # Compromiso caso 1
        db.add(Compromiso(
            caso_id=c1.id, descripcion="Asistir a los laboratorios asignados y entregar evidencias atrasadas de la Guía 3.",
            responsable="Sebastián Gómez", fecha_limite=datetime.now(timezone.utc) + timedelta(days=4),
            estado=EstadoCompromisoEnum.PENDIENTE.value
        ))
        db.add(Auditoria(
            caso_id=c1.id, usuario_nombre=u1.nombre, accion=AccionAuditoriaEnum.CAMBIAR_ESTADO.value,
            detalle="Caso avanzado a EN_SEGUIMIENTO tras acordar apoyo de computadores con Bienestar.",
            estado_anterior=EstadoCasoEnum.EN_INVESTIGACION.value, estado_nuevo=EstadoCasoEnum.EN_SEGUIMIENTO.value
        ))

        # Caso 2: En Investigación (Alerta >7 días sin actuación)
        c2 = Caso(
            numero_caso="DES-000002",
            aprendiz_id=aprendices_objs[1].id,
            motivo_desercion="Inasistencia reiterada sin justificación médica o laboral reportada.",
            descripcion_inicial="Reportado por el instructor Fernando Castro tras 5 fallas consecutivas.",
            estado=EstadoCasoEnum.EN_INVESTIGACION.value,
            asignado_a_id=u1.id,
            dias_sin_actuacion=9
        )
        db.add(c2)
        db.flush()
        db.add(Actuacion(
            caso_id=c2.id, usuario_id=u1.id, tipo=TipoActuacionEnum.LLAMADA.value, resultado=ResultadoActuacionEnum.NO_CONTACTADO.value,
            observaciones="Teléfono suena ocupado. Se envía mensaje por WhatsApp solicitando comunicación urgente.",
            proxima_accion="Enviar citación formal al correo institucional y acudiente.",
            fecha_actuacion=datetime.now(timezone.utc) - timedelta(days=9)
        ))
        db.add(Auditoria(
            caso_id=c2.id, usuario_nombre=u3.nombre, accion=AccionAuditoriaEnum.CREAR.value,
            detalle="Registro de caso por inasistencias acumuladas sin excusa.",
            estado_anterior=None, estado_nuevo=EstadoCasoEnum.EN_INVESTIGACION.value
        ))

        # Caso 3: Cerrado con Retorno Exitoso (Readmisión)
        c3 = Caso(
            numero_caso="DES-000003",
            aprendiz_id=aprendices_objs[2].id,
            motivo_desercion="Cruce con nuevo horario laboral.",
            descripcion_inicial="El aprendiz consiguió empleo de noche que coincidía con su horario de formación.",
            estado=EstadoCasoEnum.CERRADO.value,
            tipo_cierre=TipoCierreEnum.RETORNO_READMISION.value,
            justificacion_cierre="Se gestionó exitosamente el traslado de jornada a modalidad virtual para que continúe su programa.",
            fecha_cierre=datetime.now(timezone.utc) - timedelta(days=3),
            asignado_a_id=u4.id,
            dias_sin_actuacion=0
        )
        db.add(c3)
        db.flush()
        db.add(Actuacion(
            caso_id=c3.id, usuario_id=u4.id, tipo=TipoActuacionEnum.CITACION.value, resultado=ResultadoActuacionEnum.ACUERDO_ALCANZADO.value,
            observaciones="Se tramitó ante coordinación académica el cambio a la ficha virtual de Gestión Empresarial.",
            fecha_actuacion=datetime.now(timezone.utc) - timedelta(days=4)
        ))
        db.add(Auditoria(
            caso_id=c3.id, usuario_nombre=u1.nombre, accion=AccionAuditoriaEnum.CERRAR.value,
            detalle="Cierre por RETORNO_READMISION autorizado. Traslado de jornada completado.",
            estado_anterior=EstadoCasoEnum.PROPUESTO_CIERRE.value, estado_nuevo=EstadoCasoEnum.CERRADO.value
        ))

        # Caso 4: Registrado recién ingresado
        c4 = Caso(
            numero_caso="DES-000004",
            aprendiz_id=aprendices_objs[3].id,
            motivo_desercion="Situación económica familiar y necesidad de trabajo informal inmediato.",
            descripcion_inicial="El vocero de ficha informó que la aprendiz no puede costear pasajes de transporte.",
            estado=EstadoCasoEnum.REGISTRADO.value,
            asignado_a_id=None,
            dias_sin_actuacion=1
        )
        db.add(c4)
        db.flush()
        db.add(Auditoria(
            caso_id=c4.id, usuario_nombre="Coordinación Académica", accion=AccionAuditoriaEnum.CREAR.value,
            detalle="Caso creado pendiente de asignación a gestor GAES o Bienestar.",
            estado_anterior=None, estado_nuevo=EstadoCasoEnum.REGISTRADO.value
        ))

        # Caso 5: Propuesto para Cierre (Deserción Confirmada)
        c5 = Caso(
            numero_caso="DES-000005",
            aprendiz_id=aprendices_objs[4].id,
            motivo_desercion="Cambio definitivo de residencia a otra ciudad por motivos de fuerza mayor.",
            descripcion_inicial="Aprendiz radica carta formal solicitando retiro y certificado de competencias.",
            estado=EstadoCasoEnum.PROPUESTO_CIERRE.value,
            tipo_cierre=TipoCierreEnum.DESERCION_CONFIRMADA.value,
            asignado_a_id=u2.id,
            dias_sin_actuacion=1
        )
        db.add(c5)
        db.flush()
        db.add(Actuacion(
            caso_id=c5.id, usuario_id=u2.id, tipo=TipoActuacionEnum.ACTA.value, resultado=ResultadoActuacionEnum.ACUERDO_ALCANZADO.value,
            observaciones="Se recibe carta formal de retiro voluntario por traslado familiar a Medellín. Se emite paz y salvo de biblioteca y almacén.",
            proxima_accion="Remitir a Comité de Evaluación y Seguimiento para resolución de cancelación de matrícula.",
            fecha_actuacion=datetime.now(timezone.utc) - timedelta(days=1)
        ))
        db.add(Auditoria(
            caso_id=c5.id, usuario_nombre=u2.nombre, accion=AccionAuditoriaEnum.APROBAR_CIERRE.value,
            detalle="Caso propuesto para cierre definitivo con paz y salvo anexo.",
            estado_anterior=EstadoCasoEnum.EN_INVESTIGACION.value, estado_nuevo=EstadoCasoEnum.PROPUESTO_CIERRE.value
        ))

        db.commit()
