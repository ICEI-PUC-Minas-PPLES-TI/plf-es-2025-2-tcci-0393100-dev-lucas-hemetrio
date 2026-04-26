// mobile/src/components/CanvasEditor.tsx
import React, { useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Text,
  TextInput,
  View,
} from 'react-native';
import { WebView, type WebViewMessageEvent } from 'react-native-webview';

import { annotationService } from '@/services/annotationService';
import { documentService } from '@/services/documentService';
import { getToken } from '@/storage/tokenStorage';
import type { Annotation } from '@/types/annotation';
import { AnnotationType } from '@/types/annotation';
import { canvasEditorHtml } from '@/assets/canvasEditorHtml';

interface Props {
  projectUid: string;
  documentUid?: string;
  annotationUid?: string;
  initialTitle?: string;
  onSaved: (annotation: Annotation) => void;
}

export default function CanvasEditor({
  projectUid,
  documentUid,
  annotationUid,
  initialTitle,
  onSaved,
}: Props) {
  const webViewRef = useRef<WebView>(null);
  const [title, setTitle] = useState(initialTitle ?? '');
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  // uid resolvido: vem da prop ou é descoberto ao buscar anotação vinculada ao documento
  const [resolvedAnnotationUid, setResolvedAnnotationUid] = useState<string | undefined>(annotationUid);

  function inject(msg: object) {
    const js = `window.receiveMessage(${JSON.stringify(msg)}); true;`;
    webViewRef.current?.injectJavaScript(js);
  }

  async function onReady() {
    let streamUrl: string | undefined;
    let authToken: string | undefined;
    let canvasData: string | undefined;

    if (documentUid) {
      streamUrl = documentService.getDocumentStreamUrl(projectUid, documentUid);
      const token = await getToken();
      if (token) authToken = `Bearer ${token}`;

      // busca a anotação overlay já existente para este documento
      if (!annotationUid) {
        try {
          const all = await annotationService.listAnnotations(projectUid);
          const linked = all.find((a) => a.document_uid === documentUid);
          if (linked) {
            setResolvedAnnotationUid(linked.uid);
            canvasData = await annotationService.getAnnotationCanvas(projectUid, linked.uid);
          }
        } catch {
          // nenhuma anotação vinculada ou falha — canvas vazio
        }
      }
    }

    // modo edição explícito (annotationUid passado como prop)
    if (annotationUid && !canvasData) {
      try {
        canvasData = await annotationService.getAnnotationCanvas(projectUid, annotationUid);
      } catch {
        // canvas vazio
      }
    }

    inject({ type: 'init', streamUrl, authToken, canvasData });
    setIsLoading(false);
  }

  async function onSaveRequest(fabricJson: string) {
    const trimmedTitle = title.trim();
    const effectiveTitle = trimmedTitle || (documentUid ? 'Anotação' : '');

    if (!effectiveTitle) {
      Alert.alert('Atenção', 'Dê um nome para a anotação antes de salvar.');
      return;
    }

    setIsSaving(true);
    try {
      if (resolvedAnnotationUid) {
        await annotationService.updateAnnotationCanvas(projectUid, resolvedAnnotationUid, fabricJson);
        onSaved({
          uid: resolvedAnnotationUid,
          title: effectiveTitle,
          type: AnnotationType.HANDWRITING,
          content: '',
          position: '',
          canvas_path: '',
          document_uid: documentUid,
          status: 'INDEXED',
          created_at: new Date().toISOString(),
        });
      } else {
        const annotation = await annotationService.createAnnotation(projectUid, {
          title: effectiveTitle,
          type: AnnotationType.HANDWRITING,
          position: '',
          documentUid,
          canvasData: fabricJson,
        });
        setResolvedAnnotationUid(annotation.uid);
        onSaved(annotation);
      }
    } catch {
      Alert.alert('Erro', 'Não foi possível salvar a anotação.');
    } finally {
      setIsSaving(false);
    }
  }

  function onMessage(event: WebViewMessageEvent) {
    try {
      const msg = JSON.parse(event.nativeEvent.data) as { type: string; fabricJson?: string };
      if (msg.type === 'ready') {
        void onReady();
      } else if (msg.type === 'save' && msg.fabricJson) {
        void onSaveRequest(msg.fabricJson);
      } else if (msg.type === 'error') {
        Alert.alert('Erro', (msg as { type: string; message?: string }).message ?? 'Erro no editor.');
      }
    } catch {
      // ignore malformed messages
    }
  }

  return (
    <View className="flex-1 overflow-hidden rounded-2xl border border-gray-100 bg-white">
      {!documentUid && (
        <View className="border-b border-gray-100 px-4 py-3">
          <TextInput
            className="text-base font-semibold text-gray-900"
            placeholder="Nome da anotação..."
            placeholderTextColor="#9CA3AF"
            value={title}
            onChangeText={setTitle}
            editable={!annotationUid}
          />
          {isSaving && (
            <Text className="mt-0.5 text-xs text-blue-500">Salvando...</Text>
          )}
        </View>
      )}

      {isLoading && (
        <View
          style={{
            position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
            zIndex: 10, alignItems: 'center', justifyContent: 'center', backgroundColor: '#fff',
          }}
        >
          <ActivityIndicator size="large" color="#3B82F6" />
        </View>
      )}

      <WebView
        ref={webViewRef}
        source={{ html: canvasEditorHtml, baseUrl: 'http://localhost:3000' }}
        onMessage={onMessage}
        javaScriptEnabled
        domStorageEnabled
        originWhitelist={['*']}
        mixedContentMode="always"
        style={{ flex: 1 }}
      />
    </View>
  );
}
