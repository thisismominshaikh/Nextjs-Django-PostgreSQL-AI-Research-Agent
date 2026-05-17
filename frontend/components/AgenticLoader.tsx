"use client";

import { useEffect, useState } from "react";

const AGENT_STEPS = [
  { label: "Initialising research agent" },
  { label: "Resolving repository URL" },
  { label: "Cloning repository to sandbox" },
  { label: "Scanning directory structure" },
  { label: "Indexing source files" },
  { label: "Building semantic map" },
  { label: "Identifying relevant modules" },
  { label: "Reading file contents" },
  { label: "Extracting code references" },
  { label: "Cross-referencing findings" },
  { label: "Synthesising answer" },
  { label: "Verifying citations" },
];

function useElapsed(running: boolean) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!running) return;

    const startTime = Date.now();
    const id = setInterval(
      () => setElapsed(Math.floor((Date.now() - startTime) / 1000)),
      1000,
    );
    return () => {
      clearInterval(id);
      setElapsed(0);
    };
  }, [running]);

  return running ? elapsed : 0;
}

const SPINNER_FRAMES = ["⠋", "⠙", "⠸", "⠴", "⠦", "⠇"];

function Spinner() {
  const [f, setF] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setF((x) => (x + 1) % SPINNER_FRAMES.length), 100);
    return () => clearInterval(id);
  }, []);
  return <span style={{ color: "#34d399" }}>{SPINNER_FRAMES[f]}</span>;
}

function BlinkingCursor() {
  const [on, setOn] = useState(true);
  useEffect(() => {
    const id = setInterval(() => setOn((x) => !x), 530);
    return () => clearInterval(id);
  }, []);
  return (
    <span
      style={{
        display: "inline-block",
        width: 9,
        height: 15,
        background: on ? "#34d399" : "transparent",
        verticalAlign: "middle",
        borderRadius: 1,
        marginLeft: 3,
      }}
    />
  );
}

export function AgenticLoader({
  loading,
  question,
}: {
  loading: boolean;
  question?: string;
}) {
  const [visibleSteps, setVisibleSteps] = useState<number[]>([]);
  const [prevLoading, setPrevLoading] = useState(loading);

  // Adjust state during render when props change to prevent cascading render cycles
  if (loading !== prevLoading) {
    setPrevLoading(loading);
    setVisibleSteps(loading ? [0] : []);
  }

  const elapsed = useElapsed(loading);

  useEffect(() => {
    if (!loading) return;

    const timers: ReturnType<typeof setTimeout>[] = [];
    AGENT_STEPS.forEach((_, i) => {
      if (i === 0) return;
      const t = setTimeout(
        () => setVisibleSteps((prev) => [...prev, i]),
        i * 1800 + Math.random() * 500,
      );
      timers.push(t);
    });
    return () => timers.forEach(clearTimeout);
  }, [loading]);

  if (!loading) return null;

  const mm = String(Math.floor(elapsed / 60)).padStart(2, "0");
  const ss = String(elapsed % 60).padStart(2, "0");

  const mono = "var(--font-geist-mono, 'Menlo', 'Consolas', monospace)";

  return (
    <div
      style={{
        background: "#0c0c0e",
        border: "1px solid #2e2e33",
        borderRadius: 14,
        overflow: "hidden",
        fontFamily: mono,
        boxShadow: "0 0 0 1px #18181b, 0 8px 40px rgba(0,0,0,0.55)",
      }}
    >
      {/* ── Title bar ── */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "11px 16px",
          background: "#111114",
          borderBottom: "1px solid #2e2e33",
        }}
      >
        {/* traffic lights */}
        {(["#ff5f57", "#ffbd2e", "#27c93f"] as const).map((c) => (
          <span
            key={c}
            style={{ width: 11, height: 11, borderRadius: "50%", background: c, display: "inline-block" }}
          />
        ))}
        <span style={{ flex: 1 }} />
        <span style={{ color: "#9090a0", fontSize: 12, letterSpacing: "0.04em" }}>
          research-agent — bash
        </span>
        <span style={{ flex: 1 }} />
        <span style={{ color: "#9090a0", fontSize: 12, fontVariantNumeric: "tabular-nums" }}>
          {mm}:{ss}
        </span>
      </div>

      {/* ── Body ── */}
      <div style={{ padding: "18px 20px", lineHeight: 1.75, minHeight: 180 }}>

        {/* prompt line */}
        <div style={{ marginBottom: 14, fontSize: 14 }}>
          <span style={{ color: "#34d399", fontWeight: 700 }}>❯</span>
          <span style={{ color: "#c0c0cc", marginLeft: 10 }}>research</span>
          {question ? (
            <>
              <span style={{ color: "#8888a0", marginLeft: 8 }}>--query</span>
              <span style={{ color: "#f0f0f5", marginLeft: 6 }}>
                &quot;{question.length > 64 ? question.slice(0, 64) + "…" : question}&quot;
              </span>
            </>
          ) : null}
        </div>

        {/* step log */}
        <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
          {AGENT_STEPS.map((step, i) => {
            const visible = visibleSteps.includes(i);
            const isActive = visible && i === visibleSteps[visibleSteps.length - 1];
            if (!visible) return null;
            return (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  fontSize: 14,
                  animation: "fadeSlideIn 0.22s ease both",
                  opacity: isActive ? 1 : 0.45,
                }}
              >
                <span style={{ width: 16, textAlign: "center", flexShrink: 0, color: isActive ? "#34d399" : "#606068" }}>
                  {isActive ? <Spinner /> : "✓"}
                </span>
                <span style={{ color: isActive ? "#f0f0f5" : "#909098" }}>
                  {step.label}
                  {isActive && <BlinkingCursor />}
                </span>
              </div>
            );
          })}
        </div>

        {/* footer */}
        <div
          style={{
            marginTop: 18,
            paddingTop: 14,
            borderTop: "1px solid #2e2e33",
            display: "flex",
            alignItems: "center",
            gap: 9,
            fontSize: 12,
            color: "#8888a0",
          }}
        >
          <span
            style={{
              width: 7,
              height: 7,
              borderRadius: "50%",
              background: "#34d399",
              animation: "pulse 1.6s ease-in-out infinite",
              flexShrink: 0,
            }}
          />
          Agent running · synchronous execution · results will appear when complete
        </div>
      </div>

      <style>{`
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(5px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50%       { opacity: 0.3; }
        }
      `}</style>
    </div>
  );
}