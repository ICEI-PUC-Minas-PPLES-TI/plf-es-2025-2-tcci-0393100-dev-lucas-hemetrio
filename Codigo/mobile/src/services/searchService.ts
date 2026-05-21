import apiClient from '@/api/client';
import type { SearchResponse } from '@/types/search';

export const searchService = {
  async search(query: string, signal?: AbortSignal): Promise<SearchResponse> {
    const { data } = await apiClient.get<SearchResponse>('/search', {
      params: { q: query },
      signal,
    });
    return data;
  },
};
