export type UUID = string;
export type ISODateTime = string;

export interface AuthLoginRequest {
  username: string;
  password: string;
}

export interface AuthLoginResponse {
  access_token: string;
  token_type: "bearer";
}

export interface FeatureFlags {
  rag_enabled: boolean;
  summarizer_enabled: boolean;
  jargon_enabled: boolean;
}

export interface Project {
  id: UUID;
  display_label: string;
  created_at: ISODateTime;
}

export interface CreateProjectRequest {
  student_id?: string;
  display_label: string;
}

export interface UploadedFile {
  id: UUID;
  document_id: UUID;
  filename_redacted: string;
  strategy: "standard" | "deep";
  chunks_added: number;
  uploaded_at: ISODateTime;
}

export interface Citation {
  source: string;
  page: number;
  parent_id: string;
  document_id: UUID;
}

export interface ChatMessage {
  id: UUID;
  role: "user" | "assistant";
  content: string;
  sources: Citation[];
  created_at: ISODateTime;
}

export interface Thread {
  id: UUID;
  title: string | null;
  created_at: ISODateTime;
  messages?: ChatMessage[];
}

export interface SummaryRun {
  id: UUID;
  document_id: UUID;
  filename_redacted: string;
  summary: string;
  page_count: number;
  created_at: ISODateTime;
}

export type JargonLevel = 1 | 2 | 3 | 4 | 5;

export interface JargonRun {
  id: UUID;
  level: JargonLevel;
  input_preview: string;
  simplified_text: string;
  fk_grade: number;
  created_at: ISODateTime;
}

export interface RagPreviewResponse {
  preview_token: UUID;
  sample_text: string;
  entity_map: Record<string, string>;
  page_count: number;
  filename: string;
}

export interface RagUploadResponse {
  status: "ok";
  document_id: UUID;
  source: string;
  strategy: "standard" | "deep";
  chunks_added: number;
  avg_chunk_tokens: number;
}

export type RagMode = "fast" | "deep";

export interface RagQueryRequest {
  question: string;
  project_id: UUID;
  document_id?: UUID;
  thread_id?: UUID;
  mode?: RagMode;
  top_k?: number;
}

export interface RagQueryResponse {
  answer: string;
  mode: RagMode;
  top_k: number;
  thread_id: UUID;
  sources: Citation[];
}

export interface RagDocumentsListResponse {
  total_documents: number;
  documents: { document_id: UUID; filename: string }[];
}

export interface RagDeleteResponse {
  deleted: boolean;
  document_id: UUID;
  filename: string;
  chunks_removed: number;
}

export interface SummarizeJsonRequest {
  document_id: UUID;
  project_id?: UUID;
}

export interface SummarizeResponse {
  summary: string;
  page_count: number;
}

export interface JargonRequest {
  text: string;
  level?: JargonLevel;
  project_id?: UUID;
}

export interface JargonResponse {
  simplified_text: string;
  flesch_kincaid_grade: number;
  level: JargonLevel;
}

export interface ApiErrorDetail {
  detail:
    | string
    | Array<{ loc: string[]; msg: string; type?: string }>;
}
