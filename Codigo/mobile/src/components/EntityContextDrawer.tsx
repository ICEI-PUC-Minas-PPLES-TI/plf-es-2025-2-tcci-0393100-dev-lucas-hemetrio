import { useEffect, useState } from 'react';
import { ActivityIndicator, FlatList, Text, TouchableOpacity, View } from 'react-native';

import { knowledgeService } from '@/services/knowledgeService';
import type {
  CoOccurrence,
  GraphSelection,
  KnowledgeNode,
  Mention,
} from '@/types/knowledge';

export interface NavigateTarget {
  projectUid: string;
  documentUid?: string;
  annotationUid?: string;
  initialPage?: number;
}

interface Props {
  projectUid: string;
  selection: GraphSelection;
  onClose: () => void;
  onNavigateToTarget: (target: NavigateTarget) => void;
}

interface DrawerState {
  status: 'loading' | 'error' | 'ready';
  errorMessage?: string;
  header: { title: string; subtitle: string; labelBadge?: string };
  items: Array<Mention | CoOccurrence>;
  highlightTerms: string[];
}

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function renderSentenceWithHighlight(sentence: string, terms: string[]) {
  const cleaned = terms.filter((t) => t && t.trim().length > 0);
  if (cleaned.length === 0) {
    return <Text style={{ color: '#eee', fontSize: 14, lineHeight: 20 }}>"{sentence}"</Text>;
  }
  const pattern = new RegExp(`(${cleaned.map(escapeRegex).join('|')})`, 'gi');
  const parts = sentence.split(pattern);
  return (
    <Text style={{ fontSize: 14, lineHeight: 20 }}>
      <Text style={{ color: '#eee', opacity: 0.4 }}>"</Text>
      {parts.map((part, i) => {
        const isMatch = cleaned.some((t) => t.toLowerCase() === part.toLowerCase());
        return (
          <Text
            key={i}
            style={{
              color: isMatch ? '#fff' : '#eee',
              opacity: isMatch ? 1 : 0.4,
              fontWeight: isMatch ? '600' : '400',
            }}
          >
            {part}
          </Text>
        );
      })}
      <Text style={{ color: '#eee', opacity: 0.4 }}>"</Text>
    </Text>
  );
}

const LABEL_COLORS: Record<string, string> = {
  PER: '#5b8def',
  LOC: '#7fd17a',
  ORG: '#ef9a5b',
};

function nodeHeader(node: KnowledgeNode): DrawerState['header'] {
  return {
    title: node.text,
    subtitle: `${node.mention_count} menç${node.mention_count === 1 ? 'ão' : 'ões'}`,
    labelBadge: node.label,
  };
}

function edgeHeader(a: KnowledgeNode, b: KnowledgeNode, weight: number): DrawerState['header'] {
  return {
    title: `${a.text} ↔ ${b.text}`,
    subtitle: `${weight} sentenç${weight === 1 ? 'a' : 'as'} onde co-ocorrem`,
  };
}

export default function EntityContextDrawer({
  projectUid,
  selection,
  onClose,
  onNavigateToTarget,
}: Props) {
  const [state, setState] = useState<DrawerState>({
    status: 'loading',
    header: { title: '...', subtitle: '' },
    items: [],
    highlightTerms: [],
  });

  useEffect(() => {
    const controller = new AbortController();
    setState((s) => ({ ...s, status: 'loading', items: [] }));

    (async () => {
      try {
        if (selection.type === 'node') {
          const res = await knowledgeService.getNodeMentions(
            projectUid, selection.uid, controller.signal,
          );
          setState({
            status: 'ready',
            header: nodeHeader(res.node),
            items: res.mentions,
            highlightTerms: [res.node.text],
          });
        } else {
          const res = await knowledgeService.getEdgeCoOccurrences(
            projectUid, selection.a_uid, selection.b_uid, controller.signal,
          );
          setState({
            status: 'ready',
            header: edgeHeader(res.node_a, res.node_b, res.weight),
            items: res.co_occurrences,
            highlightTerms: [res.node_a.text, res.node_b.text],
          });
        }
      } catch (err: any) {
        if (err?.name === 'CanceledError' || err?.name === 'AbortError') return;
        setState((s) => ({
          ...s,
          status: 'error',
          errorMessage: 'Não foi possível carregar as menções.',
        }));
      }
    })();

    return () => controller.abort();
  }, [projectUid, selection]);

  const handleItemPress = (item: Mention | CoOccurrence) => {
    if (item.source_type === 'document') {
      onNavigateToTarget({
        projectUid,
        documentUid: item.source_uid,
        initialPage: item.page_number ?? undefined,
      });
    } else {
      onNavigateToTarget({
        projectUid,
        annotationUid: item.source_uid,
      });
    }
  };

  return (
    <View style={{ flex: 1, backgroundColor: '#252630', borderLeftWidth: 2, borderLeftColor: '#5b8def' }}>
      <View style={{ padding: 16, borderBottomWidth: 1, borderBottomColor: '#333' }}>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <View style={{ flex: 1, flexDirection: 'row', alignItems: 'center', flexWrap: 'wrap' }}>
            <Text style={{ color: '#eee', fontSize: 18, fontWeight: '600' }}>{state.header.title}</Text>
            {state.header.labelBadge && (
              <View style={{
                marginLeft: 8, paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4,
                backgroundColor: LABEL_COLORS[state.header.labelBadge] ?? '#666',
              }}>
                <Text style={{ color: '#fff', fontSize: 10, fontWeight: '700' }}>
                  {state.header.labelBadge}
                </Text>
              </View>
            )}
          </View>
          <TouchableOpacity onPress={onClose} accessibilityLabel="Fechar painel">
            <Text style={{ color: '#aaa', fontSize: 22, paddingHorizontal: 8 }}>×</Text>
          </TouchableOpacity>
        </View>
        <Text style={{ color: '#888', fontSize: 12, marginTop: 4 }}>{state.header.subtitle}</Text>
      </View>

      {state.status === 'loading' && (
        <View style={{ padding: 16 }}>
          <ActivityIndicator color="#5b8def" />
        </View>
      )}

      {state.status === 'error' && (
        <View style={{ padding: 16 }}>
          <Text style={{ color: '#e07c7c', fontSize: 13 }}>{state.errorMessage}</Text>
        </View>
      )}

      {state.status === 'ready' && state.items.length === 0 && (
        <View style={{ padding: 16 }}>
          <Text style={{ color: '#888', fontSize: 13 }}>Nenhuma menção encontrada.</Text>
        </View>
      )}

      {state.status === 'ready' && state.items.length > 0 && (
        <FlatList
          data={state.items}
          keyExtractor={(item, idx) => ('uid' in item ? item.uid : `co-${idx}`)}
          contentContainerStyle={{ padding: 12 }}
          renderItem={({ item }) => (
            <TouchableOpacity
              activeOpacity={0.7}
              onPress={() => handleItemPress(item)}
              style={{
                backgroundColor: '#1e1f25',
                padding: 12,
                borderRadius: 8,
                marginBottom: 8,
              }}
            >
              {renderSentenceWithHighlight(item.sentence_text, state.highlightTerms)}
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 8 }}>
                <Text style={{ color: '#888', fontSize: 12 }}>
                  {item.source_type === 'document' ? '📄' : '✏️'} {item.source_title}
                  {item.page_number != null ? ` · pág. ${item.page_number}` : ''}
                </Text>
                <Text style={{ color: '#888', fontSize: 14 }}>→</Text>
              </View>
            </TouchableOpacity>
          )}
        />
      )}
    </View>
  );
}
