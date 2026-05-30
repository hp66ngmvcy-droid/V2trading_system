// Shared UI primitives for TAR

function Badge({ kind, children, pulse }) {
  // kind: KEEP|REVIEW|KILL|QUEUED|RUNNING|COMPLETED|FAILED|SAFE_TO_TEST|CAUTION|HOLD_TRADING|BLOCK_TRADING|neutral
  const map = {
    KEEP: "green", REVIEW: "amber", KILL: "red",
    QUEUED: "neutral", RUNNING: "blue", COMPLETED: "green", FAILED: "red",
    SAFE_TO_TEST: "green", CAUTION: "amber", HOLD_TRADING: "amber", BLOCK_TRADING: "red",
    LONG: "green", SHORT: "red", FLAT: "neutral",
    HIGH: "red", MEDIUM: "amber", LOW: "neutral",
    PASS: "green", WARN: "amber", FAIL: "red",
  };
  const cls = map[kind] || "neutral";
  return (
    <span className={`badge ${cls}`}>
      {pulse && <span className="dotled pulse" />}
      {children || kind}
    </span>
  );
}

function ReasonCode({ code, kind }) {
  const cls = kind === "warn" ? "warn" : kind === "info" ? "info" : "";
  return <code className={`reason-code ${cls}`}>{code}</code>;
}

function Card({ title, right, children, flat, style }) {
  return (
    <div className={`card ${flat ? "flat" : ""}`} style={style}>
      {(title || right) && (
        <div className="card-head">
          <span className="title">{title}</span>
          {right && <span className="right">{right}</span>}
        </div>
      )}
      <div className="card-body">{children}</div>
    </div>
  );
}

function Metric({ label, value, sub, tone, hint }) {
  return (
    <div className={`metric ${tone || ""}`}>
      <div className="label">{label}{hint && <span className="dim" title={hint}>ⓘ</span>}</div>
      <div className={`value ${(typeof value === "string" && value.length > 8) ? "sm" : ""}`}>{value}</div>
      {sub && <div className="sub">{sub}</div>}
    </div>
  );
}

function Progress({ pct, indeterminate }) {
  if (indeterminate) return <div className="progress indeterminate"><div className="bar" /></div>;
  return <div className="progress"><div className="bar" style={{ width: `${Math.max(0, Math.min(100, pct))}%` }} /></div>;
}

function timeAgo(iso) {
  if (!iso) return "—";
  const ms = Date.now() - new Date(iso).getTime();
  const s = Math.max(0, Math.round(ms / 1000));
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function fmtDuration(s) {
  if (s == null) return "—";
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  const rem = s % 60;
  if (m < 60) return `${m}m ${rem}s`;
  const h = Math.floor(m / 60);
  return `${h}h ${m % 60}m`;
}

function fmtNum(n, digits = 2) {
  if (n == null) return "—";
  return Number(n).toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

function fmtPct(n, digits = 1) {
  if (n == null) return "—";
  return `${(n * 100).toFixed(digits)}%`;
}

function fmtPctDirect(n, digits = 1) {
  if (n == null) return "—";
  return `${n.toFixed(digits)}%`;
}

function ddTone(dd) {
  if (dd == null) return "";
  if (dd >= 40) return "red";
  if (dd >= 20) return "amber";
  return "";
}

function ddBadgeTone(dd) {
  if (dd == null) return "";
  if (dd >= 40) return "bad";
  if (dd >= 20) return "warn";
  return "";
}

function Gate({ state, name, value }) {
  // state: pass | warn | fail
  const icon = state === "pass" ? "✓" : state === "warn" ? "!" : "✕";
  return (
    <div className={`gate ${state}`}>
      <span className="icon">{icon}</span>
      <span className="name">{name}</span>
      <span className="val">{value}</span>
    </div>
  );
}

function Callout({ kind, ico, children }) {
  return (
    <div className={`callout ${kind || ""}`}>
      <span className="ico">{ico || "ⓘ"}</span>
      <div>{children}</div>
    </div>
  );
}

function Sparkline({ data, color, width = 80, height = 22 }) {
  if (!data || data.length === 0) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const stepX = width / (data.length - 1 || 1);
  const points = data.map((v, i) => `${i * stepX},${height - ((v - min) / range) * height}`).join(" ");
  return (
    <svg className="spark" width={width} height={height}>
      <polyline points={points} fill="none" stroke={color || "currentColor"} strokeWidth="1.2" />
    </svg>
  );
}

Object.assign(window, { Badge, ReasonCode, Card, Metric, Progress, timeAgo, fmtDuration, fmtNum, fmtPct, fmtPctDirect, ddTone, ddBadgeTone, Gate, Callout, Sparkline });
