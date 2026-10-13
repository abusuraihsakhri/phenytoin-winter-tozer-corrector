"""FastAPI wrapper for the clinical calculator and optional audit service."""
import hmac
import os
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from winter_tozer import correct_phenytoin
from .base import AuditLogger, SecurityException
from .models import SystemTaskPayload
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")
app = FastAPI(
    title="Phenytoin Winter–Tozer Calculator API",
    description="Research-use correction estimates and optional authenticated audit endpoints.",
    version="1.1.0",
)


class CorrectionRequest(BaseModel):
    measured_phenytoin_mg_l: float = Field(ge=0, allow_inf_nan=False)
    albumin_g_dl: float = Field(gt=0, allow_inf_nan=False)
    crcl_ml_min: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)


class ChatRequest(BaseModel):
    query: str


def require_audit_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")) -> None:
    configured = os.getenv("AUDIT_API_KEY")
    if not configured:
        raise HTTPException(status_code=503, detail="Audit API is disabled until AUDIT_API_KEY is configured")
    if not x_api_key or not hmac.compare_digest(x_api_key, configured):
        raise HTTPException(status_code=401, detail="Valid X-API-Key required")


@app.get("/health")
def health():
    return {"status": "ok", "service": "phenytoin-winter-tozer-corrector"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
    }


@app.post("/api/correct")
def api_correct(payload: CorrectionRequest):
    """Stateless corrected-total estimate; does not log measurements."""
    try:
        return correct_phenytoin(
            payload.measured_phenytoin_mg_l,
            payload.albumin_g_dl,
            payload.crcl_ml_min,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload, _: None = Depends(require_audit_key)):
    try:
        return supervisor.process_task(payload).to_dict()
    except SecurityException as exc:
        raise HTTPException(status_code=422, detail="Identifier rejected by input screening") from exc


@app.post("/api/chat")
def api_chat(req: ChatRequest, _: None = Depends(require_audit_key)):
    try:
        return {"response": supervisor.query_supervisory_chat(req.query)}
    except SecurityException as exc:
        raise HTTPException(status_code=422, detail="Identifier rejected by input screening") from exc


@app.get("/api/audit/logs")
def api_audit_logs(_: None = Depends(require_audit_key)):
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}


# Place the static mount last to avoid shadowing API routes.
app.mount("/", StaticFiles(directory=str(Path(__file__).resolve().parent.parent / "web"), html=True), name="web")
