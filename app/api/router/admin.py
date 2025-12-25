from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from app.api import deps
from app.services.datastore.datastore import LightRAGClient
from app.services.escalations.controller import escalation_service

router = APIRouter(dependencies=[Depends(deps.verify_api_key)])

class IngestRequest(BaseModel):
    text: str
    description: Optional[str] = None
    
class SearchRequest(BaseModel):
    query: str
    mode: str = "hybrid"

class UpdateEscalationRequest(BaseModel):
    status: str  # pending, assigned, in_progress, resolved
    assigned_to: Optional[str] = None

@router.post("/lightrag/ingest")
async def ingest_text(
    request: IngestRequest,
    client: LightRAGClient = Depends(deps.get_lightrag_client)
):
    """Admin endpoint to ingest text into LightRAG."""
    try:
        res = await client.insert_text(request.text, description=request.description)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/lightrag/ingest/file")
async def ingest_file(
    files: List[UploadFile] = File(...),
    domain: Optional[str] = Form(None),
    client: LightRAGClient = Depends(deps.get_lightrag_client)
):
    """
    Admin endpoint to ingest one or more files into LightRAG.
    Accepts multipart/form-data with `files`.
    """
    results = []
    for upload in files:
        try:
            res = await client.insert_file(upload, domain=domain)
            results.append({
                "filename": upload.filename,
                "success": res.get("success", True),
                "message": res.get("message"),
                "track_id": res.get("track_id"),
            })
        except Exception as e:
            results.append({
                "filename": upload.filename,
                "success": False,
                "message": str(e),
                "track_id": None,
            })
    return results

@router.post("/lightrag/search")
async def search_documents(
    request: SearchRequest,
    client: LightRAGClient = Depends(deps.get_lightrag_client)
):
    """Admin endpoint to search LightRAG."""
    try:
        result = await client.query(request.query, mode=request.mode)
        return {"response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Escalation Management Endpoints
# ============================================

@router.get("/escalations")
async def list_pending_escalations():
    """
    List all pending escalations for human agents to review.
    Returns escalations sorted by priority and creation time.
    """
    try:
        escalations = await escalation_service.get_pending_escalations()
        return {
            "count": len(escalations),
            "escalations": [
                {
                    "id": e.id,
                    "user_id": e.user_id,
                    "channel": e.channel,
                    "reason": e.reason.value,
                    "priority": e.priority.value,
                    "summary": e.summary,
                    "status": e.status,
                    "created_at": e.created_at.isoformat(),
                }
                for e in sorted(
                    escalations, 
                    key=lambda x: (
                        {"urgent": 0, "high": 1, "medium": 2, "low": 3}.get(x.priority.value, 2),
                        x.created_at
                    )
                )
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/escalations/{escalation_id}")
async def get_escalation(escalation_id: str):
    """Get detailed information about a specific escalation."""
    try:
        escalation = await escalation_service.get_escalation(escalation_id)
        if not escalation:
            raise HTTPException(status_code=404, detail="Escalation not found")
        
        return {
            "id": escalation.id,
            "user_id": escalation.user_id,
            "channel": escalation.channel,
            "thread_id": escalation.thread_id,
            "reason": escalation.reason.value,
            "priority": escalation.priority.value,
            "summary": escalation.summary,
            "status": escalation.status,
            "created_at": escalation.created_at.isoformat(),
            "metadata": escalation.metadata,
            "conversation_history": escalation.conversation_history,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/escalations/{escalation_id}")
async def update_escalation(escalation_id: str, request: UpdateEscalationRequest):
    """
    Update escalation status.
    Used by human agents to mark escalations as assigned, in_progress, or resolved.
    """
    try:
        success = await escalation_service.update_status(
            escalation_id=escalation_id,
            status=request.status,
            assigned_to=request.assigned_to
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Escalation not found")
        
        return {"success": True, "message": f"Escalation {escalation_id} updated to {request.status}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

