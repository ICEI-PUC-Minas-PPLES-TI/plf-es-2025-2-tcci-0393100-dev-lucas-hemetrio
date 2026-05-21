import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Modal,
  Pressable,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { searchService } from '@/services/searchService';
import type {
  SearchAnnotationHit,
  SearchDocumentGroup,
  SearchProjectGroup,
  SearchResponse,
  SearchTarget,
} from '@/types/search';

interface Props {
  visible: boolean;
  onClose: () => void;
  onSelectResult: (target: SearchTarget) => void;
}

type Status = 'idle' | 'short' | 'loading' | 'empty' | 'results' | 'error';

function renderSnippet(snippet: string): React.ReactNode {
  const parts = snippet.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <Text key={i} className="font-bold text-gray-900">
          {part.slice(2, -2)}
        </Text>
      );
    }
    return <Text key={i}>{part}</Text>;
  });
}

function countProjectHits(g: SearchProjectGroup): number {
  let n = g.annotations.length;
  for (const d of g.documents) {
    if (d.title_match) n += 1;
    n += d.page_hits.length;
  }
  return n;
}

const CARD_SHADOW = {
  shadowColor: '#000',
  shadowOpacity: 0.04,
  shadowOffset: { width: 0, height: 1 },
  shadowRadius: 3,
  elevation: 1,
};

export default function SearchModal({ visible, onClose, onSelectResult }: Props) {
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState<Status>('idle');
  const [data, setData] = useState<SearchResponse | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const doSearch = useCallback(async (q: string) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setStatus('loading');
    try {
      const res = await searchService.search(q, controller.signal);
      if (controller.signal.aborted) return;
      setData(res);
      setStatus(res.total === 0 ? 'empty' : 'results');
    } catch (err: any) {
      if (err?.name === 'CanceledError' || err?.name === 'AbortError') return;
      setStatus('error');
    }
  }, []);

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      abortRef.current?.abort();
      setStatus(trimmed.length === 0 ? 'idle' : 'short');
      setData(null);
      return;
    }
    const t = setTimeout(() => {
      void doSearch(trimmed);
    }, 300);
    return () => clearTimeout(t);
  }, [query, doSearch]);

  useEffect(() => {
    if (!visible) {
      abortRef.current?.abort();
      setQuery('');
      setData(null);
      setStatus('idle');
    }
  }, [visible]);

  const renderDocumentGroup = (projectUid: string, g: SearchDocumentGroup) => {
    const hitCount = (g.title_match ? 1 : 0) + g.page_hits.length;
    return (
      <View key={g.document.uid} className="mt-3 overflow-hidden rounded-xl border border-gray-100 bg-gray-50">
        <Pressable
          onPress={() =>
            onSelectResult({
              kind: 'document',
              projectUid,
              documentUid: g.document.uid,
              initialPage: 1,
            })
          }
          className="flex-row items-center justify-between px-3 py-2.5"
        >
          <View className="flex-1 flex-row items-center gap-2">
            <Text className="text-base">📄</Text>
            <Text className="flex-1 text-sm font-semibold text-gray-900" numberOfLines={1}>
              {g.document.title}
            </Text>
          </View>
          <View className="ml-2 rounded-full bg-blue-100 px-2 py-0.5">
            <Text className="text-[10px] font-bold text-blue-700">{hitCount}</Text>
          </View>
        </Pressable>

        {g.title_match && (
          <View className="mx-3 mb-2 rounded-lg border border-gray-100 bg-white px-3 py-2">
            <Text className="text-[10px] font-bold uppercase tracking-wide text-gray-400">Título</Text>
            <Text className="mt-0.5 text-xs leading-5 text-gray-700">
              {renderSnippet(g.title_match.snippet)}
            </Text>
          </View>
        )}

        {g.page_hits.map((hit, i) => (
          <Pressable
            key={`${g.document.uid}-${hit.page_number}-${i}`}
            onPress={() =>
              onSelectResult({
                kind: 'document',
                projectUid,
                documentUid: g.document.uid,
                initialPage: hit.page_number,
              })
            }
            className="mx-3 mb-2 flex-row gap-2 rounded-lg border border-gray-100 bg-white px-3 py-2"
            android_ripple={{ color: '#DBEAFE' }}
          >
            <View className="min-w-[40px] items-center justify-center rounded-md bg-blue-50 px-2 py-1">
              <Text className="text-[10px] font-bold uppercase tracking-wide text-blue-700">p.{hit.page_number}</Text>
            </View>
            <Text className="flex-1 text-xs leading-5 text-gray-700">{renderSnippet(hit.snippet)}</Text>
          </Pressable>
        ))}
      </View>
    );
  };

  const renderAnnotationHit = (projectUid: string, h: SearchAnnotationHit) => (
    <Pressable
      key={h.annotation.uid}
      onPress={() => onSelectResult({ kind: 'annotation', projectUid, annotationUid: h.annotation.uid })}
      className="mt-3 overflow-hidden rounded-xl border border-amber-100 bg-amber-50/50 px-3 py-2.5"
      android_ripple={{ color: '#FEF3C7' }}
    >
      <View className="flex-row items-center gap-2">
        <Text className="text-base">✏️</Text>
        <Text className="flex-1 text-sm font-semibold text-gray-900" numberOfLines={1}>
          {h.annotation.title}
        </Text>
      </View>
      <Text className="mt-1 text-xs leading-5 text-gray-700">{renderSnippet(h.snippet)}</Text>
    </Pressable>
  );

  const renderProject = ({ item }: { item: SearchProjectGroup }) => {
    const count = countProjectHits(item);
    return (
      <View className="mx-4 mt-4 rounded-2xl bg-white p-4" style={CARD_SHADOW}>
        <View className="flex-row items-center justify-between">
          <Text className="flex-1 text-base font-bold text-gray-900" numberOfLines={1}>
            {item.project.name}
          </Text>
          <View className="ml-2 rounded-full bg-gray-100 px-2.5 py-0.5">
            <Text className="text-[11px] font-semibold text-gray-600">
              {count} {count === 1 ? 'resultado' : 'resultados'}
            </Text>
          </View>
        </View>
        {item.documents.map((g) => renderDocumentGroup(item.project.uid, g))}
        {item.annotations.map((h) => renderAnnotationHit(item.project.uid, h))}
      </View>
    );
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="fullScreen"
      onRequestClose={onClose}
    >
      <SafeAreaView className="flex-1 bg-gray-50" edges={['top']}>
        {/* Header */}
        <View className="border-b border-gray-200 bg-white px-4 py-3">
          <View className="flex-row items-center gap-2">
            <View className="flex-1 flex-row items-center gap-2 rounded-2xl border border-gray-200 bg-gray-50 px-3 py-2.5">
              <Text className="text-base">🔍</Text>
              <TextInput
                autoFocus
                value={query}
                onChangeText={setQuery}
                placeholder="Buscar em documentos e anotações..."
                placeholderTextColor="#9CA3AF"
                className="flex-1 text-base text-gray-900"
                returnKeyType="search"
              />
              {query.length > 0 && (
                <TouchableOpacity onPress={() => setQuery('')} hitSlop={8}>
                  <Text className="text-base text-gray-400">✕</Text>
                </TouchableOpacity>
              )}
            </View>
            <TouchableOpacity onPress={onClose} hitSlop={8}>
              <Text className="text-sm font-semibold text-blue-600">Cancelar</Text>
            </TouchableOpacity>
          </View>
          {status === 'results' && data && (
            <Text className="mt-2 text-xs text-gray-500">
              {data.total} {data.total === 1 ? 'resultado' : 'resultados'} para "{data.query}"
            </Text>
          )}
        </View>

        {/* Body */}
        {status === 'idle' && (
          <View className="flex-1 items-center justify-center px-8">
            <Text className="text-5xl">🔎</Text>
            <Text className="mt-3 text-center text-sm text-gray-500">
              Digite para buscar texto em PDFs e anotações.
            </Text>
          </View>
        )}
        {status === 'short' && (
          <View className="flex-1 items-center justify-center px-8">
            <Text className="text-center text-sm text-gray-500">Digite ao menos 2 caracteres.</Text>
          </View>
        )}
        {status === 'loading' && (
          <View className="flex-1 items-center justify-center">
            <ActivityIndicator color="#2563EB" size="large" />
            <Text className="mt-3 text-xs text-gray-500">Buscando...</Text>
          </View>
        )}
        {status === 'empty' && (
          <View className="flex-1 items-center justify-center px-8">
            <Text className="text-5xl">🫥</Text>
            <Text className="mt-3 text-center text-base font-semibold text-gray-700">
              Nenhum resultado
            </Text>
            <Text className="mt-1 text-center text-xs text-gray-500">
              Não encontramos "{query.trim()}" em nenhum documento ou anotação.
            </Text>
          </View>
        )}
        {status === 'error' && (
          <View className="flex-1 items-center justify-center px-8">
            <Text className="text-5xl">⚠️</Text>
            <Text className="mt-3 text-center text-base font-semibold text-red-600">
              Erro ao buscar
            </Text>
            <TouchableOpacity
              onPress={() => void doSearch(query.trim())}
              className="mt-4 rounded-xl bg-blue-600 px-5 py-2.5"
            >
              <Text className="text-sm font-semibold text-white">Tentar novamente</Text>
            </TouchableOpacity>
          </View>
        )}
        {status === 'results' && data && (
          <FlatList
            data={data.results_by_project}
            keyExtractor={(g) => g.project.uid}
            renderItem={renderProject}
            contentContainerStyle={{ paddingBottom: 24 }}
            keyboardShouldPersistTaps="handled"
          />
        )}
      </SafeAreaView>
    </Modal>
  );
}
