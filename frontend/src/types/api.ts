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

export type LabMeasurement = {
  test_name: string;
  value: number;
  unit: string | null;
  reference_low: number | null;
  reference_high: number | null;
};

export type DocumentMetadata = {
  patient_name: string | null;
  doctor_name: string | null;
  hospital_name: string | null;
  document_date: string | null;
  specialization: string | null;
  diagnosis: string | null;
  clinical_summary: string | null;
  admission_date: string | null;
  discharge_date: string | null;
  follow_up: string | null;
  medicines: Medicine[];
  lab_measurements: LabMeasurement[];
  procedures: string[];
  allergies: string[];
  medical_devices: string[];
  vaccinations: string[];
};

export type ImportantDate = {
  date: string;
  label: string;
};

export type DocumentSummary = {
  short_summary: string;
  key_findings: string[];
  important_dates: ImportantDate[];
  highlights: string[];
};

export type ProcessingStage =
  | "uploaded"
  | "extract"
  | "ocr"
  | "classification"
  | "metadata"
  | "summary"
  | "metadata_summary"
  | "embeddings"
  | "ready"
  | "failed";

export type ProcessingJobStatus =
  | "pending"
  | "running"
  | "paused"
  | "rate_limited"
  | "completed"
  | "failed";

export type DocumentProcessingJob = {
  id: string;
  stage: ProcessingStage;
  status: ProcessingJobStatus;
  error_message: string | null;
  retry_count: number;
  next_retry_at: string | null;
  wait_reason: string | null;
  started_at: string | null;
  updated_at: string;
};

export type Document = {
  id: string;
  family_member_id: string;
  original_filename: string;
  content_type: string;
  file_size_bytes: number;
  page_count: number | null;
  status: DocumentStatus;
  processing_status: ProcessingStage;
  processing_job: DocumentProcessingJob | null;
  document_type: DocumentType | null;
  document_date: string | null;
  classification_confidence: number | null;
  classification_reasoning: string | null;
  metadata: DocumentMetadata | null;
  summary: DocumentSummary | null;
  extracted_text: string | null;
  processing_error: string | null;
  uploaded_at: string | null;
  processed_at: string | null;
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
  page: number | null;
  excerpt: string | null;
  summary: string | null;
};

export type ChatSupportingDetails = {
  patient: string | null;
  doctor: string | null;
  hospital: string | null;
  diagnosis: string | null;
  medicines: string[];
  lab_values: string[];
  procedures: string[];
  follow_up: string | null;
};

export type ChatTimelineEntry = {
  date: string | null;
  label: string | null;
  detail: string | null;
};

export type ChatAskResponse = {
  question: string;
  answer: string;
  insufficient_context: boolean;
  citations: ChatCitation[];
  supporting_details: ChatSupportingDetails | null;
  timeline: ChatTimelineEntry[];
  model_name: string | null;
};

export type TimelineEventType =
  | "document"
  | "admission"
  | "discharge"
  | "diagnosis"
  | "procedure"
  | "lab_result"
  | "medication"
  | "allergy"
  | "device"
  | "vaccination"
  | "follow_up"
  | "visit"
  | "imaging";

export type TimelineEvent = {
  id: string;
  document_id: string;
  family_member_id: string;
  event_date: string;
  event_type: TimelineEventType;
  title: string;
  description: string | null;
  source_field: string | null;
  document_type: DocumentType | null;
  original_filename: string | null;
};

export type TimelineListResponse = {
  items: TimelineEvent[];
  total: number;
};

export type HealthTrendPoint = {
  date: string;
  value: number;
  unit: string | null;
  reference_low: number | null;
  reference_high: number | null;
  document_id: string;
};

export type HealthTrendSeries = {
  test_name: string;
  unit: string | null;
  points: HealthTrendPoint[];
};

export type HealthTrendsResponse = {
  family_member_id: string;
  series: HealthTrendSeries[];
  total_measurements: number;
};

export type ApiErrorBody = {
  error?: {
    code?: string;
    message?: string;
    details?: unknown;
  };
};
