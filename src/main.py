import uvicorn
import webbrowser
import threading
import time

def open_browser():
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:8000")

def main():
    print("=" * 65)
    print("  GAES 3 - SISTEMA DE GESTION DE DESERCIONES SENA (v1.0.0)")
    print("=" * 65)
    print("  Servidor web iniciando en: http://127.0.0.1:8000")
    print("  Documentacion API Swagger: http://127.0.0.1:8000/docs")
    print("  Presione CTRL + C para detener el servidor.")
    print("=" * 65)

    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("src.app:app", host="127.0.0.1", port=8000, reload=False, log_level="info")

if __name__ == "__main__":
    main()
