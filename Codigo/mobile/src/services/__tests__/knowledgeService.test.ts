jest.mock('@/api/client', () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn() },
}));

import apiClient from '@/api/client';
import { knowledgeService } from '@/services/knowledgeService';

const mockGet = apiClient.get as jest.Mock;
const mockPost = apiClient.post as jest.Mock;

beforeEach(() => {
  mockGet.mockReset();
  mockPost.mockReset();
});

describe('knowledgeService', () => {
  it('getGraph consulta o endpoint do grafo do projeto e devolve o payload', async () => {
    const payload = { nodes: [{ uid: 'n1' }], edges: [] };
    mockGet.mockResolvedValue({ data: payload });

    const result = await knowledgeService.getGraph('p1');

    expect(mockGet).toHaveBeenCalledWith('/projects/p1/knowledge-graph', { signal: undefined });
    expect(result).toBe(payload);
  });

  it('getNodeMentions monta a rota de menções do nó', async () => {
    mockGet.mockResolvedValue({ data: { mentions: [] } });

    await knowledgeService.getNodeMentions('p1', 'n1');

    expect(mockGet).toHaveBeenCalledWith(
      '/projects/p1/knowledge-graph/nodes/n1/mentions',
      { signal: undefined },
    );
  });

  it('getEdgeCoOccurrences monta a rota de co-ocorrências da aresta', async () => {
    mockGet.mockResolvedValue({ data: { co_occurrences: [] } });

    await knowledgeService.getEdgeCoOccurrences('p1', 'a1', 'b1');

    expect(mockGet).toHaveBeenCalledWith(
      '/projects/p1/knowledge-graph/edges/a1/b1/co-occurrences',
      { signal: undefined },
    );
  });

  it('rebuildKnowledge dispara o POST de reconstrução', async () => {
    mockPost.mockResolvedValue({ data: {} });

    await knowledgeService.rebuildKnowledge('p1');

    expect(mockPost).toHaveBeenCalledWith('/projects/p1/rebuild-knowledge');
  });
});
