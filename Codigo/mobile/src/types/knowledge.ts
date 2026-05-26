export type EntityLabel = 'PER' | 'LOC' | 'ORG';

export type KnowledgeStatus = 'IDLE' | 'PROCESSING' | 'DONE' | 'FAILED';

export interface KnowledgeNode {
  uid: string;
  label: EntityLabel;
  text: string;
  mention_count: number;
}

export interface KnowledgeEdge {
  source: string;
  target: string;
  weight: number;
}

export interface KnowledgeGraphResponse {
  status: KnowledgeStatus;
  updated_at: string | null;
  nodes: KnowledgeNode[];
  edges: KnowledgeEdge[];
}

export interface Mention {
  uid: string;
  sentence_text: string;
  source_type: 'document' | 'annotation';
  source_uid: string;
  source_title: string;
  page_number: number | null;
}

export interface MentionsListResponse {
  node: KnowledgeNode;
  mentions: Mention[];
}

export interface CoOccurrence {
  sentence_text: string;
  source_type: 'document' | 'annotation';
  source_uid: string;
  source_title: string;
  page_number: number | null;
}

export interface CoOccurrencesResponse {
  node_a: KnowledgeNode;
  node_b: KnowledgeNode;
  weight: number;
  co_occurrences: CoOccurrence[];
}

export type GraphSelection =
  | { type: 'node'; uid: string }
  | { type: 'edge'; a_uid: string; b_uid: string };
