import apiClient from '@/api/client';
import type { Annotation } from '@/types/annotation';

export const annotationService = {
  async listAnnotations(projectUid: string): Promise<Annotation[]> {
    const { data } = await apiClient.get<Annotation[]>(
      `/projects/${projectUid}/annotations`,
    );
    return data;
  },

  async createAnnotation(
    projectUid: string,
    payload: {
      title: string;
      position: string;
      documentUid?: string;
      canvasData: string;
      canvasImageBase64?: string;
    },
  ): Promise<Annotation> {
    const form = new FormData();
    form.append('title', payload.title);
    form.append('position', payload.position);
    if (payload.documentUid) {
      form.append('document_uid', payload.documentUid);
    }
    form.append('canvas_data', payload.canvasData);
    if (payload.canvasImageBase64) {
      form.append('canvas_image', payload.canvasImageBase64);
    }

    const { data } = await apiClient.post<Annotation>(
      `/projects/${projectUid}/annotations`,
      form,
      { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 30000 },
    );
    return data;
  },

  async getAnnotationCanvas(projectUid: string, annUid: string): Promise<string> {
    const { data } = await apiClient.get<{ canvas_data: string }>(
      `/projects/${projectUid}/annotations/${annUid}/canvas`,
    );
    return data.canvas_data;
  },

  async updateAnnotationCanvas(
    projectUid: string,
    annUid: string,
    fabricJson: string,
    canvasImageBase64?: string,
  ): Promise<void> {
    const form = new FormData();
    form.append('canvas_data', fabricJson);
    if (canvasImageBase64) {
      form.append('canvas_image', canvasImageBase64);
    }
    await apiClient.patch(
      `/projects/${projectUid}/annotations/${annUid}/canvas`,
      form,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    );
  },

  async reprocessAnnotation(projectUid: string, annUid: string): Promise<void> {
    await apiClient.post(`/projects/${projectUid}/annotations/${annUid}/reprocess`);
  },

  async deleteAnnotation(projectUid: string, annUid: string): Promise<void> {
    await apiClient.delete(`/projects/${projectUid}/annotations/${annUid}`);
  },
};
