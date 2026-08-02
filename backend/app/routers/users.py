from fastapi import APIRouter, Depends, HTTPException

from app import storage
from app.auth import get_current_user
from app.models import Destination, FavoriteResponse, User

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/favorites", response_model=list[Destination])
def favorites(user: dict = Depends(get_current_user)):
    saved = set(user.get("favorites", []))
    return [d for d in storage.read_all("destinations") if d["id"] in saved]

@router.post("/favorites/{destination_id}", response_model=FavoriteResponse)
def toggle_favorite(destination_id: str, user: dict = Depends(get_current_user)):
    if not storage.find_by_id("destinations", destination_id): raise HTTPException(status_code=404, detail="Destination not found")
    saved = set(user.get("favorites", [])); favorite = destination_id not in saved
    if favorite: saved.add(destination_id)
    else: saved.discard(destination_id)
    updated = storage.update_by_id("users", user["id"], {"favorites": list(saved)})
    return FavoriteResponse(favorite=favorite, favorites=updated["favorites"])

@router.get("/{user_id}", response_model=User)
def get_user(user_id: str):
    user = storage.find_by_id("users", user_id)
    if not user: raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/{user_id}/itineraries")
def get_user_itineraries(user_id: str):
    return [i for i in storage.read_all("itineraries") if i["user_id"] == user_id]
