import apiClient from '@/api/client';
import type { Annotation } from '@/types/annotation';
import { AnnotationType } from '@/types/annotation';
export { AnnotationType };

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
      type: AnnotationType;
      position: string;
      documentUid?: string;
      canvasData: string;
    },
  ): Promise<Annotation> {
    const form = new FormData();
    form.append('title', payload.title);
    form.append('type', payload.type);
    form.append('position', payload.position);
    if (payload.documentUid) {
      form.append('document_uid', payload.documentUid);
    }
    form.append('canvas_data', payload.canvasData);

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

  async updateAnnotationCanvas(projectUid: string, annUid: string, fabricJson: string): Promise<void> {
    const form = new FormData();
    form.append('canvas_data', fabricJson);
    await apiClient.patch(
      `/projects/${projectUid}/annotations/${annUid}/canvas`,
      form,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    );
  },

  async deleteAnnotation(projectUid: string, annUid: string): Promise<void> {
    await apiClient.delete(`/projects/${projectUid}/annotations/${annUid}`);
  },
};
