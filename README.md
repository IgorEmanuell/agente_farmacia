# Agente IA para Atendimento de Farmácia

Este projeto implementa um agente virtual inteligente para atendimento via WhatsApp, utilizando a Evolution API.

## Funcionalidades Principais

*   Responder a dúvidas sobre medicamentos e produtos.
*   Verificar estoque e disponibilidade.
*   Informar sobre a necessidade de receita médica.
*   Criar reservas de produtos para retirada na loja.
*   Suporte inicial a texto (expansível para voz e imagem).

## Requisitos Técnicos

Consultar o documento original `pasted_content.txt` para detalhes completos.

## Como Executar (Instruções Preliminares)

*(A ser detalhado após a configuração do Docker)*

1.  Configure as variáveis de ambiente (ex: API keys) no ficheiro `.env`.
2.  Construa e execute os containers Docker:
    ```bash
    docker-compose up --build
    ```
3.  Configure o webhook da Evolution API para apontar para o endpoint exposto pela aplicação.

## Estrutura do Projeto

```
farmacia_agente_ia/
├── config/             # Ficheiros de configuração (config.yaml)
│   └── config.yaml
├── data/               # Dados persistentes (ex: base de dados SQLite)
├── src/                # Código fonte da aplicação
│   ├── __init__.py
│   ├── main.py         # Ponto de entrada da API (FastAPI)
│   ├── database.py     # Lógica de acesso à base de dados (SQLAlchemy)
│   ├── evolution_api.py # Interação com a Evolution API
│   ├── agent_logic.py  # Lógica principal do agente
│   └── models.py       # Modelos de dados (Pydantic/SQLAlchemy)
├── .env                # Variáveis de ambiente (não versionado)
├── .gitignore          # Ficheiros a ignorar pelo Git
├── Dockerfile          # Instruções para construir a imagem Docker
├── docker-compose.yml  # Orquestração dos containers
├── requirements.txt    # Dependências Python
├── README.md           # Este ficheiro
└── todo.md             # Lista de tarefas do desenvolvimento
```


### Exportação de Dados

Para exportar a base de dados SQLite para CSV, execute:
```bash
python src/export_data.py
```
