import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app import auth, otp, storage
from app.models import LoginRequest, OtpChallenge, OtpSendRequest, OtpVerifyRequest, ProfileUpdate, TokenResponse, User, UserCreate

router = APIRouter(prefix="/auth", tags=["auth"])


def _challenge(background_tasks: BackgroundTasks, email: str, message: str, name: str | None = None) -> OtpChallenge:
    code = otp.issue(email)
    background_tasks.add_task(otp.send_otp_email, email, code, name)
    return OtpChallenge(email=email, expires_in_seconds=300, message=message)


@router.post("/signup", response_model=OtpChallenge, status_code=200)
def signup(payload: UserCreate, background_tasks: BackgroundTasks):
    existing = [u for u in storage.read_all("users") if u["email"].lower() == payload.email.lower()]
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    storage.append("users", {"id": str(uuid.uuid4()), "name": payload.name, "email": payload.email, "preferred_tags": payload.preferred_tags, "budget_level": payload.budget_level, "bio": "", "avatar_url": None, "favorites": [], "is_verified": False, "password_hash": auth.hash_password(payload.password)})
    return _challenge(background_tasks, payload.email, "Verification code sent. Enter it to finish creating your account.", payload.name)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    user = next((u for u in storage.read_all("users") if u["email"].lower() == payload.email.lower()), None)
    if not user or not auth.verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    # Accounts created before email verification was introduced are treated as
    # verified so existing users can continue to sign in without disruption.
    if not user.get("is_verified", True):
        raise HTTPException(status_code=403, detail="Verify your email to activate your account")
    return TokenResponse(access_token=auth.create_access_token(user["id"]), user=User(**user))


@router.post("/send-otp", response_model=OtpChallenge)
def send_otp(payload: OtpSendRequest, background_tasks: BackgroundTasks):
    user = next((u for u in storage.read_all("users") if u["email"].lower() == payload.email.lower()), None)
    if not user: raise HTTPException(status_code=404, detail="Account not found")
    if user.get("is_verified", True):
        raise HTTPException(status_code=409, detail="This account is already verified")
    return _challenge(background_tasks, user["email"], "A new verification code has been sent.", user.get("name"))


@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(payload: OtpVerifyRequest):
    user = next((u for u in storage.read_all("users") if u["email"].lower() == payload.email.lower()), None)
    if not user: raise HTTPException(status_code=404, detail="Account not found")
    if user.get("is_verified", True):
        raise HTTPException(status_code=409, detail="This account is already verified")
    otp.verify(user["email"], payload.code)
    verified_user = storage.update_by_id("users", user["id"], {"is_verified": True})
    return TokenResponse(access_token=auth.create_access_token(user["id"]), user=User(**verified_user))


@router.put("/profile", response_model=User)
def update_profile(payload: ProfileUpdate, current_user: dict = Depends(auth.get_current_user)):
    updated = storage.update_by_id("users", current_user["id"], payload.model_dump())
    return User(**updated)


@router.get("/me", response_model=User)
def get_me(current_user: dict = Depends(auth.get_current_user)):
    return current_user
