// Lê node_modules/d3/dist/d3.min.js e gera src/assets/d3.bundle.ts
// exportando o conteúdo como string.
//
// Rodar manualmente sempre que atualizar a versão do d3:
//   node scripts/vendor-d3.mjs
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SRC = resolve(__dirname, '../node_modules/d3/dist/d3.min.js');
const DEST = resolve(__dirname, '../src/assets/d3.bundle.ts');

const d3Source = readFileSync(SRC, 'utf8');

// Escapar backslash, backticks e ${ pra usar template literal seguro.
const escaped = d3Source
  .replace(/\\/g, '\\\\')
  .replace(/`/g, '\\`')
  .replace(/\$\{/g, '\\${');

const out = `// AUTO-GERADO por scripts/vendor-d3.mjs — não editar manualmente.
// Para atualizar: cd mobile && node scripts/vendor-d3.mjs
export const D3_BUNDLE: string = \`${escaped}\`;
`;

writeFileSync(DEST, out, 'utf8');
console.log(`Wrote ${DEST} (${d3Source.length} bytes of d3)`);
