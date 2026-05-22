# Cognita — Backend

## Setup

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m spacy download pt_core_news_lg
```

O download do modelo spaCy `pt_core_news_lg` baixa ~500 MB e é usado pelo pipeline NER+RE (Sprint 7). A primeira chamada às rotas de knowledge demora alguns segundos enquanto o modelo é carregado em memória.

## Rodar

```bash
source venv/bin/activate && uvicorn app.main:app --reload
```

Requisitos externos (Bolt + S3-compat + Vision):
- Neo4j em `bolt://neo4j:password@localhost:7687`
- MinIO em `localhost:9000`
- `google-credentials.json` (gitignored) com role "Cloud Vision AI Service Agent"; `.env` com `GOOGLE_APPLICATION_CREDENTIALS=./google-credentials.json`

## Testes

```bash
source venv/bin/activate && pytest tests/ -v
```

Convenção: nenhum teste toca Neo4j real. Tudo que envolve DB é mockado via `unittest.mock.patch` — ver `tests/services/test_ocr_pipeline.py` para o padrão de orchestration tests, e `tests/api/test_search_route.py` para o padrão de route tests (`dependency_overrides` + `patch` no service).
