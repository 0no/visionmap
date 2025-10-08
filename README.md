# VisionMap Creator

Um aplicativo Python para criação de mapas visuais interativos com suporte a caixas, anotações, containers e conexões.

Operações básicas:
   - Clique duplo em uma caixa para editar seu texto ou na barra de título de um container para editar seu título
   - Use o menu Canvas para ajustar o tamanho da área de desenho, centralizar a visão ou ajustar o canvas ao conteúdoriar mapas visuais usando Python e Tkinter.

## Funcionalidades

- Criar caixas de texto no canvas
- Adicionar caixas de anotação para textos mais longos
- Criar containers para agrupar e organizar caixas relacionadas
- Conectar caixas e containers com linhas direcionais
- Adicionar rótulos às conexões para descrever relações
- Editar o texto das caixas e títulos dos containers
- Personalizar as cores das caixas e containers
- Mover caixas e containers livremente
- Redimensionar containers conforme necessário
- Controlar a ordem de sobreposição (trazer para frente/enviar para trás)
- Expandir/recolher anotações para manter o mapa limpo
- Salvar e carregar visionmaps
- Exportar o visionmap como imagem
- Exportar o visionmap como código Mermaid para integração com documentos Markdown
- Canvas redimensionável com barras de rolagem para diagramas grandes
- Navegação intuitiva usando mouse para mover e visualizar o canvas

## Requisitos

- Python 3.x
- Tkinter (geralmente vem instalado com o Python)
- Pillow (necessário para o ícone da aplicação e exportação de imagens): `pip install pillow`
- Ghostscript (opcional, para melhor qualidade nas imagens exportadas)

## Personalização

O aplicativo usa o arquivo `logo.png` na pasta raiz como ícone da janela principal. Você pode substituir este arquivo por qualquer imagem de sua preferência para personalizar a aparência do aplicativo.

## Como usar

1. Execute o arquivo `visionmap.py`:
   ```
   python visionmap.py
   ```

2. A interface apresenta os seguintes modos:
   - **Selecionar**: Para selecionar e mover caixas ou containers
   - **Adicionar Caixa**: Para criar novas caixas
   - **Adicionar Anotação**: Para criar caixas de anotação com textos mais longos
   - **Adicionar Container**: Para criar containers que agrupam caixas
   - **Conectar**: Para criar conexões entre caixas
   - **Trocar Cor**: Para alterar a cor da caixa ou container selecionado

3. Operações básicas:
   - Clique duplo em uma caixa para editar seu texto ou na barra de título de um container para editar seu título
   - Use o modo "Selecionar" para arrastar e mover caixas ou containers
   - Use Ctrl+clique para selecionar múltiplos elementos ao mesmo tempo
   - Use o menu Canvas para ajustar o tamanho da área de desenho
   - Use o modo "Adicionar Container" para criar agrupadores de caixas relacionadas
   - Arraste caixas para dentro e fora dos containers para organizá-las
   - Redimensione os containers usando o manipulador no canto inferior direito
   - Use o modo "Adicionar Anotação" para criar caixas para textos mais longos
   - Clique no botão "+" nas caixas de anotação para expandir/recolher o texto
   - Use o modo "Conectar" para criar setas ligando caixas e containers
   - Adicione rótulos às setas para descrever as relações entre elementos
   - Selecione uma caixa ou container e clique no botão "Trocar Cor" para personalizá-lo
   - Clique com o botão direito em um elemento para acessar o menu de contexto
   - Clique com o botão direito em uma conexão (seta) para editar seu rótulo ou excluí-la
   - Use o menu de contexto para trazer elementos para frente ou enviá-los para trás
   - Pressione Delete para excluir uma caixa, container ou conexão selecionado
   - Use Ctrl+S para salvar, Ctrl+O para abrir e Ctrl+N para criar um novo visionmap

## Atalhos de Teclado

### Operações de Arquivo
- `Ctrl+N`: Novo visionmap
- `Ctrl+O`: Abrir visionmap
- `Ctrl+S`: Salvar visionmap

### Modos de Operação
- `A`: Modo Seleção
- `B`: Adicionar Caixa
- `C`: Adicionar Anotação
- `D`: Adicionar Container
- `E`: Modo Conexão
- `F`: Trocar Cor

### Edição e Manipulação
- `G`: Trazer para Frente
- `H`: Enviar para Trás
- `Delete`: Excluir item selecionado

### Navegação e Canvas
- `Botão do meio do mouse`: Arrastar para mover a visão do canvas
- `Shift + Arrastar`: Arrastar para mover a visão do canvas (alternativa)
- `Roda do mouse`: Rolar verticalmente
- `Ctrl + Roda do mouse`: Rolar horizontalmente

## Formatos de arquivo

- `.vmap`: Formato nativo para salvar os visionmaps
- `.png`: Formato de exportação de imagem
- `.md`: Exportação como código Mermaid em arquivo Markdown

## Sobre a exportação Mermaid

O VisionMap Creator permite exportar seus diagramas como código [Mermaid](https://mermaid-js.github.io/), uma linguagem de marcação para criar diagramas a partir de texto. Isso é útil para:

- Integrar seus visionmaps em documentação Markdown (GitHub, GitLab, etc.)
- Compartilhar diagramas em formato de texto
- Editar ou ajustar diagramas em editores de texto
- Colaborar em diagramas usando controle de versão

Recursos da exportação Mermaid:
- **Preservação de posições**: O código Mermaid gerado inclui informações de posicionamento para manter o layout do seu diagrama
- **Estilos personalizados**: As cores das caixas e containers são preservadas no diagrama exportado
- **Visualização HTML**: Um arquivo HTML adicional é gerado para visualizar o diagrama com a renderização correta
- **Rótulos de conexão**: Os textos/rótulos das conexões são incluídos no código Mermaid

Ao exportar como Mermaid, uma janela de visualização mostrará o código gerado, que você pode copiar para a área de transferência ou visualizar diretamente em um navegador.