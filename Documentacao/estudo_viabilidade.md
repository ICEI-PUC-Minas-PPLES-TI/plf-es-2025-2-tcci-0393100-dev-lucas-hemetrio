**Estudo de Viabilidade \- TCC I**

Este documento apresenta o estudo de viabilidade para o projeto de desenvolvimento sugerido por Lucas Hemétrio Teixeira como Trabalho de Conclusão de Curso (TCC) do curso de Bacharelado em Engenharia de Software da Pontifícia Universidade Católica de Minas Gerais (PUC Minas). O projeto consiste na criação da "Cognita", uma plataforma de software inovadora, projetada exclusivamente para *tablets*, que visa transformar o processo de estudo autodirigido. A solução propõe ir além da simples organização de materiais, utilizando tecnologias de Inteligência Artificial para processar e conectar automaticamente o conhecimento do usuário, construindo uma base de conhecimento visual e interativa em formato de grafo.

O objetivo deste estudo é demonstrar a total conformidade do projeto com a Resolução do Trabalho de Conclusão de Curso I, detalhando seu enquadramento, a relevância da demanda atendida e, principalmente, a alta complexidade técnica envolvida, que justificam sua execução como um TCC de vanguarda e de alto valor acadêmico.

A Resolução do TCC I estabelece diretrizes claras para os trabalhos a serem desenvolvidos. Conforme o item 3, o projeto enquadra-se inequivocamente na modalidade de desenvolvimento de software.

A proposta atende precisamente ao item 3.2.2 da resolução, que define que projetos sem cliente específico devem atender a uma "demanda identificada pelo aluno". A demanda identificada é a lacuna existente entre ferramentas de anotação de alta qualidade e sistemas de gerenciamento de conhecimento, que força estudantes a um fluxo de trabalho digital fragmentado e ineficiente.

Adicionalmente, o projeto cumpre o item 3.2.2.2, que exige a existência de "usuários reais" (estudantes universitários, concurseiros) como beneficiários e a aplicação de uma "abordagem de *design* centrado no usuário". Todo o desenvolvimento da interface para tablet será guiado por essa abordagem, com validação contínua para garantir a máxima usabilidade.

A viabilidade técnica do Cognita depende da capacidade de integrar três componentes tecnológicos principais: um sistema de Reconhecimento de Escrita à Mão (HCR \- *Handprint Character Recognition*) e Óptico de Caracteres (OCR \- *Optical Character Recognition*); um *pipeline* de Processamento de Linguagem Natural (PLN) para a construção do grafo de conhecimento; e uma interface de usuário de alta fidelidade otimizada para tablets.

* Reconhecimento de Conteúdo (OCR/HCR): A funcionalidade de tornar 100% do conteúdo pesquisável é tecnicamente viável através de soluções de mercado.  
    
  * APIs Comerciais: Serviços como Google Cloud Vision API e Microsoft Azure AI Vision oferecem alta precisão para o reconhecimento de texto impresso e manuscrito em português. Estudos comparativos demonstram a superioridade dessas APIs em relação a alternativas de código aberto, especialmente em cenários com caligrafia variável. A documentação oficial confirma o suporte robusto para o idioma português, incluindo a escrita à mão.  
  * Soluções *Open-Source*: Bibliotecas como Tesseract e Paddle OCR são alternativas robustas e sem custo. O Tesseract possui suporte oficial para o português, embora sua precisão com caligrafia possa ser inferior à das APIs comerciais sem treinamento adicional. A existência de datasets públicos para treinamento de HCR em português, como o BRESSAY, indica a maturidade da área.  
      
* Construção do Grafo de Conhecimento: A inovação central do projeto — a construção automática de um grafo semântico — é um desafio de engenharia, não de pesquisa fundamental. O processo se baseia em um *pipeline* de PLN bem estabelecido:  
    
  * Reconhecimento de Entidades Nomeadas (NER \- *Named Entity Recognition*): A tarefa de identificar os "nós" do grafo (pessoas, locais, conceitos) é suportada por modelos pré-treinados de alto desempenho. A plataforma Hugging Face disponibiliza múltiplos modelos de NER otimizados para o português, como o bert-portuguese-ner e o bert-large-pt-ner-enamex, que podem ser facilmente integrados a uma aplicação backend.     
  * Extração de Relações (RE \- *Relation extraction*): A identificação das arestas que conectam os nós é uma área de pesquisa ativa, com abordagens e modelos desenvolvidos especificamente para o português, utilizando desde métodos supervisionados até o uso de Grandes Modelos de Linguagem (LLMs). A implementação de um pipeline que executa NER e RE para extrair triplas estruturadas (sujeito-predicado-objeto) é, portanto, tecnicamente factível.   


* Interface de Usuário (*Tablet-First*): A criação de uma interface fluida para anotação com caneta *stylus* em React Native é viável com o uso de bibliotecas modernas. A combinação de React Native Skia para renderização de alta performance no canvas, React Native Gesture Handler para captura de gestos na thread de UI, e bibliotecas como perfect-freehand para embelezar o traço, permite criar uma experiência de escrita natural e responsiva, que é um pilar da proposta de valor do sistema.


O risco tecnológico do projeto é baixo. Seus componentes mais ambiciosos não exigem a invenção de novas tecnologias, mas sim a engenharia e a integração criteriosa de ferramentas e modelos existentes, maduros e bem documentados.

Este projeto mobiliza um conjunto de conhecimentos aprofundados, abrangendo múltiplos domínios de Engenharia de Software:

* Inteligência Artificial Aplicada e Processamento de Linguagem Natural  
* Arquitetura de Software para Sistemas de Processamento de Dados  
* Modelagem de Dados para Bancos de Dados NoSQL (Grafos)  
* Design Centrado no Usuário e Engenharia de Usabilidade para Tablets  
* Engenharia de Requisitos para Sistemas com Componentes de IA  
* Segurança e Ética no Tratamento de Dados Pessoais

Em síntese, o projeto "Cognita" demonstra total conformidade com a Resolução do TCC I. Ele se enquadra como um software que atende a uma demanda real identificada pelo aluno e se compromete com uma metodologia de design centrado no usuário com alta complexidade técnica, centrada na aplicação de múltiplas tecnologias de IA (OCR, HCR, PLN) e na implementação de uma estrutura de dados avançada (grafo de conhecimento).

