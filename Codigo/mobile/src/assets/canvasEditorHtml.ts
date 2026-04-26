// mobile/src/assets/canvasEditorHtml.ts
export const canvasEditorHtml = `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=3.0, user-scalable=yes">
<style>
* { margin:0; padding:0; box-sizing:border-box; -webkit-tap-highlight-color:transparent; }
html,body { height:100%; background:#fff; font-family:-apple-system,sans-serif; overflow:hidden; }
#app { display:flex; flex-direction:column; height:100%; }
#toolbar {
  display:flex; align-items:center; gap:5px; padding:6px 8px;
  background:#fff; border-bottom:1px solid #F3F4F6;
  flex-wrap:wrap; flex-shrink:0; min-height:46px;
}
.btn {
  padding:5px 9px; border-radius:8px; border:1px solid #E5E7EB;
  background:#fff; font-size:13px; font-weight:600; color:#374151;
  cursor:pointer; white-space:nowrap; user-select:none;
}
.btn.active { background:#3B82F6; color:#fff; border-color:#3B82F6; }
.btn.save { background:#3B82F6; color:#fff; border-color:#3B82F6; }
.btn.danger { border-color:#FCA5A5; color:#EF4444; }
.sep { width:1px; height:20px; background:#E5E7EB; flex-shrink:0; }
.dot {
  width:20px; height:20px; border-radius:50%;
  border:2px solid #E5E7EB; cursor:pointer; flex-shrink:0;
}
.dot.sel { border-color:#3B82F6; box-shadow:0 0 0 2px #BFDBFE; }
#page-info { font-size:12px; color:#6B7280; }
#canvas-wrap { flex:1; overflow:auto; -webkit-overflow-scrolling:touch; }
</style>
</head>
<body>
<div id="app">
  <div id="toolbar">
    <button class="btn active" id="btn-nav" onclick="setMode('navigate')">🖐 Rolar</button>
    <button class="btn" id="btn-drw" onclick="setMode('draw')">✏️ Desenhar</button>
    <div class="sep" id="sep-mode"></div>
    <button class="btn active" id="btn-pen" onclick="setTool('pen')">🖊️</button>
    <button class="btn" id="btn-txt" onclick="setTool('text')">T</button>
    <button class="btn" id="btn-ers" onclick="setTool('eraser')">⌫</button>
    <div class="sep"></div>
    <div class="dot sel" style="background:#111827" data-c="#111827" onclick="pickColor(this)"></div>
    <div class="dot" style="background:#3B82F6" data-c="#3B82F6" onclick="pickColor(this)"></div>
    <div class="dot" style="background:#EF4444" data-c="#EF4444" onclick="pickColor(this)"></div>
    <div class="dot" style="background:#10B981" data-c="#10B981" onclick="pickColor(this)"></div>
    <div class="dot" style="background:#F59E0B" data-c="#F59E0B" onclick="pickColor(this)"></div>
    <button class="btn" id="btn-w2" onclick="setWidth(2)">Fino</button>
    <button class="btn active" id="btn-w4" onclick="setWidth(4)">Médio</button>
    <button class="btn" id="btn-w8" onclick="setWidth(8)">Grosso</button>
    <div class="sep"></div>
    <button class="btn" onclick="doUndo()">↩</button>
    <button class="btn" onclick="doRedo()">↪</button>
    <button class="btn danger" onclick="doClear()">🗑</button>
    <div class="sep" id="sep-page" style="display:none"></div>
    <button class="btn" id="btn-prev" style="display:none" onclick="prevPage()">◀</button>
    <span id="page-info" style="display:none">1/1</span>
    <button class="btn" id="btn-next" style="display:none" onclick="nextPage()">▶</button>
    <div class="sep"></div>
    <button class="btn save" onclick="doSave()">💾 Salvar</button>
  </div>
  <div id="canvas-wrap">
    <canvas id="c"></canvas>
  </div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
<script>
var fc = null;
var pdfDoc = null;
var curPage = 1;
var totPages = 1;
var currentBgImage = null;
var pageData = {}; // { pageNum: fabricJsonString } — anotações por página do PDF
var color = '#111827';
var strokeW = 4;
var tool = 'pen';
var mode = 'draw';
var isPdf = false;
var redoObjs = [];
var isRedoing = false;
var initialized = false;

// ── Bootstrap ────────────────────────────────────────────────
window.receiveMessage = function(msg) {
  if (msg.type !== 'init') return;
  if (initialized) return;
  initialized = true;
  isPdf = !!msg.streamUrl;
  initCanvas();
  if (isPdf) {
    showPdfUI();
    if (msg.canvasData) {
      try {
        var parsed = typeof msg.canvasData === 'string' ? JSON.parse(msg.canvasData) : msg.canvasData;
        // formato legado: objeto fabric direto (tem 'objects') → mapeia para página 1
        pageData = parsed && parsed.objects ? { 1: msg.canvasData } : (parsed || {});
      } catch(e) { pageData = {}; }
    }
    loadPdf(msg.streamUrl, msg.authToken);
  } else {
    setMode('navigate');
    if (msg.canvasData) loadJson(msg.canvasData);
  }
};

document.addEventListener('message', function(e){ try{ window.receiveMessage(JSON.parse(e.data)); }catch(x){} });
window.addEventListener('message', function(e){ try{ window.receiveMessage(JSON.parse(e.data)); }catch(x){} });

// ── Canvas init ───────────────────────────────────────────────
function initCanvas() {
  var wrap = document.getElementById('canvas-wrap');
  var w = wrap.clientWidth || window.innerWidth;
  var h = isPdf ? (wrap.clientHeight || window.innerHeight - 50) : 3000;

  fc = new fabric.Canvas('c', {
    width: w, height: h,
    isDrawingMode: true,
    selection: false,
    backgroundColor: '#FFFFFF',
  });

  applyBrush();

  fc.on('object:added', function() { if (!isRedoing) redoObjs = []; });
}

// ── PDF ───────────────────────────────────────────────────────
function showPdfUI() {
  ['sep-page','btn-prev','btn-next']
    .forEach(function(id){ document.getElementById(id).style.display = 'inline-block'; });
  document.getElementById('page-info').style.display = 'inline';
  setMode('navigate');
}

function loadPdf(streamUrl, authToken) {
  pdfjsLib.GlobalWorkerOptions.workerSrc =
    'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
  var headers = authToken ? { Authorization: authToken } : {};
  fetch(streamUrl, { headers: headers })
    .then(function(resp) {
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      return resp.arrayBuffer();
    })
    .then(function(buffer) {
      return pdfjsLib.getDocument({ data: buffer }).promise;
    })
    .then(function(doc) {
      pdfDoc = doc;
      totPages = doc.numPages;
      renderPage(1);
    })
    .catch(function(err) { toRN({ type: 'error', message: 'PDF load failed: ' + err.message }); });
}

function saveCurrentPage() {
  if (!fc) return;
  var json = fc.toJSON();
  delete json.backgroundImage;
  if (json.objects && json.objects.length > 0) {
    pageData[curPage] = JSON.stringify(json);
  } else {
    delete pageData[curPage];
  }
}

function renderPage(n) {
  redoObjs = [];
  curPage = n;
  document.getElementById('page-info').textContent = n + '/' + totPages;
  pdfDoc.getPage(n)
    .then(function(page) {
      var wrap = document.getElementById('canvas-wrap');
      var scale = (wrap.clientWidth || window.innerWidth) / page.getViewport({ scale: 1 }).width;
      var vp = page.getViewport({ scale: scale });
      var off = document.createElement('canvas');
      off.width = vp.width; off.height = vp.height;
      return page.render({ canvasContext: off.getContext('2d'), viewport: vp }).promise
        .then(function() {
          fc.setWidth(vp.width);
          fc.setHeight(vp.height);
          // limpa objetos da página anterior antes de carregar a nova
          fc.getObjects().slice().forEach(function(o){ fc.remove(o); });
          fabric.Image.fromURL(off.toDataURL(), function(img) {
            currentBgImage = img;
            fc.setBackgroundImage(img, function() {
              var saved = pageData[n];
              if (saved) {
                var bg = currentBgImage;
                fc.loadFromJSON(typeof saved === 'string' ? JSON.parse(saved) : saved, function() {
                  fc.setBackgroundImage(bg, function() { fc.renderAll(); });
                });
              } else {
                fc.renderAll();
              }
            });
          });
        });
    })
    .catch(function(err) { toRN({ type: 'error', message: 'Page render failed: ' + err.message }); });
}

function prevPage() { if (curPage > 1) { saveCurrentPage(); renderPage(curPage - 1); } }
function nextPage() { if (curPage < totPages) { saveCurrentPage(); renderPage(curPage + 1); } }

// ── Mode ──────────────────────────────────────────────────────
function setMode(m) {
  mode = m;
  if (!fc) return;
  var wrap = document.getElementById('canvas-wrap');
  if (m === 'navigate') {
    fc.isDrawingMode = false;
    fc.selection = false;
    fc.wrapperEl.style.pointerEvents = 'none';
    wrap.style.overflow = 'auto';
    wrap.style.touchAction = 'pan-y';
    document.getElementById('btn-nav').classList.add('active');
    document.getElementById('btn-drw').classList.remove('active');
  } else {
    fc.isDrawingMode = (tool === 'pen' || tool === 'eraser');
    fc.wrapperEl.style.pointerEvents = 'auto';
    wrap.style.overflow = 'hidden';
    wrap.style.touchAction = 'none';
    document.getElementById('btn-drw').classList.add('active');
    document.getElementById('btn-nav').classList.remove('active');
    applyBrush();
  }
}

// ── Tools ─────────────────────────────────────────────────────
function setTool(t) {
  tool = t;
  if (!fc) return;
  fc.off('mouse:down', addText);
  ['pen','txt','ers'].forEach(function(k) {
    document.getElementById('btn-' + k).classList.toggle('active', k === t.replace('eraser','ers').replace('text','txt'));
  });
  if (t === 'text') {
    fc.isDrawingMode = false;
    fc.on('mouse:down', addText);
  } else {
    fc.isDrawingMode = (mode === 'draw' || !isPdf);
    applyBrush();
  }
}

function addText(opt) {
  if (opt.target) return;
  var p = fc.getPointer(opt.e);
  var txt = new fabric.IText('', {
    left: p.x, top: p.y,
    fontSize: 18, fill: color,
    fontFamily: '-apple-system, BlinkMacSystemFont, sans-serif',
    editable: true,
  });
  fc.add(txt);
  fc.setActiveObject(txt);
  txt.enterEditing();
  fc.renderAll();
}

function applyBrush() {
  if (!fc) return;
  if (tool === 'eraser') {
    fc.freeDrawingBrush.color = '#FFFFFF';
    fc.freeDrawingBrush.width = strokeW * 3;
  } else {
    fc.freeDrawingBrush.color = color;
    fc.freeDrawingBrush.width = strokeW;
  }
}

function pickColor(el) {
  color = el.dataset.c;
  document.querySelectorAll('.dot').forEach(function(d){ d.classList.remove('sel'); });
  el.classList.add('sel');
  if (tool === 'pen') applyBrush();
}

function setWidth(w) {
  strokeW = w;
  [2,4,8].forEach(function(v) {
    var el = document.getElementById('btn-w' + v);
    if (el) el.classList.toggle('active', v === w);
  });
  applyBrush();
}

// ── Undo / Redo / Clear ───────────────────────────────────────
function doUndo() {
  var objs = fc.getObjects();
  if (!objs.length) return;
  var last = objs[objs.length - 1];
  redoObjs.push(last);
  fc.remove(last);
  fc.renderAll();
}

function doRedo() {
  if (!redoObjs.length) return;
  isRedoing = true;
  fc.add(redoObjs.pop());
  isRedoing = false;
  fc.renderAll();
}

function doClear() {
  fc.getObjects().slice().forEach(function(o){ fc.remove(o); });
  redoObjs = [];
  if (isPdf) delete pageData[curPage];
  fc.renderAll();
}

// ── Save / Load ───────────────────────────────────────────────
function doSave() {
  if (isPdf) {
    saveCurrentPage();
    toRN({ type: 'save', fabricJson: JSON.stringify(pageData) });
  } else {
    var json = fc.toJSON();
    delete json.backgroundImage;
    toRN({ type: 'save', fabricJson: JSON.stringify(json) });
  }
}

function loadJson(str) {
  try {
    fc.loadFromJSON(typeof str === 'string' ? JSON.parse(str) : str,
      function() { fc.renderAll(); });
  } catch(e) { console.warn('loadJson error', e); }
}

// ── Bridge ────────────────────────────────────────────────────
function toRN(msg) {
  if (window.ReactNativeWebView) {
    window.ReactNativeWebView.postMessage(JSON.stringify(msg));
  }
}

window.addEventListener('load', function() { toRN({ type: 'ready' }); });
</script>
</body>
</html>`;
