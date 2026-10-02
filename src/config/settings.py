from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
class Settings(BaseSettings):
    model_config=SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    DATABASE_URL:str="sqlite:///./data/gaes3.db"
    UPLOADS_DIR:str="./uploads"
    MAX_FILE_MB:int=25
    FORMATO_NUMERO_CASO:str="DES-%06d"
    MIN_ACTUACIONES_PARA_CIERRE:int=1
    REQUIERE_EVIDENCIAS_MIN_POR_TIPO_CIERRE:bool=True
    @property
    def uploads_path(self)->Path: return Path(self.UPLOADS_DIR).resolve()
settings=Settings()
