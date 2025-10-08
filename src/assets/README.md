# Assets - Recursos da Aplicação

Esta pasta contém todos os recursos estáticos da aplicação VisionMap Creator.

## Estrutura

```
src/assets/
├── __init__.py          # Documentação da pasta
├── logo.png             # Ícone da aplicação
└── README.md            # Este arquivo
```

## Como usar

Para acessar recursos de forma programática, use o utilitário `src/utils/assets.py`:

```python
from ..utils.assets import get_asset_path, asset_exists

# Obter caminho do logo
logo_path = get_asset_path("logo.png")

# Verificar se existe
if asset_exists("logo.png"):
    # Usar o recurso
    pass
```

## Adicionando novos recursos

1. Coloque o arquivo nesta pasta
2. Use o utilitário `assets.py` para acessá-lo
3. Atualize esta documentação se necessário

## Formatos suportados

- **Imagens**: PNG, JPG, GIF (para ícones e recursos visuais)
- **Dados**: JSON, XML (para configurações ou dados estáticos)
- **Texto**: TXT, MD (para documentação ou templates)