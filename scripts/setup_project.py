import os
from pathlib import Path

ROOT = Path(r'C:\Users\jdbpb\Desktop\GAES3_GAES3')
for d in ['docs/requisitos','docs/diseno','docs/pruebas','src/core','src/config','src/models','src/schemas','src/repositories','src/services','src/utils','src/ui','tests/unit/test_core','tests/unit/test_services','tests/integration','tests/fixtures','alembic/versions','scripts','data','uploads','logs']:
    (ROOT/d).mkdir(parents=True, exist_ok=True)
(ROOT/'uploads/.gitkeep').write_text('', encoding='utf-8')
(ROOT/'data/.gitkeep').write_text('', encoding='utf-8')

# README
(ROOT/'README.md').write_text('# GAES 3 - Sistema de Gestión de Deserciones SENA\n\nSistema para gestión, seguimiento y control de casos de deserción (GAES 3), con trazabilidad, auditoría inmutable, FSM, borrado lógico y seguridad por defecto.\n\n## Instalación\n```bash\npython -m venv .venv\n.venv\\Scripts\\activate\npip install -r requirements.txt\n```\n\n## Configuración\nCopiar `.env.example` a `.env`\n\n## Ejecutar\n```bash\npython -m src.main\n```\n\n## Verificación Calidad\n```bash\nruff check . --fix\nruff format .\nmypy src --ignore-missing-imports\npytest -v --cov=src --cov-report=term-missing\n```', encoding='utf-8')

# requirements
(ROOT/'requirements.txt').write_text('SQLAlchemy>=2.0.36\nalembic>=1.14.0\npydantic>=2.10.4\npydantic-settings>=2.7.0\nargon2-cffi>=23.1.0\npython-dateutil>=2.9.0.post0\nopenpyxl>=3.1.5\nfpdf2>=2.8.1\npandas>=2.2.3\npytest>=8.3.4\npytest-cov>=6.0.0\nfactory-boy>=3.3.1\nruff>=0.8.4\nmypy>=1.13.0\npython-dotenv>=1.0.1\n', encoding='utf-8')

# .env.example
(ROOT/'.env.example').write_text('APP_ENV=development\nAPP_NAME=GAES3 - Gestión Deserciones SENA\nAPP_DEBUG=true\nSECRET_KEY=change_me_in_production_generate_strong_32_plus_chars_min_32\nDATABASE_URL=sqlite:///./data/gaes3.db\nDB_ECHO=false\nLOGIN_MAX_ATTEMPTS=5\nLOGIN_BLOCK_MINUTES=15\nSESSION_INACTIVITY_MINUTES=10\nUPLOADS_DIR=./uploads\nMAX_FILE_MB=25\nALLOWED_EXTS=pdf,doc,docx,xls,xlsx,jpg,jpeg,png,heic,mp4\nBLOCKED_EXTS=exe,bat,sh,ps1,js,php,py,vbs,scr,com,msi,jar,html,htm,svg\nDAYS_REAPERTURA_MAX=90\nDAYS_SIN_SEGUIMIENTO_ALERT=7\nMIN_ACTUACIONES_PARA_CIERRE=1\nFORMATO_NUMERO_CASO=DES-%06d\nLOG_LEVEL=INFO\nAUDIT_IP_ENABLED=false\nEXPORT_BATCH_SIZE=1000\n', encoding='utf-8')

# .gitignore
(ROOT/'.gitignore').write_text('.env\ndata/*.db\ndata/*.sqlite3\nuploads/*\n!uploads/.gitkeep\n__pycache__/\n*.py[cod]\n.mypy_cache/\n.pytest_cache/\n.ruff_cache/\nhtmlcov/\n.coverage\nlogs/\n.venv/\nvenv/\n.idea/\n.vscode/\n.DS_Store\nThumbs.db\n', encoding='utf-8')

# main/app
(ROOT/'src/main.py').write_text('def main():\n    print("GAES3 - Sistema de Gestión de Deserciones SENA (v1.0.0)")\nif __name__ == "__main__":\n    main()\n', encoding='utf-8')
(ROOT/'src/app.py').write_text('# App entrypoint\n', encoding='utf-8')
(ROOT/'src/__init__.py').write_text('__version__ = "1.0.0"\n', encoding='utf-8')

# core enums
(ROOT/'src/core/enums.py').write_text('from enum import Enum\nclass EstadoCasoEnum(str,Enum):\n    REGISTRADO="REGISTRADO"; ASIGNADO="ASIGNADO"; EN_INVESTIGACION="EN_INVESTIGACION"; EN_SEGUIMIENTO="EN_SEGUIMIENTO"; PROPUESTO_CIERRE="PROPUESTO_CIERRE"; CERRADO="CERRADO"; REABIERTO="REABIERTO"; ANULADO="ANULADO"\nclass TipoActuacionEnum(str,Enum): LLAMADA="LLAMADA"; CITACION="CITACION"; REUNION="REUNION"; VISITA="VISITA"; CORREO="CORREO"; ACTA="ACTA"; ACUERDO="ACUERDO"; OTRO="OTRO"\nclass ResultadoActuacionEnum(str,Enum): CONTACTADO="CONTACTADO"; NO_CONTACTADO="NO_CONTACTADO"; ACUERDO_ALCANZADO="ACUERDO_ALCANZADO"; REPROGRAMADO="REPROGRAMADO"; CANCELADO="CANCELADO"; SIN_RESULTADO="SIN_RESULTADO"; OTRO="OTRO"\nclass EstadoCompromisoEnum(str,Enum): PENDIENTE="PENDIENTE"; CUMPLIDO="CUMPLIDO"; INCUMPLIDO="INCUMPLIDO"; VENCIDO="VENCIDO"; CERRADO="CERRADO"\nclass TipoCierreEnum(str,Enum): DESERCION_CONFIRMADA="DESERCION_CONFIRMADA"; RETORNO_READMISION="RETORNO_READMISION"; TRANSFERIDO="TRANSFERIDO"; NO_APLICA="NO_APLICA"; OTRO="OTRO"\nclass RolCodigoEnum(str,Enum): ADMIN="ADMIN"; LIDER_GAES="LIDER_GAES"; GAES_APOYO="GAES_APOYO"; COORDINADOR="COORDINADOR"; BIENESTAR="BIENESTAR"; INSTRUCTOR="INSTRUCTOR"; SOLO_LECTURA="SOLO_LECTURA"\nclass AccionAuditoriaEnum(str,Enum): CREAR="CREAR"; ACTUALIZAR="ACTUALIZAR"; ANULAR="ANULAR"; CAMBIAR_ESTADO="CAMBIAR_ESTADO"; APROBAR_CIERRE="APROBAR_CIERRE"; RECHAZAR_CIERRE="RECHAZAR_CIERRE"; CERRAR="CERRAR"; REABRIR="REABRIR"; ADJUNTAR="ADJUNTAR"; DESVINCULAR="DESVINCULAR"; CAMBIO_AUTOMATICO="CAMBIO_AUTOMATICO"\n', encoding='utf-8')

# core constants
(ROOT/'src/core/constants.py').write_text('from pathlib import Path\nAPP_NAME="GAES3 - Gestión Deserciones SENA"\nAPP_VERSION="1.0.0"\nMAX_FILE_MB_DEFAULT=25\nDAYS_REAPERTURA_MAX_DEFAULT=90\nDAYS_SIN_SEGUIMIENTO_ALERT_DEFAULT=7\nLOGIN_MAX_ATTEMPTS_DEFAULT=5\nLOGIN_BLOCK_MINUTES_DEFAULT=15\nSESSION_INACTIVITY_MINUTES_DEFAULT=10\nFORMATO_NUMERO_CASO="DES-%06d"\nBLOCKED_EXTS={"exe","bat","sh","ps1","js","php","py","vbs","scr","com","msi","jar","html","htm","svg"}\nALLOWED_EXTS_DEFAULT={"pdf","doc","docx","xls","xlsx","jpg","jpeg","png","heic","mp4"}\nPROJECT_ROOT=Path(__file__).resolve().parents[2]\n', encoding='utf-8')

# core exceptions
(ROOT/'src/core/exceptions.py').write_text('class DominioError(Exception): pass\nclass CasoActivoExistente(DominioError): pass\nclass TransicionEstadoNoPermitida(DominioError): pass\nclass EstadoTerminalError(DominioError): pass\nclass ReaperturaNoPermitida(DominioError): pass\nclass CierreNoAutorizado(DominioError): pass\nclass CompromisosPendientesError(DominioError): pass\nclass EvidenciasMinimasRequeridas(DominioError): pass\nclass JustificacionRequeridaError(DominioError): pass\nclass ArchivoNoPermitidoError(DominioError): pass\nclass ArchivoDemasiadoGrandeError(DominioError): pass\nclass PathTraversalDetectadoError(DominioError): pass\nclass NombreArchivoInvalidoError(DominioError): pass\n', encoding='utf-8')

# security
(ROOT/'src/core/security.py').write_text('from passlib.context import CryptContext\npwd_context = CryptContext(schemes=["argon2"], deprecated="auto")\ndef hash_password(p:str)->str: return pwd_context.hash(p)\ndef verify_password(p:str,h:str)->bool:\n    try: return pwd_context.verify(p,h)\n    except: return False\n', encoding='utf-8')

# validators
(ROOT/'src/core/validators.py').write_text('from pathlib import Path\nfrom src.core.exceptions import *\nfrom src.core.constants import BLOCKED_EXTS, ALLOWED_EXTS_DEFAULT, MAX_FILE_MB_DEFAULT\n\ndef validar_extension(n:str, permit=None)->str:\n    if not n or "/" in n or "\\\\" in n or ".." in n: raise NombreArchivoInvalidoError\n    p=Path(n); ext=p.suffix.lower().lstrip(".")\n    if not ext: raise ArchivoNoPermitidoError\n    if ext in BLOCKED_EXTS: raise ArchivoNoPermitidoError\n    pr=permit or ALLOWED_EXTS_DEFAULT\n    if ext not in {e.lower() for e in pr}: raise ArchivoNoPermitidoError\n    return ext\n\ndef validar_tamano(t:int,max_mb:int=MAX_FILE_MB_DEFAULT):\n    if t<=0: raise ArchivoNoPermitidoError\n    if t>max_mb*1024*1024: raise ArchivoDemasiadoGrandeError\n', encoding='utf-8')

# utils
(ROOT/'src/core/utils.py').write_text('from datetime import datetime, timezone\ndef utc_now()->datetime: return datetime.now(timezone.utc)\n', encoding='utf-8')
(ROOT/'src/config/settings.py').write_text('from pydantic_settings import BaseSettings, SettingsConfigDict\nfrom pathlib import Path\nclass Settings(BaseSettings):\n    model_config=SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")\n    DATABASE_URL:str="sqlite:///./data/gaes3.db"\n    UPLOADS_DIR:str="./uploads"\n    MAX_FILE_MB:int=25\n    FORMATO_NUMERO_CASO:str="DES-%06d"\n    MIN_ACTUACIONES_PARA_CIERRE:int=1\n    REQUIERE_EVIDENCIAS_MIN_POR_TIPO_CIERRE:bool=True\n    @property\n    def uploads_path(self)->Path: return Path(self.UPLOADS_DIR).resolve()\nsettings=Settings()\n', encoding='utf-8')

# base models
(ROOT/'src/models/base.py').write_text('from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column\nfrom sqlalchemy import DateTime, func, Boolean\nfrom datetime import datetime\nclass Base(DeclarativeBase): pass\nclass TimestampMixin:\n    fecha_creacion: Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)\n    fecha_modificacion: Mapped[datetime|None]=mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)\nclass SoftDeleteMixin:\n    activo: Mapped[bool]=mapped_column(Boolean, default=True, nullable=False)\n    anulado: Mapped[bool]=mapped_column(Boolean, default=False, nullable=False)\n', encoding='utf-8')

# docs mínimos
(ROOT/'docs/requisitos/01_Introduccion_Alcance.md').write_text('# 1. Introducción y Alcance\n\nGAES 3 - Sistema de Gestión de Deserciones SENA. Version 1.0.0\n', encoding='utf-8')
(ROOT/'docs/diseno/02_Modelo_ER.md').write_text('# 2. Modelo ER\n\nDiagrama Mermaid (resumido) en documentación completa.\n', encoding='utf-8')
(ROOT/'docs/diseno/03_Diagrama_Flujo_Estados.md').write_text('# 3. FSM\n\nEstados y transiciones controladas por rol.\n', encoding='utf-8')
(ROOT/'docs/pruebas/Plan_Pruebas.md').write_text('# Plan de Pruebas\n\nUnitarias + Integración + Funcionales. Gates: ruff 0, mypy 0, pytest 100% críticos.\n', encoding='utf-8')

# UI readme
(ROOT/'src/ui/README_UI.md').write_text('# UI\n\nEsqueleto para implementación futura.\n', encoding='utf-8')

print('ESTRUCTURA CREADA CON EXITO')
