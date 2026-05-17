"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ApiErrorCallout } from "@/components/ApiErrorCallout";
import { StatusBadge } from "@/components/StatusBadge";
import { listAllSessions } from "@/lib/api";
import { HttpApiError, toUiApiError, type UiApiError } from "@/lib/httpErrors";
import type { ListAllSessionsResponse, SessionStatus } from "@/lib/types";

const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: "All" },
  { value: "completed", label: "Completed" },
  { value: "running", label: "Running" },
  { value: "failed", label: "Failed" },
  { value: "pending", label: "Pending" },
];

export default function AllSessionsPage() {
  const [data, setData] = useState<ListAllSessionsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<UiApiError | null>(null);
  const [statusFilter, setStatusFilter] = useState("");

  useEffect(() => {
    let cancelled = false;

    listAllSessions(statusFilter || undefined)
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch((err) => {
        if (!cancelled)
          setError(
            err instanceof HttpApiError
              ? err.ui
              : toUiApiError(err, "/proxy-api/sessions/"),
          );
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [statusFilter]);

  const handleStatusFilterChange = (value: string) => {
    if (statusFilter === value) return;
    setStatusFilter(value);
    setLoading(true);
    setError(null);
  };

  return (
    <div className="flex flex-1 flex-col bg-zinc-100 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100">
      <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-8 px-4 py-10 sm:px-6 sm:py-14">
        {/* Header */}
        <div className="flex flex-wrap items-center gap-3">
          <Link
            href="/"
            className="text-sm font-medium text-zinc-600 underline-offset-4 hover:text-zinc-900 hover:underline dark:text-zinc-400 dark:hover:text-zinc-100"
          >
            ← Home
          </Link>
        </div>

        <header className="space-y-2">
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            All Research Sessions
          </h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            Every session run against any repository, most recent first.
          </p>
        </header>

        {/* Filter bar */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium text-zinc-600 dark:text-zinc-400">
            Filter by status:
          </span>
          {STATUS_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => handleStatusFilterChange(opt.value)}
              className={`inline-flex h-8 items-center rounded-lg px-3 text-sm font-medium transition-colors ${
                statusFilter === opt.value
                  ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                  : "border border-zinc-300 bg-white text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800"
              }`}
            >
              {opt.label}
            </button>
          ))}
          {data && (
            <span className="ml-auto inline-flex items-center rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs font-medium text-zinc-600 ring-1 ring-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:ring-zinc-700">
              {data.count} session{data.count !== 1 ? "s" : ""}
            </span>
          )}
        </div>

        {/* Error */}
        {error && <ApiErrorCallout error={error} />}

        {/* Loading */}
        {loading && (
          <div className="flex items-center gap-3 text-sm text-zinc-500 dark:text-zinc-400">
            <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent opacity-60" />
            Loading sessions…
          </div>
        )}

        {/* Sessions table */}
        {!loading && data && (
          <>
            {data.sessions.length === 0 ? (
              <div className="rounded-2xl border border-zinc-200 bg-white p-8 text-center dark:border-zinc-800 dark:bg-zinc-900">
                <p className="text-sm text-zinc-500 dark:text-zinc-400">
                  No sessions found
                  {statusFilter ? ` with status "${statusFilter}"` : ""}.
                </p>
                <Link
                  href="/"
                  className="mt-3 inline-block text-sm font-medium text-zinc-900 underline-offset-4 hover:underline dark:text-zinc-100"
                >
                  Run your first research session →
                </Link>
              </div>
            ) : (
              <ul className="divide-y divide-zinc-200 rounded-2xl border border-zinc-200 bg-white dark:divide-zinc-800 dark:border-zinc-800 dark:bg-zinc-900">
                {data.sessions.map((session) => (
                  <li
                    key={session.id}
                    className="flex flex-col gap-2 px-5 py-4 sm:flex-row sm:items-start sm:justify-between"
                  >
                    <div className="min-w-0 flex-1 space-y-1">
                      <p className="line-clamp-2 text-sm font-medium text-zinc-900 dark:text-zinc-100">
                        {session.question}
                      </p>
                      <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5">
                        <span className="font-mono text-xs text-zinc-400 dark:text-zinc-500">
                          #{session.id}
                        </span>
                        <span className="text-zinc-300 dark:text-zinc-600">
                          ·
                        </span>
                        <span className="max-w-xs truncate font-mono text-xs text-zinc-400 dark:text-zinc-500">
                          {session.repository_identifier}
                        </span>
                        <span className="text-zinc-300 dark:text-zinc-600">
                          ·
                        </span>
                        <span className="text-xs text-zinc-400 dark:text-zinc-500">
                          {new Date(session.created_at).toLocaleString()}
                        </span>
                        {session.input_tokens != null && (
                          <>
                            <span className="text-zinc-300 dark:text-zinc-600">
                              ·
                            </span>
                            <span className="text-xs text-zinc-400 dark:text-zinc-500">
                              {session.input_tokens.toLocaleString()} in /{" "}
                              {session.output_tokens?.toLocaleString() ?? "?"}{" "}
                              out tokens
                            </span>
                          </>
                        )}
                      </div>
                      {session.final_answer && (
                        <p className="line-clamp-2 text-xs text-zinc-500 dark:text-zinc-400">
                          {session.final_answer}
                        </p>
                      )}
                    </div>
                    <div className="flex shrink-0 items-center gap-3 sm:ml-4 sm:flex-col sm:items-end">
                      <StatusBadge status={session.status as SessionStatus} />
                      <Link
                        href={`/sessions/${session.id}`}
                        className="text-sm font-medium text-zinc-900 underline-offset-4 hover:underline dark:text-zinc-100"
                      >
                        Open →
                      </Link>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </main>
    </div>
  );
}
