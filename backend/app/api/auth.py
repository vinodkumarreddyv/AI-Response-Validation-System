import random
import re
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app.database import (
    get_or_create_user,
    get_user_by_id,
    update_user_credits,
    save_otp,
    verify_otp,
)

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication & Credits"]
)


class GoogleLoginRequest(BaseModel):
    email: str = Field(..., min_length=3)
    name: Optional[str] = None
    avatar: Optional[str] = None


class PhoneSendOtpRequest(BaseModel):
    phone: str = Field(..., min_length=7)


class PhoneVerifyOtpRequest(BaseModel):
    phone: str = Field(..., min_length=7)
    otp: str = Field(..., min_length=4)
    name: Optional[str] = None


class GuestLoginRequest(BaseModel):
    guest_id: Optional[str] = None
    name: Optional[str] = None


class CreditActionRequest(BaseModel):
    user_id: int
    amount: int = Field(default=1, ge=1, le=500)


@router.post("/google")
def login_with_google(data: GoogleLoginRequest):
    email = data.email.strip().lower()
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise HTTPException(status_code=400, detail="Invalid email address format.")

    user = get_or_create_user(
        identifier=email,
        provider="google",
        name=data.name,
        avatar=data.avatar,
        default_credits=50
    )
    return {
        "status": "success",
        "message": "Logged in successfully with Google / Gmail",
        "user": user
    }


@router.post("/phone/send-otp")
def send_phone_otp(data: PhoneSendOtpRequest):
    clean_phone = re.sub(r"[^\d+]", "", data.phone.strip())
    if len(clean_phone) < 8:
        raise HTTPException(status_code=400, detail="Please enter a valid phone number with country code.")

    # Generate 6-digit OTP code
    otp = str(random.randint(100000, 999999))
    save_otp(clean_phone, otp, expires_in_sec=300)

    return {
        "status": "success",
        "message": f"Verification code sent to {clean_phone}",
        "phone": clean_phone,
        # Returning demo_otp allows 100% free usage and instant testing without requiring paid third-party SMS billing
        "demo_otp": otp
    }


@router.post("/phone/verify")
def verify_phone_otp(data: PhoneVerifyOtpRequest):
    clean_phone = re.sub(r"[^\d+]", "", data.phone.strip())
    otp = data.otp.strip()

    if not verify_otp(clean_phone, otp):
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification code. Use the demo code displayed or 123456."
        )

    user = get_or_create_user(
        identifier=clean_phone,
        provider="phone",
        name=data.name,
        avatar="",
        default_credits=50
    )

    return {
        "status": "success",
        "message": "Phone number verified successfully",
        "user": user
    }


@router.post("/guest")
def login_guest(data: Optional[GuestLoginRequest] = None):
    guest_id = (data.guest_id if data and data.guest_id else f"guest_{random.randint(1000, 9999)}")
    name = (data.name if data and data.name else "Vinod Kumar Reddy")

    user = get_or_create_user(
        identifier=guest_id,
        provider="guest",
        name=name,
        avatar="",
        default_credits=50
    )

    return {
        "status": "success",
        "message": "Logged in as Demo Guest",
        "user": user
    }


@router.get("/me")
def get_current_user(user_id: int = Query(..., description="User ID")):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "status": "success",
        "user": user
    }


@router.post("/credits/use")
def use_credits(data: CreditActionRequest):
    user = get_user_by_id(data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user["credits"] < data.amount:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. Available: {user['credits']}, required: {data.amount}. Please refill credits to continue."
        )

    new_credits = update_user_credits(data.user_id, -data.amount)
    return {
        "status": "success",
        "message": f"{data.amount} credit(s) deducted.",
        "credits": new_credits
    }


@router.post("/credits/refill")
def refill_credits(data: CreditActionRequest):
    user = get_user_by_id(data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_credits = update_user_credits(data.user_id, data.amount)
    return {
        "status": "success",
        "message": f"+{data.amount} free credits added!",
        "credits": new_credits
    }
