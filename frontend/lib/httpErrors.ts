export type UiApiError = {
  title: string;
  message: string;
  status: number;
  endpoint: string;
  /** Short server-derived hint (e.g. Django debug page title + exception line) */
  serverHint?: string;
};

function looksLikeHtml(text: string): boolean {
  const t = text.trimStart().slice(0, 800).toLowerCase();
  return (
    t.startsWith("<!doctype html") ||
    t.startsWith("<html") ||
    (t.includes("<html") && t.includes("<body"))
  );
}

function stripTags(html: string): string {
  return html.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
}

function djangoDebugHints(html: string): { pageTitle?: string; exceptionValue?: string } {
  const pageTitle = html
    .match(/<title>([^<]{1,400})<\/title>/i)?.[1]
    ?.replace(/\s+/g, " ")
    .trim();
  const pre =
    html.match(
      /<pre[^>]*class="exception_value"[^>]*>([\s\S]*?)<\/pre>/i,
    )?.[1] ?? html.match(/Exception Value:<\/th>\s*<td[^>]*>([\s\S]*?)<\/td>/i)?.[1];
  let exceptionValue: string | undefined;
  if (pre) {
    exceptionValue = stripTags(pre).slice(0, 420);
    if (exceptionValue.length > 400) exceptionValue = `${exceptionValue.slice(0, 400)}…`;
  }
  return { pageTitle: pageTitle || undefined, exceptionValue };
}

function jsonErrorMessage(body: unknown): string {
  if (body && typeof body === "object") {
    const o = body as Record<string, unknown>;
    if (typeof o.detail === "string") return o.detail;
    const parts: string[] = [];
    for (const [k, v] of Object.entries(o)) {
      if (v === undefined) continue;
      parts.push(`${k}: ${typeof v === "string" ? v : JSON.stringify(v)}`);
    }
    if (parts.length) return parts.join(" · ").slice(0, 600);
  }
  const s = JSON.stringify(body);
  return s.length > 600 ? `${s.slice(0, 600)}…` : s;
}

export function invalidSuccessBody(
  res: Response,
  text: string,
  endpoint: string,
): UiApiError {
  if (looksLikeHtml(text)) {
    const { pageTitle, exceptionValue } = djangoDebugHints(text);
    const serverHint = [pageTitle, exceptionValue].filter(Boolean).join(" — ") || undefined;
    return {
      title: "Unexpected HTML response",
      message:
        "The server returned HTML instead of JSON. Often this is a Django DEBUG error page, a login redirect, or a wrong BACKEND_URL. Confirm the API is running and the `/proxy-api` rewrite points at your Django app.",
      status: res.status,
      endpoint,
      serverHint,
    };
  }
  const snippet = text.trim().slice(0, 220);
  return {
    title: "Invalid JSON",
    message:
      "The server returned a body that could not be parsed as JSON. If the API is correct, check for a proxy or middleware altering the response.",
    status: res.status,
    endpoint,
    serverHint: snippet ? snippet + (text.trim().length > 220 ? "…" : "") : undefined,
  };
}

export function responseToUiApiError(
  res: Response,
  text: string,
  endpoint: string,
): UiApiError {
  const status = res.status;

  if (looksLikeHtml(text)) {
    const { pageTitle, exceptionValue } = djangoDebugHints(text);
    const hintParts = [pageTitle, exceptionValue].filter(Boolean);
    const serverHint = hintParts.length ? hintParts.join(" — ") : undefined;
    return {
      title: "Server error",
      message:
        "The API returned an HTML debug page instead of JSON. That usually means an unhandled exception on the Django server while DEBUG is enabled. Check the terminal where `runserver` is running for the full traceback.",
      status,
      endpoint,
      serverHint,
    };
  }

  let body: unknown;
  try {
    body = JSON.parse(text) as unknown;
  } catch {
    const trimmed = text.trim();
    const msg =
      trimmed.length > 360 ? `${trimmed.slice(0, 360)}…` : trimmed || res.statusText;
    return {
      title: "Unexpected response",
      message: msg || "The server sent a non-JSON response.",
      status,
      endpoint,
    };
  }

  const title =
    status >= 500 ? "Server error" : status === 401 || status === 403 ? "Not allowed" : "Request failed";

  return {
    title,
    message: jsonErrorMessage(body),
    status,
    endpoint,
  };
}

export class HttpApiError extends Error {
  readonly ui: UiApiError;

  constructor(ui: UiApiError) {
    super(ui.message);
    this.name = "HttpApiError";
    this.ui = ui;
  }
}

export function toUiApiError(
  err: unknown,
  endpoint: string,
): UiApiError {
  if (err instanceof HttpApiError) return err.ui;
  const msg = err instanceof Error ? err.message : "Request failed";
  return {
    title: "Something went wrong",
    message: msg,
    status: 0,
    endpoint,
  };
}
