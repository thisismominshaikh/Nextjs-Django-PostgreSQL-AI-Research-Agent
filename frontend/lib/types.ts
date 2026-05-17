export type SessionStatus = "pending" | "running" | "completed" | "failed";

export interface ResearchSession {
  id: number;
  repository: number;
  repository_identifier: string;
  question: string;
  final_answer: string;
  references_json: unknown;
  status: SessionStatus;
  error_message: string;
  checkout_path: string;
  input_tokens: number | null;
  output_tokens: number | null;
  created_at: string;
  updated_at: string;
}

export interface Finding {
  id: number;
  file_path: string;
  note: string;
  created_at: string;
}

export interface ToolCallLog {
  id: number;
  tool_name: string;
  arguments: Record<string, unknown>;
  result_excerpt: string;
  created_at: string;
}

export interface ResearchSessionDetail extends ResearchSession {
  findings: Finding[];
  tool_calls: ToolCallLog[];
}

export interface Repository {
  id: number;
  identifier: string;
  display_name: string;
  last_analyzed_at: string | null;
}

export interface PastSessionsResponse {
  repository: Repository | null;
  sessions: ResearchSession[];
}

export interface ListRepositoriesResponse {
  count: number;
  repositories: Repository[];
}

export interface SessionFindingsResponse {
  session_id: number;
  question: string;
  status: SessionStatus;
  finding_count: number;
  findings: Finding[];
}

export interface ListAllSessionsResponse {
  count: number;
  sessions: ResearchSession[];
}
