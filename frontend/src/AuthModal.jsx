import { useState } from "react";
import { API_ENDPOINTS } from "./apiConfig";

export default function AuthModal({ isOpen, onClose, onLoginSuccess }) {
  const [activeTab, setActiveTab] = useState("both"); // "both" | "email" | "phone" | "guest"
  
  // Email State
  const [email, setEmail] = useState("");
  const [emailName, setEmailName] = useState("");
  const [emailOtpSent, setEmailOtpSent] = useState(false);
  const [emailOtpCode, setEmailOtpCode] = useState("");
  const [emailHintOtp, setEmailHintOtp] = useState("");
  const [emailSentReal, setEmailSentReal] = useState(false);

  // Phone State
  const [phoneCountry, setPhoneCountry] = useState("+91");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [phoneName, setPhoneName] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [otpCode, setOtpCode] = useState("");
  const [hintOtp, setHintOtp] = useState("");
  const [phoneSentReal, setPhoneSentReal] = useState(false);

  // Both (Dual) State
  const [bothOtpSent, setBothOtpSent] = useState(false);
  const [bothOtpCode, setBothOtpCode] = useState("");
  const [bothHintOtp, setBothHintOtp] = useState("");
  const [bothSentReal, setBothSentReal] = useState(false);

  // Loading & Error States
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!isOpen) return null;

  // DUAL (BOTH EMAIL & PHONE) FLOW
  const handleSendDualOtp = async () => {
    setError("");
    const cleanEmail = email.trim().toLowerCase();
    const cleanNumber = phoneNumber.replace(/\D/g, "");
    const fullPhone = cleanNumber.length >= 7 ? `${phoneCountry}${cleanNumber}` : null;

    if (!cleanEmail || !cleanEmail.includes("@")) {
      setError("Please enter a valid email address.");
      return;
    }
    if (!fullPhone) {
      setError("Please enter a valid mobile number.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(API_ENDPOINTS.AUTH_DUAL_OTP, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: cleanEmail, phone: fullPhone }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to dispatch verification codes.");
      }

      setBothOtpSent(true);
      setBothSentReal(Boolean(data.sent_real));
      setBothHintOtp(data.demo_otp || "");
      if (!data.sent_real && data.demo_otp) {
        setBothOtpCode(data.demo_otp);
      } else {
        setBothOtpCode("");
      }
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to dispatch verification codes.");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyDualOtp = async () => {
    setError("");
    const cleanEmail = email.trim().toLowerCase();
    const cleanNumber = phoneNumber.replace(/\D/g, "");
    const fullPhone = `${phoneCountry}${cleanNumber}`;

    if (!bothOtpCode || bothOtpCode.trim().length < 4) {
      setError("Please enter the 6-digit verification code received on your phone or email.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(API_ENDPOINTS.AUTH_DUAL_VERIFY, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: cleanEmail,
          phone: fullPhone,
          otp: bothOtpCode.trim(),
          name: emailName.trim() || cleanEmail.split("@")[0].replace(".", " "),
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Invalid or expired verification code.");
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

  // EMAIL ONLY FLOW
  const handleSendEmailOtp = async () => {
    setError("");
    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail || !cleanEmail.includes("@")) {
      setError("Please enter a valid email address.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(API_ENDPOINTS.AUTH_EMAIL_OTP, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: cleanEmail }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to send verification code to email.");
      }

      setEmailOtpSent(true);
      setEmailSentReal(Boolean(data.sent_real));
      setEmailHintOtp(data.demo_otp || "");
      if (!data.sent_real && data.demo_otp) {
        setEmailOtpCode(data.demo_otp);
      } else {
        setEmailOtpCode("");
      }
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to send verification code.");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyEmailOtp = async () => {
    setError("");
    const cleanEmail = email.trim().toLowerCase();
    if (!emailOtpCode || emailOtpCode.trim().length < 4) {
      setError("Please enter the 6-digit verification code sent to your email.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(API_ENDPOINTS.AUTH_EMAIL_VERIFY, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: cleanEmail,
          otp: emailOtpCode.trim(),
          name: emailName.trim() || cleanEmail.split("@")[0].replace(".", " "),
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Invalid or expired verification code.");
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

  // PHONE ONLY FLOW
  const handleSendPhoneOtp = async () => {
    setError("");
    const cleanNumber = phoneNumber.replace(/\D/g, "");
    const fullPhone = `${phoneCountry}${cleanNumber}`;
    if (cleanNumber.length < 7) {
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
      setPhoneSentReal(Boolean(data.sent_real));
      setHintOtp(data.demo_otp || "");
      if (!data.sent_real && data.demo_otp) {
        setOtpCode(data.demo_otp);
      } else {
        setOtpCode("");
      }
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to send SMS verification code.");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyPhoneOtp = async () => {
    setError("");
    const cleanNumber = phoneNumber.replace(/\D/g, "");
    const fullPhone = `${phoneCountry}${cleanNumber}`;
    if (!otpCode || otpCode.trim().length < 4) {
      setError("Please enter the 6-digit verification code sent to your phone.");
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
          name: phoneName.trim() || `User ${cleanNumber.slice(-4)}`,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Invalid verification code.");
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

  // INSTANT DEMO FLOW
  const handleGuestLogin = async () => {
    setError("");
    setLoading(true);
    try {
      const res = await fetch(API_ENDPOINTS.AUTH_GUEST, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: "Demo User" }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Guest login failed.");
      }

      onLoginSuccess(data.user);
      onClose();
    } catch (err) {
      console.error(err);
      setError(err.message || "Unable to start demo session.");
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
            <span className="auth-brand-bolt">🛡️</span>
          </div>
          <h2>Access ResponseGuard</h2>
          <p>Get a verification code sent to your mobile phone, email, or both</p>
        </div>

        {/* TABS */}
        <div className="auth-modal-tabs">
          <button
            className={`auth-tab-btn ${activeTab === "both" ? "active" : ""}`}
            onClick={() => { setActiveTab("both"); setError(""); }}
          >
            <span className="auth-tab-icon">📲</span>
            Phone & Email
          </button>

          <button
            className={`auth-tab-btn ${activeTab === "phone" ? "active" : ""}`}
            onClick={() => { setActiveTab("phone"); setError(""); }}
          >
            <span className="auth-tab-icon">📱</span>
            Phone Only
          </button>

          <button
            className={`auth-tab-btn ${activeTab === "email" ? "active" : ""}`}
            onClick={() => { setActiveTab("email"); setError(""); }}
          >
            <span className="auth-tab-icon">✉️</span>
            Email Only
          </button>

          <button
            className={`auth-tab-btn ${activeTab === "guest" ? "active" : ""}`}
            onClick={() => { setActiveTab("guest"); setError(""); }}
          >
            <span className="auth-tab-icon">🚀</span>
            Demo
          </button>
        </div>

        {/* ERROR NOTIFICATION */}
        {error && <div className="auth-error-banner">⚠️ {error}</div>}

        {/* TAB 1: BOTH (PHONE & EMAIL) */}
        {activeTab === "both" && (
          <div className="auth-tab-content">
            {!bothOtpSent ? (
              <>
                <div className="auth-input-group">
                  <label>Mobile Phone Number (SMS)</label>
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
                    />
                  </div>
                </div>

                <div className="auth-input-group">
                  <label>Email Address</label>
                  <input
                    type="email"
                    placeholder="e.g. name@gmail.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>

                <button
                  className="auth-primary-btn"
                  onClick={handleSendDualOtp}
                  disabled={loading || !email.trim() || phoneNumber.replace(/\D/g, "").length < 7}
                >
                  {loading ? "Sending Code..." : "Send Verification Code to Both ➔"}
                </button>
              </>
            ) : (
              <>
                <div className={`otp-info-banner ${bothSentReal ? "real-success" : ""}`}>
                  <span className="otp-info-icon">{bothSentReal ? "📲" : "📩"}</span>
                  <div>
                    <div className="otp-info-title">Code Sent to Both Destinations</div>
                    <div className="otp-info-sub">
                      Check your mobile phone SMS ({phoneCountry} {phoneNumber}) and email ({email}).
                    </div>
                  </div>
                </div>

                {!bothSentReal && bothHintOtp && (
                  <div className="otp-demo-hint">
                    ✨ <strong>Gateways unconfigured:</strong> Verification code is <code>{bothHintOtp}</code>
                  </div>
                )}

                <div className="auth-input-group">
                  <label>6-Digit Verification Code</label>
                  <input
                    type="text"
                    maxLength={6}
                    placeholder="123456"
                    className="otp-code-input"
                    value={bothOtpCode}
                    onChange={(e) => setBothOtpCode(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleVerifyDualOtp()}
                    autoFocus
                  />
                </div>

                <button
                  className="auth-primary-btn"
                  onClick={handleVerifyDualOtp}
                  disabled={loading || !bothOtpCode.trim()}
                >
                  {loading ? "Verifying..." : "Verify Code & Sign In ➔"}
                </button>

                <button
                  className="auth-text-link"
                  onClick={() => { setBothOtpSent(false); setError(""); }}
                >
                  ← Edit phone & email
                </button>
              </>
            )}
          </div>
        )}

        {/* TAB 2: PHONE ONLY */}
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
                      autoFocus
                    />
                  </div>
                </div>

                <button
                  className="auth-primary-btn"
                  onClick={handleSendPhoneOtp}
                  disabled={loading || phoneNumber.replace(/\D/g, "").length < 7}
                >
                  {loading ? "Sending SMS..." : "Send Verification Code to Mobile ➔"}
                </button>
              </>
            ) : (
              <>
                <div className={`otp-info-banner ${phoneSentReal ? "real-success" : ""}`}>
                  <span className="otp-info-icon">{phoneSentReal ? "📲" : "📱"}</span>
                  <div>
                    <div className="otp-info-title">
                      {phoneSentReal ? `SMS Sent to ${phoneCountry} ${phoneNumber}` : `Code Dispatched to ${phoneCountry} ${phoneNumber}`}
                    </div>
                    <div className="otp-info-sub">
                      {phoneSentReal
                        ? "Check your mobile phone messages for the 6-digit text."
                        : "To receive real SMS on your phone, set FAST2SMS_API_KEY or TWILIO in Render. For testing now, enter code below."}
                    </div>
                  </div>
                </div>

                {!phoneSentReal && hintOtp && (
                  <div className="otp-demo-hint">
                    ✨ <strong>SMS Gateway unconfigured:</strong> Verification code is <code>{hintOtp}</code>
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
                  {loading ? "Verifying..." : "Verify Code & Sign In ➔"}
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

        {/* TAB 3: EMAIL ONLY */}
        {activeTab === "email" && (
          <div className="auth-tab-content">
            {!emailOtpSent ? (
              <>
                <div className="auth-input-group">
                  <label>Email Address</label>
                  <input
                    type="email"
                    placeholder="e.g. name@gmail.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSendEmailOtp()}
                    autoFocus
                  />
                </div>

                <button
                  className="auth-primary-btn"
                  onClick={handleSendEmailOtp}
                  disabled={loading || !email.trim() || !email.includes("@")}
                >
                  {loading ? "Sending Code..." : "Send Verification Code to Email ➔"}
                </button>
              </>
            ) : (
              <>
                <div className={`otp-info-banner ${emailSentReal ? "real-success" : ""}`}>
                  <span className="otp-info-icon">{emailSentReal ? "✅" : "✉️"}</span>
                  <div>
                    <div className="otp-info-title">
                      {emailSentReal ? `Code Delivered to ${email}` : `Code Dispatched to ${email}`}
                    </div>
                    <div className="otp-info-sub">
                      {emailSentReal
                        ? "Check your inbox (and spam folder) for the 6-digit code."
                        : "To receive real emails, add SMTP credentials in Render. For testing now, enter code below."}
                    </div>
                  </div>
                </div>

                {!emailSentReal && emailHintOtp && (
                  <div className="otp-demo-hint">
                    ✨ <strong>SMTP Gateway unconfigured:</strong> Verification code is <code>{emailHintOtp}</code>
                  </div>
                )}

                <div className="auth-input-group">
                  <label>6-Digit Verification Code</label>
                  <input
                    type="text"
                    maxLength={6}
                    placeholder="123456"
                    className="otp-code-input"
                    value={emailOtpCode}
                    onChange={(e) => setEmailOtpCode(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleVerifyEmailOtp()}
                    autoFocus
                  />
                </div>

                <button
                  className="auth-primary-btn"
                  onClick={handleVerifyEmailOtp}
                  disabled={loading || !emailOtpCode.trim()}
                >
                  {loading ? "Verifying..." : "Verify Code & Sign In ➔"}
                </button>

                <button
                  className="auth-text-link"
                  onClick={() => { setEmailOtpSent(false); setError(""); }}
                >
                  ← Change email address
                </button>
              </>
            )}
          </div>
        )}

        {/* TAB 4: INSTANT DEMO GUEST */}
        {activeTab === "guest" && (
          <div className="auth-tab-content guest-tab">
            <div className="guest-hero-card">
              <div className="guest-hero-icon">🚀</div>
              <h3>Instant Demo Access</h3>
              <p>
                Explore full automated hallucination detection, RAG evidence checking, and PDF exports immediately without verification.
              </p>
            </div>

            <button
              className="auth-primary-btn glow"
              onClick={handleGuestLogin}
              disabled={loading}
            >
              {loading ? "Initializing..." : "Start Instant Demo 🚀"}
            </button>
          </div>
        )}

        {/* FOOTER BADGES */}
        <div className="auth-modal-footer">
          <div className="auth-perk">
            <span>⚡</span> Unlimited Validations
          </div>
          <div className="auth-perk">
            <span>🔒</span> Real OTP Verification
          </div>
          <div className="auth-perk">
            <span>🛡️</span> Instant AI Guard
          </div>
        </div>
      </div>
    </div>
  );
}
