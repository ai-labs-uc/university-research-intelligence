"""Research registry, progress monitoring, and opportunity matching APIs.

This module deliberately keeps recommendations advisory.  It uses explicit
metadata supplied by record owners; it neither scores researchers nor makes
funding, promotion, or ethics decisions.
"""

from datetime import date, datetime, timedelta
import re

from bson import ObjectId
from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from gridfs import GridFSBucket
from pydantic import BaseModel, Field

from app.core.database import get_db, next_id, utcnow
from app.core.security import get_current_user

router = APIRouter(prefix="/research", tags=["research"])

STATUSES = {"DRAFT", "PENDING_REVIEW", "ONGOING", "COMPLETED", "ARCHIVED"}
VISIBILITIES = {"INSTITUTIONAL", "RESTRICTED"}
PEOPLE_TYPES = {"FACULTY", "NON_TEACHING_STAFF", "STUDENT", "OTHER"}
ADMIN_ROLES = {"ADMIN", "RESEARCH_OFFICE"}
ALLOWED_UPLOAD_SUFFIXES = {".pdf", ".doc", ".docx"}
MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024


class MilestoneInput(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    due_date: date | None = None
    completed: bool = False


class ResearchCreate(BaseModel):
    title: str = Field(min_length=5, max_length=300)
    abstract: str = Field(min_length=20, max_length=5000)
    researcher_type: str = "FACULTY"
    college_or_unit: str = Field(min_length=2, max_length=180)
    researchers: list[str] = Field(default_factory=list, max_length=20)
    keywords: list[str] = Field(default_factory=list, max_length=15)
    sdgs: list[int] = Field(default_factory=list, max_length=17)
    status: str = "DRAFT"
    visibility: str = "INSTITUTIONAL"
    start_date: date | None = None; approved_duration_months: int | None = Field(default=None, ge=1, le=120)
    target_completion_date: date | None = None
    funding_source: str | None = Field(default=None, max_length=300)
    outputs: list[str] = Field(default_factory=list, max_length=20)
    progress_percent: int = Field(default=0, ge=0, le=100)
    milestones: list[MilestoneInput] = Field(default_factory=list, max_length=20)


class ResearchUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=5, max_length=300)
    abstract: str | None = Field(default=None, min_length=20, max_length=5000)
    researcher_type: str | None = None
    college_or_unit: str | None = Field(default=None, min_length=2, max_length=180)
    researchers: list[str] | None = Field(default=None, max_length=20)
    keywords: list[str] | None = Field(default=None, max_length=15)
    sdgs: list[int] | None = Field(default=None, max_length=17)
    status: str | None = None
    visibility: str | None = None
    start_date: date | None = None; approved_duration_months: int | None = Field(default=None, ge=1, le=120)
    target_completion_date: date | None = None
    funding_source: str | None = Field(default=None, max_length=300)
    outputs: list[str] | None = Field(default=None, max_length=20)
    milestones: list[MilestoneInput] | None = Field(default=None, max_length=20)
    progress_percent: int | None = Field(default=None, ge=0, le=100)


class ProgressUpdate(BaseModel):
    progress_percent: int = Field(ge=0, le=100)
    note: str = Field(min_length=3, max_length=1000)
    status: str | None = None
    milestones: list[MilestoneInput] | None = Field(default=None, max_length=20)


def _is_admin(user: dict) -> bool:
    return user.get("role") in ADMIN_ROLES


def _normalise_list(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value.strip() for value in values if value and value.strip()))


def _validate_values(values: dict) -> dict:
    if "status" in values and values["status"] not in STATUSES:
        raise HTTPException(status_code=422, detail=f"status must be one of: {', '.join(sorted(STATUSES))}")
    if "visibility" in values and values["visibility"] not in VISIBILITIES:
        raise HTTPException(status_code=422, detail="visibility must be INSTITUTIONAL or RESTRICTED")
    if "researcher_type" in values and values["researcher_type"] not in PEOPLE_TYPES:
        raise HTTPException(status_code=422, detail="researcher_type must identify the record owner group")
    if "keywords" in values and values["keywords"] is not None:
        values["keywords"] = _normalise_list(values["keywords"])
    if "researchers" in values and values["researchers"] is not None:
        values["researchers"] = _normalise_list(values["researchers"])
    if "outputs" in values and values["outputs"] is not None:
        values["outputs"] = _normalise_list(values["outputs"])
    if "sdgs" in values and values["sdgs"] is not None:
        if any(sdg < 1 or sdg > 17 for sdg in values["sdgs"]):
            raise HTTPException(status_code=422, detail="SDGs must be between 1 and 17")
        values["sdgs"] = sorted(set(values["sdgs"]))
    if "milestones" in values and values["milestones"] is not None:
        values["milestones"] = [item.model_dump() for item in values["milestones"]]
        # PyMongo supports datetime but not date. Convert HTML date inputs
    # before storing so registry entries and dashboard monitoring work.
    for key in ("start_date", "target_completion_date"):
        if isinstance(values.get(key), date) and not isinstance(values[key], datetime):
            values[key] = datetime.combine(values[key], datetime.min.time())
    if values.get("milestones") is not None:
        for milestone in values["milestones"]:
            due_date = milestone.get("due_date")
            if isinstance(due_date, date) and not isinstance(due_date, datetime):
                milestone["due_date"] = datetime.combine(due_date, datetime.min.time())
    return values


def _serialize(record: dict | None) -> dict | None:
    if not record:
        return None
    value = dict(record)
    value["id"] = value.pop("_id")
    return value


def _record_or_404(db, research_id: int) -> dict:
    record = db.research_projects.find_one({"_id": research_id, "is_deleted": {"$ne": True}})
    if not record:
        raise HTTPException(status_code=404, detail="Research record not found")
    return record


def _can_view(record: dict, user: dict) -> bool:
    return _is_admin(user) or record["owner_id"] == user["_id"] or record.get("visibility") == "INSTITUTIONAL"


def _can_edit(record: dict, user: dict) -> bool:
    return _is_admin(user) or record["owner_id"] == user["_id"]


def _visible_research_query(user: dict) -> dict:
    query: dict = {"is_deleted": {"$ne": True}}
    if not _is_admin(user):
        query["$or"] = [{"owner_id": user["_id"]}, {"visibility": "INSTITUTIONAL"}]
    return query


def _as_date(value) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    return value if isinstance(value, date) else None


def _opportunity_scope(opportunity: dict) -> str:
    scope = (opportunity.get("scope_type") or "").upper()
    category = (opportunity.get("category") or "").upper()
    if scope in {"NATIONAL", "INTERNATIONAL"}:
        return scope
    if "INTERNATIONAL" in category:
        return "INTERNATIONAL"
    return "NATIONAL"


def _opportunity_kind(opportunity: dict) -> str:
    kind = (opportunity.get("opportunity_type") or "").upper()
    category = (opportunity.get("category") or "").upper()
    return "GRANT" if kind == "GRANT" or category.startswith("GRANT") else "CALL_FOR_PAPER"


def _terms(record: dict) -> set[str]:
    text = " ".join([
        record.get("title", ""), record.get("abstract", ""),
        " ".join(record.get("keywords", [])), record.get("college_or_unit", ""),
    ]).lower()
    return {term for term in re.findall(r"[a-z0-9]{3,}", text) if term not in {"research", "university", "study", "using", "with", "from", "that", "this"}}


def _attachment_metadata(grid_file) -> dict:
    return {
        "id": str(grid_file._id),
        "filename": grid_file.filename,
        "content_type": (grid_file.metadata or {}).get("content_type", "application/octet-stream"),
        "length": grid_file.length,
        "uploaded_at": grid_file.upload_date,
    }


@router.get("")
def list_research(
    q: str | None = Query(default=None, max_length=120),
    status_filter: str | None = Query(default=None, alias="status"),
    researcher_type: str | None = None,
    limit: int = Query(default=100, ge=1, le=250),
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    query: dict = {"is_deleted": {"$ne": True}}
    if not _is_admin(user):
        query["$or"] = [{"owner_id": user["_id"]}, {"visibility": "INSTITUTIONAL"}]
    if status_filter:
        query["status"] = status_filter.upper()
    if researcher_type:
        query["researcher_type"] = researcher_type.upper()
    if q and q.strip():
        pattern = re.escape(q.strip())
        query["$and"] = [{"$or": [{"title": {"$regex": pattern, "$options": "i"}}, {"abstract": {"$regex": pattern, "$options": "i"}}, {"keywords": {"$regex": pattern, "$options": "i"}}, {"college_or_unit": {"$regex": pattern, "$options": "i"}}]}]
    rows = list(db.research_projects.find(query).sort([("updated_at", -1), ("_id", -1)]).limit(limit))
    return [_serialize(row) for row in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_research(payload: ResearchCreate, user: dict = Depends(get_current_user), db=Depends(get_db)):
    values = _validate_values(payload.model_dump())
    now = utcnow()
    record = {
        "_id": next_id("research_projects"),
        **values,
        "owner_id": user["_id"],
        "owner_name": user["name"],
        "is_validated": _is_admin(user),
        "is_deleted": False,
        "progress_percent": 100 if values["status"] == "COMPLETED" else int(values.get("progress_percent") or 0),
        "progress_updates": [],
        "created_at": now,
        "updated_at": now,
    }
    db.research_projects.insert_one(record)
    return _serialize(record)


@router.get("/dashboard")
def research_dashboard(user: dict = Depends(get_current_user), db=Depends(get_db)):
    match = _visible_research_query(user)
    rows = list(db.research_projects.find(match, {"status": 1, "target_completion_date": 1, "progress_percent": 1, "milestones": 1}))
    counts = {name: 0 for name in STATUSES}
    today = date.today()
    due_soon = 0
    overdue = 0
    for row in rows:
        counts[row.get("status", "DRAFT")] = counts.get(row.get("status", "DRAFT"), 0) + 1
        target = row.get("target_completion_date")
        if isinstance(target, datetime):
            target = target.date()
        if target and row.get("status") not in {"COMPLETED", "ARCHIVED"}:
            if target < today:
                overdue += 1
            elif target <= today + timedelta(days=30):
                due_soon += 1
    return {"total_research": len(rows), "by_status": counts, "due_soon": due_soon, "overdue": overdue}


@router.get("/analytics")
def research_analytics(user: dict = Depends(get_current_user), db=Depends(get_db)):
    """Return printable, role-aware analytics for registered research.

    The endpoint reports registry metadata, not productivity scores.  It keeps
    restricted records visible only to their owner and Research Office roles.
    """
    rows = list(db.research_projects.find(_visible_research_query(user), {
        "title": 1, "status": 1, "researcher_type": 1, "college_or_unit": 1,
        "start_date": 1, "target_completion_date": 1, "progress_percent": 1,
        "funding_source": 1, "visibility": 1,
    }))
    status_counts = {name: 0 for name in STATUSES}
    type_counts = {name: 0 for name in PEOPLE_TYPES}
    unit_counts: dict[str, int] = {}
    year_counts: dict[str, int] = {}
    active_progress: list[int] = []
    for row in rows:
        status_name = row.get("status", "DRAFT")
        type_name = row.get("researcher_type", "OTHER")
        status_counts[status_name] = status_counts.get(status_name, 0) + 1
        type_counts[type_name] = type_counts.get(type_name, 0) + 1
        unit = row.get("college_or_unit") or "Unspecified unit"
        unit_counts[unit] = unit_counts.get(unit, 0) + 1
        started = _as_date(row.get("start_date"))
        if started:
            year_counts[str(started.year)] = year_counts.get(str(started.year), 0) + 1
        if status_name == "ONGOING":
            active_progress.append(int(row.get("progress_percent") or 0))

    total = len(rows)
    return {
        "generated_at": utcnow(),
        "total_research": total,
        "by_status": status_counts,
        "by_researcher_type": type_counts,
        "by_college_or_unit": [
            {"label": label, "value": value}
            for label, value in sorted(unit_counts.items(), key=lambda item: (-item[1], item[0]))[:10]
        ],
        "by_start_year": [
            {"label": label, "value": value}
            for label, value in sorted(year_counts.items())
        ],
        "completed_rate": round((status_counts.get("COMPLETED", 0) / total) * 100, 1) if total else 0,
        "ongoing_average_progress": round(sum(active_progress) / len(active_progress), 1) if active_progress else 0,
    }


@router.get("/{research_id}")
def get_research(research_id: int, user: dict = Depends(get_current_user), db=Depends(get_db)):
    record = _record_or_404(db, research_id)
    if not _can_view(record, user):
        raise HTTPException(status_code=403, detail="You are not authorized to view this research record")
    return _serialize(record)


@router.put("/{research_id}")
def update_research(research_id: int, payload: ResearchUpdate, user: dict = Depends(get_current_user), db=Depends(get_db)):
    record = _record_or_404(db, research_id)
    if not _can_edit(record, user):
        raise HTTPException(status_code=403, detail="You are not authorized to update this research record")
    values = _validate_values(payload.model_dump(exclude_unset=True))
    if not values:
        return _serialize(record)
    values["updated_at"] = utcnow()
    if values.get("status") == "COMPLETED" and "progress_percent" not in values:
        values["progress_percent"] = 100
    db.research_projects.update_one({"_id": research_id}, {"$set": values})
    return _serialize(_record_or_404(db, research_id))


@router.delete("/{research_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_research(research_id: int, user: dict = Depends(get_current_user), db=Depends(get_db)):
    record = _record_or_404(db, research_id)
    if not _can_edit(record, user):
        raise HTTPException(status_code=403, detail="You are not authorized to delete this research record")
    db.research_projects.update_one({"_id": research_id}, {"$set": {"is_deleted": True, "deleted_at": utcnow(), "updated_at": utcnow()}})
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{research_id}/progress")
def update_progress(research_id: int, payload: ProgressUpdate, user: dict = Depends(get_current_user), db=Depends(get_db)):
    record = _record_or_404(db, research_id)
    if not _can_edit(record, user):
        raise HTTPException(status_code=403, detail="You are not authorized to update progress")
    values = {"progress_percent": payload.progress_percent, "updated_at": utcnow()}
    if payload.status:
        values = _validate_values({**values, "status": payload.status.upper()})
    if payload.milestones is not None:
        values["milestones"] = [item.model_dump() for item in payload.milestones]
    if payload.progress_percent == 100 and not payload.status:
        values["status"] = "COMPLETED"
    update = {"$set": values, "$push": {"progress_updates": {"percent": payload.progress_percent, "note": payload.note.strip(), "updated_by": user["_id"], "updated_at": utcnow()}}}
    db.research_projects.update_one({"_id": research_id}, update)
    return _serialize(_record_or_404(db, research_id))


@router.post("/{research_id}/validate")
def validate_research(research_id: int, user: dict = Depends(get_current_user), db=Depends(get_db)):
    if not _is_admin(user):
        raise HTTPException(status_code=403, detail="Research Office validation is required")
    record = _record_or_404(db, research_id)
    db.research_projects.update_one({"_id": research_id}, {"$set": {"is_validated": True, "validated_by": user["_id"], "validated_at": utcnow(), "updated_at": utcnow()}})
    return _serialize(_record_or_404(db, research_id))


@router.get("/{research_id}/attachments")
def list_attachments(research_id: int, user: dict = Depends(get_current_user), db=Depends(get_db)):
    record = _record_or_404(db, research_id)
    if not _can_view(record, user):
        raise HTTPException(status_code=403, detail="You are not authorized to view attachments")
    bucket = GridFSBucket(db)
    files = bucket.find({"metadata.research_id": research_id}).sort("uploadDate", -1)
    return [_attachment_metadata(file) for file in files]


@router.post("/{research_id}/attachments", status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    research_id: int,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    record = _record_or_404(db, research_id)
    if not _can_edit(record, user):
        raise HTTPException(status_code=403, detail="You are not authorized to upload attachments")
    filename = (file.filename or "").strip()
    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if not filename or suffix not in ALLOWED_UPLOAD_SUFFIXES:
        raise HTTPException(status_code=422, detail="Only PDF, DOC, and DOCX research files can be uploaded")
    data = await file.read(MAX_ATTACHMENT_BYTES + 1)
    if not data:
        raise HTTPException(status_code=422, detail="The selected file is empty")
    if len(data) > MAX_ATTACHMENT_BYTES:
        raise HTTPException(status_code=413, detail="Each attachment must be 10 MB or smaller")
    bucket = GridFSBucket(db)
    file_id = bucket.upload_from_stream(
        filename,
        data,
        metadata={"research_id": research_id, "uploaded_by": user["_id"], "content_type": file.content_type or "application/octet-stream"},
    )
    uploaded = bucket.open_download_stream(file_id)
    return _attachment_metadata(uploaded)


@router.get("/{research_id}/attachments/{attachment_id}")
def download_attachment(research_id: int, attachment_id: str, user: dict = Depends(get_current_user), db=Depends(get_db)):
    record = _record_or_404(db, research_id)
    if not _can_view(record, user):
        raise HTTPException(status_code=403, detail="You are not authorized to download attachments")
    try:
        file_id = ObjectId(attachment_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Attachment not found")
    bucket = GridFSBucket(db)
    try:
        stored = bucket.open_download_stream(file_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Attachment not found")
    if stored.metadata.get("research_id") != research_id:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return Response(
        content=stored.read(),
        media_type=stored.metadata.get("content_type") or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{stored.filename}"'},
    )


@router.delete("/{research_id}/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(research_id: int, attachment_id: str, user: dict = Depends(get_current_user), db=Depends(get_db)):
    record = _record_or_404(db, research_id)
    if not _can_edit(record, user):
        raise HTTPException(status_code=403, detail="You are not authorized to delete attachments")
    try:
        file_id = ObjectId(attachment_id)
        bucket = GridFSBucket(db)
        stored = bucket.open_download_stream(file_id)
        if stored.metadata.get("research_id") != research_id:
            raise HTTPException(status_code=404, detail="Attachment not found")
        bucket.delete(file_id)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{research_id}/recommendations")
def recommendations(research_id: int, user: dict = Depends(get_current_user), db=Depends(get_db)):
    record = _record_or_404(db, research_id)
    if not _can_view(record, user):
        raise HTTPException(status_code=403, detail="You are not authorized to view recommendations")
    terms = _terms(record)
    if not terms:
        return []
    candidates = db.research_opportunities.find({"is_current": True, "status": {"$ne": "CLOSED"}})
    matched = []
    today = date.today()
    for opportunity in candidates:
        deadline = _as_date(opportunity.get("deadline"))
        if deadline and deadline < today:
            continue
        opportunity_text = " ".join([opportunity.get("title", ""), opportunity.get("summary", ""), opportunity.get("organization", "")]).lower()
        overlap = sorted(term for term in terms if re.search(rf"\b{re.escape(term)}\b", opportunity_text))
        if overlap:
            kind = _opportunity_kind(opportunity)
            scope = _opportunity_scope(opportunity)
            days_remaining = (deadline - today).days if deadline else None
            reasons = [f"Matches research terms: {', '.join(overlap[:5])}", f"{scope.title()} {kind.replace('_', ' ').title()}"]
            if days_remaining is not None:
                reasons.append(f"Closes in {days_remaining} day{'s' if days_remaining != 1 else ''}")
            matched.append({
                "id": opportunity["_id"], "title": opportunity.get("title"), "organization": opportunity.get("organization"),
                "category": opportunity.get("category"), "deadline": deadline, "source_url": opportunity.get("source_url"),
                "opportunity_type": kind, "scope": scope, "days_remaining": days_remaining,
                "score": len(overlap), "reasons": reasons,
            })
    return sorted(matched, key=lambda item: (-item["score"], item["title"] or ""))[:10]
