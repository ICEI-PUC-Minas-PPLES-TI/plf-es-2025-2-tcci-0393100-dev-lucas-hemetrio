import { forwardRef, useEffect, useImperativeHandle, useRef } from 'react';
import { WebView, WebViewMessageEvent } from 'react-native-webview';
import { View } from 'react-native';

import { knowledgeGraphHtml } from '@/assets/knowledgeGraphHtml';
import type {
  GraphSelection,
  KnowledgeEdge,
  KnowledgeNode,
} from '@/types/knowledge';

export interface KnowledgeGraphWebViewHandle {
  zoomIn: () => void;
  zoomOut: () => void;
  zoomReset: () => void;
}

interface Props {
  nodes: KnowledgeNode[];
  edges: KnowledgeEdge[];
  selection: GraphSelection | null;
  focusNodeUid?: string | null;
  onSelectNode: (uid: string) => void;
  onSelectEdge: (aUid: string, bUid: string) => void;
  onDeselect: () => void;
}

function KnowledgeGraphWebViewInner({
  nodes,
  edges,
  selection,
  focusNodeUid,
  onSelectNode,
  onSelectEdge,
  onDeselect,
}: Props, ref: React.Ref<KnowledgeGraphWebViewHandle>) {
  const webviewRef = useRef<WebView>(null);
  const readyRef = useRef(false);

  const send = (msg: unknown) => {
    const json = JSON.stringify(msg).replace(/\\/g, '\\\\').replace(/'/g, "\\'");
    webviewRef.current?.injectJavaScript(`window.postMessage('${json}', '*'); true;`);
  };

  useImperativeHandle(ref, () => ({
    zoomIn: () => send({ type: 'zoom-in' }),
    zoomOut: () => send({ type: 'zoom-out' }),
    zoomReset: () => send({ type: 'zoom-reset' }),
  }));

  useEffect(() => {
    if (readyRef.current && nodes.length > 0) {
      send({ type: 'set-graph', nodes, edges });
      if (selection) send({ type: 'highlight-selection', selection });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, edges]);

  useEffect(() => {
    if (readyRef.current) send({ type: 'highlight-selection', selection });
  }, [selection]);

  useEffect(() => {
    if (readyRef.current && focusNodeUid) send({ type: 'focus-node', uid: focusNodeUid });
  }, [focusNodeUid]);

  const handleMessage = (event: WebViewMessageEvent) => {
    try {
      const msg = JSON.parse(event.nativeEvent.data);
      if (msg.type === 'ready') {
        readyRef.current = true;
        if (nodes.length > 0) send({ type: 'set-graph', nodes, edges });
        if (selection) send({ type: 'highlight-selection', selection });
      } else if (msg.type === 'select-node') {
        onSelectNode(msg.uid);
      } else if (msg.type === 'select-edge') {
        onSelectEdge(msg.a_uid, msg.b_uid);
      } else if (msg.type === 'deselect') {
        onDeselect();
      }
    } catch {
      // ignorar mensagens malformadas
    }
  };

  return (
    <View style={{ flex: 1, backgroundColor: '#1e1f25' }}>
      <WebView
        ref={webviewRef}
        originWhitelist={['*']}
        source={{ html: knowledgeGraphHtml }}
        onMessage={handleMessage}
        javaScriptEnabled
        domStorageEnabled
        scrollEnabled={false}
        bounces={false}
        androidLayerType="hardware"
        style={{ flex: 1, backgroundColor: '#1e1f25' }}
      />
    </View>
  );
}

const KnowledgeGraphWebView = forwardRef<KnowledgeGraphWebViewHandle, Props>(
  KnowledgeGraphWebViewInner,
);

export default KnowledgeGraphWebView;
