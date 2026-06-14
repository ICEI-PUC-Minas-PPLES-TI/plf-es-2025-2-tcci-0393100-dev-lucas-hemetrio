import apiClient, { API_BASE_URL } from '@/api/client';
import type { Document } from '@/types/document';

export const documentService = {
  async listDocuments(projectUid: string): Promise<Document[]> {
    const { data } = await apiClient.get<Document[]>(`/projects/${projectUid}/documents`);
    return data;
  },

  async uploadDocument(
    projectUid: string,
    file: { uri: string; name: string; mimeType: string },
  ): Promise<Document> {
    const form = new FormData();
    form.append('file', {
      uri: file.uri,
      name: file.name,
      type: file.mimeType,
    } as unknown as Blob);

    const { data } = await apiClient.post<Document>(
      `/projects/${projectUid}/documents`,
      form,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 300000,
      },
    );
    return data;
  },

  async deleteDocument(projectUid: string, docUid: string): Promise<void> {
    await apiClient.delete(`/projects/${projectUid}/documents/${docUid}`);
  },

  async reprocessDocument(projectUid: string, docUid: string): Promise<void> {
    await apiClient.post(`/projects/${projectUid}/documents/${docUid}/reprocess`);
  },

  async getDocumentUrl(projectUid: string, docUid: string): Promise<string> {
    const { data } = await apiClient.get<{ url: string }>(
      `/projects/${projectUid}/documents/${docUid}/url`,
    );
    return data.url;
  },

  getDocumentStreamUrl(projectUid: string, docUid: string): string {
    return `${API_BASE_URL}/projects/${projectUid}/documents/${docUid}/stream`;
  },

  async getDocumentBase64(projectUid: string, docUid: string): Promise<string> {
    const response = await apiClient.get(
      `/projects/${projectUid}/documents/${docUid}/stream`,
      { responseType: 'arraybuffer', timeout: 30000 },
    );
    const bytes = new Uint8Array(response.data as ArrayBuffer);
    const chunks: string[] = [];
    for (let i = 0; i < bytes.length; i += 8192) {
      chunks.push(String.fromCharCode(...bytes.subarray(i, i + 8192)));
    }
    return 'data:application/pdf;base64,' + btoa(chunks.join(''));
  },
};
