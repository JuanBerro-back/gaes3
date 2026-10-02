from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
def hash_password(p:str)->str: return pwd_context.hash(p)
def verify_password(p:str,h:str)->bool:
    try: return pwd_context.verify(p,h)
    except: return False
