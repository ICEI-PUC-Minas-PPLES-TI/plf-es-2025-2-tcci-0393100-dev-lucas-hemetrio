import * as DocumentPicker from 'expo-document-picker';
import { FileText, Trash2, Upload } from 'lucide-react-native/icons';
import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, FlatList, Text, TouchableOpacity, View } from 'react-native';

import { documentService } from '@/services/documentService';
import { Document, DocumentStatus } from '@/types/document';

interface Props {
  projectUid: string;
  selectedDocumentId?: string | null;
  onSelectDocument?: (uid: string) => void;
}

const STATUS_STYLES: Record<DocumentStatus, { container: string; text: string; label: string }> = {
  [DocumentStatus.PROCESSING]: {
    container: 'border border-blue-200 bg-blue-50 px-2.5 py-1 rounded-lg',
    text: 'text-xs font-semibold text-blue-700',
    label: 'Processando',
  },
  [DocumentStatus.INDEXED]: {
    container: 'border border-green-200 bg-green-50 px-2.5 py-1 rounded-lg',
    text: 'text-xs font-semibold text-green-700',
    label: 'Indexado',
  },
  [DocumentStatus.FAILED]: {
    container: 'border border-red-200 bg-red-50 px-2.5 py-1 rounded-lg',
    text: 'text-xs font-semibold text-red-700',
    label: 'Falha no processamento',
  },
};

export default function DocumentList({ projectUid, selectedDocumentId, onSelectDocument }: Props) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);

  const loadDocuments = useCallback(async () => {
    setIsLoading(true);
    try {
      const docs = await documentService.listDocuments(projectUid);
      setDocuments(docs);
    } catch (err) {
      console.error('[DocumentList] loadDocuments error:', err);
      Alert.alert('Erro', 'Não foi possível carregar os documentos.');
    } finally {
      setIsLoading(false);
    }
  }, [projectUid]);

  useEffect(() => {
    void loadDocuments();
  }, [loadDocuments]);

  useEffect(() => {
    const hasPending = documents.some((d) => d.status === DocumentStatus.PROCESSING && !d.uid.startsWith('temp-'));
    if (!hasPending) return;
    const id = setInterval(() => {
      void loadDocuments();
    }, 5000);
    return () => clearInterval(id);
  }, [documents, loadDocuments]);

  function handleUpload() {
    DocumentPicker.getDocumentAsync({
      type: 'application/pdf',
      copyToCacheDirectory: true,
    }).then((result) => {
      if (result.canceled || !result.assets?.[0]) return;

      const asset = result.assets[0];
      const tempDoc: Document = {
        uid: `temp-${Date.now()}`,
        title: asset.name,
        file_path: '',
        status: DocumentStatus.PROCESSING,
        created_at: new Date().toISOString(),
      };

      setDocuments((prev) => [tempDoc, ...prev]);
      setIsUploading(true);

      documentService
        .uploadDocument(projectUid, {
          uri: asset.uri,
          name: asset.name,
          mimeType: asset.mimeType ?? 'application/pdf',
        })
        .then((realDoc) => {
          setDocuments((prev) => prev.map((d) => (d.uid === tempDoc.uid ? realDoc : d)));
        })
        .catch(() => {
          setDocuments((prev) => prev.filter((d) => d.uid !== tempDoc.uid));
          Alert.alert('Erro', 'Não foi possível enviar o documento.');
        })
        .finally(() => {
          setIsUploading(false);
        });
    });
  }

  function confirmDelete(doc: Document) {
    Alert.alert('Excluir documento', `Deseja excluir "${doc.title}"?`, [
      { text: 'Cancelar', style: 'cancel' },
      {
        text: 'Excluir',
        style: 'destructive',
        onPress: () => void handleDelete(doc),
      },
    ]);
  }

  async function handleDelete(doc: Document) {
    try {
      await documentService.deleteDocument(projectUid, doc.uid);
      setDocuments((prev) => prev.filter((d) => d.uid !== doc.uid));
    } catch {
      Alert.alert('Erro', 'Não foi possível excluir o documento.');
    }
  }

  async function handleReprocess(doc: Document) {
    try {
      await documentService.reprocessDocument(projectUid, doc.uid);
      await loadDocuments();
    } catch {
      Alert.alert('Erro', 'Não foi possível reprocessar o documento.');
    }
  }

  function renderItem({ item }: { item: Document }) {
    const isTemp = item.uid.startsWith('temp-');
    const isSelected = item.uid === selectedDocumentId;
    const statusStyle = STATUS_STYLES[item.status] ?? STATUS_STYLES[DocumentStatus.PROCESSING];

    return (
      <TouchableOpacity
        activeOpacity={0.85}
        onPress={() => !isTemp && onSelectDocument?.(item.uid)}
        className={`mb-3 rounded-2xl border p-4 ${
          isSelected ? 'border-primary bg-blue-50' : 'border-gray-100 bg-white'
        }`}
      >
        <View className="flex-row items-center">
          <View className="mr-3 h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gray-100">
            <FileText size={20} color={isSelected ? '#3B82F6' : '#6B7280'} />
          </View>

          <View className="flex-1">
            <Text className="text-sm font-semibold text-gray-900" numberOfLines={1}>
              {item.title}
            </Text>
            <View className="mt-1.5">
              <View className={`self-start ${statusStyle.container}`}>
                <Text className={statusStyle.text}>{statusStyle.label}</Text>
              </View>
            </View>
          </View>

          {!isTemp && (
            <TouchableOpacity
              activeOpacity={0.7}
              onPress={() => confirmDelete(item)}
              className="ml-2 shrink-0 p-1"
            >
              <Trash2 size={18} color="#EF4444" />
            </TouchableOpacity>
          )}
        </View>

        {item.status === DocumentStatus.FAILED && !isTemp && (
          <TouchableOpacity
            activeOpacity={0.85}
            onPress={() => void handleReprocess(item)}
            className="mt-3 self-stretch rounded-lg border border-red-200 bg-red-50 px-3 py-2"
          >
            <Text className="text-center text-xs font-semibold text-red-700">
              Tentar novamente
            </Text>
          </TouchableOpacity>
        )}
      </TouchableOpacity>
    );
  }

  return (
    <View className="mt-6 flex-1">
      <View className="mb-4 flex-row items-center justify-between">
        <Text className="text-lg font-bold text-gray-900">Documentos</Text>
        <TouchableOpacity
          activeOpacity={0.85}
          onPress={handleUpload}
          disabled={isUploading}
          className="flex-row items-center gap-2 rounded-xl bg-primary px-4 py-2.5"
        >
          {isUploading ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Upload size={16} color="#fff" />
          )}
          <Text className="text-sm font-semibold text-white">
            {isUploading ? 'Enviando...' : 'Enviar PDF'}
          </Text>
        </TouchableOpacity>
      </View>

      {isLoading ? (
        <View className="flex-1 items-center justify-center py-12">
          <ActivityIndicator size="large" color="#3B82F6" />
        </View>
      ) : (
        <FlatList
          data={documents}
          keyExtractor={(item) => item.uid}
          renderItem={renderItem}
          contentContainerStyle={{ paddingBottom: 24 }}
          ListEmptyComponent={
            <View className="items-center py-12">
              <FileText size={40} color="#D1D5DB" />
              <Text className="mt-3 text-sm text-gray-400">
                Nenhum documento neste projeto ainda.
              </Text>
            </View>
          }
        />
      )}
    </View>
  );
}
