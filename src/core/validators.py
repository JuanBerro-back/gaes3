from pathlib import Path
from src.core.exceptions import *
from src.core.constants import BLOCKED_EXTS, ALLOWED_EXTS_DEFAULT, MAX_FILE_MB_DEFAULT

def validar_extension(n:str, permit=None)->str:
    if not n or "/" in n or "\\" in n or ".." in n: raise NombreArchivoInvalidoError
    p=Path(n); ext=p.suffix.lower().lstrip(".")
    if not ext: raise ArchivoNoPermitidoError
    if ext in BLOCKED_EXTS: raise ArchivoNoPermitidoError
    pr=permit or ALLOWED_EXTS_DEFAULT
    if ext not in {e.lower() for e in pr}: raise ArchivoNoPermitidoError
    return ext

def validar_tamano(t:int,max_mb:int=MAX_FILE_MB_DEFAULT):
    if t<=0: raise ArchivoNoPermitidoError
    if t>max_mb*1024*1024: raise ArchivoDemasiadoGrandeError
