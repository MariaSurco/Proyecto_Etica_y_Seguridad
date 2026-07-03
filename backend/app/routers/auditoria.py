from fastapi import APIRouter, Depends
from app.security.rbac import require_permission

router = APIRouter(prefix="/auditoria", tags=["auditoria"])

@router.get("/logs")
def list_logs(user: dict = Depends(require_permission("auditoria:consultar"))):
    return []
