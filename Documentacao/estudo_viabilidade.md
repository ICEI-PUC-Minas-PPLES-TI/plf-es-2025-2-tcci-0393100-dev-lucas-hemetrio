\# Estudo de Viabilidade \- TCC I

Este documento apresenta o estudo de viabilidade para o projeto de desenvolvimento sugerido por Lucas Hemétrio Teixeira como Trabalho de Conclusão de Curso (TCC) do curso de Bacharelado em Engenharia de Software da Pontifícia Universidade Católica de Minas Gerais (PUC Minas). O projeto consiste na criação da "Cognita", uma plataforma de software inovadora, projetada exclusivamente para tablets, que visa transformar o processo de estudo autodirigido. A solução propõe ir além da simples organização de materiais, utilizando tecnologias de Inteligência Artificial para processar e conectar automaticamente o conhecimento do usuário, construindo uma base de conhecimento visual e interativa em formato de grafo.

O objetivo deste estudo é demonstrar a total conformidade do projeto com a Resolução do Trabalho de Conclusão de Curso I, detalhando seu enquadramento, a relevância da demanda atendida e, principalmente, a alta complexidade técnica envolvida, que justificam sua execução como um TCC de vanguarda e de alto valor acadêmico.

A Resolução do TCC I estabelece diretrizes claras para os trabalhos a serem desenvolvidos. Conforme o item 3, o projeto enquadra-se inequivocamente na modalidade de desenvolvimento de software.

A proposta atende precisamente ao item 3.2.2 da resolução, que define que projetos sem cliente específico devem atender a uma "demanda identificada pelo aluno". A demanda identificada é a lacuna existente entre ferramentas de anotação de alta qualidade e sistemas de gerenciamento de conhecimento, que força estudantes a um fluxo de trabalho digital fragmentado e ineficiente.

Adicionalmente, o projeto cumpre o item 3.2.2.2, que exige a existência de "usuários reais" (estudantes universitários, concurseiros) como beneficiários e a aplicação de uma "abordagem de design centrado no usuário". Todo o desenvolvimento da interface para tablet será guiado por essa abordagem, com validação contínua para garantir a máxima usabilidade.

A viabilidade de um TCC em Engenharia de Software é medida por sua complexidade técnica. O projeto "Cognita" é inerentemente complexo, envolvendo desafios significativos em múltiplas frentes.

* Processamento de Dados Não Estruturados (OCR e HCR): Um dos pilares do sistema é a capacidade de tornar 100% do conteúdo do usuário pesquisável. Isso exige a implementação de dois processos de IA distintos:  
  * OCR (Reconhecimento Óptico de Caracteres): Para extrair texto de documentos PDF, transformando imagens em dados.  
  * HCR (Reconhecimento de Escrita à Mão): Um desafio mais complexo, que envolve a conversão de anotações manuscritas (traços vetoriais) em texto estruturado através da integração com APIs de IA especializadas.

* Construção Automatizada de Grafo de Conhecimento: Este é o principal desafio e a maior inovação do projeto. A implementação exigirá:  
  * Processamento de Linguagem Natural (NLP): Utilização de modelos de linguagem para realizar a extração de entidades (conceitos, nomes, locais) de todo o texto processado.  
  * Geração de Embeddings Semânticos: Conversão de textos em vetores numéricos para permitir a análise de similaridade e a identificação de relações contextuais entre diferentes notas e documentos.  
  * Modelagem e Persistência em Banco de Dados de Grafo: Utilização de uma tecnologia NoSQL específica, como o Neo4j, para armazenar e consultar eficientemente a rede de nós (conceitos) e arestas (relações) que compõem o conhecimento do usuário.  
* Design de Interface para Interação Complexa: Projetar uma interface para tablet que permita ao usuário interagir de forma fluida com anotações, documentos e, ao mesmo tempo, visualizar e navegar em um grafo de conhecimento complexo é um desafio significativo de Engenharia de Usabilidade e Design de Interação (IxD).

Este projeto mobiliza um conjunto de conhecimentos aprofundados, abrangendo múltiplos domínios de Engenharia de Software:

* Inteligência Artificial Aplicada e Processamento de Linguagem Natural (NLP)  
* Arquitetura de Software para Sistemas de Processamento de Dados  
* Modelagem de Dados para Bancos de Dados NoSQL (Grafos)  
* Design Centrado no Usuário e Engenharia de Usabilidade para Tablets  
* Engenharia de Requisitos para Sistemas com Componentes de IA  
* Segurança e Ética no Tratamento de Dados Pessoais

Em síntese, o projeto "Cognita" demonstra total conformidade com a Resolução do TCC I. Ele se enquadra como um software que atende a uma demanda real identificada pelo aluno e se compromete com uma metodologia de design centrado no usuário com alta complexidade técnica, centrada na aplicação de múltiplas tecnologias de IA (OCR, HCR, NLP) e na implementação de uma estrutura de dados avançada (grafo de conhecimento).

