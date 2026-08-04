export type DocumentStatus =
  | "pending"
  | "processing"
  | "completed"
  | "failed"
  | "rejected";

export type DocumentType =
  | "prescription"
  | "lab_report"
  | "hospital_bill"
  | "pharmacy_bill"
  | "discharge_summary"
  | "imaging_report"
  | "other"
  | "unrelated";

export type RelationshipType =
  | "self"
  | "mother"
  | "father"
  | "child"
  | "spouse"
  | "other";

export type UserPublic = {
  id: string;
  email: string;
  full_name: string;
};

export type UserDetail = UserPublic & {
  created_at: string;
  updated_at: string;
};

export type AuthResponse = {
  user: UserPublic;
  access_token: string;
  token_type: string;
  expires_in: number;
};

export type SessionUser = {
  user: UserDetail;
};

export type MessageResponse = {
  message: string;
};

export type Medicine = {
  name: string;
  dosage: string | null;
  frequency: string | null;
  duration: string | null;
};

export type DocumentMetadata = {
  patient_name: string | null;
  doctor_name: string | null;
  hospital_name: string | null;
  document_date: string | null;
  specialization: string | null;
  diagnosis: string | null;
  medicines: Medicine[];
};

export type ImportantDate = {
  date: string;
  label: string;
};

export type DocumentSummary = {
  short_summary: string;
  key_findings: string[];
  important_dates: ImportantDate[];
};

export type Document = {
  id: string;
  family_member_id: string;
  original_filename: string;
  content_type: string;
  file_size_bytes: number;
  status: DocumentStatus;
  document_type: DocumentType | null;
  document_date: string | null;
  classification_confidence: number | null;
  classification_reasoning: string | null;
  metadata: DocumentMetadata | null;
  summary: DocumentSummary | null;
  extracted_text: string | null;
  processing_error: string | null;
  created_at: string;
  updated_at: string;
};

export type DocumentListResponse = {
  items: Document[];
  total: number;
};

export type DocumentUploadListResponse = {
  items: Document[];
  total: number;
};

export type FamilyMember = {
  id: string;
  name: string;
  relationship_type: RelationshipType;
  date_of_birth: string | null;
  created_at: string;
  updated_at: string;
};

export type FamilyMemberListResponse = {
  items: FamilyMember[];
  total: number;
};

export type FamilyMemberCreate = {
  name: string;
  relationship_type: RelationshipType;
  date_of_birth?: string | null;
};

export type FamilyMemberUpdate = {
  name?: string;
  relationship_type?: RelationshipType;
  date_of_birth?: string | null;
};

export type SearchRequest = {
  query: string;
  limit?: number;
  min_score?: number;
  family_member_id?: string | null;
};

export type SearchCitation = {
  document_id: string;
  original_filename: string;
  document_type: DocumentType | null;
  document_date: string | null;
  family_member_id: string;
  excerpt: string | null;
  summary: string | null;
};

export type SearchResultItem = {
  rank: number;
  score: number;
  document_id: string;
  citation: SearchCitation;
};

export type SearchResponse = {
  query: string;
  total: number;
  results: SearchResultItem[];
  citations: SearchCitation[];
};

export type ChatAskRequest = {
  question: string;
  top_k?: number;
  min_score?: number;
  family_member_id?: string | null;
};

export type ChatCitation = {
  document_id: string;
  original_filename: string;
  document_type: DocumentType | null;
  document_date: string | null;
  family_member_id: string;
  score: number;
  excerpt: string | null;
  summary: string | null;
};

export type ChatAskResponse = {
  question: string;
  answer: string;
  insufficient_context: boolean;
  citations: ChatCitation[];
  model_name: string | null;
};

export type ApiErrorBody = {
  error?: {
    code?: string;
    message?: string;
    details?: unknown;
  };
};
