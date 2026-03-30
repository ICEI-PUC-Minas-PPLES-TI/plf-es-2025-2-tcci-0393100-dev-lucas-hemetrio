export enum DocumentStatus {
  UPLOADING = 'UPLOADING',
  PROCESSING = 'PROCESSING',
  INDEXED = 'INDEXED',
}

export interface Document {
  uid: string;
  title: string;
  file_path: string;
  status: DocumentStatus;
  created_at: string;
}
