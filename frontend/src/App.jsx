import { useState, useEffect } from "react";
import Validator from "./Validator";
import Dashboard from "./Dashboard";
import AuthModal from "./AuthModal";
import { API_ENDPOINTS } from "./apiConfig";
import "./App.css";

function App() {
  const [page, setPage] = useState("validator");
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem("responseguard_user");
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState("");

  // Sync user state with localStorage
  useEffect(() => {
    if (user) {
      localStorage.setItem("responseguard_user", JSON.stringify(user));
    } else {
      localStorage.removeItem("responseguard_user");
    }
  }, [user]);

  // Sync fresh profile from backend when user is loaded
  useEffect(() => {
    if (!user?.id) return;
    fetch(`${API_ENDPOINTS.AUTH_ME}?user_id=${user.id}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data?.user) {
          setUser(data.user);
        }
      })
      .catch((err) => console.warn("Failed to fetch fresh user profile:", err));
  }, [user?.id]);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(""), 4000);
  };

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    showToast(`Welcome ${userData.name || "back"}!`);
  };

  const handleLogout = () => {
    setUser(null);
    setUserMenuOpen(false);
    showToast("Signed out successfully.");
  };

  return (
    <div>
      {/* GLOBAL TOAST NOTIFICATION */}
      {toastMessage && (
        <div className="app-global-toast">
          {toastMessage}
        </div>
      )}

      {/* NAVIGATION */}
      <nav className="app-navigation">
        <div className="nav-brand">
          <div className="nav-brand-icon">AI</div>
          <div>
            <strong>ResponseGuard</strong>
            <span>AI Response Validation System</span>
          </div>
        </div>

        <div className="nav-buttons">
          <button
            className={page === "validator" ? "nav-button active" : "nav-button"}
            onClick={() => setPage("validator")}
          >
            Validator
          </button>

          <button
            className={page === "dashboard" ? "nav-button active" : "nav-button"}
            onClick={() => setPage("dashboard")}
          >
            Dashboard
          </button>
        </div>

        {/* RIGHT SIDE: AUTH & USER PROFILE */}
        <div className="nav-actions">
          {user ? (
            <div className="nav-user-container">
              {/* USER PROFILE BUTTON */}
              <div className="nav-user-profile-wrapper">
                <button
                  className="nav-user-profile-btn"
                  onClick={() => setUserMenuOpen((prev) => !prev)}
                >
                  {user.avatar ? (
                    <img src={user.avatar} alt="Avatar" className="user-avatar-img" />
                  ) : (
                    <div className="user-avatar-placeholder">
                      {user.provider === "google"
                        ? "G"
                        : user.provider === "phone"
                        ? "📱"
                        : "👤"}
                    </div>
                  )}
                  <span className="nav-user-name">{user.name || "User"}</span>
                  <span className="nav-caret">▾</span>
                </button>

                {/* USER DROPDOWN MENU */}
                {userMenuOpen && (
                  <div className="nav-user-dropdown" onClick={(e) => e.stopPropagation()}>
                    <div className="user-dropdown-header">
                      <div className="user-dropdown-name">{user.name || "User"}</div>
                      <div className="user-dropdown-sub">
                        {user.email || user.phone || "user@example.com"}
                      </div>
                      <div className="user-dropdown-badge">
                        Logged in via {user.provider === "google" ? "Google / Gmail" : user.provider === "phone" ? "Mobile Phone" : "Demo Guest"}
                      </div>
                    </div>

                    <div className="user-dropdown-divider" />

                    <button className="user-dropdown-logout-btn" onClick={handleLogout}>
                      Sign Out
                    </button>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="nav-guest-actions">
              <button
                className="nav-signin-btn"
                onClick={() => setAuthModalOpen(true)}
              >
                <span>Sign In</span>
              </button>
            </div>
          )}

          <div className="nav-status">
            <span></span>
            System Online
          </div>
        </div>
      </nav>

      {/* AUTH MODAL */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onLoginSuccess={handleLoginSuccess}
      />

      {/* MAIN CONTENT */}
      {page === "validator" ? (
        <Validator
          user={user}
          openAuthModal={() => setAuthModalOpen(true)}
        />
      ) : (
        <main className="dashboard-page">
          <Dashboard />
        </main>
      )}
    </div>
  );
}

export default App;