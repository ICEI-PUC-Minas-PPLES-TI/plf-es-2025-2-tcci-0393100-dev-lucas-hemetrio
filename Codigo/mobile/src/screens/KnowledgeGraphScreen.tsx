import { useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Modal,
  SafeAreaView,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import EntityContextDrawer, { NavigateTarget } from '@/components/EntityContextDrawer';
import KnowledgeGraphWebView, { KnowledgeGraphWebViewHandle } from '@/components/KnowledgeGraphWebView';
import { knowledgeService } from '@/services/knowledgeService';
import type {
  GraphSelection,
  KnowledgeEdge,
  KnowledgeGraphResponse,
  KnowledgeNode,
  KnowledgeStatus,
} from '@/types/knowledge';

interface Props {
  visible: boolean;
  projectUid: string;
  projectName: string;
  onClose: () => void;
  onNavigateToTarget: (target: NavigateTarget) => void;
}

interface GraphData {
  status: KnowledgeStatus;
  nodes: KnowledgeNode[];
  edges: KnowledgeEdge[];
}

const POLL_INTERVAL_MS = 5000;
const MAX_SEARCH_RESULTS = 5;

export default function KnowledgeGraphScreen({
  visible,
  projectUid,
  projectName,
  onClose,
  onNavigateToTarget,
}: Props) {
  const [data, setData] = useState<GraphData | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [selection, setSelection] = useState<GraphSelection | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [focusNodeUid, setFocusNodeUid] = useState<string | null>(null);
  const [showIsolated, setShowIsolated] = useState(false);
  const pollTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const graphRef = useRef<KnowledgeGraphWebViewHandle>(null);

  const fetchOnce = async () => {
    try {
      const res: KnowledgeGraphResponse = await knowledgeService.getGraph(projectUid);
      setData({ status: res.status, nodes: res.nodes, edges: res.edges });
      setFetchError(null);
      if (res.status === 'PROCESSING') schedulePoll();
    } catch {
      setFetchError('Não foi possível carregar o grafo.');
    }
  };

  const schedulePoll = () => {
    if (pollTimer.current) clearTimeout(pollTimer.current);
    pollTimer.current = setTimeout(fetchOnce, POLL_INTERVAL_MS);
  };

  useEffect(() => {
    if (!visible) return;
    setData(null);
    setFetchError(null);
    setSelection(null);
    setSearchQuery('');
    setFocusNodeUid(null);
    fetchOnce();
    return () => {
      if (pollTimer.current) clearTimeout(pollTimer.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible, projectUid]);

  const handleRetry = async () => {
    try {
      await knowledgeService.rebuildKnowledge(projectUid);
      setData({ status: 'PROCESSING', nodes: [], edges: [] });
      schedulePoll();
    } catch {
      setFetchError('Falha ao disparar reprocessamento.');
    }
  };

  const visibleNodes = useMemo(() => {
    if (!data) return [];
    if (showIsolated) return data.nodes;
    const connected = new Set<string>();
    data.edges.forEach((e) => {
      connected.add(e.source);
      connected.add(e.target);
    });
    return data.nodes.filter((n) => connected.has(n.uid));
  }, [data, showIsolated]);

  const isolatedCount = useMemo(() => {
    if (!data) return 0;
    return data.nodes.length - visibleNodes.length;
  }, [data, visibleNodes]);

  const searchResults = useMemo(() => {
    if (!data || searchQuery.trim().length < 2) return [];
    const q = searchQuery.trim().toLowerCase();
    return visibleNodes
      .filter((n) => n.text.toLowerCase().includes(q))
      .sort((a, b) => b.mention_count - a.mention_count)
      .slice(0, MAX_SEARCH_RESULTS);
  }, [visibleNodes, searchQuery, data]);

  const handleSearchPick = (node: KnowledgeNode) => {
    setSelection({ type: 'node', uid: node.uid });
    setFocusNodeUid(node.uid);
    setSearchQuery('');
    setTimeout(() => setFocusNodeUid(null), 100);
  };

  const renderBody = () => {
    if (fetchError) {
      return (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 }}>
          <Text style={{ color: '#e07c7c', fontSize: 14 }}>{fetchError}</Text>
        </View>
      );
    }
    if (!data) {
      return (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
          <ActivityIndicator color="#5b8def" size="large" />
        </View>
      );
    }
    if (data.status === 'PROCESSING') {
      return (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 }}>
          <ActivityIndicator color="#5b8def" size="large" />
          <Text style={{ color: '#ccc', marginTop: 12 }}>Construindo grafo de conhecimento…</Text>
        </View>
      );
    }
    if (data.status === 'FAILED') {
      return (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 }}>
          <Text style={{ color: '#ccc', marginBottom: 16 }}>Falha ao construir grafo.</Text>
          <TouchableOpacity
            onPress={handleRetry}
            style={{ backgroundColor: '#5b8def', paddingHorizontal: 16, paddingVertical: 10, borderRadius: 8 }}
          >
            <Text style={{ color: '#fff', fontWeight: '600' }}>Tentar novamente</Text>
          </TouchableOpacity>
        </View>
      );
    }
    if (data.nodes.length === 0) {
      return (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 }}>
          <Text style={{ color: '#ccc', textAlign: 'center' }}>
            Nenhuma entidade extraída ainda.{'\n'}Adicione documentos ou anotações para construir o grafo.
          </Text>
        </View>
      );
    }
    return (
      <View style={{ flex: 1, flexDirection: 'row' }}>
        <View style={{ flex: selection ? 6 : 10 }}>
          <KnowledgeGraphWebView
            ref={graphRef}
            nodes={visibleNodes}
            edges={data.edges}
            selection={selection}
            focusNodeUid={focusNodeUid}
            onSelectNode={(uid) => setSelection({ type: 'node', uid })}
            onSelectEdge={(a_uid, b_uid) => setSelection({ type: 'edge', a_uid, b_uid })}
            onDeselect={() => setSelection(null)}
          />
          <View style={{
            position: 'absolute', right: 12, bottom: 12,
            backgroundColor: '#2a2b32',
            borderRadius: 8,
            borderWidth: 1, borderColor: '#444',
            overflow: 'hidden',
            width: 44,
          }}>
            <TouchableOpacity
              onPress={() => graphRef.current?.zoomIn()}
              style={{ height: 44, alignItems: 'center', justifyContent: 'center', borderBottomWidth: 1, borderBottomColor: '#444' }}
            >
              <Text style={{ color: '#eee', fontSize: 22, fontWeight: '600', lineHeight: 24 }}>+</Text>
            </TouchableOpacity>
            <TouchableOpacity
              onPress={() => graphRef.current?.zoomOut()}
              style={{ height: 44, alignItems: 'center', justifyContent: 'center' }}
            >
              <Text style={{ color: '#eee', fontSize: 22, fontWeight: '600', lineHeight: 24 }}>−</Text>
            </TouchableOpacity>
          </View>
        </View>
        {selection && (
          <View style={{ flex: 4 }}>
            <EntityContextDrawer
              projectUid={projectUid}
              selection={selection}
              onClose={() => setSelection(null)}
              onNavigateToTarget={(target) => {
                onNavigateToTarget(target);
                onClose();
              }}
            />
          </View>
        )}
      </View>
    );
  };

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      <SafeAreaView style={{ flex: 1, backgroundColor: '#1e1f25' }}>
        <View style={{
          flexDirection: 'row', alignItems: 'center', padding: 12,
          borderBottomWidth: 1, borderBottomColor: '#333',
        }}>
          <TouchableOpacity onPress={onClose} style={{ paddingRight: 12 }}>
            <Text style={{ color: '#5b8def', fontSize: 16 }}>← Voltar</Text>
          </TouchableOpacity>
          <Text
            style={{ color: '#eee', fontSize: 16, fontWeight: '600', flex: 1 }}
            numberOfLines={1}
          >
            🕸️ Grafo · {projectName}
          </Text>
          <TouchableOpacity
            onPress={() => setShowIsolated((v) => !v)}
            style={{
              marginRight: 8,
              paddingHorizontal: 10, paddingVertical: 6,
              borderRadius: 8,
              borderWidth: 1,
              borderColor: showIsolated ? '#5b8def' : '#444',
              backgroundColor: showIsolated ? '#1f2a40' : '#2a2b32',
            }}
            disabled={!data || data.status !== 'DONE'}
          >
            <Text style={{ color: showIsolated ? '#cdd9f3' : '#888', fontSize: 12 }}>
              Isolados {showIsolated ? '●' : '○'}{isolatedCount > 0 ? ` (${isolatedCount})` : ''}
            </Text>
          </TouchableOpacity>
          <View style={{ flex: 1, maxWidth: 280, position: 'relative' }}>
            <TextInput
              value={searchQuery}
              onChangeText={setSearchQuery}
              placeholder="Buscar entidade…"
              placeholderTextColor="#666"
              style={{
                backgroundColor: '#2a2b32',
                color: '#eee',
                paddingHorizontal: 12,
                paddingVertical: 8,
                borderRadius: 8,
                fontSize: 13,
              }}
            />
            {searchResults.length > 0 && (
              <View style={{
                position: 'absolute', top: 40, left: 0, right: 0,
                backgroundColor: '#2a2b32',
                borderRadius: 8,
                borderWidth: 1, borderColor: '#444',
                zIndex: 10,
              }}>
                <FlatList
                  data={searchResults}
                  keyExtractor={(n) => n.uid}
                  keyboardShouldPersistTaps="always"
                  renderItem={({ item }) => (
                    <TouchableOpacity
                      onPress={() => handleSearchPick(item)}
                      style={{
                        paddingHorizontal: 12, paddingVertical: 10,
                        flexDirection: 'row', alignItems: 'center',
                      }}
                    >
                      <Text style={{ color: '#eee', fontSize: 13, flex: 1 }}>{item.text}</Text>
                      <Text style={{ color: '#888', fontSize: 11, marginLeft: 8 }}>
                        {item.label} · {item.mention_count}
                      </Text>
                    </TouchableOpacity>
                  )}
                />
              </View>
            )}
          </View>
        </View>

        {renderBody()}
      </SafeAreaView>
    </Modal>
  );
}
