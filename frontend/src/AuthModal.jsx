import { useState } from "react";
import { API_ENDPOINTS } from "./apiConfig";

export default function AuthModal({ isOpen, onClose, onLoginSuccess }) {
  const [activeTab, setActiveTab] = useState("google"); // "google" | "phone" | "guest"
  
  // Google / Email State
  const [googleEmail, setGoogleEmail] = useState("");
  const [googleName, setGoogleName] = useState("");

  // Phone State
  const [phoneCountry, setPhoneCountry] = useState("+91");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [phoneName, setPhoneName] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [otpCode, setOtpCode] = useState("");
  const [hintOtp, setHintOtp] = useState("");

  // Loading & Error States
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!isOpen) return null;

  const handleGoogleSubmit = async (emailOverride, nameOverride) => {
    setError("");
    const emailToUse = (emailOverride || googleEmail).trim();
    const nameToUse = (nameOverride || googleName).trim() || emailToUse.split("@")[0];

    if (!emailToUse || !emailToUse.includes("@")) {
      setError("Please enter a valid Gmail / Google email address.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(API_ENDPOINTS.AUTH_GOOGLE, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: emailToUse,
          name: nameToUse,
          avatar: `https://api.dicebear.com/7.x/bottts/svg?seed=${encodeURIComponent(emailToUse)}`,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Google login failed.");
      }

      onLoginSuccess(data.user);
      onClose();
    } catch (err) {
      console.error(err);
      setError(err.message || "Unable to sign in with Google.");
    } finally {
      setLoading(false);
    }
  };

  const handleSendPhoneOtp = async () => {
    setError("");
    const fullPhone = `${phoneCountry}${phoneNumber.replace(/\D/g, "")}`;
    if (phoneNumber.replace(/\D/g, "").length < 7) {
      setError("Please enter a valid mobile number.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(API_ENDPOINTS.AUTH_PHONE_OTP, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone: fullPhone }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to send verification code.");
      }

      setOtpSent(true);
      setHintOtp(data.demo_otp || "123456");
      setOtpCode(data.demo_otp || "123456"); // Pre-fill convenience for user
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to send SMS code.");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyPhoneOtp = async () => {
    setError("");
    const fullPhone = `${phoneCountry}${phoneNumber.replace(/\D/g, "")}`;
    if (!otpCode || otpCode.trim().length < 4) {
      setError("Please enter the verification code.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(API_ENDPOINTS.AUTH_PHONE_VERIFY, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          phone: fullPhone,
          otp: otpCode.trim(),
          name: phoneName.trim() || `User ${phoneNumber.slice(-4)}`,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Verification failed.");
      }

      onLoginSuccess(data.user);
      onClose();
    } catch (err) {
      console.error(err);
      setError(err.message || "Verification code is incorrect.");
    } finally {
      setLoading(false);
    }
  };

  const handleGuestLogin = async () => {
    setError("");
    setLoading(true);
    try {
      const res = await fetch(API_ENDPOINTS.AUTH_GUEST, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Guest login failed.");
      }

      onLoginSuccess(data.user);
      onClose();
    } catch (err) {
      console.error(err);
      setError(err.message || "Unable to start guest session.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-modal-backdrop" onClick={onClose}>
      <div className="auth-modal-dialog" onClick={(e) => e.stopPropagation()}>
        {/* CLOSE BUTTON */}
        <button className="auth-modal-close" onClick={onClose} aria-label="Close">
          ✕
        </button>

        {/* MODAL HEADER */}
        <div className="auth-modal-header">
          <div className="auth-brand-badge">
            <span className="auth-brand-bolt">⚡</span>
          </div>
          <h2>Access ResponseGuard</h2>
          <p>Sign in to unlock AI response validation with <strong>50 free credits</strong></p>
        </div>

        {/* TABS */}
        <div className="auth-modal-tabs">
          <button
            className={`auth-tab-btn ${activeTab === "google" ? "active" : ""}`}
            onClick={() => { setActiveTab("google"); setError(""); }}
          >
            <svg className="auth-tab-icon" viewBox="0 0 24 24" width="16" height="16">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
            </svg>
            Gmail / Google
          </button>

          <button
            className={`auth-tab-btn ${activeTab === "phone" ? "active" : ""}`}
            onClick={() => { setActiveTab("phone"); setError(""); }}
          >
            <span className="auth-tab-icon">📱</span>
            Phone Number
          </button>

          <button
            className={`auth-tab-btn ${activeTab === "guest" ? "active" : ""}`}
            onClick={() => { setActiveTab("guest"); setError(""); }}
          >
            <span className="auth-tab-icon">🚀</span>
            Instant Demo
          </button>
        </div>

        {/* ERROR NOTIFICATION */}
        {error && <div className="auth-error-banner">⚠️ {error}</div>}

        {/* TAB 1: GOOGLE / GMAIL */}
        {activeTab === "google" && (
          <div className="auth-tab-content">
            <button
              className="google-one-click-btn"
              onClick={() => handleGoogleSubmit("vinod.reddy@gmail.com", "Vinod Reddy")}
              disabled={loading}
            >
              <svg viewBox="0 0 24 24" width="20" height="20">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
              </svg>
              <span>{loading ? "Authenticating..." : "1-Click Sign In with Google"}</span>
            </button>

            <div className="auth-divider">
              <span>or sign in with custom Gmail</span>
            </div>

            <div className="auth-input-group">
              <label>Gmail / Google Email</label>
              <input
                type="email"
                placeholder="e.g. name@gmail.com"
                value={googleEmail}
                onChange={(e) => setGoogleEmail(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleGoogleSubmit()}
              />
            </div>

            <div className="auth-input-group">
              <label>Your Name (Optional)</label>
              <input
                type="text"
                placeholder="e.g. Vinod Reddy"
                value={googleName}
                onChange={(e) => setGoogleName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleGoogleSubmit()}
              />
            </div>

            <button
              className="auth-primary-btn"
              onClick={() => handleGoogleSubmit()}
              disabled={loading || !googleEmail.trim()}
            >
              {loading ? "Signing in..." : "Continue with Gmail ➔"}
            </button>
          </div>
        )}

        {/* TAB 2: PHONE NUMBER + OTP */}
        {activeTab === "phone" && (
          <div className="auth-tab-content">
            {!otpSent ? (
              <>
                <div className="auth-input-group">
                  <label>Mobile Phone Number</label>
                  <div className="phone-input-row">
                    <select
                      value={phoneCountry}
                      onChange={(e) => setPhoneCountry(e.target.value)}
                      className="phone-country-select"
                    >
                      <option value="+91">🇮🇳 +91 (IN)</option>
                      <option value="+1">🇺🇸 +1 (US)</option>
                      <option value="+44">🇬🇧 +44 (UK)</option>
                      <option value="+61">🇦🇺 +61 (AU)</option>
                      <option value="+971">🇦🇪 +971 (AE)</option>
                      <option value="+65">🇸🇬 +65 (SG)</option>
                    </select>
                    <input
                      type="tel"
                      placeholder="9876543210"
                      value={phoneNumber}
                      onChange={(e) => setPhoneNumber(e.target.value)}
                      className="phone-number-field"
                      onKeyDown={(e) => e.key === "Enter" && handleSendPhoneOtp()}
                    />
                  </div>
                </div>

                <div className="auth-input-group">
                  <label>Your Name (Optional)</label>
                  <input
                    type="text"
                    placeholder="e.g. Vinod"
                    value={phoneName}
                    onChange={(e) => setPhoneName(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSendPhoneOtp()}
                  />
                </div>

                <button
                  className="auth-primary-btn"
                  onClick={handleSendPhoneOtp}
                  disabled={loading || phoneNumber.replace(/\D/g, "").length < 7}
                >
                  {loading ? "Sending Code..." : "Send Verification OTP ➔"}
                </button>
              </>
            ) : (
              <>
                <div className="otp-info-banner">
                  <span className="otp-info-icon">📩</span>
                  <div>
                    <div className="otp-info-title">Code sent to {phoneCountry} {phoneNumber}</div>
                    <div className="otp-info-sub">Enter the 6-digit code below to confirm login.</div>
                  </div>
                </div>

                {hintOtp && (
                  <div className="otp-demo-hint">
                    ✨ <strong>Free Instant Code:</strong> <code>{hintOtp}</code> (or <code>123456</code>)
                  </div>
                )}

                <div className="auth-input-group">
                  <label>6-Digit Verification Code</label>
                  <input
                    type="text"
                    maxLength={6}
                    placeholder="123456"
                    className="otp-code-input"
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleVerifyPhoneOtp()}
                    autoFocus
                  />
                </div>

                <button
                  className="auth-primary-btn"
                  onClick={handleVerifyPhoneOtp}
                  disabled={loading || !otpCode.trim()}
                >
                  {loading ? "Verifying..." : "Verify & Start Validating ➔"}
                </button>

                <button
                  className="auth-text-link"
                  onClick={() => { setOtpSent(false); setError(""); }}
                >
                  ← Change phone number
                </button>
              </>
            )}
          </div>
        )}

        {/* TAB 3: INSTANT DEMO GUEST */}
        {activeTab === "guest" && (
          <div className="auth-tab-content guest-tab">
            <div className="guest-hero-card">
              <div className="guest-hero-icon">⚡</div>
              <h3>Instant 50 Evaluation Credits</h3>
              <p>
                No password, email, or verification required. Instantly explore full automated hallucination detection, RAG evidence checking, and PDF exports.
              </p>
            </div>

            <button
              className="auth-primary-btn glow"
              onClick={handleGuestLogin}
              disabled={loading}
            >
              {loading ? "Initializing..." : "Start Instant Demo (+50 Credits) 🚀"}
            </button>
          </div>
        )}

        {/* FOOTER BADGES */}
        <div className="auth-modal-footer">
          <div className="auth-perk">
            <span>⚡</span> 50 Free Credits
          </div>
          <div className="auth-perk">
            <span>🔒</span> 100% Free & Open
          </div>
          <div className="auth-perk">
            <span>🛡️</span> Instant Evaluation
          </div>
        </div>
      </div>
    </div>
  );
}
