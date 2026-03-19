import apiClient from '@/api/client';
import type { Project, ProjectPayload } from '@/types/project';

export const projectService = {
  async listProjects(): Promise<Project[]> {
    const { data } = await apiClient.get<Project[]>('/projects');
    return data;
  },

  async createProject(payload: ProjectPayload): Promise<Project> {
    const { data } = await apiClient.post<Project>('/projects', payload);
    return data;
  },

  async renameProject(projectUid: string, payload: ProjectPayload): Promise<Project> {
    const { data } = await apiClient.patch<Project>(`/projects/${projectUid}`, payload);
    return data;
  },

  async deleteProject(projectUid: string): Promise<void> {
    await apiClient.delete(`/projects/${projectUid}`);
  },
};