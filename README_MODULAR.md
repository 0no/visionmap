# VisionMap Creator

Um aplicativo Python para criação de mapas visuais interativos com suporte a caixas, anotações, containers e conexões.

## Estrutura do Projeto

O projeto foi organizado seguindo boas práticas de desenvolvimento de software:

```
VisionMap/
├── main.py                     # Ponto de entrada da aplicação
├── logo.png                    # Ícone da aplicação
├── README.md                   # Este arquivo
├── visionmap.py                # Arquivo original (mantido para referência)
└── src/                        # Código fonte modular
    ├── __init__.py
    ├── models/                 # Modelos de dados
    │   ├── __init__.py
    │   ├── base.py            # Classe base abstrata
    │   ├── box.py             # Caixa básica
    │   ├── note_box.py        # Caixa de anotação
    │   ├── container.py       # Container para agrupar elementos
    │   └── connection.py      # Conexões entre elementos
    ├── ui/                    # Interface do usuário
    │   ├── __init__.py
    │   ├── main_window.py     # Janela principal
    │   ├── event_handlers.py  # Gerenciador de eventos
    │   ├── menu_manager.py    # Gerenciador de menus
    │   └── toolbar_manager.py # Gerenciador da toolbar
    └── utils/                 # Utilitários
        ├── __init__.py
        ├── file_manager.py    # Operações de arquivo
        ├── export_utils.py    # Utilitários de exportação
        └── import_utils.py    # Utilitários de importação
```

## Funcionalidades

### Elementos Visuais
- **Caixas básicas**: Elementos retangulares com texto editável
- **Caixas de anotação**: Elementos com texto expansível em janela separada
- **Containers**: Agrupadores que podem conter caixas e outros containers
- **Conexões**: Linhas conectando elementos, com suporte a rótulos

### Interações
- **Seleção única e múltipla**: Ctrl+clique ou seleção por área
- **Movimentação**: Arrastar elementos individuais ou em grupo
- **Edição**: Duplo clique para editar texto/títulos
- **Redimensionamento**: Containers podem ser redimensionados
- **Camadas**: Trazer para frente/enviar para trás

### Arquivo
- **Salvar/Abrir**: Formato próprio .vmap
- **Exportar**: Imagens PNG e diagramas Mermaid
- **Importar**: Diagramas Mermaid

### Navegação
- **Zoom**: Ctrl+roda do mouse
- **Pan**: Botão do meio ou Shift+arrastar
- **Rolagem**: Roda do mouse (vertical/horizontal)

## Atalhos de Teclado

### Operações de Arquivo
- `Ctrl+N`: Novo visionmap
- `Ctrl+O`: Abrir arquivo
- `Ctrl+S`: Salvar arquivo

### Modos de Edição
- `A`: Modo seleção
- `B`: Adicionar caixa
- `C`: Adicionar anotação
- `D`: Adicionar container
- `E`: Conectar elementos
- `F`: Trocar cor
- `G`: Trazer para frente
- `H`: Enviar para trás

### Seleção
- `Ctrl+A`: Selecionar tudo
- `Esc`: Limpar seleção
- `Delete`: Excluir selecionados

## Como Executar

1. Certifique-se de ter Python 3.6+ instalado
2. Instale as dependências:
   ```bash
   pip install tkinter pillow
   ```
3. Execute a aplicação:
   ```bash
   python main.py
   ```

## Dependências

- **tkinter**: Interface gráfica (geralmente incluída com Python)
- **Pillow (PIL)**: Manipulação de imagens
- **pickle**: Serialização de dados (biblioteca padrão)
- **os**: Operações do sistema (biblioteca padrão)
- **math**: Operações matemáticas (biblioteca padrão)
- **re**: Expressões regulares (biblioteca padrão)

## Arquitetura

### Padrão MVC
O projeto segue uma adaptação do padrão Model-View-Controller:

- **Models** (`src/models/`): Classes que representam os dados e lógica de negócio
- **Views** (`src/ui/`): Interface do usuário e gerenciamento de eventos
- **Utils** (`src/utils/`): Utilitários para operações auxiliares

### Hierarquia de Classes
```
VisualElement (base abstrata)
├── VisionMapBox
│   └── NoteBox
└── Container

Connection (standalone)
```

### Gerenciadores
- **EventHandlers**: Centraliza o tratamento de eventos do mouse e teclado
- **MenuManager**: Gerencia a criação e comportamento dos menus
- **ToolbarManager**: Gerencia a barra de ferramentas

## Contribuição

O código foi modularizado para facilitar manutenção e extensão. Para adicionar novas funcionalidades:

1. **Novos elementos visuais**: Herdar de `VisualElement`
2. **Novos formatos de exportação**: Adicionar em `export_utils.py`
3. **Novos eventos**: Estender `EventHandlers`
4. **Nova interface**: Criar novos gerenciadores em `src/ui/`

## Versão

**v1.2.0** - Versão modularizada com arquitetura aprimorada

## Licença

Projeto desenvolvido para fins educacionais e de demonstração.