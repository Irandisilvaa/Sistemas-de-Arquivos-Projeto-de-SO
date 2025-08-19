Sistema de Arquivos Simulado em Python
Sobre o Projeto
Este projeto é um sistema de arquivos simulado desenvolvido em Python, com uma interface gráfica intuitiva construída com Tkinter. O principal objetivo é servir como uma ferramenta didática, permitindo que os usuários explorem e compreendam de forma prática o funcionamento interno de sistemas de arquivos reais. Ele simula operações como a criação, leitura, escrita, exclusão e gerenciamento de arquivos e diretórios, tudo em um ambiente seguro e controlado.

Estrutura e Funcionalidades Internas
O sistema é baseado em uma árvore hierárquica de diretórios que opera inteiramente na memória. A lógica interna gerencia o uso de um "disco" simulado, com um limite de tamanho definido por MAX_DISK_SIZE.

Nós de Diretório (DirectoryNode): Representam diretórios e funcionam como tabelas de índices. Eles contêm uma lista de filhos (children), que podem ser outros diretórios ou arquivos.

Nós de Arquivo (FileNode): Representam arquivos. Eles armazenam metadados essenciais, como nome, tamanho, conteúdo, datas de criação, modificação e acesso. Esses dados simulam o que seria um inode em um sistema de arquivos real.

Sistema de Arquivos (FileSystem): Controla todas as operações, incluindo:

Navegação: cd para navegar entre diretórios.

Gerenciamento: mkdir (criar diretório), touch (criar arquivo), ls (listar conteúdo).

Manipulação de Conteúdo: Ler e escrever conteúdo em arquivos.

Lixeira e Restauração: O sistema move arquivos e diretórios para uma lixeira (.lixeira) em vez de excluí-los permanentemente. A restauração preserva os metadados e o local original do arquivo.

Uso do Disco: O sistema calcula e atualiza o espaço ocupado em tempo real, garantindo que o limite de armazenamento não seja excedido.

Interface Gráfica (GUI)
A interface gráfica foi desenhada para ser intuitiva e facilitar a interação do usuário com o sistema.

Navegação e Visualização:

Barra de caminho que exibe o diretório atual.

Visualização da lista de arquivos e pastas.

Operações com Botões:

Criar novas pastas.

Criar novos arquivos de texto.

Importar arquivos externos (como imagens e PDFs).

Remover arquivos ou pastas (enviando-os para a lixeira).

Restaurar itens diretamente da lixeira.

Atualizar a lista de arquivos.

Recursos Visuais:

Uma barra de uso de disco que indica visualmente o espaço ocupado.

Exibição detalhada de informações de cada nó (tipo, tamanho, datas de acesso/modificação).

Pesquisa: Funcionalidade para pesquisar arquivos e pastas de forma recursiva.

Como Executar
Para rodar o projeto, execute o arquivo principal a partir da linha de comando:

python interface.py

Conceitos Fundamentais Abordados
Este projeto oferece uma excelente oportunidade para entender conceitos de ciência da computação, incluindo:

Gerenciamento de arquivos e metadados.

Estruturas de dados em árvore.

Tabelas de índices e alocação de blocos.

Sistema de permissões e segurança (simulação de lixeira).

Programação orientada a objetos (classes FileNode, DirectoryNode e FileSystem).

Separação da lógica de backend e frontend.
