// mobile/src/components/CanvasEditor.tsx
import React, { useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  type LayoutChangeEvent,
  Text,
  TextInput,
  View,
} from 'react-native';
import { WebView, type WebViewMessageEvent } from 'react-native-webview';

import { annotationService } from '@/services/annotationService';
import { documentService } from '@/services/documentService';
import { getToken } from '@/storage/tokenStorage';
import type { Annotation } from '@/types/annotation';
import { canvasEditorHtml } from '@/assets/canvasEditorHtml';

interface Props {
  projectUid: string;
  documentUid?: string;
  annotationUid?: string;
  initialTitle?: string;
  initialPage?: number;
  onSaved: (annotation: Annotation) => void;
}

export default function CanvasEditor({
  projectUid,
  documentUid,
  annotationUid,
  initialTitle,
  initialPage,
  onSaved,
}: Props) {
  const webViewRef = useRef<WebView>(null);
  const [title, setTitle] = useState(initialTitle ?? '');
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  // uid resolvido: vem da prop ou é descoberto ao buscar anotação vinculada ao documento
  const [resolvedAnnotationUid, setResolvedAnnotationUid] = useState<string | undefined>(annotationUid);
  // promessas pendentes de export de PNG do WebView (correlacionadas por requestId)
  const pendingPngRequests = useRef<Record<string, { resolve: (s: string) => void; reject: (e: Error) => void }>>({});

  function inject(msg: object) {
    const js = `window.receiveMessage(${JSON.stringify(msg)}); true;`;
    webViewRef.current?.injectJavaScript(js);
  }

  // largura do container na última medição — detecta resize (ex.: sidebar abrir/
  // fechar empurra o painel) para o canvas reescalar sem remontar nem cortar nada.
  const lastWidth = useRef(0);
  function onContainerLayout(event: LayoutChangeEvent) {
    const width = Math.round(event.nativeEvent.layout.width);
    if (lastWidth.current && width !== lastWidth.current) {
      inject({ type: 'resize' });
    }
    lastWidth.current = width;
  }

  function requestPng(): Promise<string> {
    return new Promise((resolve, reject) => {
      const requestId = String(Date.now()) + '-' + Math.random().toString(36).slice(2);
      pendingPngRequests.current[requestId] = { resolve, reject };
      inject({ type: 'requestPng', requestId });
      setTimeout(() => {
        if (pendingPngRequests.current[requestId]) {
          delete pendingPngRequests.current[requestId];
          reject(new Error('PNG export timeout'));
        }
      }, 5000);
    });
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
    if (initialPage && initialPage > 1) {
      inject({ type: 'set-initial-page', page: initialPage });
    }
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
      const canvasImageBase64 = await requestPng().catch(() => '');

      if (resolvedAnnotationUid) {
        await annotationService.updateAnnotationCanvas(
          projectUid,
          resolvedAnnotationUid,
          fabricJson,
          canvasImageBase64,
        );
        onSaved({
          uid: resolvedAnnotationUid,
          title: effectiveTitle,
          content: '',
          position: '',
          canvas_path: '',
          canvas_image_path: '',
          document_uid: documentUid,
          status: 'PROCESSING',
          extracted_text: '',
          created_at: new Date().toISOString(),
        });
      } else {
        const annotation = await annotationService.createAnnotation(projectUid, {
          title: effectiveTitle,
          position: '',
          documentUid,
          canvasData: fabricJson,
          canvasImageBase64,
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
      const msg = JSON.parse(event.nativeEvent.data) as {
        type: string;
        fabricJson?: string;
        requestId?: string;
        dataUrl?: string;
        error?: string;
      };

      if (msg.type === 'pngResponse' && msg.requestId) {
        const pending = pendingPngRequests.current[msg.requestId];
        if (pending) {
          delete pendingPngRequests.current[msg.requestId];
          if (msg.error) pending.reject(new Error(msg.error));
          else pending.resolve(msg.dataUrl ?? '');
        }
        return;
      }

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
    <View
      className="flex-1 overflow-hidden rounded-2xl border border-gray-100 bg-white"
      onLayout={onContainerLayout}
    >
      {!documentUid && !annotationUid && (
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
