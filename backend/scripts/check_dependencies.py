import sys

def check_imports():
    packages = {
        "fastapi": "FastAPI",
        "sqlalchemy": "SQLAlchemy (Database)",
        "redis": "Redis (Cache)",
        "jose": "JWT Auth",
        "passlib": "Password Hashing",
        "sklearn": "Machine Learning",
        "torch": "PyTorch (Deep Learning)",
        "pytest": "Testing",
        "httpx": "HTTP Client (Ollama)"
    }
    
    print("🔍 Verificando dependencias...\n")
    
    for module, name in packages.items():
        try:
            __import__(module)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} - NO INSTALADO")
    
    print("\n✨ Verificación completa!")

if __name__ == "__main__":
    check_imports()