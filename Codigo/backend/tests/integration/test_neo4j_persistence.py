"""TI-03 — Teste de integração de persistência do grafo no Neo4j (protocolo Bolt).

Cenário (Tabela 9, doc): persistir 50 nós e 100 relações de uma vez; a transação
deve ser commitada e uma query de contagem deve retornar os números exatos.

Roda contra uma instância Neo4j de teste **dedicada e descartável** (ex.: container
Docker). Configure a URL e o teste roda; sem ela, é pulado:

    export NEO4J_TEST_URL="bolt://neo4j:senha@localhost:7687"
    pytest tests/integration -v

ATENÇÃO: aponte para um banco descartável — o teste cria e apaga um subgrafo
próprio (limpa só o que criou, via um Project marcador).
"""
import os
import uuid
from itertools import combinations

import pytest

NEO4J_TEST_URL = os.getenv("NEO4J_TEST_URL")

pytestmark = pytest.mark.skipif(
    not NEO4J_TEST_URL,
    reason="defina NEO4J_TEST_URL apontando para um Neo4j de teste descartável",
)

N_NODES = 50
N_EDGES = 100


@pytest.fixture
def test_project():
    """Conecta o neomodel ao Neo4j de teste e entrega um Project marcador isolado.

    Limpa o subgrafo do projeto ao final (DETACH DELETE), mesmo em caso de falha.
    """
    from neomodel import config, db

    from app.models.project import Project

    config.DATABASE_URL = NEO4J_TEST_URL
    db.install_all_labels()

    marker = f"ti03-{uuid.uuid4()}"
    project = Project(name=marker).save()
    try:
        yield project
    finally:
        db.cypher_query(
            """
            MATCH (p:Project {uid: $uid})-[:HAS_KNOWLEDGE_NODE]->(n:KnowledgeNode)
            OPTIONAL MATCH (m:Mention)-[:OF_ENTITY]->(n)
            DETACH DELETE p, n, m
            """,
            {"uid": project.uid},
        )
        # garante remoção do próprio Project caso não tenha nós ligados
        db.cypher_query("MATCH (p:Project {uid:$uid}) DETACH DELETE p", {"uid": project.uid})


def test_persists_50_nodes_and_100_edges_in_one_transaction(test_project):
    from neomodel import db

    from app.models.knowledge_node import KnowledgeNode

    pairs = list(combinations(range(N_NODES), 2))[:N_EDGES]
    assert len(pairs) == N_EDGES  # 50 nós permitem 1225 pares; 100 é viável

    with db.transaction:
        nodes = []
        for i in range(N_NODES):
            node = KnowledgeNode(
                label="PER",
                text_norm=f"entidade-{i}",
                text_display=f"Entidade {i}",
                mention_count=1,
            ).save()
            test_project.knowledge_nodes.connect(node)
            nodes.append(node)
        for a, b in pairs:
            nodes[a].co_occurs_with.connect(nodes[b])

    node_count, _ = db.cypher_query(
        """
        MATCH (p:Project {uid: $uid})-[:HAS_KNOWLEDGE_NODE]->(n:KnowledgeNode)
        RETURN count(n)
        """,
        {"uid": test_project.uid},
    )
    edge_count, _ = db.cypher_query(
        """
        MATCH (p:Project {uid: $uid})-[:HAS_KNOWLEDGE_NODE]->(a:KnowledgeNode)
              -[r:CO_OCCURS_WITH]->(b:KnowledgeNode)
        RETURN count(r)
        """,
        {"uid": test_project.uid},
    )

    assert node_count[0][0] == N_NODES
    assert edge_count[0][0] == N_EDGES
