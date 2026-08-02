import uuid

from fastapi import APIRouter, Depends, HTTPException

from app import auth, otp, storage
from app.models import LoginRequest, OtpChallenge, OtpSendRequest, OtpVerifyRequest, ProfileUpdate, TokenResponse, User, UserCreate

router = APIRouter(prefix="/auth", tags=["auth"])


def _challenge(email: str, message: str, name: str | None = None) -> OtpChallenge:
    return OtpChallenge(email=email, expires_in_seconds=otp.issue(email, name), message=message)


@router.post("/signup", response_model=OtpChallenge, status_code=201)
def signup(payload: UserCreate):
    existing = [u for u in storage.read_all("users") if u["email"].lower() == payload.email.lower()]
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    storage.append("users", {"id": str(uuid.uuid4()), "name": payload.name, "email": payload.email, "preferred_tags": payload.preferred_tags, "budget_level": payload.budget_level, "bio": "", "avatar_url": None, "favorites": [], "password_hash": auth.hash_password(payload.password)})
    return _challenge(payload.email, "Verification code sent. Enter it to finish creating your account.", payload.name)


@router.post("/login", response_model=OtpChallenge)
def login(payload: LoginRequest):
    user = next((u for u in storage.read_all("users") if u["email"].lower() == payload.email.lower()), None)
    if not user or not auth.verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return _challenge(user["email"], "Verification code sent. Enter it to sign in.", user.get("name"))


@router.post("/send-otp", response_model=OtpChallenge)
def send_otp(payload: OtpSendRequest):
    user = next((u for u in storage.read_all("users") if u["email"].lower() == payload.email.lower()), None)
    if not user: raise HTTPException(status_code=404, detail="Account not found")
    return _challenge(user["email"], "A new verification code has been sent.", user.get("name"))


@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(payload: OtpVerifyRequest):
    user = next((u for u in storage.read_all("users") if u["email"].lower() == payload.email.lower()), None)
    if not user: raise HTTPException(status_code=404, detail="Account not found")
    otp.verify(user["email"], payload.code)
    return TokenResponse(access_token=auth.create_access_token(user["id"]), user=User(**user))


@router.put("/profile", response_model=User)
def update_profile(payload: ProfileUpdate, current_user: dict = Depends(auth.get_current_user)):
    updated = storage.update_by_id("users", current_user["id"], payload.model_dump())
    return User(**updated)


@router.get("/me", response_model=User)
def get_me(current_user: dict = Depends(auth.get_current_user)):
    return current_user
