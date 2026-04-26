export enum AnnotationType {
  HANDWRITING = 'HANDWRITING',
  TEXT = 'TEXT',
}

export interface Annotation {
  uid: string;
  title: string;
  type: AnnotationType;
  content: string;
  position: string;
  canvas_path: string;
  document_uid?: string;
  status: 'UPLOADING' | 'PROCESSING' | 'INDEXED';
  created_at: string;
}
