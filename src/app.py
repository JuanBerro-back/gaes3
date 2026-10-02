from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from typing import List, Optional
from pathlib import Path

from src.database import get_db, init_db
from src.models.entities import Usuario, Aprendiz, Caso, Actuacion, Compromiso, Auditoria
from src.schemas.caso_schemas import (
    AprendizCreate, AprendizResponse, UsuarioResponse,
    ActuacionCreate, ActuacionResponse, CompromisoCreate, CompromisoResponse,
    CasoCreate, CasoResponse, CasoDetailResponse, TransicionRequest
)
from src.services.caso_service import CasoService, TRANSICIONES_PERMITIDAS
from src.core.enums import EstadoCasoEnum, RolCodigoEnum, TipoCierreEnum
from src.core.exceptions import DominioError

app = FastAPI(
    title="GAES3 - Sistema de Gestión de Deserciones SENA",
    version="1.0.0",
    description="""## 🟢 [👉 HAZ CLIC AQUÍ PARA ABRIR LA INTERFAZ WEB DEL SENA (http://127.0.0.1:8000)](http://127.0.0.1:8000/)

*(Esta página actual es solo la documentación técnica OpenAPI de los endpoints. La aplicación gráfica interactiva se encuentra en la raíz: http://127.0.0.1:8000)*"""
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_path = Path(__file__).resolve().parent / "ui" / "static"
static_path.mkdir(parents=True, exist_ok=True)
(static_path / "css").mkdir(parents=True, exist_ok=True)
(static_path / "js").mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

@app.on_event("startup")
def on_startup():
    init_db()
    from src.database import SessionLocal
    db = SessionLocal()
    try:
        CasoService.seed_data_si_vacio(db)
    finally:
        db.close()

@app.get("/")
def read_root():
    index_file = static_path / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "GAES 3 Backend Activo. Frontend en construcción."}

@app.get("/api/health")
def health():
    return {"status": "ok", "app": "GAES 3 SENA", "version": "1.0.0"}

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    total_casos = db.query(func.count(Caso.id)).scalar() or 0
    casos_cerrados = db.query(func.count(Caso.id)).filter(Caso.estado == EstadoCasoEnum.CERRADO.value).scalar() or 0
    casos_anulados = db.query(func.count(Caso.id)).filter(Caso.estado == EstadoCasoEnum.ANULADO.value).scalar() or 0
    casos_activos = total_casos - casos_cerrados - casos_anulados

    alertas_inactividad = db.query(func.count(Caso.id)).filter(
        Caso.dias_sin_actuacion >= 7,
        Caso.estado.notin_([EstadoCasoEnum.CERRADO.value, EstadoCasoEnum.ANULADO.value])
    ).scalar() or 0

    retornos_exitosos = db.query(func.count(Caso.id)).filter(
        Caso.estado == EstadoCasoEnum.CERRADO.value,
        Caso.tipo_cierre == TipoCierreEnum.RETORNO_READMISION.value
    ).scalar() or 0

    deserciones_confirmadas = db.query(func.count(Caso.id)).filter(
        Caso.estado == EstadoCasoEnum.CERRADO.value,
        Caso.tipo_cierre == TipoCierreEnum.DESERCION_CONFIRMADA.value
    ).scalar() or 0

    # Distribución por estados
    estados_dist = {}
    for st, count in db.query(Caso.estado, func.count(Caso.id)).group_by(Caso.estado).all():
        estados_dist[st] = count

    # Distribución por programa
    programas_dist = {}
    q_prog = db.query(Aprendiz.programa, func.count(Caso.id)).join(Caso, Caso.aprendiz_id == Aprendiz.id).group_by(Aprendiz.programa).all()
    for prog, count in q_prog:
        programas_dist[prog] = count

    # Casos recientes
    recientes_objs = db.query(Caso).order_by(desc(Caso.fecha_creacion)).limit(5).all()
    recientes = []
    for c in recientes_objs:
        recientes.append({
            "id": c.id,
            "numero_caso": c.numero_caso,
            "aprendiz": f"{c.aprendiz.nombres} {c.aprendiz.apellidos}",
            "ficha": c.aprendiz.ficha,
            "programa": c.aprendiz.programa,
            "estado": c.estado,
            "dias_sin_actuacion": c.dias_sin_actuacion,
            "fecha": c.fecha_creacion.strftime("%Y-%m-%d %H:%M")
        })

    return {
        "total_casos": total_casos,
        "casos_activos": casos_activos,
        "casos_cerrados": casos_cerrados,
        "alertas_inactividad": alertas_inactividad,
        "retornos_exitosos": retornos_exitosos,
        "deserciones_confirmadas": deserciones_confirmadas,
        "estados_dist": estados_dist,
        "programas_dist": programas_dist,
        "recientes": recientes
    }

@app.get("/api/casos")
def list_casos(
    estado: Optional[str] = None,
    search: Optional[str] = None,
    ficha: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Caso).join(Aprendiz, Caso.aprendiz_id == Aprendiz.id)

    if estado and estado != "TODOS":
        if estado == "ACTIVOS":
            query = query.filter(Caso.estado.notin_([EstadoCasoEnum.CERRADO.value, EstadoCasoEnum.ANULADO.value]))
        elif estado == "ALERTAS":
            query = query.filter(
                Caso.dias_sin_actuacion >= 7,
                Caso.estado.notin_([EstadoCasoEnum.CERRADO.value, EstadoCasoEnum.ANULADO.value])
            )
        else:
            query = query.filter(Caso.estado == estado)

    if ficha:
        query = query.filter(Aprendiz.ficha.ilike(f"%{ficha}%"))

    if search:
        s = f"%{search}%"
        query = query.filter(
            or_(
                Caso.numero_caso.ilike(s),
                Aprendiz.nombres.ilike(s),
                Aprendiz.apellidos.ilike(s),
                Aprendiz.numero_documento.ilike(s),
                Aprendiz.ficha.ilike(s),
                Caso.motivo_desercion.ilike(s)
            )
        )

    casos_objs = query.order_by(desc(Caso.fecha_creacion)).all()
    resultado = []
    for c in casos_objs:
        total_act = len(c.actuaciones)
        total_comp = len(c.compromisos)
        resultado.append({
            "id": c.id,
            "numero_caso": c.numero_caso,
            "aprendiz": {
                "id": c.aprendiz.id,
                "tipo_documento": c.aprendiz.tipo_documento,
                "numero_documento": c.aprendiz.numero_documento,
                "nombres": c.aprendiz.nombres,
                "apellidos": c.aprendiz.apellidos,
                "email": c.aprendiz.email,
                "telefono": c.aprendiz.telefono,
                "ficha": c.aprendiz.ficha,
                "programa": c.aprendiz.programa,
                "jornada": c.aprendiz.jornada,
                "activo": c.aprendiz.activo,
                "fecha_creacion": c.aprendiz.fecha_creacion
            },
            "motivo_desercion": c.motivo_desercion,
            "estado": c.estado,
            "asignado_a": {
                "id": c.asignado_a.id,
                "nombre": c.asignado_a.nombre,
                "email": c.asignado_a.email,
                "rol": c.asignado_a.rol
            } if c.asignado_a else None,
            "tipo_cierre": c.tipo_cierre,
            "dias_sin_actuacion": c.dias_sin_actuacion,
            "fecha_creacion": c.fecha_creacion,
            "total_actuaciones": total_act,
            "total_compromisos": total_comp
        })
    return resultado

@app.post("/api/casos")
def create_caso(payload: CasoCreate, db: Session = Depends(get_db)):
    try:
        nuevo = CasoService.crear_caso(
            db=db,
            aprendiz_id=payload.aprendiz_id,
            motivo=payload.motivo_desercion,
            descripcion=payload.descripcion_inicial,
            asignado_a_id=payload.asignado_a_id
        )
        return {"id": nuevo.id, "numero_caso": nuevo.numero_caso, "message": "Caso registrado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/casos/{caso_id}")
def get_caso_detail(caso_id: int, db: Session = Depends(get_db)):
    caso = db.query(Caso).filter(Caso.id == caso_id).first()
    if not caso:
        raise HTTPException(status_code=404, detail="Caso no encontrado")

    transiciones = TRANSICIONES_PERMITIDAS.get(caso.estado, [])

    return {
        "id": caso.id,
        "numero_caso": caso.numero_caso,
        "aprendiz": {
            "id": caso.aprendiz.id,
            "tipo_documento": caso.aprendiz.tipo_documento,
            "numero_documento": caso.aprendiz.numero_documento,
            "nombres": caso.aprendiz.nombres,
            "apellidos": caso.aprendiz.apellidos,
            "email": caso.aprendiz.email,
            "telefono": caso.aprendiz.telefono,
            "ficha": caso.aprendiz.ficha,
            "programa": caso.aprendiz.programa,
            "jornada": caso.aprendiz.jornada,
            "activo": caso.aprendiz.activo,
            "fecha_creacion": caso.aprendiz.fecha_creacion
        },
        "motivo_desercion": caso.motivo_desercion,
        "descripcion_inicial": caso.descripcion_inicial,
        "estado": caso.estado,
        "asignado_a": {
            "id": caso.asignado_a.id,
            "nombre": caso.asignado_a.nombre,
            "email": caso.asignado_a.email,
            "rol": caso.asignado_a.rol
        } if caso.asignado_a else None,
        "tipo_cierre": caso.tipo_cierre,
        "justificacion_cierre": caso.justificacion_cierre,
        "fecha_cierre": caso.fecha_cierre,
        "dias_sin_actuacion": caso.dias_sin_actuacion,
        "fecha_creacion": caso.fecha_creacion,
        "actuaciones": [
            {
                "id": a.id,
                "caso_id": a.caso_id,
                "tipo": a.tipo,
                "resultado": a.resultado,
                "observaciones": a.observaciones,
                "proxima_accion": a.proxima_accion,
                "fecha_actuacion": a.fecha_actuacion,
                "usuario_nombre": a.usuario.nombre if a.usuario else "Gestor GAES"
            } for a in caso.actuaciones
        ],
        "compromisos": [
            {
                "id": cmp.id,
                "caso_id": cmp.caso_id,
                "descripcion": cmp.descripcion,
                "responsable": cmp.responsable,
                "fecha_limite": cmp.fecha_limite,
                "estado": cmp.estado,
                "fecha_cumplimiento": cmp.fecha_cumplimiento
            } for cmp in caso.compromisos
        ],
        "auditorias": [
            {
                "id": aud.id,
                "usuario_nombre": aud.usuario_nombre,
                "accion": aud.accion,
                "detalle": aud.detalle,
                "estado_anterior": aud.estado_anterior,
                "estado_nuevo": aud.estado_nuevo,
                "fecha": aud.fecha
            } for aud in caso.auditorias
        ],
        "transiciones_permitidas": transiciones
    }

@app.post("/api/casos/{caso_id}/transicion")
def transicionar_caso(caso_id: int, payload: TransicionRequest, db: Session = Depends(get_db)):
    try:
        updated = CasoService.transicionar_estado(
            db=db,
            caso_id=caso_id,
            nuevo_estado=payload.nuevo_estado,
            justificacion=payload.justificacion,
            usuario_nombre=payload.usuario_nombre,
            tipo_cierre=payload.tipo_cierre,
            asignado_a_id=payload.asignado_a_id
        )
        return {"status": "ok", "nuevo_estado": updated.estado, "numero_caso": updated.numero_caso}
    except DominioError as de:
        raise HTTPException(status_code=400, detail=str(de))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/casos/{caso_id}/actuaciones")
def add_actuacion(caso_id: int, payload: ActuacionCreate, db: Session = Depends(get_db)):
    try:
        act = CasoService.agregar_actuacion(
            db=db,
            caso_id=caso_id,
            tipo=payload.tipo,
            resultado=payload.resultado,
            observaciones=payload.observaciones,
            proxima_accion=payload.proxima_accion,
            usuario_nombre=payload.usuario_nombre or "Líder GAES"
        )
        return {"id": act.id, "message": "Actuación registrada con éxito"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/casos/{caso_id}/compromisos")
def add_compromiso(caso_id: int, payload: CompromisoCreate, db: Session = Depends(get_db)):
    try:
        cmp = CasoService.agregar_compromiso(
            db=db,
            caso_id=caso_id,
            descripcion=payload.descripcion,
            responsable=payload.responsable,
            fecha_limite=payload.fecha_limite
        )
        return {"id": cmp.id, "message": "Compromiso registrado"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.patch("/api/compromisos/{compromiso_id}/estado")
def update_compromiso(compromiso_id: int, payload: dict, db: Session = Depends(get_db)):
    nuevo_estado = payload.get("nuevo_estado")
    if not nuevo_estado:
        raise HTTPException(status_code=400, detail="nuevo_estado requerido")
    try:
        cmp = CasoService.actualizar_compromiso(db, compromiso_id, nuevo_estado)
        return {"id": cmp.id, "estado": cmp.estado}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/aprendices")
def list_aprendices(search: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Aprendiz).filter(Aprendiz.activo == True)
    if search:
        s = f"%{search}%"
        q = q.filter(
            or_(
                Aprendiz.nombres.ilike(s),
                Aprendiz.apellidos.ilike(s),
                Aprendiz.numero_documento.ilike(s),
                Aprendiz.ficha.ilike(s),
                Aprendiz.programa.ilike(s)
            )
        )
    return q.all()

@app.post("/api/aprendices")
def create_aprendiz(payload: AprendizCreate, db: Session = Depends(get_db)):
    existente = db.query(Aprendiz).filter(Aprendiz.numero_documento == payload.numero_documento).first()
    if existente:
        raise HTTPException(status_code=400, detail=f"Ya existe un aprendiz con el documento {payload.numero_documento}")
    ap = Aprendiz(**payload.dict())
    db.add(ap)
    db.commit()
    db.refresh(ap)
    return ap

@app.get("/api/usuarios")
def list_usuarios(db: Session = Depends(get_db)):
    return db.query(Usuario).filter(Usuario.activo == True).all()
