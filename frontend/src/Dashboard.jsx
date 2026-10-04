import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend,
} from "recharts";

const API = "http://127.0.0.1:8000/api/dashboard";
const REPORT_API = "http://127.0.0.1:8000/api/report";

const COLORS = ["#22c55e", "#f59e0b", "#ef4444"];

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [batches, setBatches] = useState([]);
  const [detail, setDetail] = useState(null);

  const [filters, setFilters] = useState({
    verdict: "",
    min: "",
    max: "",
    batch: "",
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [exporting, setExporting] = useState(false);

  const load = async () => {
    setLoading(true);
    setError("");

    try {
      const params = new URLSearchParams();

      if (filters.verdict) {
        params.set("verdict", filters.verdict);
      }

      if (filters.min !== "") {
        params.set("min_score", filters.min);
      }

      if (filters.max !== "") {
        params.set("max_score", filters.max);
      }

      if (filters.batch) {
        params.set("batch_id", filters.batch);
      }

      const query = params.toString();

      const summaryResponse = await fetch(
        `${API}/summary${query ? `?${query}` : ""}`
      );

      if (!summaryResponse.ok) {
        throw new Error("Unable to load dashboard summary.");
      }

      const batchesResponse = await fetch(`${API}/batches`);

      if (!batchesResponse.ok) {
        throw new Error("Unable to load evaluation batches.");
      }

      const summary = await summaryResponse.json();
      const batchResult = await batchesResponse.json();

      setData(summary);
      setBatches(Array.isArray(batchResult.batches) ? batchResult.batches : []);
    } catch (err) {
      setError(err.message || "Dashboard loading failed.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [filters]);

  const viewEvaluation = async (id) => {
    try {
      setError("");

      const response = await fetch(`${API}/evaluation/${id}`);

      if (!response.ok) {
        throw new Error("Unable to load evaluation details.");
      }

      const result = await response.json();

      setDetail(result.record || null);
    } catch (err) {
      setError(err.message || "Unable to load evaluation details.");
    }
  };

  const exportPDF = async () => {
    try {
      setExporting(true);
      setError("");

      const batch = filters.batch || "single";

      const response = await fetch(
        `${REPORT_API}/export?batch_id=${encodeURIComponent(batch)}`
      );

      if (!response.ok) {
        throw new Error("Unable to generate PDF report.");
      }

      const blob = await response.blob();

      const url = window.URL.createObjectURL(blob);

      const link = document.createElement("a");

      link.href = url;
      link.download = `AI_Response_Validation_Report_${batch}.pdf`;

      document.body.appendChild(link);

      link.click();

      link.remove();

      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message || "PDF export failed.");
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <>
        <style>{dashboardStyles}</style>

        <div className="dashboard-loading">
          <div className="loading-spinner"></div>
          <div>Loading evaluation dashboard...</div>
        </div>
      </>
    );
  }

  if (error && !data) {
    return (
      <>
        <style>{dashboardStyles}</style>

        <div className="dashboard-error-page">
          <div className="dashboard-error-card">
            <h2>Dashboard Connection Error</h2>

            <p>{error}</p>

            <div className="endpoint-box">
              <strong>Backend endpoint:</strong>
              <br />
              http://127.0.0.1:8000/api/dashboard/summary
              <br />
              <br />

              <strong>Batch endpoint:</strong>
              <br />
              http://127.0.0.1:8000/api/dashboard/batches
            </div>

            <button className="primary-button" onClick={load}>
              ↻ Retry
            </button>
          </div>
        </div>
      </>
    );
  }

  const safeData = data || {};

  const verdictSummary = safeData.verdict_summary || {};

  const dimensions = safeData.average_dimension_scores || {};

  const hallucination = safeData.hallucination_statistics || {};

  const completeness = safeData.completeness_statistics || {};

  const issues = safeData.most_frequent_issues || {};

  const records = Array.isArray(safeData.records)
    ? safeData.records
    : [];

  const batchSummary = Array.isArray(safeData.batch_summary)
    ? safeData.batch_summary
    : [];

  const passCount = Number(verdictSummary.pass?.count || 0);

  const needsCount = Number(
    verdictSummary.needs_improvement?.count || 0
  );

  const failCount = Number(
    verdictSummary.fail?.count || 0
  );

  const passPercentage = Number(
    verdictSummary.pass?.percentage || 0
  );

  const needsPercentage = Number(
    verdictSummary.needs_improvement?.percentage || 0
  );

  const failPercentage = Number(
    verdictSummary.fail?.percentage || 0
  );

  const totalResponses = Number(
    safeData.total_responses || 0
  );

  const averageScore = Number(
    safeData.average_score || 0
  );

  const averageWeightedScore = Number(
    safeData.average_weighted_score || 0
  );

  const verdictChartData = [
    {
      name: "Pass",
      value: passCount,
    },
    {
      name: "Needs Improvement",
      value: needsCount,
    },
    {
      name: "Fail",
      value: failCount,
    },
  ];

  const dimensionChartData = [
    {
      name: "Relevance",
      score: Number(dimensions.relevance || 0),
    },
    {
      name: "Accuracy",
      score: Number(dimensions.accuracy || 0),
    },
    {
      name: "Hallucination",
      score: Number(
        dimensions.hallucination_detection || 0
      ),
    },
    {
      name: "Completeness",
      score: Number(dimensions.completeness || 0),
    },
  ];

  const distribution =
    safeData.dimension_score_distribution || {};

  const scoreDistributionData = [
    {
      range: "1",
      count: Number(distribution["1"] || 0),
    },
    {
      range: "2",
      count: Number(distribution["2"] || 0),
    },
    {
      range: "3",
      count: Number(distribution["3"] || 0),
    },
    {
      range: "4",
      count: Number(distribution["4"] || 0),
    },
    {
      range: "5",
      count: Number(distribution["5"] || 0),
    },
  ];

  const batchChartData = batchSummary.map((batch) => ({
    name: batch.batch_id || "Unknown",
    score: Number(batch.average_score || 0),
  }));

  const issueData = [
    {
      name: "Low Accuracy",
      count: Number(issues.low_accuracy || 0),
    },
    {
      name: "Low Relevance",
      count: Number(issues.low_relevance || 0),
    },
    {
      name: "Incomplete Responses",
      count: Number(
        issues.incomplete_responses || 0
      ),
    },
    {
      name: "Hallucinated Claims",
      count: Number(
        issues.hallucinated_claims || 0
      ),
    },
  ].filter((item) => item.count > 0);

  const hallucinatedResponses = Number(
    hallucination.responses_with_hallucinated_claims || 0
  );

  const unsupportedClaims = Number(
    hallucination.unsupported_claim_frequency || 0
  );

  const contradictoryClaims = Number(
    hallucination.contradictory_claim_frequency || 0
  );

  const missingResponses = Number(
    completeness.responses_with_missing_information || 0
  );

  const missingAspectFrequency =
    Array.isArray(completeness.missing_aspects_frequency)
      ? completeness.missing_aspects_frequency
      : [];

  return (
    <>
      <style>{dashboardStyles}</style>

      <section className="dashboard">

        {/* HEADER */}

        <div className="dashboard-header">

          <div>
            <div className="dashboard-eyebrow">
               EVALUATION SCORING DASHBOARD
            </div>

            <h1>Evaluation Dashboard</h1>

            <p>
              Visual overview of stored evaluation results,
              dimension scores, hallucination statistics,
              completeness issues and batch trends.
            </p>
          </div>

          <div className="dashboard-header-buttons">

            <button
              className="refresh-button"
              onClick={load}
            >
              ↻ Refresh
            </button>

            <button
              className="export-button"
              onClick={exportPDF}
              disabled={exporting}
            >
              {exporting
                ? "Generating PDF..."
                : "Export PDF"}
            </button>

          </div>

        </div>


        {/* ERROR */}

        {error && (
          <div className="dashboard-warning">
            {error}
          </div>
        )}


        {/* FILTERS */}

        <div className="dashboard-controls">

          <select
            value={filters.verdict}
            onChange={(event) =>
              setFilters({
                ...filters,
                verdict: event.target.value,
              })
            }
          >
            <option value="">
              All Verdicts
            </option>

            <option value="CORRECT">
              Pass / Correct
            </option>

            <option value="PARTIALLY CORRECT">
              Needs Improvement
            </option>

            <option value="INCORRECT">
              Fail / Incorrect
            </option>

          </select>


          <input
            type="number"
            placeholder="Min score"
            value={filters.min}
            onChange={(event) =>
              setFilters({
                ...filters,
                min: event.target.value,
              })
            }
          />


          <input
            type="number"
            placeholder="Max score"
            value={filters.max}
            onChange={(event) =>
              setFilters({
                ...filters,
                max: event.target.value,
              })
            }
          />


          <select
            value={filters.batch}
            onChange={(event) =>
              setFilters({
                ...filters,
                batch: event.target.value,
              })
            }
          >

            <option value="">
              All Batches
            </option>

            {batches.map((batch, index) => (
              <option
                key={
                  batch.batch_id ||
                  batch.id ||
                  index
                }
                value={
                  batch.batch_id ||
                  batch.id ||
                  ""
                }
              >
                {batch.batch_id ||
                  batch.id ||
                  `Batch ${index + 1}`}
              </option>
            ))}

          </select>


          <button
            className="clear-button"
            onClick={() =>
              setFilters({
                verdict: "",
                min: "",
                max: "",
                batch: "",
              })
            }
          >
            Clear Filters
          </button>

        </div>


        {/* STAT CARDS */}

        <div className="dashboard-stat-grid">

          <Stat
            title="Total Responses"
            value={totalResponses}
            subtitle="Stored M4 records"
          />

          <Stat
            title="Average Score"
            value={averageScore.toFixed(1)}
            subtitle="Out of 100"
          />

          <Stat
            title="Pass"
            value={passCount}
            subtitle={`${passPercentage.toFixed(1)}%`}
          />

          <Stat
            title="Hallucinated Responses"
            value={hallucinatedResponses}
            subtitle={`${Number(
              hallucination.hallucination_frequency_percentage || 0
            ).toFixed(1)}% of responses`}
          />

        </div>


        {/* EXTRA SCORE INFORMATION */}

        <div className="score-information">

          <div>
            <span>Weighted Average</span>
            <strong>
              {averageWeightedScore.toFixed(2)} / 5
            </strong>
          </div>

          <div>
            <span>Needs Improvement</span>
            <strong>
              {needsCount} ({needsPercentage.toFixed(1)}%)
            </strong>
          </div>

          <div>
            <span>Fail</span>
            <strong>
              {failCount} ({failPercentage.toFixed(1)}%)
            </strong>
          </div>

        </div>


        {/* CHARTS */}

        <div className="dashboard-chart-grid">

          {/* VERDICT */}

          <Chart
            title="Pass / Needs Improvement / Fail"
            subtitle="Verdict distribution"
          >

            <ResponsiveContainer
              width="100%"
              height="100%"
            >

              <PieChart>

                <Pie
                  data={verdictChartData}
                  dataKey="value"
                  nameKey="name"
                  outerRadius={85}
                  label={({ name, value }) =>
                    `${name}: ${value}`
                  }
                >

                  {verdictChartData.map(
                    (_, index) => (
                      <Cell
                        key={index}
                        fill={COLORS[index]}
                      />
                    )
                  )}

                </Pie>

                <Tooltip />

                <Legend />

              </PieChart>

            </ResponsiveContainer>

          </Chart>


          {/* DIMENSIONS */}

          <Chart
            title="Average Dimension Scores"
            subtitle="Average 1–5 scores"
          >

            <ResponsiveContainer
              width="100%"
              height="100%"
            >

              <BarChart
                data={dimensionChartData}
              >

                <CartesianGrid
                  strokeDasharray="3 3"
                />

                <XAxis
                  dataKey="name"
                  tick={{
                    fontSize: 11,
                  }}
                />

                <YAxis
                  domain={[0, 5]}
                  ticks={[
                    0,
                    1,
                    2,
                    3,
                    4,
                    5,
                  ]}
                />

                <Tooltip />

                <Bar
                  dataKey="score"
                  fill="#2563eb"
                  radius={[5, 5, 0, 0]}
                />

              </BarChart>

            </ResponsiveContainer>

          </Chart>


          {/* SCORE DISTRIBUTION */}

          <Chart
            title="Individual Score Distribution"
            subtitle="Dimension scores across evaluations"
          >

            <ResponsiveContainer
              width="100%"
              height="100%"
            >

              <BarChart
                data={scoreDistributionData}
              >

                <CartesianGrid
                  strokeDasharray="3 3"
                />

                <XAxis dataKey="range" />

                <YAxis
                  allowDecimals={false}
                />

                <Tooltip />

                <Bar
                  dataKey="count"
                  fill="#7c3aed"
                  radius={[5, 5, 0, 0]}
                />

              </BarChart>

            </ResponsiveContainer>

          </Chart>


          {/* BATCH TREND */}

          <Chart
            title="Batch Trends"
            subtitle="Average score by batch"
          >

            <ResponsiveContainer
              width="100%"
              height="100%"
            >

              <LineChart
                data={batchChartData}
              >

                <CartesianGrid
                  strokeDasharray="3 3"
                />

                <XAxis dataKey="name" />

                <YAxis
                  domain={[0, 100]}
                />

                <Tooltip />

                <Legend />

                <Line
                  type="monotone"
                  dataKey="score"
                  name="Average Score"
                  stroke="#2563eb"
                  strokeWidth={3}
                  dot={{
                    r: 5,
                  }}
                />

              </LineChart>

            </ResponsiveContainer>

          </Chart>

        </div>


        {/* HALLUCINATION + COMPLETENESS */}

        <div className="dashboard-two-column">

          <div className="dashboard-card">

            <h3>
              Hallucination & Completeness
            </h3>

            <div className="metric-list">

              <MetricRow
                label="Responses with hallucinations"
                value={hallucinatedResponses}
              />

              <MetricRow
                label="Unsupported claims"
                value={unsupportedClaims}
              />

              <MetricRow
                label="Contradictory claims"
                value={contradictoryClaims}
              />

              <MetricRow
                label="Missing/incomplete responses"
                value={missingResponses}
              />

            </div>

          </div>


          <div className="dashboard-card">

            <h3>
              Most Frequent Issues
            </h3>

            {issueData.length > 0 ? (

              <div className="issue-list">

                {issueData.map((item) => (

                  <div
                    className="issue-row"
                    key={item.name}
                  >

                    <span>
                      {item.name}
                    </span>

                    <strong>
                      {item.count}
                    </strong>

                  </div>

                ))}

              </div>

            ) : (

              <div className="empty-message">
                No recurring issues detected.
              </div>

            )}

          </div>

        </div>


        {/* MISSING ASPECTS */}

        {missingAspectFrequency.length > 0 && (

          <div className="dashboard-card">

            <h3>
              Missing Information Frequency
            </h3>

            <div className="issue-list">

              {missingAspectFrequency.map(
                (item, index) => {

                  const name =
                    typeof item === "string"
                      ? item
                      : item.aspect ||
                        item.name ||
                        `Aspect ${index + 1}`;

                  const count =
                    typeof item === "object"
                      ? item.count || 0
                      : 1;

                  return (
                    <div
                      className="issue-row"
                      key={index}
                    >

                      <span>
                        {name}
                      </span>

                      <strong>
                        {count}
                      </strong>

                    </div>
                  );
                }
              )}

            </div>

          </div>

        )}


        {/* BATCH SUMMARY */}

        <div className="dashboard-card">

          <div className="section-title-row">

            <div>
              <h3>
                Evaluation Batches
              </h3>

              <p>
                Stored batch evaluation summaries
              </p>
            </div>

          </div>


          {batchSummary.length > 0 ? (

            <div className="table-wrapper">

              <table className="dashboard-table">

                <thead>

                  <tr>
                    <th>Batch</th>
                    <th>Total</th>
                    <th>Average</th>
                    <th>Correct</th>
                    <th>Partial</th>
                    <th>Incorrect</th>
                  </tr>

                </thead>

                <tbody>

                  {batchSummary.map(
                    (batch, index) => {

                      const correct =
                        Number(
                          batch.verdict_distribution
                            ?.pass?.count || 0
                        );

                      const partial =
                        Number(
                          batch.verdict_distribution
                            ?.needs_improvement
                            ?.count || 0
                        );

                      const incorrect =
                        Number(
                          batch.verdict_distribution
                            ?.fail?.count || 0
                        );

                      return (
                        <tr
                          key={
                            batch.batch_id ||
                            index
                          }
                        >

                          <td>
                            <strong>
                              {batch.batch_id ||
                                `Batch ${index + 1}`}
                            </strong>
                          </td>

                          <td>
                            {Number(
                              batch.total_responses || 0
                            )}
                          </td>

                          <td>
                            <strong>
                              {Number(
                                batch.average_score || 0
                              ).toFixed(1)}
                            </strong>
                          </td>

                          <td className="pass-text">
                            {correct}
                          </td>

                          <td className="partial-text">
                            {partial}
                          </td>

                          <td className="fail-text">
                            {incorrect}
                          </td>

                        </tr>
                      );
                    }
                  )}

                </tbody>

              </table>

            </div>

          ) : (

            <div className="empty-message">
              No batch records available.
            </div>

          )}

        </div>


        {/* DRILL DOWN */}

        <div className="dashboard-card">

          <div className="section-title-row">

            <div>

              <h3>
                Evaluation Records — Drill Down
              </h3>

              <p>
                View individual evaluation results
              </p>

            </div>

          </div>


          {records.length > 0 ? (

            <div className="table-wrapper">

              <table className="dashboard-table">

                <thead>

                  <tr>
                    <th>ID</th>
                    <th>Question</th>
                    <th>Score</th>
                    <th>Verdict</th>
                    <th>Details</th>
                  </tr>

                </thead>

                <tbody>

                  {records.map(
                    (record, index) => {

                      const id =
                        record.id ??
                        record.submission_id ??
                        index;

                      const score =
                        record.score ??
                        record.final_score ??
                        record.weighted_score ??
                        0;

                      const verdict =
                        record.dashboard_verdict ||
                        record.verdict ||
                        "—";

                      return (
                        <tr key={id}>

                          <td>
                            #{id}
                          </td>

                          <td className="question-cell">
                            <button
                          className="question-link"
                          onClick={() => view(record.id || record.submission_id)}
                          title="View evaluation details"
                            >
                          {String(record.question || "-").slice(0, 90)}
                             </button>
                          </td>

                          <td>
                            <strong>
                              {Number(
                                score
                              ).toFixed(1)}
                            </strong>
                          </td>

                          <td>

                            <span
                              className={
                                getVerdictClass(
                                  verdict
                                )
                              }
                            >
                              {verdict}
                            </span>

                          </td>

                          <td>

                            <button
                              className="view-button"
                              onClick={() =>
                                viewEvaluation(id)
                              }
                            >
                              View
                            </button>

                          </td>

                        </tr>
                      );
                    }
                  )}

                </tbody>

              </table>

            </div>

          ) : (

            <div className="empty-message">
              No individual records returned.
            </div>

          )}

        </div>


        {/* DETAIL */}

        {detail && (

          <div className="dashboard-card detail-panel">

            <div className="section-title-row">

              <div>

                <h3>
                  Evaluation #
                  {detail.id ??
                    detail.submission_id}
                  {" "}Details
                </h3>

              </div>

              <button
                className="close-detail"
                onClick={() =>
                  setDetail(null)
                }
              >
                ×
              </button>

            </div>


            <div className="detail-grid">

              <Detail
                label="Relevance"
                value={
                  detail.relevance_score
                }
              />

              <Detail
                label="Accuracy"
                value={
                  detail.accuracy_score
                }
              />

              <Detail
                label="Hallucination"
                value={
                  detail.hallucination_score
                }
              />

              <Detail
                label="Completeness"
                value={
                  detail.completeness_score
                }
              />

            </div>


            <div className="detail-content">

              <div className="detail-item">

                <strong>
                  Question
                </strong>

                <p>
                  {detail.question || "—"}
                </p>

              </div>


              <div className="detail-item">

                <strong>
                  AI Response
                </strong>

                <p>
                  {detail.ai_response || "—"}
                </p>

              </div>


              <div className="detail-item">

                <strong>
                  Verdict
                </strong>

                <p>
                  {detail.dashboard_verdict ||
                    detail.verdict ||
                    "—"}
                </p>

              </div>


              <div className="detail-item">

                <strong>
                  Final Score
                </strong>

                <p>
                  {detail.score ??
                    detail.final_score ??
                    detail.weighted_score ??
                    "—"}
                </p>

              </div>


              <div className="detail-item">

                <strong>
                  Verdict Reasoning
                </strong>

                <p>
                  {detail.verdict_reasoning ||
                    "—"}
                </p>

              </div>

            </div>

          </div>

        )}

      </section>
    </>
  );
}


function Stat({
  title,
  value,
  subtitle,
}) {
  return (
    <div className="stat-card">

      <div className="stat-label">
        {title}
      </div>

      <div className="stat-value">
        {value}
      </div>

      <div className="stat-subtitle">
        {subtitle}
      </div>

    </div>
  );
}


function Chart({
  title,
  subtitle,
  children,
}) {
  return (
    <div className="dashboard-card chart-card">

      <h3>{title}</h3>

      <p className="chart-subtitle">
        {subtitle}
      </p>

      <div className="chart-container">
        {children}
      </div>

    </div>
  );
}


function MetricRow({
  label,
  value,
}) {
  return (
    <div className="metric-row">

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

    </div>
  );
}


function Detail({
  label,
  value,
}) {
  return (
    <div className="detail-box">

      <span>
        {label}
      </span>

      <strong>
        {value ?? "—"} / 5
      </strong>

    </div>
  );
}


function getVerdictClass(verdict) {
  const value =
    String(verdict)
      .toUpperCase()
      .replace("_", " ");

  if (
    value === "CORRECT" ||
    value === "PASS"
  ) {
    return "verdict-badge verdict-pass";
  }

  if (
    value.includes("PARTIAL") ||
    value.includes("NEEDS")
  ) {
    return "verdict-badge verdict-partial";
  }

  if (
    value === "INCORRECT" ||
    value === "FAIL"
  ) {
    return "verdict-badge verdict-fail";
  }

  return "verdict-badge";
}


const dashboardStyles = `
* {
  box-sizing: border-box;
}

.dashboard {
  min-height: 100vh;
  background: #f5f7fb;
  padding: 32px;
  color: #172033;
  font-family:
    Inter,
    ui-sans-serif,
    system-ui,
    -apple-system,
    BlinkMacSystemFont,
    "Segoe UI",
    sans-serif;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
  margin-bottom: 24px;
}

.dashboard-eyebrow {
  font-size: 12px;
  font-weight: 800;
  color: #4f46e5;
  letter-spacing: 1.2px;
  margin-bottom: 8px;
}

.dashboard-header h1 {
  margin: 0;
  font-size: 34px;
  line-height: 1.15;
  font-weight: 800;
  color: #111827;
}

.dashboard-header p {
  margin: 10px 0 0;
  max-width: 850px;
  color: #667085;
  font-size: 14px;
  line-height: 1.6;
}

.dashboard-header-buttons {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

.refresh-button,
.export-button,
.clear-button,
.view-button,
.primary-button {
  border: 0;
  border-radius: 9px;
  cursor: pointer;
  font-weight: 700;
  transition: 0.2s ease;
}

.refresh-button {
  background: white;
  color: #344054;
  border: 1px solid #d0d5dd;
  padding: 11px 17px;
}

.refresh-button:hover {
  background: #f9fafb;
}

.export-button {
  background: #4f46e5;
  color: white;
  padding: 11px 18px;
}

.export-button:hover {
  background: #4338ca;
}

.export-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.dashboard-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  background: white;
  border: 1px solid #e4e7ec;
  border-radius: 14px;
  padding: 15px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(16, 24, 40, 0.04);
}

.dashboard-controls select,
.dashboard-controls input {
  min-height: 40px;
  border: 1px solid #d0d5dd;
  background: white;
  border-radius: 8px;
  padding: 0 12px;
  font-size: 13px;
  color: #344054;
  outline: none;
}

.dashboard-controls select:focus,
.dashboard-controls input:focus {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.clear-button {
  padding: 0 14px;
  background: #f2f4f7;
  color: #344054;
  border: 1px solid #d0d5dd;
}

.clear-button:hover {
  background: #e4e7ec;
}

.dashboard-warning {
  background: #fff7ed;
  color: #9a3412;
  border: 1px solid #fed7aa;
  padding: 12px 15px;
  border-radius: 10px;
  margin-bottom: 18px;
}

.dashboard-stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.stat-card {
  background: white;
  border: 1px solid #e4e7ec;
  border-radius: 14px;
  padding: 20px;
  min-height: 130px;
  box-shadow: 0 2px 8px rgba(16, 24, 40, 0.04);
}

.stat-label {
  color: #667085;
  font-size: 13px;
  font-weight: 600;
}

.stat-value {
  color: #111827;
  font-size: 31px;
  font-weight: 800;
  margin-top: 10px;
}

.stat-subtitle {
  color: #98a2b3;
  font-size: 12px;
  margin-top: 6px;
}

.score-information {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.score-information > div {
  background: #eef2ff;
  border: 1px solid #c7d2fe;
  border-radius: 12px;
  padding: 13px 17px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 15px;
}

.score-information span {
  color: #475467;
  font-size: 13px;
  font-weight: 600;
}

.score-information strong {
  color: #3730a3;
  font-size: 15px;
}

.dashboard-chart-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 18px;
  margin-bottom: 18px;
}

.dashboard-card {
  background: white;
  border: 1px solid #e4e7ec;
  border-radius: 14px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(16, 24, 40, 0.04);
}

.dashboard-card h3 {
  margin: 0;
  font-size: 16px;
  color: #101828;
}

.chart-card {
  min-height: 370px;
}

.chart-subtitle {
  color: #98a2b3;
  font-size: 12px;
  margin: 7px 0 12px;
}

.chart-container {
  height: 280px;
  width: 100%;
}

.dashboard-two-column {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
  margin-bottom: 18px;
}

.metric-list {
  margin-top: 15px;
}

.metric-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 13px 0;
  border-bottom: 1px solid #f2f4f7;
  gap: 20px;
}

.metric-row:last-child {
  border-bottom: 0;
}

.metric-row span {
  color: #475467;
  font-size: 13px;
}

.metric-row strong {
  color: #111827;
  font-size: 15px;
}

.issue-list {
  margin-top: 12px;
}

.issue-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 13px 0;
  border-bottom: 1px solid #f2f4f7;
}

.issue-row:last-child {
  border-bottom: 0;
}

.issue-row span {
  color: #475467;
  font-size: 13px;
}

.issue-row strong {
  background: #eef2ff;
  color: #4338ca;
  min-width: 30px;
  text-align: center;
  padding: 4px 8px;
  border-radius: 20px;
  font-size: 12px;
}

.empty-message {
  color: #98a2b3;
  font-size: 13px;
  padding: 20px 0 5px;
}

.section-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  margin-bottom: 15px;
}

.section-title-row p {
  margin: 5px 0 0;
  color: #98a2b3;
  font-size: 12px;
}

.table-wrapper {
  width: 100%;
  overflow-x: auto;
}

.dashboard-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.dashboard-table th {
  background: #f9fafb;
  color: #667085;
  text-align: left;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 12px;
  border-bottom: 1px solid #e4e7ec;
}

.dashboard-table td {
  padding: 13px 12px;
  border-bottom: 1px solid #f2f4f7;
  color: #475467;
  vertical-align: middle;
}

.dashboard-table tbody tr:hover {
  background: #fafbff;
}

.question-cell {
  max-width: 420px;
}

.pass-text {
  color: #15803d !important;
  font-weight: 700;
}

.partial-text {
  color: #b45309 !important;
  font-weight: 700;
}

.fail-text {
  color: #dc2626 !important;
  font-weight: 700;
}

.verdict-badge {
  display: inline-flex;
  align-items: center;
  padding: 5px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  background: #f2f4f7;
  color: #475467;
}

.verdict-pass {
  background: #dcfce7;
  color: #166534;
}

.verdict-partial {
  background: #fef3c7;
  color: #92400e;
}

.verdict-fail {
  background: #fee2e2;
  color: #991b1b;
}

.view-button {
  background: #eef2ff;
  color: #4338ca;
  padding: 7px 12px;
}

.view-button:hover {
  background: #e0e7ff;
}

.detail-panel {
  margin-top: 18px;
  border-color: #c7d2fe;
}

.close-detail {
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 50%;
  background: #f2f4f7;
  color: #475467;
  font-size: 20px;
  cursor: pointer;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.detail-box {
  background: #f8fafc;
  border: 1px solid #e4e7ec;
  border-radius: 10px;
  padding: 14px;
}

.detail-box span {
  display: block;
  color: #667085;
  font-size: 12px;
  margin-bottom: 7px;
}

.detail-box strong {
  color: #111827;
  font-size: 18px;
}

.detail-content {
  display: grid;
  gap: 14px;
}

.detail-item {
  background: #f9fafb;
  border-radius: 10px;
  padding: 14px;
}

.detail-item strong {
  color: #344054;
  font-size: 12px;
}

.detail-item p {
  margin: 7px 0 0;
  color: #475467;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.dashboard-loading {
  min-height: 70vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  background: #f5f7fb;
  color: #475467;
  font-family: system-ui, sans-serif;
}

.loading-spinner {
  width: 34px;
  height: 34px;
  border: 4px solid #e4e7ec;
  border-top-color: #4f46e5;
  border-radius: 50%;
  animation: dashboard-spin 0.8s linear infinite;
}

@keyframes dashboard-spin {
  to {
    transform: rotate(360deg);
  }
}

.dashboard-error-page {
  min-height: 70vh;
  background: #f5f7fb;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 30px;
  font-family: system-ui, sans-serif;
}

.dashboard-error-card {
  width: min(560px, 100%);
  background: white;
  border: 1px solid #fecaca;
  border-radius: 14px;
  padding: 28px;
  box-shadow: 0 10px 30px rgba(16, 24, 40, 0.08);
}

.dashboard-error-card h2 {
  margin: 0 0 10px;
  color: #991b1b;
}

.dashboard-error-card p {
  color: #475467;
}

.endpoint-box {
  background: #f8fafc;
  border-radius: 8px;
  padding: 14px;
  font-family: monospace;
  font-size: 12px;
  line-height: 1.6;
  margin: 15px 0;
  color: #344054;
}

.primary-button {
  background: #4f46e5;
  color: white;
  padding: 10px 17px;
}

@media (max-width: 1000px) {
  .dashboard-stat-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .dashboard-chart-grid {
    grid-template-columns: 1fr;
  }

  .dashboard-two-column {
    grid-template-columns: 1fr;
  }

  .detail-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 650px) {
  .dashboard {
    padding: 18px;
  }

  .dashboard-header {
    flex-direction: column;
  }

  .dashboard-header-buttons {
    width: 100%;
  }

  .dashboard-header-buttons button {
    flex: 1;
  }

  .dashboard-stat-grid {
    grid-template-columns: 1fr;
  }

  .score-information {
    grid-template-columns: 1fr;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }

  .dashboard-controls {
    flex-direction: column;
  }

  .dashboard-controls select,
  .dashboard-controls input,
  .clear-button {
    width: 100%;
  }
}
`;