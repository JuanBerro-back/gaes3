from pathlib import Path
APP_NAME="GAES3 - Gestión Deserciones SENA"
APP_VERSION="1.0.0"
MAX_FILE_MB_DEFAULT=25
DAYS_REAPERTURA_MAX_DEFAULT=90
DAYS_SIN_SEGUIMIENTO_ALERT_DEFAULT=7
LOGIN_MAX_ATTEMPTS_DEFAULT=5
LOGIN_BLOCK_MINUTES_DEFAULT=15
SESSION_INACTIVITY_MINUTES_DEFAULT=10
FORMATO_NUMERO_CASO="DES-%06d"
BLOCKED_EXTS={"exe","bat","sh","ps1","js","php","py","vbs","scr","com","msi","jar","html","htm","svg"}
ALLOWED_EXTS_DEFAULT={"pdf","doc","docx","xls","xlsx","jpg","jpeg","png","heic","mp4"}
PROJECT_ROOT=Path(__file__).resolve().parents[2]
