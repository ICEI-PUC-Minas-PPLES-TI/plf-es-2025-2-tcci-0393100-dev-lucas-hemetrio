import { D3_BUNDLE } from './d3.bundle';

/**
 * HTML completo carregado no WebView. d3 é embutido inline (sem CDN).
 *
 * Bridge:
 *   RN → WebView (via injectJavaScript + window.postMessage):
 *     - { type: 'set-graph', nodes, edges }
 *     - { type: 'highlight-selection', selection }
 *     - { type: 'focus-node', uid }
 *
 *   WebView → RN (via window.ReactNativeWebView.postMessage):
 *     - { type: 'select-node', uid }
 *     - { type: 'select-edge', a_uid, b_uid }
 *     - { type: 'deselect' }
 *     - { type: 'ready' }
 */
export const knowledgeGraphHtml = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0"/>
<style>
  html, body { margin:0; padding:0; width:100%; height:100%; background:#1e1f25; overflow:hidden; }
  svg { width:100%; height:100%; display:block; touch-action:none; }
  .node circle { cursor:pointer; }
  .node text { pointer-events:none; user-select:none; font: 11px -apple-system, sans-serif; fill:#ccc; }
  .legend { font: 11px -apple-system, sans-serif; fill:#999; }
</style>
<script>${D3_BUNDLE}</script>
</head>
<body>
<svg id="canvas"></svg>
<script>
(function() {
  const COLORS = { PER:'#5b8def', LOC:'#7fd17a', ORG:'#ef9a5b' };
  const FALLBACK_COLOR = '#888';

  let nodes = [];
  let edges = [];
  let selection = null;
  let sim = null;
  let svg, g, linkSel, nodeSel, zoomBehavior;

  function nodeRadius(n) {
    const r = 6 + Math.sqrt(Math.max(0, n.mention_count)) * 2;
    return Math.max(6, Math.min(28, r));
  }
  function edgeWidth(e) {
    const w = 1 + Math.sqrt(Math.max(1, e.weight)) * 0.8;
    return Math.max(1, Math.min(6, w));
  }

  function init() {
    svg = d3.select('#canvas');
    g = svg.append('g');

    zoomBehavior = d3.zoom()
      .scaleExtent([0.2, 4])
      .on('zoom', (ev) => {
        g.attr('transform', ev.transform);
        if (nodeSel) {
          nodeSel.selectAll('text').style('display', ev.transform.k > 0.7 ? 'block' : 'none');
        }
      });
    svg.call(zoomBehavior);

    svg.on('click', (ev) => {
      if (ev.target.tagName === 'svg') {
        selection = null;
        rerenderHighlight();
        post({ type: 'deselect' });
      }
    });

    // Legenda
    const legend = svg.append('g').attr('class','legend')
      .attr('transform','translate(16,'+ (window.innerHeight - 70) +')');
    const items = [['#5b8def','Pessoas'], ['#7fd17a','Lugares'], ['#ef9a5b','Organizações']];
    items.forEach((it, i) => {
      const row = legend.append('g').attr('transform', 'translate(0,' + (i*18) + ')');
      row.append('circle').attr('r',5).attr('cx',6).attr('cy',-4).attr('fill', it[0]);
      row.append('text').attr('x', 18).attr('y', 0).text(it[1]);
    });

    post({ type: 'ready' });
  }

  function setGraph(n, e) {
    nodes = n.map(d => ({ ...d }));
    edges = e.map(d => ({ ...d, source: d.source, target: d.target }));

    g.selectAll('*').remove();
    const linkLayer = g.append('g').attr('class','links');
    const nodeLayer = g.append('g').attr('class','nodes');

    linkSel = linkLayer.selectAll('line').data(edges).enter().append('line')
      .attr('stroke', '#555')
      .attr('stroke-width', edgeWidth)
      .style('cursor','pointer')
      .on('click', (ev, d) => {
        ev.stopPropagation();
        const a = typeof d.source === 'object' ? d.source.uid : d.source;
        const b = typeof d.target === 'object' ? d.target.uid : d.target;
        selection = { type:'edge', a_uid:a, b_uid:b };
        rerenderHighlight();
        post({ type:'select-edge', a_uid:a, b_uid:b });
      });

    nodeSel = nodeLayer.selectAll('g').data(nodes).enter().append('g').attr('class','node');
    nodeSel.append('circle')
      .attr('r', nodeRadius)
      .attr('fill', d => COLORS[d.label] || FALLBACK_COLOR)
      .on('click', (ev, d) => {
        ev.stopPropagation();
        selection = { type:'node', uid:d.uid };
        rerenderHighlight();
        post({ type:'select-node', uid:d.uid });
      });
    nodeSel.append('text')
      .attr('text-anchor','middle')
      .attr('dy', d => nodeRadius(d) + 12)
      .text(d => d.text);

    nodeSel.call(d3.drag()
      .on('start', (ev,d) => { if (!ev.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
      .on('drag', (ev,d) => { d.fx = ev.x; d.fy = ev.y; })
      .on('end', (ev,d) => { if (!ev.active) sim.alphaTarget(0); d.fx = null; d.fy = null; }));

    sim = d3.forceSimulation(nodes)
      .force('charge', d3.forceManyBody().strength(-180))
      .force('link', d3.forceLink(edges).id(d => d.uid).distance(60))
      .force('center', d3.forceCenter(window.innerWidth/2, window.innerHeight/2))
      .force('x', d3.forceX(window.innerWidth/2).strength(0.02))
      .force('y', d3.forceY(window.innerHeight/2).strength(0.02))
      .on('tick', () => {
        linkSel
          .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
        nodeSel.attr('transform', d => 'translate('+ d.x +','+ d.y +')');
      });
  }

  function rerenderHighlight() {
    if (!nodeSel || !linkSel) return;
    if (!selection) {
      linkSel.attr('stroke','#555');
      nodeSel.select('circle').attr('stroke', null).attr('stroke-width', null);
      return;
    }
    if (selection.type === 'node') {
      const sel = selection.uid;
      nodeSel.select('circle')
        .attr('stroke', d => d.uid === sel ? '#fff' : null)
        .attr('stroke-width', d => d.uid === sel ? 2 : null);
      linkSel.attr('stroke', d => {
        const a = typeof d.source === 'object' ? d.source.uid : d.source;
        const b = typeof d.target === 'object' ? d.target.uid : d.target;
        return (a === sel || b === sel) ? '#aaa' : '#333';
      });
    } else {
      const a = selection.a_uid, b = selection.b_uid;
      nodeSel.select('circle')
        .attr('stroke', d => (d.uid === a || d.uid === b) ? '#fff' : null)
        .attr('stroke-width', d => (d.uid === a || d.uid === b) ? 2 : null);
      linkSel.attr('stroke', d => {
        const sa = typeof d.source === 'object' ? d.source.uid : d.source;
        const sb = typeof d.target === 'object' ? d.target.uid : d.target;
        const isThis = (sa === a && sb === b) || (sa === b && sb === a);
        const touches = sa === a || sa === b || sb === a || sb === b;
        if (isThis) return '#fff';
        if (touches) return '#aaa';
        return '#333';
      });
    }
  }

  function focusNode(uid) {
    const n = nodes.find(x => x.uid === uid);
    if (!n) return;
    const k = 1.6;
    const tx = window.innerWidth/2 - n.x * k;
    const ty = window.innerHeight/2 - n.y * k;
    svg.transition().duration(500)
      .call(zoomBehavior.transform, d3.zoomIdentity.translate(tx,ty).scale(k));
    const sel = nodeSel.filter(d => d.uid === uid).select('circle');
    const r0 = nodeRadius(n);
    sel.transition().duration(400).attr('r', r0 * 1.3)
       .transition().duration(400).attr('r', r0);
    selection = { type:'node', uid };
    rerenderHighlight();
  }

  function post(msg) {
    if (window.ReactNativeWebView) {
      window.ReactNativeWebView.postMessage(JSON.stringify(msg));
    }
  }

  function zoomStep(factor) {
    if (!svg || !zoomBehavior) return;
    svg.transition().duration(250).call(zoomBehavior.scaleBy, factor);
  }

  function handle(msg) {
    if (msg.type === 'set-graph') setGraph(msg.nodes, msg.edges);
    else if (msg.type === 'highlight-selection') { selection = msg.selection; rerenderHighlight(); }
    else if (msg.type === 'focus-node') focusNode(msg.uid);
    else if (msg.type === 'zoom-in') zoomStep(1.4);
    else if (msg.type === 'zoom-out') zoomStep(1/1.4);
    else if (msg.type === 'zoom-reset') {
      if (svg && zoomBehavior) svg.transition().duration(300).call(zoomBehavior.transform, d3.zoomIdentity);
    }
  }

  document.addEventListener('message', (ev) => { try { handle(JSON.parse(ev.data)); } catch(e) {} });
  window.addEventListener('message', (ev) => { try { handle(JSON.parse(ev.data)); } catch(e) {} });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
</script>
</body>
</html>`;
