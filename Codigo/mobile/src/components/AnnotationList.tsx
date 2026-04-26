import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, FlatList, Text, TouchableOpacity, View } from 'react-native';

import { annotationService } from '@/services/annotationService';
import type { Annotation } from '@/types/annotation';
import { AnnotationType } from '@/types/annotation';

interface Props {
  projectUid: string;
  selectedAnnotationId?: string | null;
  onSelectAnnotation: (annotation: Annotation) => void;
  onNew: () => void;
}

export default function AnnotationList({ projectUid, selectedAnnotationId, onSelectAnnotation, onNew }: Props) {
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const loadAnnotations = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await annotationService.listAnnotations(projectUid);
      setAnnotations(data.filter((a) => !a.document_uid));
    } catch {
      Alert.alert('Erro', 'Não foi possível carregar as anotações.');
    } finally {
      setIsLoading(false);
    }
  }, [projectUid]);

  useEffect(() => {
    void loadAnnotations();
  }, [loadAnnotations]);

  function confirmDelete(ann: Annotation) {
    Alert.alert('Excluir anotação', `Deseja excluir "${ann.title}"?`, [
      { text: 'Cancelar', style: 'cancel' },
      {
        text: 'Excluir',
        style: 'destructive',
        onPress: async () => {
          try {
            await annotationService.deleteAnnotation(projectUid, ann.uid);
            setAnnotations((prev) => prev.filter((a) => a.uid !== ann.uid));
          } catch {
            Alert.alert('Erro', 'Não foi possível excluir a anotação.');
          }
        },
      },
    ]);
  }

  function renderItem({ item }: { item: Annotation }) {
    const isSelected = item.uid === selectedAnnotationId;

    return (
      <TouchableOpacity
        activeOpacity={0.85}
        onPress={() => onSelectAnnotation(item)}
        className={`mb-3 flex-row items-center rounded-2xl border p-4 ${
          isSelected ? 'border-primary bg-blue-50' : 'border-gray-100 bg-white'
        }`}
      >
        <View className="mr-3 h-10 w-10 items-center justify-center rounded-xl bg-gray-100">
          <Text style={{ fontSize: 16 }}>{item.type === AnnotationType.TEXT ? 'T' : '✏️'}</Text>
        </View>

        <View className="flex-1">
          <Text className="text-sm font-semibold text-gray-900" numberOfLines={1}>
            {item.title}
          </Text>
          <Text className="mt-0.5 text-xs text-gray-400">
            {item.document_uid ? 'Overlay de PDF' : 'Whiteboard livre'}
            {' · '}
            {new Date(item.created_at).toLocaleDateString('pt-BR')}
          </Text>
        </View>

        <TouchableOpacity
          activeOpacity={0.7}
          onPress={() => confirmDelete(item)}
          className="ml-2 p-1"
        >
          <Text style={{ color: '#EF4444', fontSize: 16 }}>✕</Text>
        </TouchableOpacity>
      </TouchableOpacity>
    );
  }

  return (
    <View className="flex-1">
      <View className="mb-4 flex-row items-center justify-between">
        <Text className="text-lg font-bold text-gray-900">Anotações</Text>
        <TouchableOpacity
          activeOpacity={0.85}
          onPress={onNew}
          className="flex-row items-center gap-2 rounded-xl bg-primary px-3 py-2"
        >
          <Text className="text-sm font-semibold text-white">+ Nova</Text>
        </TouchableOpacity>
      </View>

      {isLoading ? (
        <View className="flex-1 items-center justify-center">
          <ActivityIndicator size="large" color="#3B82F6" />
        </View>
      ) : (
        <FlatList
          data={annotations}
          keyExtractor={(item) => item.uid}
          renderItem={renderItem}
          contentContainerStyle={{ paddingBottom: 24 }}
          ListEmptyComponent={
            <View className="items-center py-12">
              <Text style={{ fontSize: 32, color: '#D1D5DB' }}>✏️</Text>
              <Text className="mt-3 text-sm text-gray-400">
                Nenhuma anotação neste projeto ainda.
              </Text>
            </View>
          }
        />
      )}
    </View>
  );
}
