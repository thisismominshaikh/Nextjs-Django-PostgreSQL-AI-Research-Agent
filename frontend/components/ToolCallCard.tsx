"use client";

import { useState } from "react";
import type { ToolCallLog } from "@/lib/types";
import {
  ChevronRight,
  FileIcon,
  FolderIcon,
  GitIcon,
  SearchIcon,
  TerminalIcon,
  WrenchIcon,
} from "@/components/icons";

function renderIcon(name: string, size: number) {
  const n = name.toLowerCase();
  if (n.includes("read") || n.includes("file") || n.includes("cat")) {
    return <FileIcon width={size} height={size} />;
  }
  if (n.includes("search") || n.includes("grep") || n.includes("find")) {
    return <SearchIcon width={size} height={size} />;
  }
  if (n.includes("shell") || n.includes("bash") || n.includes("exec")) {
    return <TerminalIcon width={size} height={size} />;
  }
  if (n.includes("git") || n.includes("clone")) {
    return <GitIcon width={size} height={size} />;
  }
  if (n.includes("list") || n.includes("dir") || n.includes("ls")) {
    return <FolderIcon width={size} height={size} />;
  }
  return <WrenchIcon width={size} height={size} />;
}

function summarizeArgs(args: Record<string, unknown>): string {
  const entries = Object.entries(args);
  if (!entries.length) return "";
  const [k, raw] = entries[0];
  const v = typeof raw === "string" ? raw : JSON.stringify(raw);
  const head = `${k}: ${v}`;
  return head.length > 90 ? head.slice(0, 90) + "…" : head;
}

export function ToolCallCard({
  call,
  index,
}: {
  call: ToolCallLog;
  index: number;
}) {
  const [open, setOpen] = useState(false);
  const summary = summarizeArgs(call.arguments);

  return (
    <div className="animate-slide-in rounded-lg border border-border bg-card/60">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-colors hover:bg-[color-mix(in_oklab,var(--muted)_60%,transparent)]"
      >
        <span className="w-6 font-mono text-[10px] tabular-nums text-muted-foreground">
          {String(index + 1).padStart(2, "0")}
        </span>
        <span className="flex h-6 w-6 items-center justify-center rounded-md bg-primary/10 text-primary">
          {renderIcon(call.tool_name, 14)}
        </span>
        <span className="font-mono text-sm text-foreground">
          {call.tool_name}
        </span>
        {summary ? (
          <span className="truncate font-mono text-xs text-muted-foreground">
            ({summary})
          </span>
        ) : null}
        <span
          className={`ml-auto text-muted-foreground transition-transform ${
            open ? "rotate-90" : ""
          }`}
        >
          <ChevronRight width={14} height={14} />
        </span>
      </button>
      {open ? (
        <div className="space-y-3 border-t border-border px-3 py-3">
          {Object.keys(call.arguments).length ? (
            <div>
              <p className="mb-1 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                arguments
              </p>
              <pre className="scrollbar-thin overflow-x-auto rounded-md bg-background/60 p-2 font-mono text-xs text-foreground/90">
                {JSON.stringify(call.arguments, null, 2)}
              </pre>
            </div>
          ) : null}
          {call.result_excerpt ? (
            <div>
              <p className="mb-1 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                result
              </p>
              <pre className="scrollbar-thin max-h-72 overflow-auto whitespace-pre-wrap rounded-md bg-background/60 p-2 font-mono text-xs text-foreground/80">
                {call.result_excerpt}
              </pre>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
