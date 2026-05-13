export enum DocumentStatus {
  PROCESSING = 'PROCESSING',
  INDEXED = 'INDEXED',
  FAILED = 'FAILED',
}

export interface Document {
  uid: string;
  title: string;
  file_path: string;
  status: DocumentStatus;
  created_at: string;
  page_count?: number;
}
