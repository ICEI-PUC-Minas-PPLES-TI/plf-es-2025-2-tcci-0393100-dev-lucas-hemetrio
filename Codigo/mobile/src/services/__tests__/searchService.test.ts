jest.mock('@/api/client', () => ({
  __esModule: true,
  default: { get: jest.fn() },
}));

import apiClient from '@/api/client';
import { searchService } from '@/services/searchService';

const mockGet = apiClient.get as jest.Mock;

beforeEach(() => {
  mockGet.mockReset();
});

describe('searchService', () => {
  it('search chama /search passando o termo como query param e devolve o payload', async () => {
    const payload = { query: 'redes', total: 0, results_by_project: [] };
    mockGet.mockResolvedValue({ data: payload });

    const result = await searchService.search('redes');

    expect(mockGet).toHaveBeenCalledWith('/search', { params: { q: 'redes' }, signal: undefined });
    expect(result).toBe(payload);
  });
});
