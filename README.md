# Cognita

O sistema Cognita nasce para solucionar uma lacuna fundamental no ecossistema de ferramentas de estudo digital: a fragmentação entre aplicativos de anotação de alta fidelidade, que tratam documentos como objetos isolados, e as plataformas de Gestão de Conhecimento Pessoal (PKM - Personal Knowledge Management), que, embora foquem na conexão de ideias, oferecem uma experiência básica de interação com os materiais-fonte.   

A proposta central do Cognita é unificar esses dois mundos, criando uma plataforma coesa para o estudo ativo. O objetivo é transformar um repositório passivo de informações em uma base de conhecimento dinâmica e interconectada, onde a inovação chave reside na construção de um grafo de conhecimento de forma automática, utilizando técnicas de Processamento de Linguagem Natural (PLN) para descobrir e visualizar conexões latentes entre os conceitos estudados pelo usuário. 


## Alunos integrantes da equipe

* Lucas Hemétrio Teixeira

## Professores responsáveis

* Cleiton Silva Tavares
* Danilo de Quadros Maia Filho
* Leonardo Vilela Cardoso
* Raphael Ramos Dias Costa

## Instruções de utilização

O sistema é dividido em dois componentes, ambos em `Codigo/`: o **backend** (API FastAPI + grafo Neo4j) e o **aplicativo mobile** (React Native / Expo, projetado para tablet em orientação horizontal).

### Pré-requisitos

- Python 3.11+ e Node.js 20+ (com npm)
- Uma instância **Neo4j** (protocolo Bolt) — ex.: via Docker
- Um armazenamento de objetos compatível com S3 — o projeto usa **MinIO** (ex.: via Docker)
- Credenciais do **Google Cloud Vision** (arquivo `google-credentials.json`) para o OCR/HCR

Exemplo para subir Neo4j e MinIO com Docker:

```bash
docker run -d --name neo4j -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/password neo4j:5
docker run -d --name minio -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ":9001"
```

### Backend (API)

```bash
cd Codigo/backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m spacy download pt_core_news_lg      # ~500 MB, usado no pipeline NER + co-ocorrência
cp .env.example .env                          # preencha SECRET_KEY, NEO4J_URL, MinIO e GOOGLE_APPLICATION_CREDENTIALS
uvicorn app.main:app --reload
```

A API sobe em `http://localhost:8000`. O modelo spaCy é carregado na primeira chamada às rotas de grafo, então a primeira requisição demora alguns segundos. Detalhes adicionais em `Codigo/backend/README.md`.

### Aplicativo mobile

```bash
cd Codigo/mobile
npm install
```

O app usa módulos nativos (reanimated, secure-store, webview), portanto **não roda no Expo Go** — é preciso um *development build*:

```bash
npm run build:dev:android        # gera o APK de desenvolvimento via EAS
npx expo start --dev-client      # inicia o Metro; abra o build no dispositivo/emulador
```

Instale o APK gerado num **tablet Android em modo paisagem** (o layout é desenhado para tela ampla). Se o app rodar num dispositivo físico, ajuste a URL do backend em `src/api/client.ts` para o IP da máquina onde a API está rodando (o padrão atende `localhost` e o emulador Android `10.0.2.2`).

### Testes

```bash
# Backend (unitários + integração)
cd Codigo/backend && source venv/bin/activate && pytest tests/ -v

# Mobile (Jest + React Native Testing Library)
cd Codigo/mobile && npm test
```

O teste de integração do Neo4j (TI-03) é pulado por padrão; para executá-lo, aponte para uma instância Neo4j descartável:

```bash
export NEO4J_TEST_URL="bolt://neo4j:senha@localhost:7687"
pytest tests/integration -v
```
