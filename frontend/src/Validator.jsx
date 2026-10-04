import { useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000/api/evaluation/submit";

function App() {
  const [question, setQuestion] = useState("");
  const [aiResponse, setAiResponse] = useState("");
  const [referenceAnswer, setReferenceAnswer] = useState("");
  const [evidence, setEvidence] = useState("");
  const [referenceFile, setReferenceFile] = useState(null);
  const [uploadingReference, setUploadingReference] = useState(false);

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleReferenceUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setError("");
    setUploadingReference(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        "http://127.0.0.1:8000/api/evaluation/upload-reference",
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail
            ? JSON.stringify(data.detail)
            : `Reference upload failed with status ${response.status}`
        );
      }

      setReferenceFile({ name: data.filename, size: file.size });
      setEvidence(data.text || "");
    } catch (err) {
      console.error(err);
      setReferenceFile(null);
      setEvidence("");
      setError(err.message || "Unable to upload reference document.");
    } finally {
      setUploadingReference(false);
    }
  };

  const validateResponse = async () => {
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
        evidence: evidence.trim()
          ? [
              {
                text: evidence.trim(),
                distance: 0.1,
                index: 1,
              },
            ]
          : [],
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
    setEvidence("");
    setReferenceFile(null);
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
       
      {/* MAIN */}
      <main className="container">

        {/* HERO */}
        <section className="hero">
          <div>
            <span className="eyebrow">AI QUALITY ASSURANCE</span>

            <h2>
               AI Responses Validation System
            </h2>

            <p>
              Compare an AI-generated answer against trusted
              references  
            </p>
          </div>

          <div className="hero-card">
            <div className="hero-card-icon">✓</div>
            <div>
              <strong>Evidence-based validation</strong>
              <span>Semantic + factual analysis</span>
            </div>
          </div>
        </section>

        {/* WORKSPACE */}
        <section className="workspace">

          {/* INPUT PANEL */}
          <div className="panel input-panel">

            <div className="panel-header">
              <div>
                <span className="panel-number">01</span>
                <h3>Response Input</h3>
              </div>

              <button
                className="clear-button"
                onClick={clearAll}
              >
                Clear
              </button>
            </div>

            <div className="field">
              <label>Question</label>

              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Enter the question asked to the AI..."
                rows="3"
                disabled={loading || !!result}
              />
            </div>

            <div className="field">
              <label>AI Response</label>

              <textarea
                value={aiResponse}
                onChange={(e) => setAiResponse(e.target.value)}
                placeholder="Enter the AI-generated response..."
                rows="5"
                disabled={loading || !!result}
              />
            </div>

            <div className="field">
              <label>
                Reference Answer
                <span className="optional">Optional</span>
              </label>

              <textarea
                value={referenceAnswer}
                onChange={(e) =>
                  setReferenceAnswer(e.target.value)
                }
                placeholder="Enter the trusted/reference answer..."
                rows="3"
                disabled={loading || !!result}
              />
            </div>

            <div className="field">
  <label>
    Reference Document
    <span className="optional">Optional</span>
  </label>

  <div className="reference-upload">

    <label
      className={`reference-upload-box ${
        referenceFile ? "has-file" : ""
      }`}
    >
      <div className="upload-icon">
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
        </svg>
      </div>

      <div className="upload-content">
        <strong>
          {uploadingReference
            ? "Uploading document..."
            : referenceFile
            ? referenceFile.name
            : "Upload Reference Document"}
        </strong>

        <span>
          {referenceFile
            ? "Document uploaded successfully"
            : "PDF, DOCX, TXT, CSV, JSON, XLSX"}
        </span>

        {!referenceFile && (
          <small>Click to browse or drop a file here</small>
        )}
      </div>

      {!referenceFile && (
        <div className="upload-arrow">
          →
        </div>
      )}

      <input
        id="reference-document-input"
        type="file"
        accept=".pdf,.docx,.txt,.csv,.json,.xlsx"
        onChange={handleReferenceUpload}
        disabled={uploadingReference || loading || !!result}
        hidden
      />
    </label>

    {referenceFile && (
      <div className="reference-file">
        <span>✓</span>
        <span>{referenceFile.name}</span>

        <button
          type="button"
          disabled={loading || !!result}
          onClick={() => {
            setReferenceFile(null);
            setEvidence("");
          }}
        >
          Remove
        </button>
      </div>
    )}

  </div>
</div>
            {error && (
              <div className="error-box">
                <span>⚠</span>
                <div>
                  <strong>Validation Error</strong>
                  <p>{error}</p>
                </div>
              </div>
            )}

            <button
              className="validate-button"
              onClick={validateResponse}
              disabled={loading || !!result}
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  Analyzing response...
                </>
              ) : result ? (
                <>
                  Response Validated
                  <span>✓</span>
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
                <span className="panel-number">02</span>
                <h3>Validation Result</h3>
              </div>
            </div>

            {!result && !loading && (
              <div className="empty-state">
                <div className="empty-icon">✦</div>

                <h3>Ready to analyze</h3>

                <p>
                  Submit an AI response to see its factual
                  accuracy, semantic similarity and evidence
                  analysis.
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

            {loading && (
              <div className="loading-state">
                <div className="loader"></div>

                <h3>Analyzing response</h3>

                <p>
                  Comparing response with reference and
                  retrieved evidence...
                </p>
              </div>
            )}

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
                    <span>VERDICT</span>

                    <h2>{result.verdict}</h2>

                    <p>
                      {result.verdict === "CORRECT" &&
                        "The response is supported by the reference information."}

                      {result.verdict ===
                        "PARTIALLY CORRECT" &&
                        "The response contains the expected fact but does not fully answer the question."}

                      {result.verdict === "INCORRECT" &&
                        "The response contradicts the expected information."}
                    </p>
                  </div>

                  <div className="score">
                    <strong>
                      {Math.round((result.score || 0) * 100)}
                    </strong>
                    <span>Score</span>
                  </div>
                </div>

                {/* METRICS */}
                <div className="metrics">

                  <div className="metric">
                    <span>
                      {result.reference_similarity != null
                        ? "Reference Similarity"
                        : "Document Similarity"}
                    </span>
                    <strong>
                      {result.reference_similarity != null
                        ? (result.reference_similarity * 100).toFixed(1)
                        : result.best_evidence_similarity != null
                        ? (result.best_evidence_similarity * 100).toFixed(1)
                        : "—"}
                      %
                    </strong>
                  </div>

                  <div className="metric">
                    <span>Best Evidence</span>
                    <strong>
                      {result.best_evidence_similarity != null
                        ? (
                            result.best_evidence_similarity * 100
                          ).toFixed(1)
                        : "—"}
                      %
                    </strong>
                  </div>

                  <div className="metric">
                    <span>Expected Fact</span>
                    <strong className="fact">
                      {result.expected_fact ||
                         result.evidence_scores?.[0]?.text?.split(/[.!?]/)[0] ||
                       "—"}
                    </strong>
                  </div>

                  <div className="metric">
                    <span>Contradiction</span>
                    <strong>
                      {result.direct_fact_contradiction
                        ? "Detected"
                        : "None"}
                    </strong>
                  </div>
                </div>

               {/* FACT / EVIDENCE ANALYSIS */}
<div className="analysis-card">

  <div className="analysis-title">
    <h4>
      {result.reference_similarity != null
        ? "Fact Analysis"
        : "Evidence Analysis"}
    </h4>
    <span>Validation engine</span>
  </div>

  <div className="analysis-row">
    <span>Evidence support</span>

    <b className="yes">
      {result.best_evidence_similarity != null
        ? `${(result.best_evidence_similarity * 100).toFixed(1)}%`
        : "—"}
    </b>
  </div>

  <div className="analysis-row">
    <span>Direct contradiction</span>

    <b className={result.direct_fact_contradiction ? "no" : "yes"}>
      {result.direct_fact_contradiction ? "YES" : "NO"}
    </b>
  </div>

  <div className="analysis-row">
    <span>
      {result.reference_similarity != null
        ? "Reference exact match"
        : "Reference answer"}
    </span>

    <b>
      {result.reference_similarity != null
        ? (result.reference_exact_match ? "YES" : "NO")
        : "Not provided"}
    </b>
  </div>

  <div className="probabilities">

    <div>
      <span>Supported</span>
      <strong>
        {result.best_evidence_similarity != null
          ? `${(result.best_evidence_similarity * 100).toFixed(1)}%`
          : "—"}
      </strong>
    </div>

    <div>
      <span>Neutral</span>
      <strong>
        {result.best_evidence_similarity != null
          ? `${((1 - result.best_evidence_similarity) * 100).toFixed(1)}%`
          : "—"}
      </strong>
    </div>

    <div>
      <span>Contradiction</span>
      <strong>
        {result.direct_fact_contradiction
          ? "100.0%"
          : "0.0%"}
      </strong>
    </div>

  </div>

</div>
                {/* EVIDENCE */}
                {result.evidence_scores &&
                  result.evidence_scores.length > 0 && (
                    <div className="evidence-card">

                      <div className="analysis-title">
                        <h4>Retrieved Evidence</h4>

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
                              <p>{item.text}</p>

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
            <span className="tech-label">PIPELINE</span>
            <strong>Retrieve → Compare → Validate</strong>
          </div>

          <div className="tech-items">
            <span>Sentence Transformers</span>
            <span>FAISS</span>
            <span>Fact Matching</span>
            <span>Contradiction Detection</span>
          </div>
        </section>

      </main>

      <footer>
        <span>ResponseGuard</span>
        <span>AI Response Validation System</span>
      </footer>
    </div>
  );
}

export default App;