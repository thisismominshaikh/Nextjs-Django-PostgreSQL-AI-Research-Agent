import type {
  ListAllSessionsResponse,
  ListRepositoriesResponse,
  PastSessionsResponse,
  ResearchSession,
  ResearchSessionDetail,
  SessionFindingsResponse,
} from "@/lib/types";

import {
  HttpApiError,
  invalidSuccessBody,
  responseToUiApiError,
} from "@/lib/httpErrors";

const PREFIX = "/proxy-api";

async function readJson<T>(res: Response, endpoint: string): Promise<T> {
  const text = await res.text();
  if (!res.ok) {
    throw new HttpApiError(responseToUiApiError(res, text, endpoint));
  }
  try {
    return JSON.parse(text) as T;
  } catch {
    throw new HttpApiError(invalidSuccessBody(res, text, endpoint));
  }
}

export async function startResearchSession(
  repo_url: string,
  question: string,
): Promise<ResearchSession> {
  const endpoint = `${PREFIX}/sessions/start/`;
  const res = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_url, question }),
  });
  return readJson<ResearchSession>(res, endpoint);
}

export async function getResearchSession(
  id: number,
): Promise<ResearchSessionDetail> {
  const endpoint = `${PREFIX}/sessions/${id}/`;
  const res = await fetch(endpoint, { cache: "no-store" });
  return readJson<ResearchSessionDetail>(res, endpoint);
}

export async function listPastSessions(
  repo_url: string,
): Promise<PastSessionsResponse> {
  const q = new URLSearchParams({ repo_url });
  const endpoint = `${PREFIX}/repositories/sessions/?${q}`;
  const res = await fetch(endpoint, { cache: "no-store" });
  return readJson<PastSessionsResponse>(res, endpoint);
}

export async function listRepositories(
  search?: string,
): Promise<ListRepositoriesResponse> {
  const q = search ? `?search=${encodeURIComponent(search)}` : "";
  const endpoint = `${PREFIX}/repositories/${q}`;
  const res = await fetch(endpoint, { cache: "no-store" });
  return readJson<ListRepositoriesResponse>(res, endpoint);
}

export async function getSessionFindings(
  id: number,
): Promise<SessionFindingsResponse> {
  const endpoint = `${PREFIX}/sessions/${id}/findings/`;
  const res = await fetch(endpoint, { cache: "no-store" });
  return readJson<SessionFindingsResponse>(res, endpoint);
}

export async function listAllSessions(
  status?: string,
  limit?: number,
): Promise<ListAllSessionsResponse> {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (limit) params.set("limit", String(limit));
  const q = params.toString() ? `?${params}` : "";
  const endpoint = `${PREFIX}/sessions/${q}`;
  const res = await fetch(endpoint, { cache: "no-store" });
  return readJson<ListAllSessionsResponse>(res, endpoint);
}
