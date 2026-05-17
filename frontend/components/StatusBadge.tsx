import type { SessionStatus } from "@/lib/types";

const map: Record<string, { label: string; className: string; dot: string }> = {
  completed: {
    label: "completed",
    className: "bg-success/15 text-success ring-success/30",
    dot: "bg-success",
  },
  failed: {
    label: "failed",
    className: "bg-destructive/15 text-destructive ring-destructive/30",
    dot: "bg-destructive",
  },
  running: {
    label: "running",
    className: "bg-primary/15 text-primary ring-primary/30",
    dot: "bg-primary animate-pulse",
  },
  pending: {
    label: "pending",
    className: "bg-warning/15 text-warning ring-warning/30",
    dot: "bg-warning animate-pulse",
  },
};

export function StatusBadge({ status }: { status: SessionStatus | string }) {
  const v = map[status] ?? map.pending;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 font-mono text-[11px] uppercase tracking-wider ring-1 ${v.className}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${v.dot}`} />
      {v.label}
    </span>
  );
}
