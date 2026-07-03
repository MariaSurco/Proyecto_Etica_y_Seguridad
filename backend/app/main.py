from fastapi import FastAPI
from app.routers import auth, auditoria

app = FastAPI(title="Sistema Seguro de Apoyo a Campañas Bancarias")
app.include_router(auth.router)
app.include_router(auditoria.router)

@app.get("/health")
def health():
    return {"status": "ok"}
