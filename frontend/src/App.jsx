import { useState } from "react";
import Validator from "./Validator";
import Dashboard from "./Dashboard";
import "./App.css";

function App() {
  const [page, setPage] = useState("validator");

  return (
    <div>
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

        <div className="nav-status">
          <span></span>
          System Online
        </div>
      </nav>

      {page === "validator" ? (
        <Validator />
      ) : (
        <main className="dashboard-page">
          <Dashboard />
        </main>
      )}
    </div>
  );
}

export default App;