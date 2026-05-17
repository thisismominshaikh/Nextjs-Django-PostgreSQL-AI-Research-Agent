import type { UiApiError } from "@/lib/httpErrors";

export function ApiErrorCallout({ error }: { error: UiApiError }) {
  return (
    <div
      role="alert"
      className="overflow-hidden rounded-2xl border border-red-200/90 bg-linear-to-br from-red-50 via-white to-amber-50/40 shadow-sm dark:border-red-900/50 dark:from-red-950/50 dark:via-zinc-900 dark:to-zinc-900"
    >
      <div className="flex gap-3 px-4 py-4 sm:px-5 sm:py-5">
        <div
          className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-red-600 text-white shadow-sm dark:bg-red-700"
          aria-hidden
        >
          <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
          </svg>
        </div>
        <div className="min-w-0 flex-1 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-sm font-semibold text-red-950 dark:text-red-100">
              {error.title}
            </h3>
            {error.status ? (
              <span className="inline-flex items-center rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800 tabular-nums dark:bg-red-900/60 dark:text-red-100">
                HTTP {error.status}
              </span>
            ) : null}
          </div>
          <p className="text-sm leading-6 text-red-900/90 dark:text-red-100/90">
            {error.message}
          </p>
          {error.serverHint ? (
            <div className="rounded-xl border border-red-200/70 bg-white/80 px-3 py-2 dark:border-red-900/40 dark:bg-zinc-950/60">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-red-700/80 dark:text-red-300/80">
                Server said
              </p>
              <p className="mt-1 font-mono text-xs leading-5 text-red-950/90 wrap-break-word dark:text-red-50/90">
                {error.serverHint}
              </p>
            </div>
          ) : null}
          <p className="text-[11px] text-zinc-500 dark:text-zinc-400">
            <span className="font-mono">{error.endpoint}</span>
          </p>
        </div>
      </div>
    </div>
  );
}
