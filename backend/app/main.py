from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, auditoria, dp

app = FastAPI(title="Sistema Seguro de Apoyo a Campañas Bancarias")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(auditoria.router)
app.include_router(dp.router)

@app.get("/health")
def health():
    return {"status": "ok"}
