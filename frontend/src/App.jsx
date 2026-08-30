import { useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000/api/evaluation/submit";

function App() {
  const [question, setQuestion] = useState("");
  const [aiResponse, setAiResponse] = useState("");
  const [referenceAnswer, setReferenceAnswer] = useState("");
  const [sourceDocument, setSourceDocument] = useState("");

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const validateResponse = async () => {
    setError("");
    setResult(null);

    // Required fields
    if (!question.trim()) {
      setError("Please enter a question.");
      return;
    }

    if (!aiResponse.trim()) {
      setError("Please enter the AI response.");
      return;
    }

    // Reference answer and source document are OPTIONAL.
    // If they are empty, the backend will use retrieved evidence.
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

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail
            ? JSON.stringify(data.detail)
            : `Request failed with status ${response.status}`
        );
      }

      setResult(data.validation || data);
    } catch (err) {
      console.error(err);

      setError(
        err.message ||
          "Unable to connect to the validation server."
      );
    } finally {
      setLoading(false);
    }
  };

  const clearAll = () => {
    setQuestion("");
    setAiResponse("");
    setReferenceAnswer("");
    setSourceDocument("");
    setResult(null);
    setError("");
  };

  const getStatusClass = () => {
    if (!result) return "";

    if (result.verdict === "CORRECT") {
      return "correct";
    }

    if (result.verdict === "PARTIALLY CORRECT") {
      return "partial";
    }

    return "incorrect";
  };

  const getStatusIcon = () => {
    if (!result) return "";

    if (result.verdict === "CORRECT") return "✓";
    if (result.verdict === "PARTIALLY CORRECT") return "!";
    return "×";
  };

  return (
    <div className="app">

      {/* HEADER */}
      <header className="header">
        <div className="brand">
          <div className="brand-icon">AI</div>

          <div>
            <h1>ResponseGuard</h1>
            <p>AI Response Validation System</p>
          </div>
        </div>

        <div className="status">
          <span className="status-dot"></span>
          System Online
        </div>
      </header>

      {/* MAIN */}
      <main className="container">

        {/* HERO */}
        <section className="hero">
          <div>
            <span className="eyebrow">
              AI QUALITY ASSURANCE
            </span>

            <h2>
              Validate AI responses
              <br />
              with confidence.
            </h2>

            <p>
              Compare an AI-generated answer against trusted
              references and retrieved evidence.
            </p>
          </div>

          <div className="hero-card">
            <div className="hero-card-icon">✓</div>

            <div>
              <strong>
                Evidence-based validation
              </strong>

              <span>
                Semantic + factual analysis
              </span>
            </div>
          </div>
        </section>

        {/* WORKSPACE */}
        <section className="workspace">

          {/* INPUT PANEL */}
          <div className="panel input-panel">

            <div className="panel-header">
              <div>
                <span className="panel-number">
                  01
                </span>

                <h3>
                  Response Input
                </h3>
              </div>

              <button
                className="clear-button"
                onClick={clearAll}
              >
                Clear
              </button>
            </div>

            {/* QUESTION */}
            <div className="field">
              <label>
                Question
                <span className="required">
                  Required
                </span>
              </label>

              <textarea
                value={question}
                onChange={(e) =>
                  setQuestion(e.target.value)
                }
                placeholder="Enter the question asked to the AI..."
                rows="3"
              />
            </div>

            {/* AI RESPONSE */}
            <div className="field">
              <label>
                AI Response
                <span className="required">
                  Required
                </span>
              </label>

              <textarea
                value={aiResponse}
                onChange={(e) =>
                  setAiResponse(e.target.value)
                }
                placeholder="Enter the AI-generated response..."
                rows="5"
              />
            </div>

            {/* REFERENCE ANSWER */}
            <div className="field">
              <label>
                Reference Answer
                <span className="optional">
                  Optional
                </span>
              </label>

              <textarea
                value={referenceAnswer}
                onChange={(e) =>
                  setReferenceAnswer(e.target.value)
                }
                placeholder="Enter the trusted/reference answer..."
                rows="3"
              />
            </div>

            {/* SOURCE DOCUMENT */}
            <div className="field">
              <label>
                Reference Source / Document
                <span className="optional">
                  Optional
                </span>
              </label>

              <textarea
                value={sourceDocument}
                onChange={(e) =>
                  setSourceDocument(e.target.value)
                }
                placeholder="Paste source document or reference material..."
                rows="5"
              />
            </div>

            {/* ERROR */}
            {error && (
              <div className="error-box">
                <span>⚠</span>

                <div>
                  <strong>
                    Validation Error
                  </strong>

                  <p>
                    {error}
                  </p>
                </div>
              </div>
            )}

            {/* SUBMIT */}
            <button
              className="validate-button"
              onClick={validateResponse}
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  Analyzing response...
                </>
              ) : (
                <>
                  Validate Response
                  <span>→</span>
                </>
              )}
            </button>

          </div>

          {/* RESULT PANEL */}
          <div className="panel result-panel">

            <div className="panel-header">
              <div>
                <span className="panel-number">
                  02
                </span>

                <h3>
                  Validation Result
                </h3>
              </div>
            </div>

            {/* EMPTY STATE */}
            {!result && !loading && (
              <div className="empty-state">

                <div className="empty-icon">
                  ✦
                </div>

                <h3>
                  Ready to analyze
                </h3>

                <p>
                  Submit an AI response to see its
                  factual accuracy, semantic similarity
                  and evidence analysis.
                </p>

                <div className="analysis-list">

                  <div>
                    <span>01</span>
                    Reference comparison
                  </div>

                  <div>
                    <span>02</span>
                    Direct fact checking
                  </div>

                  <div>
                    <span>03</span>
                    Contradiction detection
                  </div>

                  <div>
                    <span>04</span>
                    Evidence similarity
                  </div>

                </div>

              </div>
            )}

            {/* LOADING */}
            {loading && (
              <div className="loading-state">

                <div className="loader"></div>

                <h3>
                  Analyzing response
                </h3>

                <p>
                  Comparing response with reference
                  and retrieved evidence...
                </p>

              </div>
            )}

            {/* RESULT */}
            {result && !loading && (
              <div className="result-content">

                {/* VERDICT */}
                <div
                  className={`verdict-card ${getStatusClass()}`}
                >

                  <div className="verdict-icon">
                    {getStatusIcon()}
                  </div>

                  <div className="verdict-info">

                    <span>
                      VERDICT
                    </span>

                    <h2>
                      {result.verdict}
                    </h2>

                    <p>
                      {result.verdict === "CORRECT" &&
                        "The response is supported by the available evidence."
                      }

                      {result.verdict ===
                        "PARTIALLY CORRECT" &&
                        "The response contains useful information but may not fully answer the question."
                      }

                      {result.verdict === "INCORRECT" &&
                        "The response contradicts or is not sufficiently supported by the available information."
                      }
                    </p>

                  </div>

                  <div className="score">

                    <strong>
                      {Math.round(
                        (result.score || 0) * 100
                      )}
                    </strong>

                    <span>
                      Score
                    </span>

                  </div>

                </div>

                {/* METRICS */}
                <div className="metrics">

                  <div className="metric">
                    <span>
                      Reference Similarity
                    </span>

                    <strong>
                      {result.reference_similarity != null
                        ? (
                            result.reference_similarity *
                            100
                          ).toFixed(1)
                        : "—"}
                      %
                    </strong>
                  </div>

                  <div className="metric">
                    <span>
                      Best Evidence
                    </span>

                    <strong>
                      {result.best_evidence_similarity != null
                        ? (
                            result.best_evidence_similarity *
                            100
                          ).toFixed(1)
                        : "—"}
                      %
                    </strong>
                  </div>

                  <div className="metric">
                    <span>
                      Expected Fact
                    </span>

                    <strong className="fact">
                      {result.expected_fact || "—"}
                    </strong>
                  </div>

                  <div className="metric">
                    <span>
                      Contradiction
                    </span>

                    <strong>
                      {result.direct_fact_contradiction
                        ? "Detected"
                        : "None"}
                    </strong>
                  </div>

                </div>

                {/* FACT ANALYSIS */}
                <div className="analysis-card">

                  <div className="analysis-title">

                    <h4>
                      Fact Analysis
                    </h4>

                    <span>
                      Validation engine
                    </span>

                  </div>

                  <div className="analysis-row">

                    <span>
                      Direct fact match
                    </span>

                    <b
                      className={
                        result.direct_fact_match
                          ? "yes"
                          : "no"
                      }
                    >
                      {result.direct_fact_match
                        ? "YES"
                        : "NO"}
                    </b>

                  </div>

                  <div className="analysis-row">

                    <span>
                      Direct contradiction
                    </span>

                    <b
                      className={
                        result.direct_fact_contradiction
                          ? "no"
                          : "yes"
                      }
                    >
                      {result.direct_fact_contradiction
                        ? "YES"
                        : "NO"}
                    </b>

                  </div>

                  <div className="analysis-row">

                    <span>
                      Reference exact match
                    </span>

                    <b
                      className={
                        result.reference_exact_match
                          ? "yes"
                          : "no"
                      }
                    >
                      {result.reference_exact_match
                        ? "YES"
                        : "NO"}
                    </b>

                  </div>

                  {result.contradiction && (
                    <div className="probabilities">

                      <div>
                        <span>
                          Entailment
                        </span>

                        <strong>
                          {(
                            (result.contradiction.entailment ||
                              0) * 100
                          ).toFixed(1)}
                          %
                        </strong>
                      </div>

                      <div>
                        <span>
                          Neutral
                        </span>

                        <strong>
                          {(
                            (result.contradiction.neutral ||
                              0) * 100
                          ).toFixed(1)}
                          %
                        </strong>
                      </div>

                      <div>
                        <span>
                          Contradiction
                        </span>

                        <strong>
                          {(
                            (result.contradiction.contradiction ||
                              0) * 100
                          ).toFixed(1)}
                          %
                        </strong>
                      </div>

                    </div>
                  )}

                </div>

                {/* EVIDENCE */}
                {result.evidence_scores &&
                  result.evidence_scores.length > 0 && (
                    <div className="evidence-card">

                      <div className="analysis-title">

                        <h4>
                          Retrieved Evidence
                        </h4>

                        <span>
                          {result.evidence_scores.length} item
                          {result.evidence_scores.length !== 1
                            ? "s"
                            : ""}
                        </span>

                      </div>

                      {result.evidence_scores
                        .slice(0, 3)
                        .map((item, index) => (
                          <div
                            className="evidence-item"
                            key={index}
                          >

                            <div className="evidence-index">
                              {index + 1}
                            </div>

                            <div className="evidence-text">

                              <p>
                                {item.text}
                              </p>

                              <div className="evidence-meta">

                                <span>
                                  Similarity:{" "}
                                  {(
                                    item.similarity * 100
                                  ).toFixed(1)}
                                  %
                                </span>

                                <span>
                                  Distance:{" "}
                                  {item.distance}
                                </span>

                              </div>

                            </div>

                          </div>
                        ))}

                    </div>
                  )}

              </div>
            )}

          </div>

        </section>

        {/* FOOTER INFO */}
        <section className="technology">

          <div>
            <span className="tech-label">
              PIPELINE
            </span>

            <strong>
              Retrieve → Compare → Validate
            </strong>
          </div>

          <div className="tech-items">

            <span>
              Sentence Transformers
            </span>

            <span>
              FAISS
            </span>

            <span>
              Fact Matching
            </span>

            <span>
              Contradiction Detection
            </span>

          </div>

        </section>

      </main>

      <footer>

        <span>
          ResponseGuard
        </span>

        <span>
          AI Response Validation System
        </span>

      </footer>

    </div>
  );
}

export default App;