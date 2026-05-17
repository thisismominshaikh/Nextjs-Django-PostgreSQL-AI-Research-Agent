"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { ApiErrorCallout } from "@/components/ApiErrorCallout";
import { ArrowLeft, SpinIcon, TerminalIcon } from "@/components/icons";
import { listPastSessions, startResearchSession } from "@/lib/api";
import { HttpApiError, toUiApiError, type UiApiError } from "@/lib/httpErrors";
import Link from "next/link";

interface PendingRun {
  repo_url: string;
  question: string;
  submitted_at: string;
}

const POLL_MS = 1500;

export default function NewSessionPage() {
  const router = useRouter();
  const startedRef = useRef(false);

  const [pending, setPending] = useState<PendingRun | null>(null);
  const [error, setError] = useState<UiApiError | null>(null);
  const [phase, setPhase] = useState<
    "starting" | "waiting" | "redirecting" | "no-pending"
  >("starting");

  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;

    let raw: string | null = null;
    try {
      raw = sessionStorage.getItem("pending-run");
    } catch {}
    if (!raw) {
      setPhase("no-pending");
      return;
    }
    let p: PendingRun;
    try {
      p = JSON.parse(raw) as PendingRun;
    } catch {
      setPhase("no-pending");
      return;
    }
    setPending(p);

    let cancelled = false;
    let pollTimer: ReturnType<typeof setTimeout> | null = null;
    const submittedAtMs = new Date(p.submitted_at).getTime();

    // Fire the (synchronous) start request; resolves only when the agent
    // finishes. We don't await — we poll past sessions to find the row
    // mid-run so the user sees Claude-Code-style live progress immediately.
    startResearchSession(p.repo_url, p.question)
      .then((session) => {
        if (cancelled) return;
        try {
          sessionStorage.removeItem("pending-run");
        } catch {}
        setPhase("redirecting");
        router.replace(`/sessions/${session.id}`);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(
          err instanceof HttpApiError
            ? err.ui
            : toUiApiError(err, "/proxy-api/sessions/start/"),
        );
      });

    setPhase("waiting");

    async function pollForSession() {
      try {
        const data = await listPastSessions(p.repo_url);
        if (cancelled) return;
        // Find a session whose created_at is >= submitted_at and matches the question.
        const match = data.sessions.find((s) => {
          const created = new Date(s.created_at).getTime();
          return (
            created >= submittedAtMs - 5000 &&
            s.question.trim() === p.question.trim()
          );
        });
        if (match) {
          try {
            sessionStorage.removeItem("pending-run");
          } catch {}
          setPhase("redirecting");
          router.replace(`/sessions/${match.id}`);
          return;
        }
      } catch {
        // Ignore intermittent poll errors — start request will surface real errors.
      }
      pollTimer = setTimeout(pollForSession, POLL_MS);
    }
    // Start polling shortly after submitting.
    pollTimer = setTimeout(pollForSession, 700);

    return () => {
      cancelled = true;
      if (pollTimer) clearTimeout(pollTimer);
    };
  }, [router]);

  return (
    <div className="min-h-screen flex-1">
      <header className="border-b border-border/60">
        <div className="mx-auto flex max-w-4xl items-center gap-3 px-4 py-3 sm:px-6">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 font-mono text-xs text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft width={14} height={14} />
            cancel
          </Link>
          <span className="ml-auto inline-flex items-center gap-1.5 font-mono text-[11px] text-primary">
            <TerminalIcon width={14} height={14} />
            agent boot
          </span>
        </div>
      </header>

      <main className="mx-auto w-full max-w-3xl space-y-6 px-4 py-12 sm:px-6">
        {phase === "no-pending" ? (
          <div className="rounded-xl border border-border bg-card p-6">
            <p className="text-sm text-foreground">No pending run.</p>
            <Link
              href="/"
              className="mt-3 inline-block font-mono text-xs text-primary hover:underline"
            >
              ← back to start
            </Link>
          </div>
        ) : null}

        {pending ? (
          <section className="space-y-2">
            <p className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
              question
            </p>
            <h1 className="text-pretty text-xl font-semibold tracking-tight">
              {pending.question}
            </h1>
            <p className="font-mono text-[11px] text-muted-foreground break-all">
              {pending.repo_url}
            </p>
          </section>
        ) : null}

        {error ? <ApiErrorCallout error={error} /> : null}

        {phase !== "no-pending" && !error ? (
          <div className="space-y-4 rounded-xl border border-border bg-card/60 p-5">
            <Stage
              label="connecting to research api"
              done={phase !== "starting"}
              active={phase === "starting"}
            />
            <Stage
              label="cloning repository & priming the agent"
              done={false}
              active={phase === "waiting" || phase === "redirecting"}
            />
            <Stage
              label="opening live transcript"
              done={false}
              active={phase === "redirecting"}
            />
          </div>
        ) : null}

        {phase !== "no-pending" && !error ? (
          <p className="font-mono text-[11px] text-muted-foreground">
            you&apos;ll be redirected automatically once the agent appears in the
            session log.
          </p>
        ) : null}
      </main>
    </div>
  );
}

function Stage({
  label,
  active,
  done,
}: {
  label: string;
  active: boolean;
  done: boolean;
}) {
  return (
    <div className="flex items-center gap-3">
      <span
        className={`flex h-5 w-5 items-center justify-center rounded-full ${
          done
            ? "bg-success/20 text-success"
            : active
              ? "bg-primary/20 text-primary"
              : "bg-muted text-muted-foreground"
        }`}
      >
        {active ? (
          <SpinIcon width={12} height={12} />
        ) : (
          <span className="h-1.5 w-1.5 rounded-full bg-current" />
        )}
      </span>
      <span
        className={`font-mono text-sm ${
          active ? "text-shimmer" : done ? "text-foreground" : "text-muted-foreground"
        }`}
      >
        {label}
      </span>
    </div>
  );
}
