import csv
import io
import json

from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query as SAQuery, Session

from app.api.deps import get_project_by_api_key, get_project_membership
from app.core.db import get_db
from app.models.project import Project, ProjectMembership
from app.models.trace import Trace
from app.schemas.trace import TraceBatchIn, TraceListOut, TraceOut

router = APIRouter(prefix="/api/v1", tags=["traces"])

TRACE_EXPORT_COLUMNS = [
    "id", "client_trace_id", "model", "provider", "prompt", "completion",
    "prompt_tokens", "completion_tokens", "latency_ms", "cost", "status",
    "error_message", "tags", "created_at",
]


def _filtered_traces_query(
    db: Session, project_id: str, model: str | None, status_filter: str | None
) -> SAQuery:
    """Shared by list_traces and export_traces so the two can never drift -
    same filters, same project scoping, same ordering."""
    query = db.query(Trace).filter_by(project_id=project_id)
    if model is not None:
        query = query.filter_by(model=model)
    if status_filter is not None:
        query = query.filter_by(status=status_filter)
    return query.order_by(Trace.created_at.desc())


@router.post("/traces", status_code=201)
def ingest_traces(
    payload: TraceBatchIn,
    project: Project = Depends(get_project_by_api_key),
    db: Session = Depends(get_db),
):
    # A retried batch (SDK retries on network error / 5xx) resends the same
    # client_trace_id values - skip any that are already stored instead of
    # inserting duplicates. Traces without a client_trace_id (e.g. sent
    # manually) always insert, since there's nothing to de-duplicate against.
    incoming_client_ids = [t.client_trace_id for t in payload.traces if t.client_trace_id is not None]
    existing_client_ids: set[str] = set()
    if incoming_client_ids:
        existing_client_ids = {
            row[0]
            for row in db.query(Trace.client_trace_id)
            .filter(
                Trace.project_id == project.id,
                Trace.client_trace_id.in_(incoming_client_ids),
            )
            .all()
        }

    # The existing-rows check above only catches IDs already committed to the
    # DB. It does not catch the same client_trace_id appearing twice *within
    # this one payload* (e.g. a caller building a batch from a source that
    # accidentally repeats an entry) - `.in_(incoming_client_ids)` de-dupes
    # implicitly on the read, so nothing there would have caught it. Without
    # this, two rows sharing a client_trace_id would both pass the check
    # above, both get queued for insert, and the unique constraint would
    # reject the whole `add_all` as one transaction - discarding every trace
    # in the batch, including unrelated ones that had nothing to do with the
    # collision (see IntegrityError handler below, which then misreports the
    # entire batch as "already delivered" even though none of it was stored).
    seen_in_batch: set[str] = set()
    new_traces: list[Trace] = []
    for trace_in in payload.traces:
        cid = trace_in.client_trace_id
        if cid is not None:
            if cid in existing_client_ids or cid in seen_in_batch:
                continue
            seen_in_batch.add(cid)
        new_traces.append(Trace(project_id=project.id, **trace_in.model_dump()))
    skipped = len(payload.traces) - len(new_traces)

    db.add_all(new_traces)
    try:
        db.commit()
    except IntegrityError:
        # Lost the race: a concurrent request inserted one of these
        # client_trace_ids between our check and this commit. Safe to treat
        # the whole attempted insert as already-delivered rather than 500.
        db.rollback()
        return {"ingested": 0, "skipped_duplicates": len(payload.traces)}

    return {"ingested": len(new_traces), "skipped_duplicates": skipped}


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
    query = _filtered_traces_query(db, project_id, model, status_filter)

    total = query.with_entities(func.count(Trace.id)).scalar()
    items = query.offset(offset).limit(limit).all()

    return TraceListOut(
        items=[TraceOut.model_validate(t) for t in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/projects/{project_id}/traces/export")
def export_traces(
    project_id: str,
    model: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    format: str = Query(default="csv", pattern="^(csv|json)$"),
    membership: ProjectMembership = Depends(get_project_membership),
    db: Session = Depends(get_db),
):
    # Same filters and ordering as list_traces, but no limit/offset - export
    # means "everything matching," not one page of it. Registered before
    # GET /traces/{trace_id} so FastAPI doesn't match "export" as a trace ID.
    traces = _filtered_traces_query(db, project_id, model, status_filter).all()
    filename = f"traces_{project_id}.{format}"

    if format == "json":
        body = json.dumps(
            [TraceOut.model_validate(t).model_dump(mode="json") for t in traces]
        )
        return StreamingResponse(
            iter([body]),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(TRACE_EXPORT_COLUMNS)
    for t in traces:
        writer.writerow([getattr(t, col) for col in TRACE_EXPORT_COLUMNS])
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
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
