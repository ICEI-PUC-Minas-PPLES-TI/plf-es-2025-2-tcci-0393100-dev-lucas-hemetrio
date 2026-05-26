import apiClient from '@/api/client';
import type {
  CoOccurrencesResponse,
  KnowledgeGraphResponse,
  MentionsListResponse,
} from '@/types/knowledge';

export const knowledgeService = {
  async getGraph(projectUid: string, signal?: AbortSignal): Promise<KnowledgeGraphResponse> {
    const { data } = await apiClient.get<KnowledgeGraphResponse>(
      `/projects/${projectUid}/knowledge-graph`,
      { signal },
    );
    return data;
  },

  async getNodeMentions(
    projectUid: string,
    nodeUid: string,
    signal?: AbortSignal,
  ): Promise<MentionsListResponse> {
    const { data } = await apiClient.get<MentionsListResponse>(
      `/projects/${projectUid}/knowledge-graph/nodes/${nodeUid}/mentions`,
      { signal },
    );
    return data;
  },

  async getEdgeCoOccurrences(
    projectUid: string,
    aUid: string,
    bUid: string,
    signal?: AbortSignal,
  ): Promise<CoOccurrencesResponse> {
    const { data } = await apiClient.get<CoOccurrencesResponse>(
      `/projects/${projectUid}/knowledge-graph/edges/${aUid}/${bUid}/co-occurrences`,
      { signal },
    );
    return data;
  },

  async rebuildKnowledge(projectUid: string): Promise<void> {
    await apiClient.post(`/projects/${projectUid}/rebuild-knowledge`);
  },
};
