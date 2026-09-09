import React, { useState } from "react";

const API_URL = "http://127.0.0.1:8000/api/evaluation/submit";

function App() {
  const [question, setQuestion] = useState("");
  const [aiResponse, setAiResponse] = useState("");
  const [referenceAnswer, setReferenceAnswer] = useState("");
  const [sourceDocument, setSourceDocument] = useState("");

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const examples = [
    {
      question: "What is photosynthesis?",
      response:
        "Photosynthesis is the process by which green plants use sunlight, water and carbon dioxide to produce glucose and oxygen.",
    },
    {
      question: "What is the boiling point of water?",
      response:
        "Water boils at 100 degrees Celsius at standard atmospheric pressure.",
    },
    {
      question: "Why does ice float on water?",
      response:
        "Ice floats because solid ice is less dense than liquid water. Water expands when it freezes, making ice less dense.",
    },
  ];

  // =========================================================
  // LOAD EXAMPLE
  // =========================================================

  const loadExample = (example) => {
    setQuestion(example.question);
    setAiResponse(example.response);
    setReferenceAnswer("");
    setSourceDocument("");
    setResult(null);
    setError("");

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  // =========================================================
  // SUBMIT EVALUATION
  // =========================================================

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError("");
    setResult(null);

    if (!question.trim()) {
      setError("Please enter a question.");
      return;
    }

    if (!aiResponse.trim()) {
      setError("Please enter the AI response.");
      return;
    }

    setLoading(true);

    try {
      const payload = {
        question: question.trim(),
        ai_response: aiResponse.trim(),
        reference_answer: referenceAnswer.trim() || null,
        source_document: sourceDocument.trim() || null,
      };

      const response = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          errorText || `Evaluation failed (${response.status}).`
        );
      }

      const data = await response.json();

      setResult(data);

      setTimeout(() => {
        document
          .getElementById("evaluation-results")
          ?.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
      }, 100);
    } catch (err) {
      setError(
        err.message ||
          "Unable to connect to the backend. Make sure FastAPI is running."
      );
    } finally {
      setLoading(false);
    }
  };

  // =========================================================
  // CLEAR
  // =========================================================

  const clearAll = () => {
    setQuestion("");
    setAiResponse("");
    setReferenceAnswer("");
    setSourceDocument("");
    setResult(null);
    setError("");

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  // =========================================================
  // SCORE CONVERSION
  // =========================================================

  // Converts a backend 0–1 score to UI 0–100.
  // If backend already gives 0–100, keeps it unchanged.
  const getPercentage = (value) => {
    if (value === null || value === undefined || value === "") {
      return null;
    }

    const number = Number(value);

    if (Number.isNaN(number)) {
      return null;
    }

    if (number >= 0 && number <= 1) {
      return Math.round(number * 100);
    }

    return Math.round(number);
  };

  // =========================================================
  // AGENT SCORE
  // =========================================================

  // M2 agents use a 1–5 scale.
  const getAgentScore = (agent) => {
    if (!agent) {
      return null;
    }

    const value =
      agent.score ??
      agent.final_score ??
      agent.accuracy_score ??
      agent.relevance_score ??
      agent.completeness_score;

    if (value === null || value === undefined || value === "") {
      return null;
    }

    const score = Number(value);

    if (Number.isNaN(score)) {
      return null;
    }

    return Math.max(1, Math.min(5, score));
  };

  // =========================================================
  // SCORE CLASSES
  // =========================================================

  const getScoreClass = (score) => {
    if (score === null || score === undefined) {
      return "neutral";
    }

    if (score >= 80) {
      return "good";
    }

    if (score >= 50) {
      return "medium";
    }

    return "bad";
  };

  const getAgentClass = (score) => {
    if (score === null || score === undefined) {
      return "neutral";
    }

    if (score >= 4) {
      return "good";
    }

    if (score >= 3) {
      return "medium";
    }

    return "bad";
  };

  const getVerdictClass = (verdict) => {
    const value = String(verdict || "").toLowerCase();

    if (value === "correct") {
      return "good";
    }

    if (value.includes("partially")) {
      return "medium";
    }

    if (value.includes("incorrect")) {
      return "bad";
    }

    return "neutral";
  };

  // =========================================================
  // VALIDATION DATA
  // =========================================================

  const validation = result?.validation || {};

  const referenceScore =
    validation.reference_similarity !== undefined &&
    validation.reference_similarity !== null
      ? getPercentage(validation.reference_similarity)
      : null;

  const evidenceScore =
    validation.best_evidence_score !== undefined &&
    validation.best_evidence_score !== null
      ? getPercentage(validation.best_evidence_score)
      : null;

  // IMPORTANT:
  // final_score from backend may be 0–1.
  // getPercentage converts 0.74 → 74.
  const finalScore =
    validation.final_score !== undefined &&
    validation.final_score !== null
      ? getPercentage(validation.final_score)
      : validation.score !== undefined &&
        validation.score !== null
      ? getPercentage(validation.score)
      : validation.overall_score !== undefined &&
        validation.overall_score !== null
      ? getPercentage(validation.overall_score)
      : null;

  // =========================================================
  // M2 RESULTS
  // =========================================================

  const relevance =
    validation.relevance ||
    validation.relevance_result ||
    result?.agent_evaluation?.relevance ||
    null;

  const accuracy =
    validation.accuracy ||
    validation.accuracy_result ||
    result?.agent_evaluation?.accuracy ||
    null;

  const hallucination =
    validation.hallucination ||
    validation.hallucination_result ||
    result?.agent_evaluation?.hallucination ||
    null;

  const completeness =
    validation.completeness ||
    validation.completeness_result ||
    result?.agent_evaluation?.completeness ||
    null;

  const relevanceScore = getAgentScore(relevance);
  const accuracyScore = getAgentScore(accuracy);
  const completenessScore = getAgentScore(completeness);

  const hallucinationDetected =
    hallucination?.detected ??
    hallucination?.hallucination_detected ??
    false;

  const evidence = result?.retrieved_evidence || [];

  // =========================================================
  // UI
  // =========================================================

  return (
    <div className="app">
      <style>{`

        * {
          box-sizing: border-box;
        }

        html {
          scroll-behavior: smooth;
        }

        body {
          margin: 0;
          font-family:
            Inter,
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            sans-serif;
          background: #f5f7fb;
          color: #182033;
        }

        button,
        textarea {
          font-family: inherit;
        }

        button {
          -webkit-tap-highlight-color: transparent;
        }

        .app {
          min-height: 100vh;
          background:
            radial-gradient(
              circle at top left,
              rgba(91, 92, 246, 0.08),
              transparent 32%
            ),
            #f5f7fb;
        }

        /* =====================================================
           HEADER
        ===================================================== */

        .header {
          height: 78px;
          background: rgba(255, 255, 255, 0.97);
          border-bottom: 1px solid #e7eaf1;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 42px;
          position: sticky;
          top: 0;
          z-index: 20;
          backdrop-filter: blur(12px);
        }

        .brand {
          display: flex;
          align-items: center;
          gap: 13px;
        }

        .logo {
          width: 44px;
          height: 44px;
          border-radius: 13px;
          background: #172033;
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 800;
          font-size: 17px;
          box-shadow: 0 6px 18px rgba(23, 32, 51, 0.18);
        }

        .brand-title {
          font-size: 19px;
          font-weight: 800;
        }

        .brand-subtitle {
          margin-top: 2px;
          color: #7d879a;
          font-size: 12px;
        }

        .online {
          display: flex;
          align-items: center;
          gap: 9px;
          color: #687386;
          font-size: 14px;
          font-weight: 600;
        }

        .online-dot {
          width: 9px;
          height: 9px;
          border-radius: 50%;
          background: #37b96b;
          box-shadow:
            0 0 0 5px rgba(55, 185, 107, 0.12);
        }

        /* =====================================================
           MAIN
        ===================================================== */

        .container {
          width: min(1240px, calc(100% - 40px));
          margin: 0 auto;
          padding: 42px 0 70px;
        }

        .hero {
          margin-bottom: 30px;
        }

        .eyebrow {
          color: #5b5cf6;
          font-weight: 800;
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: 1.5px;
          margin-bottom: 9px;
        }

        .hero h1 {
          margin: 0;
          font-size: clamp(30px, 4vw, 44px);
          letter-spacing: -1.5px;
          line-height: 1.1;
        }

        .hero p {
          margin: 12px 0 0;
          color: #697489;
          font-size: 16px;
          max-width: 720px;
          line-height: 1.6;
        }

        .main-grid {
          display: grid;
          grid-template-columns:
            minmax(0, 1.15fr)
            minmax(330px, 0.85fr);
          gap: 24px;
          align-items: start;
        }

        .card {
          background: white;
          border: 1px solid #e7eaf1;
          border-radius: 20px;
          box-shadow:
            0 10px 35px rgba(30, 42, 70, 0.06);
        }

        /* =====================================================
           INPUT
        ===================================================== */

        .input-card {
          padding: 28px;
        }

        .card-title {
          margin: 0;
          font-size: 19px;
          font-weight: 800;
        }

        .card-description {
          color: #7b8598;
          font-size: 13px;
          margin: 7px 0 25px;
        }

        .field {
          margin-bottom: 19px;
        }

        .label-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 8px;
        }

        .label {
          font-size: 13px;
          font-weight: 800;
          color: #253149;
        }

        .required {
          color: #5b5cf6;
          font-size: 11px;
          font-weight: 800;
        }

        .optional {
          color: #9aa3b4;
          font-size: 11px;
          font-weight: 700;
        }

        textarea {
          width: 100%;
          min-height: 112px;
          resize: vertical;
          border: 1px solid #dfe4ee;
          border-radius: 13px;
          outline: none;
          padding: 14px 15px;
          font-size: 14px;
          color: #202a3d;
          background: #fbfcfe;
          transition: 0.2s;
          line-height: 1.55;
        }

        textarea:focus {
          border-color: #7778fa;
          background: white;
          box-shadow:
            0 0 0 4px rgba(91, 92, 246, 0.09);
        }

        textarea::placeholder {
          color: #a4adbd;
        }

        .small-textarea {
          min-height: 92px;
        }

        .actions {
          display: flex;
          gap: 10px;
          margin-top: 8px;
        }

        .analyze-button {
          flex: 1;
          border: 0;
          border-radius: 13px;
          padding: 14px 18px;
          background: #5b5cf6;
          color: white;
          font-size: 14px;
          font-weight: 800;
          cursor: pointer;
          box-shadow:
            0 8px 20px rgba(91, 92, 246, 0.22);
          transition: 0.2s;
        }

        .analyze-button:hover {
          transform: translateY(-1px);
          background: #4e4fe9;
        }

        .analyze-button:disabled {
          opacity: 0.65;
          cursor: not-allowed;
          transform: none;
        }

        .clear-button {
          border: 1px solid #dfe4ee;
          background: white;
          color: #687386;
          border-radius: 13px;
          padding: 14px 18px;
          font-weight: 700;
          cursor: pointer;
        }

        .clear-button:hover {
          background: #f8f9fc;
        }

        /* =====================================================
           EXAMPLES
        ===================================================== */

        .examples-card {
          padding: 25px;
        }

        .examples-title {
          font-weight: 800;
          font-size: 16px;
          margin-bottom: 6px;
        }

        .examples-subtitle {
          color: #8992a3;
          font-size: 12px;
          margin-bottom: 17px;
        }

        .example {
          width: 100%;
          text-align: left;
          border: 1px solid #e8ebf2;
          background: #fafbfe;
          border-radius: 13px;
          padding: 13px;
          margin-bottom: 10px;
          cursor: pointer;
          transition: 0.2s;
        }

        .example:hover {
          border-color: #b9baff;
          background: #f8f8ff;
          transform: translateY(-1px);
        }

        .example-number {
          display: inline-flex;
          width: 25px;
          height: 25px;
          border-radius: 8px;
          align-items: center;
          justify-content: center;
          background: #eeeeff;
          color: #5b5cf6;
          font-size: 11px;
          font-weight: 900;
          margin-right: 8px;
        }

        .example-question {
          font-size: 13px;
          font-weight: 750;
          color: #303b50;
        }

        .features {
          margin-top: 24px;
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 10px;
        }

        .feature {
          border: 1px solid #edf0f5;
          border-radius: 12px;
          padding: 12px;
          background: #fff;
        }

        .feature-icon {
          font-size: 18px;
          margin-bottom: 7px;
        }

        .feature-title {
          font-size: 12px;
          font-weight: 800;
        }

        .feature-text {
          font-size: 11px;
          color: #8a93a5;
          margin-top: 3px;
          line-height: 1.4;
        }

        /* =====================================================
           ERROR
        ===================================================== */

        .error {
          margin-top: 15px;
          border: 1px solid #ffd0d0;
          background: #fff4f4;
          color: #c23939;
          padding: 12px 14px;
          border-radius: 11px;
          font-size: 13px;
          font-weight: 600;
        }

        /* =====================================================
           RESULTS
        ===================================================== */

        .results {
          margin-top: 28px;
          scroll-margin-top: 95px;
        }

        .results-header {
          display: flex;
          justify-content: space-between;
          align-items: end;
          margin-bottom: 17px;
        }

        .results-title {
          margin: 0;
          font-size: 24px;
          font-weight: 850;
        }

        .submission-id {
          font-size: 11px;
          color: #8a94a7;
        }

        .summary {
          display: grid;
          grid-template-columns: 260px 1fr;
          gap: 18px;
          margin-bottom: 18px;
        }

        .score-card {
          padding: 28px;
          text-align: center;
        }

        .score-label {
          font-size: 11px;
          color: #8992a3;
          text-transform: uppercase;
          letter-spacing: 1.2px;
          font-weight: 800;
        }

        .score {
          font-size: 56px;
          font-weight: 900;
          letter-spacing: -3px;
          margin: 8px 0 0;
        }

        .score.good {
          color: #1f9d59;
        }

        .score.medium {
          color: #d78b16;
        }

        .score.bad {
          color: #d64949;
        }

        .score.neutral {
          color: #667085;
        }

        .score-max {
          color: #a0a8b8;
          font-size: 13px;
        }

        .verdict-card {
          padding: 25px;
          display: flex;
          flex-direction: column;
          justify-content: center;
        }

        .verdict-label {
          color: #8992a3;
          font-size: 11px;
          text-transform: uppercase;
          font-weight: 800;
          letter-spacing: 1.1px;
        }

        .verdict {
          font-size: 28px;
          font-weight: 900;
          margin: 7px 0;
        }

        .verdict.good {
          color: #1f9d59;
        }

        .verdict.medium {
          color: #d78b16;
        }

        .verdict.bad {
          color: #d64949;
        }

        .verdict.neutral {
          color: #657084;
        }

        .verdict-description {
          color: #7d8799;
          font-size: 13px;
          line-height: 1.5;
        }

        /* =====================================================
           METRICS
        ===================================================== */

        .metrics {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 14px;
          margin-bottom: 18px;
        }

        .metric {
          padding: 20px;
        }

        .metric-top {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }

        .metric-name {
          font-size: 12px;
          font-weight: 800;
          color: #586276;
        }

        .metric-value {
          font-size: 22px;
          font-weight: 900;
        }

        .metric-value.good {
          color: #1f9d59;
        }

        .metric-value.medium {
          color: #d78b16;
        }

        .metric-value.bad {
          color: #d64949;
        }

        .metric-value.neutral {
          color: #8b94a6;
        }

        .bar {
          height: 7px;
          background: #edf0f5;
          border-radius: 99px;
          overflow: hidden;
        }

        .bar-fill {
          height: 100%;
          border-radius: 99px;
          background: #5b5cf6;
          transition: width 0.4s ease;
        }

        /* =====================================================
           AGENTS
        ===================================================== */

        .agent-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 15px;
          margin-bottom: 18px;
        }

        .agent-card {
          padding: 22px;
        }

        .agent-header {
          display: flex;
          align-items: center;
          gap: 11px;
          margin-bottom: 15px;
        }

        .agent-icon {
          width: 38px;
          height: 38px;
          border-radius: 11px;
          background: #f0f0ff;
          color: #5b5cf6;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 900;
          font-size: 18px;
          flex-shrink: 0;
        }

        .agent-title {
          font-size: 14px;
          font-weight: 850;
        }

        .agent-score {
          margin-left: auto;
          font-size: 21px;
          font-weight: 900;
          white-space: nowrap;
        }

        .agent-score.good {
          color: #1f9d59;
        }

        .agent-score.medium {
          color: #d78b16;
        }

        .agent-score.bad {
          color: #d64949;
        }

        .agent-score.neutral {
          color: #8b94a6;
        }

        .agent-label {
          background: #f8f9fc;
          border-radius: 11px;
          padding: 11px 12px;
          color: #4e5a70;
          font-size: 12px;
          font-weight: 800;
          margin-bottom: 10px;
        }

        .reasoning {
          background: #f8f9fc;
          border-radius: 11px;
          padding: 12px;
          color: #687386;
          font-size: 12px;
          line-height: 1.55;
        }

        .hallucination-status {
          padding: 11px 13px;
          border-radius: 10px;
          font-size: 12px;
          font-weight: 800;
          margin-bottom: 11px;
        }

        .hallucination-safe {
          background: #edf9f2;
          color: #20864f;
        }

        .hallucination-danger {
          background: #fff0f0;
          color: #c53f3f;
        }

        .unavailable {
          background: #f8f9fc;
          color: #8a93a5;
          padding: 12px;
          border-radius: 11px;
          font-size: 12px;
          line-height: 1.5;
        }

        /* =====================================================
           EVIDENCE
        ===================================================== */

        .evidence-card {
          padding: 24px;
        }

        .section-heading {
          margin: 0;
          font-size: 17px;
          font-weight: 850;
        }

        .section-description {
          color: #8a93a4;
          font-size: 12px;
          margin: 5px 0 16px;
        }

        .evidence-item {
          border: 1px solid #e8ebf1;
          background: #fbfcfe;
          border-radius: 12px;
          padding: 14px;
          margin-bottom: 10px;
        }

        .evidence-top {
          display: flex;
          justify-content: space-between;
          gap: 10px;
          margin-bottom: 7px;
        }

        .evidence-number {
          font-size: 11px;
          font-weight: 900;
          color: #5b5cf6;
        }

        .evidence-score {
          font-size: 11px;
          color: #657084;
          font-weight: 800;
          white-space: nowrap;
        }

        .evidence-text {
          color: #4f5a6d;
          font-size: 12px;
          line-height: 1.55;
        }

        /* =====================================================
           EMPTY
        ===================================================== */

        .empty {
          min-height: 380px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          text-align: center;
          padding: 35px;
        }

        .empty-icon {
          width: 72px;
          height: 72px;
          border-radius: 22px;
          background: #f0f0ff;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #5b5cf6;
          font-size: 31px;
          margin-bottom: 20px;
        }

        .empty h2 {
          margin: 0;
          font-size: 21px;
        }

        .empty p {
          color: #8a93a4;
          max-width: 400px;
          line-height: 1.6;
          font-size: 13px;
          margin: 9px 0 0;
        }

        .footer {
          text-align: center;
          color: #9aa2b2;
          font-size: 11px;
          margin-top: 35px;
        }

        /* =====================================================
           RESPONSIVE
        ===================================================== */

        @media (max-width: 900px) {

          .main-grid {
            grid-template-columns: 1fr;
          }

          .summary {
            grid-template-columns: 1fr;
          }

          .metrics {
            grid-template-columns: 1fr 1fr;
          }

        }

        @media (max-width: 600px) {

          .header {
            padding: 0 18px;
          }

          .container {
            width: min(100% - 24px, 1240px);
            padding-top: 28px;
          }

          .online {
            display: none;
          }

          .input-card,
          .examples-card,
          .score-card,
          .verdict-card,
          .agent-card,
          .evidence-card {
            padding: 20px;
          }

          .metrics,
          .agent-grid,
          .features {
            grid-template-columns: 1fr;
          }

          .actions {
            flex-direction: column;
          }

          .results-header {
            align-items: flex-start;
            flex-direction: column;
            gap: 8px;
          }

          .evidence-top {
            flex-direction: column;
          }

        }

      `}</style>

      {/* =====================================================
          HEADER
      ===================================================== */}

      <header className="header">
        <div className="brand">

          <div className="logo">
            AI
          </div>

          <div>

            <div className="brand-title">
              ResponseGuard
            </div>

            <div className="brand-subtitle">
              AI Response Validation System
            </div>

          </div>

        </div>

        <div className="online">
          <span className="online-dot"></span>
          System Online
        </div>

      </header>

      <main className="container">

        {/* =====================================================
            HERO
        ===================================================== */}

        <section className="hero">

          <div className="eyebrow">
            AI Evaluation Platform
          </div>

          <h1>
            Validate AI responses with confidence.
          </h1>

          <p>
            Analyze AI-generated answers for relevance,
            factual accuracy, hallucinations, and
            supporting evidence.
          </p>

        </section>

        {/* =====================================================
            INPUT
        ===================================================== */}

        <section className="main-grid">

          <div className="card input-card">

            <h2 className="card-title">
              Evaluate an AI Response
            </h2>

            <p className="card-description">
              Enter the question and AI-generated response
              you want to validate.
            </p>

            <form onSubmit={handleSubmit}>

              {/* QUESTION */}

              <div className="field">

                <div className="label-row">

                  <label className="label">
                    Question
                  </label>

                  <span className="required">
                    REQUIRED
                  </span>

                </div>

                <textarea
                  value={question}
                  onChange={(e) =>
                    setQuestion(e.target.value)
                  }
                  placeholder="Enter the question asked to the AI..."
                />

              </div>

              {/* AI RESPONSE */}

              <div className="field">

                <div className="label-row">

                  <label className="label">
                    AI Response
                  </label>

                  <span className="required">
                    REQUIRED
                  </span>

                </div>

                <textarea
                  value={aiResponse}
                  onChange={(e) =>
                    setAiResponse(e.target.value)
                  }
                  placeholder="Enter the AI-generated response..."
                />

              </div>

              {/* REFERENCE ANSWER */}

              <div className="field">

                <div className="label-row">

                  <label className="label">
                    Reference Answer
                  </label>

                  <span className="optional">
                    OPTIONAL
                  </span>

                </div>

                <textarea
                  className="small-textarea"
                  value={referenceAnswer}
                  onChange={(e) =>
                    setReferenceAnswer(e.target.value)
                  }
                  placeholder="Enter the trusted/reference answer..."
                />

              </div>

              {/* SOURCE */}

              <div className="field">

                <div className="label-row">

                  <label className="label">
                    Reference Source / Document
                  </label>

                  <span className="optional">
                    OPTIONAL
                  </span>

                </div>

                <textarea
                  className="small-textarea"
                  value={sourceDocument}
                  onChange={(e) =>
                    setSourceDocument(e.target.value)
                  }
                  placeholder="Paste source document or reference material..."
                />

              </div>

              {error && (
                <div className="error">
                  ⚠ {error}
                </div>
              )}

              <div className="actions">

                <button
                  type="submit"
                  className="analyze-button"
                  disabled={loading}
                >
                  {loading
                    ? "⏳ Analyzing..."
                    : "✨ Analyze Response"}
                </button>

                <button
                  type="button"
                  className="clear-button"
                  onClick={clearAll}
                >
                  Clear
                </button>

              </div>

            </form>

          </div>

          {/* =====================================================
              EXAMPLES
          ===================================================== */}

          <div className="card examples-card">

            <div className="examples-title">
              Try an example
            </div>

            <div className="examples-subtitle">
              Load a sample question and response instantly.
            </div>

            {examples.map((example, index) => (

              <button
                key={example.question}
                type="button"
                className="example"
                onClick={() =>
                  loadExample(example)
                }
              >

                <span className="example-number">
                  {String(index + 1).padStart(2, "0")}
                </span>

                <span className="example-question">
                  {example.question}
                </span>

              </button>

            ))}

            <div className="features">

              <div className="feature">

                <div className="feature-icon">
                  🎯
                </div>

                <div className="feature-title">
                  Relevance
                </div>

                <div className="feature-text">
                  Checks whether the answer addresses
                  the question.
                </div>

              </div>

              <div className="feature">

                <div className="feature-icon">
                  ✓
                </div>

                <div className="feature-title">
                  Accuracy
                </div>

                <div className="feature-text">
                  Checks factual correctness.
                </div>

              </div>

              <div className="feature">

                <div className="feature-icon">
                  🛡
                </div>

                <div className="feature-title">
                  Hallucination
                </div>

                <div className="feature-text">
                  Detects unsupported claims.
                </div>

              </div>

              <div className="feature">

                <div className="feature-icon">
                  📚
                </div>

                <div className="feature-title">
                  Evidence
                </div>

                <div className="feature-text">
                  Shows retrieved supporting information.
                </div>

              </div>

            </div>

          </div>

        </section>

        {/* =====================================================
            RESULTS
        ===================================================== */}

        <section
          className="results"
          id="evaluation-results"
        >

          {!result ? (

            <div className="card empty">

              <div className="empty-icon">
                ✦
              </div>

              <h2>
                Ready to analyze
              </h2>

              <p>
                Submit an AI response to see its validation
                score, relevance, accuracy, hallucination
                detection, and supporting evidence.
              </p>

            </div>

          ) : (

            <>

              {/* RESULT HEADER */}

              <div className="results-header">

                <div>

                  <div className="eyebrow">
                    Evaluation Complete
                  </div>

                  <h2 className="results-title">
                    Evaluation Result
                  </h2>

                </div>

                {result.submission_id && (

                  <div className="submission-id">
                    Submission #{result.submission_id}
                  </div>

                )}

              </div>

              {/* =================================================
                  SUMMARY
              ================================================= */}

              <div className="summary">

                <div className="card score-card">

                  <div className="score-label">
                    Overall Score
                  </div>

                  <div
                    className={`score ${getScoreClass(
                      finalScore
                    )}`}
                  >
                    {finalScore !== null
                      ? finalScore
                      : "—"}
                  </div>

                  <div className="score-max">
                    {finalScore !== null
                      ? "out of 100"
                      : "Score unavailable"}
                  </div>

                </div>

                <div className="card verdict-card">

                  <div className="verdict-label">
                    Final Verdict
                  </div>

                  <div
                    className={`verdict ${getVerdictClass(
                      validation.verdict
                    )}`}
                  >
                    {validation.verdict ||
                      "Evaluation completed"}
                  </div>

                  <div className="verdict-description">
                    The response has been evaluated using
                    the available reference information and
                    retrieved evidence.
                  </div>

                </div>

              </div>

              {/* =================================================
                  METRICS
              ================================================= */}

              <div className="metrics">

                <Metric
                  title="Reference Similarity"
                  score={referenceScore}
                  type="percentage"
                />

                <Metric
                  title="Best Evidence"
                  score={evidenceScore}
                  type="percentage"
                />

                <Metric
                  title="Relevance"
                  score={relevanceScore}
                  type="agent"
                />

                <Metric
                  title="Accuracy"
                  score={accuracyScore}
                  type="agent"
                />

              </div>

              {/* =================================================
                  AGENT RESULTS
              ================================================= */}

              <div className="agent-grid">

                {/* RELEVANCE */}

                <AgentCard
                  icon="🎯"
                  title="Relevance Judge"
                  score={relevanceScore}
                  label={relevance?.label}
                  reasoning={relevance?.reasoning}
                />

                {/* ACCURACY */}

                <AgentCard
                  icon="✓"
                  title="Accuracy Judge"
                  score={accuracyScore}
                  label={accuracy?.label}
                  reasoning={accuracy?.reasoning}
                />

                {/* HALLUCINATION */}

                <div className="card agent-card">

                  <div className="agent-header">

                    <div className="agent-icon">
                      🛡
                    </div>

                    <div className="agent-title">
                      Hallucination Detection
                    </div>

                  </div>

                  <div
                    className={`hallucination-status ${
                      hallucinationDetected
                        ? "hallucination-danger"
                        : "hallucination-safe"
                    }`}
                  >

                    {hallucinationDetected
                      ? "⚠ Hallucination Detected"
                      : "✓ No Hallucination Detected"}

                  </div>

                  {hallucination?.reasoning ? (

                    <div className="reasoning">
                      {hallucination.reasoning}
                    </div>

                  ) : (

                    <div className="reasoning">

                      {hallucinationDetected
                        ? "One or more claims are not sufficiently supported by the available evidence."
                        : "The evaluated claims are supported by the available evidence."}

                    </div>

                  )}

                  {/* CLAIMS */}

                  {Array.isArray(
                    hallucination?.claims
                  ) &&
                    hallucination.claims.length > 0 && (

                      <div style={{ marginTop: 10 }}>

                        {hallucination.claims.map(
                          (claim, index) => (

                            <div
                              key={index}
                              className="reasoning"
                              style={{
                                marginBottom: 8,
                              }}
                            >

                              <strong>
                                Claim {index + 1}
                              </strong>

                              <br />

                              {claim.text ||
                                claim.claim ||
                                "Claim"}

                              {claim.status && (
                                <>
                                  <br />

                                  <strong>
                                    Status:
                                  </strong>{" "}

                                  {claim.status}
                                </>
                              )}

                            </div>

                          )
                        )}

                      </div>

                    )}

                </div>

                {/* COMPLETENESS */}

                <div className="card agent-card">

                  <div className="agent-header">

                    <div className="agent-icon">
                      ☑
                    </div>

                    <div className="agent-title">
                      Completeness Judge
                    </div>

                    {completenessScore !== null && (

                      <div
                        className={`agent-score ${getAgentClass(
                          completenessScore
                        )}`}
                      >
                        {completenessScore} / 5
                      </div>

                    )}

                  </div>

                  {completeness ? (

                    <>

                      {completeness.label && (

                        <div className="agent-label">
                          {completeness.label}
                        </div>

                      )}

                      {completeness.reasoning && (

                        <div className="reasoning">
                          {completeness.reasoning}
                        </div>

                      )}

                    </>

                  ) : (

                    <div className="unavailable">

                      Completeness Agent is not currently
                      connected to the Evaluation
                      Orchestrator.

                    </div>

                  )}

                </div>

              </div>

              {/* =================================================
                  EVIDENCE
              ================================================= */}

              <div className="card evidence-card">

                <h3 className="section-heading">
                  Supporting Evidence
                </h3>

                <p className="section-description">
                  Evidence retrieved from the reference
                  knowledge base.
                </p>

                {evidence.length === 0 ? (

                  <div className="reasoning">
                    No retrieved evidence was returned.
                  </div>

                ) : (

                  evidence.map((item, index) => (

                    <div
                      className="evidence-item"
                      key={index}
                    >

                      <div className="evidence-top">

                        <span className="evidence-number">
                          EVIDENCE {index + 1}
                        </span>

                        <span className="evidence-score">

                          Similarity:{" "}

                          {item.semantic_similarity !==
                            undefined
                            ? `${Math.round(
                                Number(
                                  item.semantic_similarity
                                ) * 100
                              )}%`
                            : "—"}

                        </span>

                      </div>

                      <div className="evidence-text">
                        {item.text ||
                          "No evidence text available."}
                      </div>

                    </div>

                  ))

                )}

              </div>

            </>

          )}

        </section>

        <div className="footer">
          ResponseGuard • AI Response Validation System
        </div>

      </main>

    </div>
  );
}


/* =============================================================
   METRIC COMPONENT
============================================================= */

function Metric({
  title,
  score,
  type = "percentage",
}) {

  if (type === "agent") {

    const percentage =
      score !== null && score !== undefined
        ? Math.round((score / 5) * 100)
        : null;

    const className =
      score === null || score === undefined
        ? "neutral"
        : score >= 4
        ? "good"
        : score >= 3
        ? "medium"
        : "bad";

    return (
      <div className="card metric">

        <div className="metric-top">

          <div className="metric-name">
            {title}
          </div>

          <div
            className={`metric-value ${className}`}
          >
            {score !== null &&
            score !== undefined
              ? `${score}/5`
              : "—"}
          </div>

        </div>

        <div className="bar">

          <div
            className="bar-fill"
            style={{
              width:
                percentage !== null
                  ? `${percentage}%`
                  : "0%",
            }}
          />

        </div>

      </div>
    );
  }

  const className =
    score === null || score === undefined
      ? "neutral"
      : score >= 80
      ? "good"
      : score >= 50
      ? "medium"
      : "bad";

  return (
    <div className="card metric">

      <div className="metric-top">

        <div className="metric-name">
          {title}
        </div>

        <div
          className={`metric-value ${className}`}
        >
          {score !== null &&
          score !== undefined
            ? `${score}%`
            : "—"}
        </div>

      </div>

      <div className="bar">

        <div
          className="bar-fill"
          style={{
            width:
              score !== null &&
              score !== undefined
                ? `${Math.min(
                    Math.max(score, 0),
                    100
                  )}%`
                : "0%",
          }}
        />

      </div>

    </div>
  );
}


/* =============================================================
   AGENT CARD
============================================================= */

function AgentCard({
  icon,
  title,
  score,
  label,
  reasoning,
}) {

  const className =
    score === null || score === undefined
      ? "neutral"
      : score >= 4
      ? "good"
      : score >= 3
      ? "medium"
      : "bad";

  return (
    <div className="card agent-card">

      <div className="agent-header">

        <div className="agent-icon">
          {icon}
        </div>

        <div className="agent-title">
          {title}
        </div>

        <div
          className={`agent-score ${className}`}
        >
          {score !== null &&
          score !== undefined
            ? `${score} / 5`
            : "—"}
        </div>

      </div>

      {label && (

        <div className="agent-label">
          {label}
        </div>

      )}

      {reasoning ? (

        <div className="reasoning">
          {reasoning}
        </div>

      ) : (

        <div className="reasoning">
          Agent reasoning is not available.
        </div>

      )}

    </div>
  );
}

export default App;