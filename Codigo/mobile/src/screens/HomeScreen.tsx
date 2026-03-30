import React, { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Modal,
  Pressable,
  Text,
  TextInput,
  TouchableOpacity,
  useWindowDimensions,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '@/context/AuthContext';
import { projectService } from '@/services/projectService';
import type { Project } from '@/types/project';
import DocumentList from '@/components/DocumentList';
import { Menu, PanelRightClose } from 'lucide-react-native/icons';


export default function HomeScreen() {
  const { signOut } = useAuth();
  const { width } = useWindowDimensions();
  const isTablet = width >= 768;

  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [isLoadingProjects, setIsLoadingProjects] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(isTablet);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [modalMode, setModalMode] = useState<'create' | 'rename'>('create');
  const [projectName, setProjectName] = useState('');
  const [projectBeingEdited, setProjectBeingEdited] = useState<Project | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    setIsSidebarOpen(isTablet);
  }, [isTablet]);

  useEffect(() => {
    void loadProjects();
  }, []);

  useEffect(() => {
    if (!selectedProjectId && projects.length > 0) {
      setSelectedProjectId(projects[0].uid);
    }

    if (selectedProjectId && !projects.some((project) => project.uid === selectedProjectId)) {
      setSelectedProjectId(projects[0]?.uid ?? null);
    }
  }, [projects, selectedProjectId]);

  const selectedProject = useMemo(
    () => projects.find((project) => project.uid === selectedProjectId) ?? null,
    [projects, selectedProjectId],
  );

  async function loadProjects() {
    setIsLoadingProjects(true);
    setErrorMessage(null);

    try {
      const data = await projectService.listProjects();
      setProjects(data);
    } catch {
      setErrorMessage('Não foi possível carregar seus projetos.');
    } finally {
      setIsLoadingProjects(false);
    }
  }

  function openCreateProjectModal() {
    setModalMode('create');
    setProjectBeingEdited(null);
    setProjectName('');
    setIsModalVisible(true);

    if (!isTablet) {
      setIsSidebarOpen(false);
    }
  }

  function openRenameProjectModal(project: Project) {
    setModalMode('rename');
    setProjectBeingEdited(project);
    setProjectName(project.name);
    setIsModalVisible(true);
  }

  async function submitProjectForm() {
    const trimmedName = projectName.trim();

    if (!trimmedName) {
      setErrorMessage('Informe um nome para o projeto.');
      return;
    }

    setIsSaving(true);
    setErrorMessage(null);

    try {
      if (modalMode === 'create') {
        const createdProject = await projectService.createProject({ name: trimmedName });
        setProjects((currentProjects) => [createdProject, ...currentProjects]);
        setSelectedProjectId(createdProject.uid);
      } else if (projectBeingEdited) {
        const updatedProject = await projectService.renameProject(projectBeingEdited.uid, {
          name: trimmedName,
        });

        setProjects((currentProjects) =>
          currentProjects.map((project) =>
            project.uid === updatedProject.uid ? updatedProject : project,
          ),
        );
      }

      setIsModalVisible(false);
      setProjectBeingEdited(null);
      setProjectName('');
    } catch {
      setErrorMessage('Não foi possível salvar o projeto.');
    } finally {
      setIsSaving(false);
    }
  }

  function confirmDeleteProject(project: Project) {
    Alert.alert('Excluir projeto', `Deseja excluir "${project.name}"? Esta ação não pode ser desfeita.`, [
      { text: 'Cancelar', style: 'cancel' },
      {
        text: 'Excluir',
        style: 'destructive',
        onPress: () => void deleteProject(project.uid),
      },
    ]);
  }

  async function deleteProject(projectUid: string) {
    setIsSaving(true);
    setErrorMessage(null);

    try {
      await projectService.deleteProject(projectUid);
      setProjects((currentProjects) => currentProjects.filter((project) => project.uid !== projectUid));
      setSelectedProjectId((currentSelectedId) =>
        currentSelectedId === projectUid ? null : currentSelectedId,
      );
    } catch {
      setErrorMessage('Não foi possível excluir o projeto.');
    } finally {
      setIsSaving(false);
    }
  }

  function renderProjectItem({ item }: { item: Project }) {
    const isSelected = item.uid === selectedProjectId;

    return (
      <TouchableOpacity
        className={`mb-3 rounded-2xl border px-4 py-4 ${
          isSelected ? 'border-primary bg-blue-50' : 'border-gray-200 bg-white'
        }`}
        activeOpacity={0.85}
        onPress={() => setSelectedProjectId(item.uid)}
      >
        <Text className="text-base font-semibold text-gray-900">{item.name}</Text>
      </TouchableOpacity>
    );
  }

  return (
    <SafeAreaView className="flex-1 bg-gray-50">
      <View className="flex-1 flex-row">
        {isSidebarOpen && !isTablet ? (
          <Pressable
            className="absolute inset-0 z-10 bg-black/30"
            onPress={() => setIsSidebarOpen(false)}
          />
        ) : null}

        {isSidebarOpen && (
          <View
            className={`z-20 border-r border-gray-200 bg-white ${
              isTablet ? 'w-80' : 'absolute left-0 top-0 h-full w-80 shadow-lg'
            }`}
          >
            <View className="flex-row items-center justify-between border-b border-gray-100 px-5 py-5">
              <View>
                <Text className="text-2xl font-bold text-gray-900">Cognita</Text>
                <Text className="mt-1 text-sm text-gray-500">Projetos</Text>
              </View>

              <TouchableOpacity
                className="h-10 w-10 items-center justify-center rounded-xl border border-gray-200 bg-white"
                activeOpacity={0.85}
                onPress={() => setIsSidebarOpen(false)}
              >
                <PanelRightClose size={18} color="#111827" />
              </TouchableOpacity>
            </View>

            <View className="flex-1 px-5 py-4">
              <TouchableOpacity
                className="mb-4 rounded-2xl bg-primary px-4 py-3"
                activeOpacity={0.85}
                onPress={openCreateProjectModal}
              >
                <Text className="text-center text-sm font-semibold text-white">Novo projeto</Text>
              </TouchableOpacity>

              {isLoadingProjects ? (
                <View className="mt-6 items-center justify-center">
                  <ActivityIndicator color="#3B82F6" />
                </View>
              ) : (
                <FlatList
                  data={projects}
                  keyExtractor={(item) => item.uid}
                  renderItem={renderProjectItem}
                  contentContainerStyle={{ paddingBottom: 24 }}
                  ListEmptyComponent={
                    <View className="mt-8 rounded-2xl border border-dashed border-gray-300 bg-gray-50 px-4 py-6">
                      <Text className="text-sm font-semibold text-gray-800">Nenhum projeto criado</Text>
                      <Text className="mt-1 text-sm text-gray-500">
                        Use o botão acima para criar o primeiro projeto.
                      </Text>
                    </View>
                  }
                />
              )}
            </View>

            <View className="border-t border-gray-100 px-5 py-4">
              <TouchableOpacity
                className="rounded-2xl border border-gray-200 bg-white px-4 py-3"
                onPress={signOut}
                activeOpacity={0.8}
              >
                <Text className="text-center text-sm font-semibold text-gray-800">Sair</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        <View className="flex-1 px-4 py-4 md:px-6 lg:px-10">
          {!isSidebarOpen ? (
            <TouchableOpacity
              className="absolute left-4 top-4 z-30 h-11 w-11 items-center justify-center rounded-2xl border border-gray-200 bg-white shadow"
              activeOpacity={0.9}
              onPress={() => setIsSidebarOpen(true)}
            >
              <Menu size={20} color="#111827" />
            </TouchableOpacity>
          ) : null}

          {errorMessage ? (
            <View className="mb-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3">
              <Text className="text-sm font-semibold text-red-700">{errorMessage}</Text>
            </View>
          ) : null}

          <View className="flex-1 rounded-3xl border border-gray-200 bg-white px-5 py-5 shadow-sm">
            {selectedProject ? (
              <>
                <Text className="text-2xl font-bold text-gray-900">{selectedProject.name}</Text>

                <View className="mt-4 flex-row flex-wrap gap-3">
                  <TouchableOpacity
                    className="rounded-2xl border border-gray-200 bg-white px-4 py-3"
                    activeOpacity={0.85}
                    onPress={() => openRenameProjectModal(selectedProject)}
                  >
                    <Text className="text-sm font-semibold text-gray-800">Renomear projeto</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3"
                    activeOpacity={0.85}
                    onPress={() => confirmDeleteProject(selectedProject)}
                  >
                    <Text className="text-sm font-semibold text-red-700">Excluir projeto</Text>
                  </TouchableOpacity>
                </View>

                <DocumentList projectUid={selectedProject.uid} />
              </>
            ) : (
              <View className="flex-1 items-center justify-center px-6">
                <Text className="text-center text-2xl font-bold text-gray-900">
                  Nenhum projeto selecionado
                </Text>
                <Text className="mt-2 text-center text-base text-gray-500">
                  Selecione um projeto na lateral ou crie um novo para começar.
                </Text>
              </View>
            )}
          </View>
        </View>
      </View>

      <Modal
        animationType="fade"
        transparent
        visible={isModalVisible}
        onRequestClose={() => setIsModalVisible(false)}
      >
        <View className="flex-1 items-center justify-center bg-black/40 px-5">
          <View className="w-full max-w-xl rounded-3xl bg-white p-5">
            <Text className="text-xl font-bold text-gray-900">
              {modalMode === 'create' ? 'Novo projeto' : 'Renomear projeto'}
            </Text>
            <Text className="mt-1 text-sm text-gray-500">
              {modalMode === 'create'
                ? 'Defina o nome do novo projeto.'
                : 'Atualize o nome do projeto selecionado.'}
            </Text>

            <TextInput
              className="mt-5 rounded-2xl border border-gray-200 bg-gray-50 px-4 py-4 text-base text-gray-900"
              placeholder="Nome do projeto"
              placeholderTextColor="#9CA3AF"
              value={projectName}
              onChangeText={setProjectName}
              autoFocus
            />

            <View className="mt-5 flex-row justify-end gap-3">
              <TouchableOpacity
                className="rounded-2xl border border-gray-200 bg-white px-4 py-3"
                activeOpacity={0.85}
                onPress={() => setIsModalVisible(false)}
                disabled={isSaving}
              >
                <Text className="text-sm font-semibold text-gray-800">Cancelar</Text>
              </TouchableOpacity>
              <TouchableOpacity
                className="rounded-2xl bg-primary px-4 py-3"
                activeOpacity={0.85}
                onPress={() => void submitProjectForm()}
                disabled={isSaving}
              >
                <Text className="text-sm font-semibold text-white">
                  {isSaving ? 'Salvando...' : 'Salvar'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}
