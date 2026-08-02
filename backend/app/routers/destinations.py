from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from app import storage
from app.auth import get_current_user, get_optional_user
from app.models import Destination, DestinationReview, LikeResponse, ReviewCreate

router = APIRouter(prefix="/destinations", tags=["destinations"])


def _hydrate(destination: dict, user_id: str | None = None) -> dict:
    reviews = [r for r in storage.read_all("reviews") if r["destination_id"] == destination["id"]]
    likes = [l for l in storage.read_all("destination_likes") if l["destination_id"] == destination["id"]]
    average = sum(r["rating"] for r in reviews) / len(reviews) if reviews else destination["rating"]
    return {**destination, "rating": round(average, 1), "review_count": len(reviews), "like_count": len(likes), "liked_by_current_user": bool(user_id and any(l["user_id"] == user_id for l in likes))}


@router.get("", response_model=list[Destination])
def search_destinations(q: str | None = None, category: str | None = None, tag: str | None = None, min_rating: float | None = Query(default=None, ge=1, le=5), max_cost_fcfa: int | None = None, user: dict | None = Depends(get_optional_user)):
    results = [_hydrate(d, user["id"] if user else None) for d in storage.read_all("destinations")]
    if q: results = [d for d in results if q.lower() in d["name"].lower() or q.lower() in d["description"].lower()]
    if category: results = [d for d in results if d["category"].lower() == category.lower()]
    if tag: results = [d for d in results if tag.lower() in [t.lower() for t in d.get("tags", [])]]
    if min_rating is not None: results = [d for d in results if d["rating"] >= min_rating]
    if max_cost_fcfa is not None: results = [d for d in results if d["avg_cost_fcfa"] <= max_cost_fcfa]
    return results


@router.get("/{destination_id}", response_model=Destination)
def get_destination(destination_id: str, user: dict | None = Depends(get_optional_user)):
    destination = storage.find_by_id("destinations", destination_id)
    if not destination: raise HTTPException(status_code=404, detail="Destination not found")
    return _hydrate(destination, user["id"] if user else None)


@router.get("/{destination_id}/reviews", response_model=list[DestinationReview])
def reviews(destination_id: str):
    if not storage.find_by_id("destinations", destination_id): raise HTTPException(status_code=404, detail="Destination not found")
    return sorted([r for r in storage.read_all("reviews") if r["destination_id"] == destination_id], key=lambda r: r["created_at"], reverse=True)


@router.post("/{destination_id}/reviews", response_model=DestinationReview, status_code=201)
def create_review(destination_id: str, payload: ReviewCreate, user: dict = Depends(get_current_user)):
    if not storage.find_by_id("destinations", destination_id): raise HTTPException(status_code=404, detail="Destination not found")
    record = {"id": str(uuid.uuid4()), "destination_id": destination_id, "user_id": user["id"], "user_name": user["name"], "rating": payload.rating, "comment": payload.comment, "created_at": datetime.now(timezone.utc).isoformat()}
    storage.append("reviews", record)
    return record


@router.post("/{destination_id}/like", response_model=LikeResponse)
def toggle_like(destination_id: str, user: dict = Depends(get_current_user)):
    if not storage.find_by_id("destinations", destination_id): raise HTTPException(status_code=404, detail="Destination not found")
    likes = storage.read_all("destination_likes")
    existing = next((like for like in likes if like["destination_id"] == destination_id and like["user_id"] == user["id"]), None)
    storage.write_all("destination_likes", [like for like in likes if like is not existing] if existing else likes + [{"destination_id": destination_id, "user_id": user["id"]}])
    count = len([like for like in storage.read_all("destination_likes") if like["destination_id"] == destination_id])
    return LikeResponse(liked=not bool(existing), like_count=count)
