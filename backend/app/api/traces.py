from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_project_by_api_key, get_project_membership
from app.core.db import get_db
from app.models.project import Project, ProjectMembership
from app.models.trace import Trace
from app.schemas.trace import TraceBatchIn, TraceListOut, TraceOut

router = APIRouter(prefix="/api/v1", tags=["traces"])


@router.post("/traces", status_code=201)
def ingest_traces(
    payload: TraceBatchIn,
    project: Project = Depends(get_project_by_api_key),
    db: Session = Depends(get_db),
):
    traces = [Trace(project_id=project.id, **trace.model_dump()) for trace in payload.traces]
    db.add_all(traces)
    db.commit()
    return {"ingested": len(traces)}


@router.get("/projects/{project_id}/traces", response_model=TraceListOut)
def list_traces(
    project_id: str,
    model: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    membership: ProjectMembership = Depends(get_project_membership),
    db: Session = Depends(get_db),
):
    query = db.query(Trace).filter_by(project_id=project_id)
    if model is not None:
        query = query.filter_by(model=model)
    if status_filter is not None:
        query = query.filter_by(status=status_filter)

    total = query.with_entities(func.count(Trace.id)).scalar()
    items = (
        query.order_by(Trace.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return TraceListOut(
        items=[TraceOut.model_validate(t) for t in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/projects/{project_id}/traces/{trace_id}", response_model=TraceOut)
def get_trace(
    project_id: str,
    trace_id: str,
    membership: ProjectMembership = Depends(get_project_membership),
    db: Session = Depends(get_db),
):
    trace = db.query(Trace).filter_by(id=trace_id, project_id=project_id).first()
    if trace is None:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, "Trace not found")
    return trace
