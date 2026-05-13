export enum AnnotationType {
  HANDWRITING = 'HANDWRITING',
  TEXT = 'TEXT',
}

export type AnnotationStatus = 'PROCESSING' | 'INDEXED' | 'FAILED';

export interface Annotation {
  uid: string;
  title: string;
  type: AnnotationType;
  content: string;
  position: string;
  canvas_path: string;
  canvas_image_path: string;
  document_uid?: string;
  status: AnnotationStatus;
  extracted_text: string;
  created_at: string;
}
