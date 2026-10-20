import os
import random
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
    tags=["Authentication"]
)


def send_email_code(email: str, code: str) -> bool:
    """Dispatches a real verification code to the recipient's email address using SMTP."""
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_pass = os.environ.get("SMTP_PASSWORD", "").strip()
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com").strip()
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))

    if not (smtp_user and smtp_pass):
        print(f"[AUTH EMAIL] SMTP_USER/SMTP_PASSWORD not configured. Code for {email} is: {code}")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Your ResponseGuard Verification Code: {code}"
        msg["From"] = f"ResponseGuard <{smtp_user}>"
        msg["To"] = email

        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 12px; background: #ffffff;">
            <div style="text-align: center; margin-bottom: 20px;">
                <h2 style="color: #4f46e5; margin: 0; font-size: 24px;">ResponseGuard</h2>
                <p style="color: #64748b; font-size: 13px; margin: 4px 0 0 0;">AI Response Validation System</p>
            </div>
            <div style="background: #f8fafc; padding: 24px; border-radius: 10px; text-align: center; border: 1px solid #edf2f7;">
                <p style="margin: 0 0 12px 0; color: #334155; font-size: 15px; font-weight: 500;">Your verification code is:</p>
                <div style="font-size: 34px; font-weight: 800; letter-spacing: 8px; color: #1e293b; background: #ffffff; padding: 14px 24px; border-radius: 8px; border: 2px dashed #cbd5e1; display: inline-block;">
                    {code}
                </div>
                <p style="margin: 16px 0 0 0; color: #94a3b8; font-size: 12px;">This code is valid for 5 minutes. Please do not share it with anyone.</p>
            </div>
        </div>
        """
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [email], msg.as_string())

        print(f"[AUTH EMAIL] Real email sent successfully to {email}")
        return True
    except Exception as exc:
        print(f"[AUTH EMAIL ERROR] Failed to send email to {email}: {exc}")
        return False


def send_sms_code(phone: str, code: str) -> bool:
    """Dispatches real SMS using Twilio or Fast2SMS if API credentials are provided."""
    twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
    twilio_token = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
    twilio_from = os.environ.get("TWILIO_PHONE_NUMBER", "").strip()

    if twilio_sid and twilio_token and twilio_from:
        try:
            import urllib.request
            import urllib.parse
            import base64

            url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
            data = urllib.parse.urlencode({
                "To": phone,
                "From": twilio_from,
                "Body": f"Your ResponseGuard verification code is: {code}. Valid for 5 minutes."
            }).encode("utf-8")

            req = urllib.request.Request(url, data=data, method="POST")
            auth_header = base64.b64encode(f"{twilio_sid}:{twilio_token}".encode("ascii")).decode("ascii")
            req.add_header("Authorization", f"Basic {auth_header}")

            with urllib.request.urlopen(req, timeout=10) as resp:
                print(f"[AUTH SMS] Real Twilio SMS sent to {phone}, status {resp.status}")
                return True
        except Exception as exc:
            print(f"[AUTH SMS ERROR] Twilio failed: {exc}")
            return False

    fast2sms_key = os.environ.get("FAST2SMS_API_KEY", "").strip()
    if fast2sms_key:
        try:
            import urllib.request
            clean_num = "".join(filter(str.isdigit, phone))[-10:]
            url = f"https://www.fast2sms.com/dev/bulkV2?authorization={fast2sms_key}&route=otp&variables_values={code}&flash=0&numbers={clean_num}"
            req = urllib.request.Request(url, headers={"User-Agent": "ResponseGuard"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                print(f"[AUTH SMS] Real Fast2SMS dispatched to {clean_num}")
                return True
        except Exception as exc:
            print(f"[AUTH SMS ERROR] Fast2SMS failed: {exc}")
            return False

    print(f"[AUTH SMS] No SMS gateway configured. Code for {phone} is: {code}")
    return False


class EmailSendOtpRequest(BaseModel):
    email: str = Field(..., min_length=3)


class EmailVerifyOtpRequest(BaseModel):
    email: str = Field(..., min_length=3)
    otp: str = Field(..., min_length=4)
    name: Optional[str] = None


class PhoneSendOtpRequest(BaseModel):
    phone: str = Field(..., min_length=7)


class PhoneVerifyOtpRequest(BaseModel):
    phone: str = Field(..., min_length=7)
    otp: str = Field(..., min_length=4)
    name: Optional[str] = None


class GoogleLoginRequest(BaseModel):
    email: str = Field(..., min_length=3)
    name: Optional[str] = None
    avatar: Optional[str] = None


class GuestLoginRequest(BaseModel):
    guest_id: Optional[str] = None
    name: Optional[str] = None


class CreditActionRequest(BaseModel):
    user_id: int
    amount: int = Field(default=1, ge=1, le=500)


@router.post("/email/send-otp")
def send_email_otp(data: EmailSendOtpRequest):
    email = data.email.strip().lower()
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise HTTPException(status_code=400, detail="Invalid email address format.")

    otp = str(random.randint(100000, 999999))
    save_otp(email, otp, expires_in_sec=300)
    sent_real = send_email_code(email, otp)

    return {
        "status": "success",
        "message": f"Verification code sent to {email}",
        "email": email,
        "sent_real": sent_real,
        "demo_otp": otp if not sent_real else None
    }


@router.post("/email/verify")
def verify_email_otp(data: EmailVerifyOtpRequest):
    email = data.email.strip().lower()
    otp = data.otp.strip()

    if not verify_otp(email, otp):
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification code."
        )

    user = get_or_create_user(
        identifier=email,
        provider="google",
        name=data.name or email.split("@")[0].replace(".", " ").title(),
        avatar=f"https://api.dicebear.com/7.x/bottts/svg?seed={email}"
    )

    return {
        "status": "success",
        "message": "Email verified successfully",
        "user": user
    }


@router.post("/phone/send-otp")
def send_phone_otp(data: PhoneSendOtpRequest):
    clean_phone = re.sub(r"[^\d+]", "", data.phone.strip())
    if len(clean_phone) < 8:
        raise HTTPException(status_code=400, detail="Please enter a valid phone number with country code.")

    otp = str(random.randint(100000, 999999))
    save_otp(clean_phone, otp, expires_in_sec=300)
    sent_real = send_sms_code(clean_phone, otp)

    return {
        "status": "success",
        "message": f"Verification code sent to {clean_phone}",
        "phone": clean_phone,
        "sent_real": sent_real,
        "demo_otp": otp if not sent_real else None
    }


@router.post("/phone/verify")
def verify_phone_otp(data: PhoneVerifyOtpRequest):
    clean_phone = re.sub(r"[^\d+]", "", data.phone.strip())
    otp = data.otp.strip()

    if not verify_otp(clean_phone, otp):
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification code."
        )

    user = get_or_create_user(
        identifier=clean_phone,
        provider="phone",
        name=data.name or f"User {clean_phone[-4:]}",
        avatar=""
    )

    return {
        "status": "success",
        "message": "Phone number verified successfully",
        "user": user
    }


@router.post("/google")
def login_with_google(data: GoogleLoginRequest):
    email = data.email.strip().lower()
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise HTTPException(status_code=400, detail="Invalid email address format.")

    user = get_or_create_user(
        identifier=email,
        provider="google",
        name=data.name,
        avatar=data.avatar
    )
    return {
        "status": "success",
        "message": "Logged in successfully with Google / Gmail",
        "user": user
    }


@router.post("/guest")
def login_guest(data: Optional[GuestLoginRequest] = None):
    guest_id = (data.guest_id if data and data.guest_id else f"guest_{random.randint(1000, 9999)}")
    name = (data.name if data and data.name else "Demo User")

    user = get_or_create_user(
        identifier=guest_id,
        provider="guest",
        name=name,
        avatar=""
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
    new_credits = update_user_credits(data.user_id, -data.amount)
    return {"status": "success", "credits": new_credits}


@router.post("/credits/refill")
def refill_credits(data: CreditActionRequest):
    user = get_user_by_id(data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    new_credits = update_user_credits(data.user_id, data.amount)
    return {"status": "success", "credits": new_credits}
