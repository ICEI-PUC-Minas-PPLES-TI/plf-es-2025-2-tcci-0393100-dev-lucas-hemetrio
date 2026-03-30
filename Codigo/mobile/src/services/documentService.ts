import apiClient from '@/api/client';
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
        timeout: 60000,
      },
    );
    return data;
  },

  async deleteDocument(projectUid: string, docUid: string): Promise<void> {
    await apiClient.delete(`/projects/${projectUid}/documents/${docUid}`);
  },
};
