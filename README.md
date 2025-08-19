# 🗂️ Sistema de Arquivos Simulado em Python

## 📌 Sobre o Projeto
Este projeto é um **sistema de arquivos simulado** desenvolvido em **Python**, com uma **interface gráfica** construída em **Tkinter**.  
O objetivo principal é servir como uma **ferramenta didática**, permitindo que os usuários explorem e compreendam, de forma prática, o funcionamento interno de sistemas de arquivos reais.  

Ele simula operações como:
- Criação, leitura, escrita e exclusão de arquivos e diretórios.
- Navegação entre pastas.
- Gerenciamento de espaço em disco.
- Lixeira e restauração de arquivos.

Tudo isso acontece em um **ambiente seguro e controlado**, ideal para fins educacionais.

---

## ⚙️ Estrutura e Funcionalidades

O sistema é baseado em uma **árvore hierárquica de diretórios**, totalmente em memória, com gerenciamento de um "disco" simulado limitado por `MAX_DISK_SIZE`.

### 🔹 Componentes Internos
- **DirectoryNode (Diretórios)**  
  Representam pastas, funcionando como tabelas de índices.  
  Cada diretório armazena filhos (`children`), que podem ser arquivos ou outros diretórios.

- **FileNode (Arquivos)**  
  Representam arquivos, contendo:  
  - Nome  
  - Tamanho  
  - Conteúdo  
  - Datas de criação, modificação e acesso  
  (simulando inodes de sistemas reais)

- **FileSystem (Sistema de Arquivos)**  
  Responsável pelas operações principais:
  - **Navegação:** `cd` para trocar de diretório  
  - **Gerenciamento:** `mkdir` (criar diretório), `touch` (criar arquivo), `ls` (listar conteúdo)  
  - **Manipulação de Conteúdo:** leitura e escrita em arquivos  
  - **Lixeira:** itens removidos vão para `.lixeira` em vez de exclusão definitiva  
  - **Uso do Disco:** cálculo em tempo real do espaço ocupado  

---

## 🖥️ Interface Gráfica (GUI)

A interface foi projetada para ser **intuitiva** e facilitar o uso.

### 🔹 Navegação e Visualização
- Barra de caminho exibindo o diretório atual.  
- Lista visual de arquivos e pastas.  

### 🔹 Operações Disponíveis
- Criar novas pastas  
- Criar arquivos de texto   
- Remover arquivos/pastas (enviando para a lixeira)  
- Restaurar itens da lixeira
- Editar o conteúdo dos arquivos
- Copiar arquivos e colar em outro lugar na árvore 

### 🔹 Recursos Visuais
- **Barra de uso do disco** mostrando o espaço ocupado.  
- Exibição detalhada de informações de arquivos (tipo, tamanho, datas).  
- **Pesquisa recursiva** de arquivos e diretórios.  

---

## 🚀 Como Executar

Execute o interface.py ou abertura.py 

