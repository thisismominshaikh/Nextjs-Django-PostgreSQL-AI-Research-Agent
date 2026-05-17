"use client";

import Link from "next/link";
import { useState } from "react";

import { AgenticLoader } from "@/components/AgenticLoader";
import { ApiErrorCallout } from "@/components/ApiErrorCallout";
import { StatusBadge } from "@/components/StatusBadge";
import {
  listPastSessions,
  listRepositories,
  startResearchSession,
} from "@/lib/api";
import { HttpApiError, toUiApiError, type UiApiError } from "@/lib/httpErrors";
import type {
  ListRepositoriesResponse,
  PastSessionsResponse,
  ResearchSession,
} from "@/lib/types";

export default function Home() {
  const [repoUrl, setRepoUrl] = useState(
    "https://github.com/psf/requests",
  );
  const [question, setQuestion] = useState(
    "How does Requests pick the default CA bundle?",
  );
  const [loading, setLoading] = useState(false);
  const [formError, setFormError] = useState<UiApiError | null>(null);
  const [session, setSession] = useState<ResearchSession | null>(null);

  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<UiApiError | null>(null);
  const [history, setHistory] = useState<PastSessionsResponse | null>(null);

  const [reposLoading, setReposLoading] = useState(false);
  const [reposError, setReposError] = useState<UiApiError | null>(null);
  const [repos, setRepos] = useState<ListRepositoriesResponse | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    setSession(null);
    const ru = repoUrl.trim();
    const q = question.trim();
    if (!ru || !q) {
      setFormError({
        title: "Missing fields",
        message: "Repository URL and question are required.",
        status: 0,
        endpoint: `${typeof window !== "undefined" ? window.location.origin : ""}/`,
      });
      return;
    }
    setLoading(true);
    try {
      const data = await startResearchSession(ru, q);
      setSession(data);
    } catch (err) {
      setFormError(
        err instanceof HttpApiError
          ? err.ui
          : toUiApiError(err, "/proxy-api/sessions/start/"),
      );
    } finally {
      setLoading(false);
    }
  }

  async function onLoadHistory() {
    setHistoryError(null);
    setHistory(null);
    setRepos(null);
    const ru = repoUrl.trim();
    if (!ru) {
      setHistoryError({
        title: "Missing repository",
        message: "Enter a repository URL first.",
        status: 0,
        endpoint: "/proxy-api/repositories/sessions/",
      });
      return;
    }
    setHistoryLoading(true);
    try {
      const data = await listPastSessions(ru);
      setHistory(data);
    } catch (err) {
      setHistoryError(
        err instanceof HttpApiError
          ? err.ui
          : toUiApiError(err, "/proxy-api/repositories/sessions/"),
      );
    } finally {
      setHistoryLoading(false);
    }
  }

  async function onBrowseRepos() {
    setReposError(null);
    setRepos(null);
    setHistory(null);
    setReposLoading(true);
    try {
      const data = await listRepositories();
      setRepos(data);
    } catch (err) {
      setReposError(
        err instanceof HttpApiError
          ? err.ui
          : toUiApiError(err, "/proxy-api/repositories/"),
      );
    } finally {
      setReposLoading(false);
    }
  }

  return (
    <div className="flex flex-1 flex-col bg-zinc-100 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100">
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-10 px-4 py-10 sm:px-6 sm:py-14">
        <header className="space-y-2">
          <p className="text-sm font-medium text-zinc-500 dark:text-zinc-400">
            Codebase Research Agent
          </p>
          <h1 className="text-balance text-3xl font-semibold tracking-tight sm:text-4xl">
            Ask a question about a Git repo
          </h1>
          <p className="max-w-2xl text-pretty text-sm leading-6 text-zinc-600 dark:text-zinc-400">
            Powered by Groq. The agent clones the repo, explores the
            code with tool calls, and returns a cited answer.
          </p>
        </header>

        <form
          onSubmit={onSubmit}
          className="space-y-5 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900"
        >
          <div className="space-y-2">
            <label
              htmlFor="repo_url"
              className="text-sm font-medium text-zinc-800 dark:text-zinc-200"
            >
              Repository URL
            </label>
            <input
              id="repo_url"
              name="repo_url"
              type="url"
              autoComplete="off"
              placeholder="https://github.com/org/repo"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              disabled={loading}
              className="block w-full rounded-xl border border-zinc-300 bg-white px-3 py-2.5 text-sm outline-none ring-zinc-400/40 placeholder:text-zinc-400 focus:border-zinc-500 focus:ring-2 disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-950 dark:focus:border-zinc-500"
            />
          </div>
          <div className="space-y-2">
            <label
              htmlFor="question"
              className="text-sm font-medium text-zinc-800 dark:text-zinc-200"
            >
              Question
            </label>
            <textarea
              id="question"
              name="question"
              rows={4}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={loading}
              className="block w-full resize-y rounded-xl border border-zinc-300 bg-white px-3 py-2.5 text-sm outline-none ring-zinc-400/40 placeholder:text-zinc-400 focus:border-zinc-500 focus:ring-2 disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-950 dark:focus:border-zinc-500"
            />
          </div>

          {formError ? <ApiErrorCallout error={formError} /> : null}

          <div className="flex flex-wrap gap-3">
            <button
              type="submit"
              disabled={loading}
              className="inline-flex h-11 items-center justify-center gap-2 rounded-xl bg-zinc-900 px-5 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-white"
            >
              {loading ? (
                <>
                  <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent opacity-70" />
                  Running research…
                </>
              ) : (
                "Run research"
              )}
            </button>
            <button
              type="button"
              onClick={onLoadHistory}
              disabled={historyLoading || loading}
              className="inline-flex h-11 items-center justify-center rounded-xl border border-zinc-300 bg-transparent px-5 text-sm font-medium text-zinc-800 transition hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-zinc-600 dark:text-zinc-100 dark:hover:bg-zinc-800"
            >
              {historyLoading ? "Loading…" : "Past sessions for this repo"}
            </button>
            <button
              type="button"
              onClick={onBrowseRepos}
              disabled={reposLoading || loading}
              className="inline-flex h-11 items-center justify-center rounded-xl border border-zinc-300 bg-transparent px-5 text-sm font-medium text-zinc-800 transition hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-zinc-600 dark:text-zinc-100 dark:hover:bg-zinc-800"
            >
              {reposLoading ? "Loading…" : "Browse all repositories"}
            </button>
            <Link
              href="/sessions"
              className="inline-flex h-11 items-center justify-center rounded-xl border border-zinc-300 bg-transparent px-5 text-sm font-medium text-zinc-800 transition hover:bg-zinc-50 dark:border-zinc-600 dark:text-zinc-100 dark:hover:bg-zinc-800"
            >
              All sessions
            </Link>
          </div>
        </form>

        {/* ── Agentic loader ── */}
        <AgenticLoader loading={loading} question={question} />

        {/* ── Result after running ── */}
        {session ? (
          <section className="space-y-4 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="text-lg font-semibold tracking-tight">Result</h2>
              <StatusBadge status={session.status} />
              <Link
                href={`/sessions/${session.id}`}
                className="ml-auto text-sm font-medium text-zinc-900 underline-offset-4 hover:underline dark:text-zinc-100"
              >
                Full session →
              </Link>
            </div>
            {session.error_message ? (
              <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-200">
                {session.error_message}
              </p>
            ) : null}
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
                Answer
              </h3>
              <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-4 text-sm leading-6 whitespace-pre-wrap text-zinc-800 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-200">
                {session.final_answer || "—"}
              </div>
            </div>
            <div className="flex flex-wrap gap-4 text-xs text-zinc-500 dark:text-zinc-400">
              {session.input_tokens != null ? (
                <span>Input tokens: {session.input_tokens.toLocaleString()}</span>
              ) : null}
              {session.output_tokens != null ? (
                <span>Output tokens: {session.output_tokens.toLocaleString()}</span>
              ) : null}
            </div>
            {session.references_json &&
            Array.isArray(session.references_json) &&
            session.references_json.length > 0 ? (
              <details className="rounded-xl border border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-950">
                <summary className="cursor-pointer px-4 py-3 text-sm font-medium text-zinc-800 dark:text-zinc-200">
                  References ({(session.references_json as unknown[]).length})
                </summary>
                <pre className="max-h-80 overflow-auto border-t border-zinc-200 p-4 font-mono text-xs leading-relaxed text-zinc-700 dark:border-zinc-800 dark:text-zinc-300">
                  {JSON.stringify(session.references_json, null, 2)}
                </pre>
              </details>
            ) : null}
          </section>
        ) : null}

        {/* ── History error ── */}
        {historyError ? <ApiErrorCallout error={historyError} /> : null}

        {/* ── Past sessions for this repo ── */}
        {history ? (
          <section className="space-y-3">
            <h2 className="text-lg font-semibold tracking-tight">
              Past sessions
            </h2>
            {history.repository ? (
              <p className="text-sm text-zinc-600 dark:text-zinc-400">
                {history.repository.display_name || history.repository.identifier}
                {history.repository.last_analyzed_at && (
                  <span className="ml-2 text-xs text-zinc-400 dark:text-zinc-500">
                    · last analyzed {new Date(history.repository.last_analyzed_at).toLocaleString()}
                  </span>
                )}
              </p>
            ) : (
              <p className="text-sm text-zinc-600 dark:text-zinc-400">
                No repository record yet for this URL.
              </p>
            )}
            <SessionList sessions={history.sessions} />
          </section>
        ) : null}

        {/* ── Repos error ── */}
        {reposError ? <ApiErrorCallout error={reposError} /> : null}

        {/* ── All repositories ── */}
        {repos ? (
          <section className="space-y-3">
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-semibold tracking-tight">
                All repositories
              </h2>
              <span className="inline-flex items-center rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs font-medium text-zinc-600 ring-1 ring-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:ring-zinc-700">
                {repos.count}
              </span>
            </div>
            {repos.repositories.length === 0 ? (
              <p className="text-sm text-zinc-500 dark:text-zinc-400">
                No repositories have been analyzed yet.
              </p>
            ) : (
              <ul className="divide-y divide-zinc-200 rounded-2xl border border-zinc-200 bg-white dark:divide-zinc-800 dark:border-zinc-800 dark:bg-zinc-900">
                {repos.repositories.map((repo) => (
                  <li key={repo.id} className="flex flex-col gap-1 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
                    <div className="min-w-0 space-y-1">
                      <p className="truncate font-medium text-sm text-zinc-900 dark:text-zinc-100">
                        {repo.display_name || repo.identifier}
                      </p>
                      <p className="truncate font-mono text-xs text-zinc-500 dark:text-zinc-400">
                        {repo.identifier}
                      </p>
                    </div>
                    <div className="flex shrink-0 items-center gap-3">
                      {repo.last_analyzed_at && (
                        <span className="text-xs text-zinc-400 dark:text-zinc-500">
                          {new Date(repo.last_analyzed_at).toLocaleDateString()}
                        </span>
                      )}
                      <button
                        type="button"
                        onClick={() => {
                          setRepoUrl(repo.identifier);
                          setRepos(null);
                        }}
                        className="text-sm font-medium text-zinc-900 underline-offset-4 hover:underline dark:text-zinc-100"
                      >
                        Use this repo
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        ) : null}
      </main>
    </div>
  );
}

function SessionList({ sessions }: { sessions: ResearchSession[] }) {
  return (
    <ul className="divide-y divide-zinc-200 rounded-2xl border border-zinc-200 bg-white dark:divide-zinc-800 dark:border-zinc-800 dark:bg-zinc-900">
      {sessions.length === 0 ? (
        <li className="px-4 py-6 text-sm text-zinc-500 dark:text-zinc-400">
          No sessions found.
        </li>
      ) : (
        sessions.map((s) => (
          <li
            key={s.id}
            className="flex flex-col gap-2 px-4 py-4 sm:flex-row sm:items-center sm:justify-between"
          >
            <div className="min-w-0 space-y-1">
              <p className="truncate text-sm font-medium text-zinc-900 dark:text-zinc-100">
                {s.question}
              </p>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">
                #{s.id} · {new Date(s.created_at).toLocaleString()}
                {s.input_tokens != null && (
                  <span className="ml-2">· {s.input_tokens.toLocaleString()} in / {s.output_tokens?.toLocaleString() ?? "?"} out tokens</span>
                )}
              </p>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <StatusBadge status={s.status} />
              <Link
                href={`/sessions/${s.id}`}
                className="text-sm font-medium text-zinc-900 underline-offset-4 hover:underline dark:text-zinc-100"
              >
                Open
              </Link>
            </div>
          </li>
        ))
      )}
    </ul>
  );
}
