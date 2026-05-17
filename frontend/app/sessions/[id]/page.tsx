"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiErrorCallout } from "@/components/ApiErrorCallout";
import { StatusBadge } from "@/components/StatusBadge";
import { getResearchSession } from "@/lib/api";
import { HttpApiError, toUiApiError, type UiApiError } from "@/lib/httpErrors";
import type { Finding, ResearchSessionDetail, ToolCallLog } from "@/lib/types";

const MONO = "var(--font-geist-mono, 'Menlo', 'Consolas', monospace)";

function toolGlyph(name: string): string {
  const n = name.toLowerCase();
  if (n.includes("read") || n.includes("file") || n.includes("cat")) return "◈";
  if (n.includes("search") || n.includes("find") || n.includes("grep")) return "◉";
  if (n.includes("list") || n.includes("dir") || n.includes("ls"))  return "≡";
  if (n.includes("save") || n.includes("finding"))                   return "✦";
  if (n.includes("clone") || n.includes("git"))                      return "↓";
  if (n.includes("exec") || n.includes("run") || n.includes("bash")) return "▶";
  if (n.includes("previous") || n.includes("past") || n.includes("session")) return "◷";
  return "◎";
}

function Label({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        fontFamily: MONO,
        fontSize: 11,
        textTransform: "uppercase" as const,
        letterSpacing: "0.09em",
        color: "#9090a0",
        marginBottom: 6,
        fontWeight: 600,
      }}
    >
      {children}
    </div>
  );
}

function CodeBlock({ children }: { children: React.ReactNode }) {
  return (
    <pre
      style={{
        margin: 0,
        background: "#07070a",
        border: "1px solid #2e2e38",
        borderRadius: 8,
        padding: "12px 14px",
        fontFamily: MONO,
        fontSize: 13,
        color: "#c8c8d8",
        overflowX: "auto",
        lineHeight: 1.65,
        whiteSpace: "pre-wrap" as const,
        wordBreak: "break-word" as const,
      }}
    >
      {children}
    </pre>
  );
}

function ToolCallRow({ call, index }: { call: ToolCallLog; index: number }) {
  const [open, setOpen] = useState(false);
  const glyph = toolGlyph(call.tool_name);
  const argEntries = Object.entries(call.arguments).slice(0, 2);

  return (
    <li style={{ borderBottom: "1px solid #22222a", animation: `fadeSlideIn 0.2s ease ${index * 0.04}s both` }}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        style={{
          width: "100%",
          textAlign: "left",
          display: "flex",
          alignItems: "flex-start",
          gap: 12,
          padding: "12px 18px",
          background: "transparent",
          cursor: "pointer",
          fontFamily: MONO,
          fontSize: 14,
          lineHeight: 1.55,
          border: "none",
          outline: "none",
          transition: "background 0.12s",
        }}
        onMouseEnter={(e) => (e.currentTarget.style.background = "#13131a")}
        onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
      >
        <span style={{ color: "#34d399", flexShrink: 0, marginTop: 1, fontSize: 15 }}>
          {glyph}
        </span>
        <span style={{ flex: 1, minWidth: 0 }}>
          <span style={{ color: "#f0f0f8", fontWeight: 600 }}>{call.tool_name}</span>
          {argEntries.map(([k, v]) => (
            <span key={k}>
              <span style={{ color: "#8080a8", marginLeft: 8 }}>--{k}</span>
              <span style={{ color: "#a5b4fc", marginLeft: 5 }}>
                {String(v).length > 48 ? String(v).slice(0, 48) + "…" : String(v)}
              </span>
            </span>
          ))}
        </span>
        <span
          style={{
            color: "#7070a0",
            fontSize: 11,
            flexShrink: 0,
            transition: "transform 0.15s",
            transform: open ? "rotate(90deg)" : "rotate(0)",
            marginTop: 3,
          }}
        >
          ▶
        </span>
      </button>

      {open && (
        <div
          style={{
            borderTop: "1px solid #22222a",
            padding: "14px 18px 16px 44px",
            display: "flex",
            flexDirection: "column",
            gap: 12,
          }}
        >
          {Object.keys(call.arguments).length > 0 && (
            <div>
              <Label>Arguments</Label>
              <CodeBlock>{JSON.stringify(call.arguments, null, 2)}</CodeBlock>
            </div>
          )}
          {call.result_excerpt && (
            <div>
              <Label>Result excerpt</Label>
              <CodeBlock>{call.result_excerpt}</CodeBlock>
            </div>
          )}
          <div style={{ fontFamily: MONO, fontSize: 11, color: "#9090a0" }}>
            {new Date(call.created_at).toLocaleTimeString()}
          </div>
        </div>
      )}
    </li>
  );
}

function ToolCallTerminal({ toolCalls }: { toolCalls: ToolCallLog[] }) {
  if (toolCalls.length === 0)
    return <p className="text-sm text-zinc-500 dark:text-zinc-400">No tool calls logged.</p>;

  return (
    <div
      style={{
        background: "#0c0c0e",
        border: "1px solid #2e2e33",
        borderRadius: 14,
        overflow: "hidden",
        boxShadow: "0 0 0 1px #18181b, 0 6px 32px rgba(0,0,0,0.5)",
      }}
    >
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
        {(["#ff5f57", "#ffbd2e", "#27c93f"] as const).map((c) => (
          <span key={c} style={{ width: 11, height: 11, borderRadius: "50%", background: c, display: "inline-block" }} />
        ))}
        <span style={{ flex: 1 }} />
        <span style={{ color: "#9090a0", fontSize: 12, fontFamily: MONO, letterSpacing: "0.04em" }}>
          tool-calls · {toolCalls.length} invocations
        </span>
        <span style={{ flex: 1 }} />
      </div>

      <ul style={{ listStyle: "none", margin: 0, padding: 0, maxHeight: "38rem", overflowY: "auto" }}>
        {toolCalls.map((t, i) => (
          <ToolCallRow key={t.id} call={t} index={i} />
        ))}
      </ul>

      <style>{`
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(4px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}

function FindingsPanel({ findings }: { findings: Finding[] }) {
  if (findings.length === 0)
    return <p className="text-sm text-zinc-500 dark:text-zinc-400">No findings recorded.</p>;

  return (
    <ul className="space-y-3">
      {findings.map((f, i) => (
        <li
          key={f.id}
          className="rounded-xl border border-zinc-200 bg-white p-4 text-sm dark:border-zinc-800 dark:bg-zinc-900"
        >
          <div className="flex items-start justify-between gap-3">
            <p className="font-mono text-xs text-emerald-600 dark:text-emerald-400 break-all">
              {f.file_path || "(no path)"}
            </p>
            <span className="shrink-0 font-mono text-xs text-zinc-400 dark:text-zinc-500">
              #{i + 1}
            </span>
          </div>
          <p className="mt-2 leading-6 whitespace-pre-wrap text-zinc-700 dark:text-zinc-300">{f.note}</p>
          <p className="mt-2 font-mono text-xs text-zinc-400 dark:text-zinc-500">
            {new Date(f.created_at).toLocaleTimeString()}
          </p>
        </li>
      ))}
    </ul>
  );
}

function ReferencesPanel({ references }: { references: unknown }) {
  if (!Array.isArray(references) || references.length === 0) {
    return <p className="text-sm text-zinc-500 dark:text-zinc-400">No references recorded.</p>;
  }

  type Ref = { file?: string; start_line?: number; end_line?: number; note?: string };
  const refs = references as Ref[];

  return (
    <ul className="space-y-2">
      {refs.map((ref, i) => (
        <li
          key={i}
          className="rounded-xl border border-zinc-200 bg-white p-4 text-sm dark:border-zinc-800 dark:bg-zinc-900"
        >
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-xs font-semibold text-violet-600 dark:text-violet-400 break-all">
              {ref.file ?? "(unknown file)"}
            </span>
            {(ref.start_line != null || ref.end_line != null) && (
              <span className="font-mono text-xs text-zinc-400 dark:text-zinc-500">
                L{ref.start_line ?? "?"}
                {ref.end_line != null && ref.end_line !== ref.start_line ? `–${ref.end_line}` : ""}
              </span>
            )}
          </div>
          {ref.note && (
            <p className="mt-1.5 text-zinc-600 dark:text-zinc-400">{ref.note}</p>
          )}
        </li>
      ))}
    </ul>
  );
}

type Tab = "answer" | "tool-calls" | "findings" | "references";

function SessionBody({ id }: { id: number }) {
  const [session, setSession] = useState<ResearchSessionDetail | null>(null);
  const [loadError, setLoadError] = useState<UiApiError | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>("answer");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setLoadError(null);
      try {
        const data = await getResearchSession(id);
        if (!cancelled) setSession(data);
      } catch (e) {
        if (!cancelled)
          setLoadError(
            e instanceof HttpApiError ? e.ui : toUiApiError(e, `/proxy-api/sessions/${id}/`),
          );
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [id]);

  return (
    <>
      {loading && (
        <div className="flex items-center gap-3 text-sm text-zinc-500 dark:text-zinc-400">
          <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent opacity-60" />
          Loading session…
        </div>
      )}
      {loadError && <ApiErrorCallout error={loadError} />}

      {session && (
        <>
          {/* ── Header ── */}
          <header className="space-y-3">
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl font-semibold tracking-tight">Session #{session.id}</h1>
              <StatusBadge status={session.status} />
            </div>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              <span className="font-mono">{session.repository_identifier}</span>
              <span className="mx-2">·</span>
              {new Date(session.created_at).toLocaleString()}
              {session.input_tokens != null && (
                <span className="ml-2">
                  · {session.input_tokens.toLocaleString()} in / {session.output_tokens?.toLocaleString() ?? "?"} out tokens
                </span>
              )}
            </p>
            <div className="rounded-2xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
              <h2 className="text-sm font-medium text-zinc-500 dark:text-zinc-400">Question</h2>
              <p className="mt-2 text-sm leading-6 whitespace-pre-wrap">{session.question}</p>
            </div>
          </header>

          {/* ── Error message ── */}
          {session.error_message && (
            <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-200">
              {session.error_message}
            </p>
          )}

          {/* ── Tabs ── */}
          <div className="border-b border-zinc-200 dark:border-zinc-800">
            <nav className="-mb-px flex gap-1 overflow-x-auto" aria-label="Tabs">
              {(
                [
                  { key: "answer", label: "Answer" },
                  {
                    key: "tool-calls",
                    label: "Tool Calls",
                    count: session.tool_calls.length,
                  },
                  {
                    key: "findings",
                    label: "Findings",
                    count: session.findings.length,
                  },
                  {
                    key: "references",
                    label: "References",
                    count: Array.isArray(session.references_json)
                      ? session.references_json.length
                      : 0,
                  },
                ] as { key: Tab; label: string; count?: number }[]
              ).map((tab) => (
                <button
                  key={tab.key}
                  type="button"
                  onClick={() => setActiveTab(tab.key)}
                  className={`inline-flex shrink-0 items-center gap-1.5 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
                    activeTab === tab.key
                      ? "border-zinc-900 text-zinc-900 dark:border-zinc-100 dark:text-zinc-100"
                      : "border-transparent text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200"
                  }`}
                >
                  {tab.label}
                  {tab.count != null && tab.count > 0 && (
                    <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
                      {tab.count}
                    </span>
                  )}
                </button>
              ))}
            </nav>
          </div>

          {/* ── Tab panels ── */}
          {activeTab === "answer" && (
            <div className="rounded-2xl border border-zinc-200 bg-white p-5 text-sm leading-7 whitespace-pre-wrap dark:border-zinc-800 dark:bg-zinc-900">
              {session.final_answer || "—"}
            </div>
          )}

          {activeTab === "tool-calls" && (
            <ToolCallTerminal toolCalls={session.tool_calls} />
          )}

          {activeTab === "findings" && (
            <FindingsPanel findings={session.findings} />
          )}

          {activeTab === "references" && (
            <ReferencesPanel references={session.references_json} />
          )}
        </>
      )}
    </>
  );
}

export default function SessionDetailPage() {
  const params = useParams();
  const rawId = params?.id;
  const id = typeof rawId === "string" ? Number.parseInt(rawId, 10) : NaN;

  return (
    <div className="flex flex-1 flex-col bg-zinc-100 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100">
      <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-8 px-4 py-10 sm:px-6 sm:py-14">
        <div className="flex flex-wrap items-center gap-3">
          <Link
            href="/"
            className="text-sm font-medium text-zinc-600 underline-offset-4 hover:text-zinc-900 hover:underline dark:text-zinc-400 dark:hover:text-zinc-100"
          >
            ← Home
          </Link>
        </div>
        {!Number.isFinite(id) ? (
          <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-200" role="alert">
            Invalid session id
          </p>
        ) : (
          <SessionBody id={id} />
        )}
      </main>
    </div>
  );
}
