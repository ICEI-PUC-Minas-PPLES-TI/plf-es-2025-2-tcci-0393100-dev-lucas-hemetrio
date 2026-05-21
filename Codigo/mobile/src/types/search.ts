export interface SearchProjectRef {
  uid: string;
  name: string;
}

export interface SearchDocumentRef {
  uid: string;
  title: string;
}

export interface SearchAnnotationRef {
  uid: string;
  title: string;
}

export interface SearchPageHit {
  page_number: number;
  snippet: string;
  score: number;
}

export interface SearchTitleMatch {
  snippet: string;
}

export interface SearchDocumentGroup {
  document: SearchDocumentRef;
  title_match: SearchTitleMatch | null;
  page_hits: SearchPageHit[];
}

export interface SearchAnnotationHit {
  annotation: SearchAnnotationRef;
  snippet: string;
  score: number;
}

export interface SearchProjectGroup {
  project: SearchProjectRef;
  documents: SearchDocumentGroup[];
  annotations: SearchAnnotationHit[];
}

export interface SearchResponse {
  query: string;
  total: number;
  results_by_project: SearchProjectGroup[];
}

export type SearchTarget =
  | { kind: 'document'; projectUid: string; documentUid: string; initialPage?: number }
  | { kind: 'annotation'; projectUid: string; annotationUid: string };
