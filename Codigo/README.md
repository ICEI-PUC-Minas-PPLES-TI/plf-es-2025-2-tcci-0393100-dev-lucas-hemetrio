# Código do Projeto

Todo o código do sistema Cognita, dividido em dois subprojetos:

- **`backend/`** — API REST em FastAPI com grafo de conhecimento no Neo4j (ver `backend/README.md`).
- **`mobile/`** — aplicativo React Native (Expo) para tablet.

As instruções completas de instalação e execução (pré-requisitos, variáveis de ambiente, mobile e testes) estão no [README na raiz do repositório](../README.md).

Atalho para rodar a API (a partir de `Codigo/backend/`):

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```