# GeoCS Copilot

Protótipo de automação para Customer Success em geotecnologia, com demonstração principal inspirada em um cenário de telecom/Vivo usando ArcGIS para cobertura, rede, ativos e equipes de campo.

A aplicação simula uma triagem inteligente para clientes que usam a Plataforma ArcGIS, classificando solicitações por produto, categoria, prioridade, sentimento, impacto de negócio, SLA sugerido e equipe responsável.

## Stack

- Python
- Streamlit
- DuckDB / MotherDuck
- Pandas
- Plotly

## Estrutura do projeto

```
geocs_copilot/
├── app.py              # Interface Streamlit
├── requirements.txt
├── seed_data.py        # Script para inicializar o banco manualmente
└── src/
    ├── __init__.py
    ├── classifier.py   # Lógica de classificação por regras
    └── db.py           # Conexão DuckDB / MotherDuck
```

## Como rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

Sem token MotherDuck, o app usa um arquivo local `geocs_copilot.duckdb`.

## Como usar com MotherDuck

Crie o arquivo `.streamlit/secrets.toml`:

```toml
MOTHERDUCK_TOKEN = "seu_token"
```

## Deploy no Streamlit Cloud

1. Suba o projeto para o GitHub.
2. Acesse [streamlit.io/cloud](https://streamlit.io/cloud).
3. Aponte para `app.py`.
4. Em Secrets, adicione:

```toml
MOTHERDUCK_TOKEN = "seu_token"
```

## Demonstração sugerida

Use os exemplos prontos na aba **Nova solicitação**:

- **Vivo** — Telecom / Rede (exemplo principal)
- Starbucks — Expansão de lojas
- BP — Operações de campo
- Eletrobras Chesf — Gestão de ativos
- Prefeitura do Recife — Centro de Operações
- Natura — Sustentabilidade

## Sobre a arquitetura

Neste MVP, a classificação foi construída com regras programadas para garantir estabilidade e previsibilidade. A arquitetura foi pensada para permitir que, em uma próxima etapa, um modelo de IA substitua ou complemente o módulo `src/classifier.py` sem alterar a interface ou a estrutura do sistema.
