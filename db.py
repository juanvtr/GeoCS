
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional

import duckdb
import pandas as pd
import streamlit as st

DB_NAME = "geocs360"


def get_motherduck_token() -> Optional[str]:
    try:
        if "MOTHERDUCK_TOKEN" in st.secrets:
            return st.secrets["MOTHERDUCK_TOKEN"]
    except Exception:
        pass
    return os.getenv("MOTHERDUCK_TOKEN")


def get_db_name() -> str:
    try:
        if "MOTHERDUCK_DB_NAME" in st.secrets:
            return st.secrets["MOTHERDUCK_DB_NAME"]
    except Exception:
        pass
    return os.getenv("MOTHERDUCK_DB_NAME", DB_NAME)


@st.cache_resource(show_spinner=False)
def get_connection():
    db_name = get_db_name()
    token = get_motherduck_token()

    if token:
        # Connect to MotherDuck workspace first, then create/use the target DB.
        con = duckdb.connect(f"md:?motherduck_token={token}")
        con.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        con.execute(f"USE {db_name}")
        return con

    return duckdb.connect(f"{db_name}.duckdb")


def execute(sql: str, params: Optional[list] = None):
    con = get_connection()
    return con.execute(sql, params or [])


def query_df(sql: str, params: Optional[list] = None) -> pd.DataFrame:
    return execute(sql, params).df()


def fetch_scalar(sql: str, params: Optional[list] = None, default=0):
    """Return the first column of the first row safely.

    This avoids the Streamlit Cloud crash where a seed COUNT query may
    unexpectedly return no row during app bootstrap/reload.
    """
    cur = execute(sql, params)
    if cur is None:
        return default

    row = cur.fetchone()
    if row is None or len(row) == 0 or row[0] is None:
        return default

    return row[0]


def column_exists(table_name: str, column_name: str) -> bool:
    try:
        df = query_df(f"PRAGMA table_info('{table_name}')")
        if df.empty:
            return False
        return column_name.lower() in [str(v).lower() for v in df["name"].tolist()]
    except Exception:
        return False


def add_column_if_missing(table_name: str, column_name: str, column_type: str) -> None:
    if column_exists(table_name, column_name):
        return
    try:
        execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
    except Exception as exc:
        msg = str(exc).lower()
        if "already exists" in msg or "duplicate" in msg:
            return
        raise


def ensure_ticket_response_columns() -> None:
    add_column_if_missing("tickets", "admin_response", "VARCHAR")
    add_column_if_missing("tickets", "responded_by", "VARCHAR")
    add_column_if_missing("tickets", "responded_at", "TIMESTAMP")


def init_db() -> None:
    execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id   VARCHAR PRIMARY KEY,
            name      VARCHAR,
            email     VARCHAR UNIQUE,
            password  VARCHAR,
            role      VARCHAR,
            client_id VARCHAR,
            is_active BOOLEAN
        );
        """
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS clients (
            client_id VARCHAR PRIMARY KEY,
            client_name VARCHAR,
            sector VARCHAR,
            business_context VARCHAR,
            criticality VARCHAR,
            default_sla_hours INTEGER,
            main_products VARCHAR,
            city VARCHAR,
            state VARCHAR,
            latitude DOUBLE,
            longitude DOUBLE,
            health_score INTEGER,
            churn_risk VARCHAR
        );
        """
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id VARCHAR PRIMARY KEY,
            created_at TIMESTAMP,
            client_id VARCHAR,
            client_name VARCHAR,
            requester VARCHAR,
            original_message VARCHAR,
            product VARCHAR,
            category VARCHAR,
            priority VARCHAR,
            sentiment VARCHAR,
            business_impact VARCHAR,
            sla_hours INTEGER,
            responsible_team VARCHAR,
            summary VARCHAR,
            next_action VARCHAR,
            suggested_response VARCHAR,
            region_detected VARCHAR,
            business_objective VARCHAR,
            status VARCHAR
        );
        """
    )

    ensure_ticket_response_columns()


def _client_rows() -> list[tuple]:
    return [
        (
            "cli_vivo",
            "Vivo",
            "Telecom",
            "Gestão geográfica de infraestrutura de rede, cobertura, torres, fibra, antenas, expansão 5G e apoio a equipes de planejamento e campo.",
            "Crítica",
            2,
            "ArcGIS Enterprise, ArcGIS Dashboards, ArcGIS Field Maps",
            "São Paulo",
            "SP",
            -23.5505,
            -46.6333,
            96,
            "Baixo",
        ),
        (
            "cli_starbucks",
            "Starbucks",
            "Varejo",
            "Expansão global de lojas apoiada por análise de potencial de consumo, mobilidade urbana, demografia e clusters de varejo.",
            "Alta",
            4,
            "ArcGIS Dashboards, ArcGIS Online",
            "São Paulo",
            "SP",
            -23.5505,
            -46.6333,
            93,
            "Baixo",
        ),
        (
            "cli_bp",
            "BP",
            "Óleo e Gás / Operações de Campo",
            "Integração de dados operacionais e geográficos para otimizar logística de campo, reduzir custos e aumentar produtividade operacional.",
            "Alta",
            4,
            "ArcGIS Field Maps, ArcGIS Dashboards, ArcGIS Survey123",
            "Rio de Janeiro",
            "RJ",
            -22.9068,
            -43.1729,
            78,
            "Médio",
        ),
        (
            "cli_chesf",
            "Eletrobras Chesf",
            "Energia",
            "Gestão de ativos do setor elétrico integrando informações geográficas e operacionais para operação e manutenção da infraestrutura energética.",
            "Crítica",
            1,
            "ArcGIS Enterprise, ArcGIS Dashboards",
            "Recife",
            "PE",
            -8.0476,
            -34.8770,
            71,
            "Médio",
        ),
        (
            "cli_recife",
            "Prefeitura do Recife",
            "Prefeituras / Setor Público",
            "Centro de Operações da Cidade com dados em tempo real para monitorar ocorrências e apoiar decisões rápidas em eventos críticos.",
            "Crítica",
            1,
            "ArcGIS Dashboards, ArcGIS Enterprise",
            "Recife",
            "PE",
            -8.0476,
            -34.8770,
            64,
            "Alto",
        ),
        (
            "cli_natura",
            "Natura",
            "Sustentabilidade / Cadeia Produtiva",
            "Integração de dados geográficos e corporativos para apoiar cadeia produtiva, logística, sustentabilidade e rastreabilidade.",
            "Alta",
            6,
            "ArcGIS Dashboards, ArcGIS Online",
            "Cajamar",
            "SP",
            -23.3556,
            -46.8769,
            88,
            "Baixo",
        ),
    ]


def seed_clients_if_empty() -> None:
    count = int(fetch_scalar("SELECT COUNT(*) FROM clients", default=0))
    if count == 0:
        for row in _client_rows():
            execute("INSERT INTO clients VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", list(row))
        return

    # Mantém dados de referência atualizados mesmo em bancos já populados.
    for row in _client_rows():
        execute(
            """
            UPDATE clients
            SET sector = ?, business_context = ?, criticality = ?, default_sla_hours = ?,
                main_products = ?, city = ?, state = ?, latitude = ?, longitude = ?,
                health_score = ?, churn_risk = ?
            WHERE client_id = ?
            """,
            [row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[0]],
        )


def seed_users_if_empty() -> None:
    count = int(fetch_scalar("SELECT COUNT(*) FROM users", default=0))
    if count > 0:
        return

    users = [
        ("usr_admin", "Juan Vitor", "admin@geocs.com", "admin123", "admin", None, True),
        ("usr_vivo", "Portal Vivo", "vivo@cliente.com", "vivo123", "client", "cli_vivo", True),
        ("usr_starbucks", "Portal Starbucks", "starbucks@cliente.com", "starbucks123", "client", "cli_starbucks", True),
        ("usr_recife", "Portal Recife", "recife@cliente.com", "recife123", "client", "cli_recife", True),
        ("usr_viewer", "Viewer Executivo", "viewer@geocs.com", "viewer123", "viewer", None, True),
    ]

    for user in users:
        execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)", list(user))


def authenticate_user(email: str, password: str) -> Optional[Dict]:
    # DEMO ONLY: em produção use hash de senha com bcrypt/passlib.
    df = query_df(
        """
        SELECT *
        FROM users
        WHERE lower(email) = lower(?)
          AND password = ?
          AND is_active = TRUE
        """,
        [email, password],
    )
    return None if df.empty else df.iloc[0].to_dict()


def is_admin(user: Dict) -> bool:
    return user.get("role") == "admin"


def is_client(user: Dict) -> bool:
    return user.get("role") == "client"


def is_viewer(user: Dict) -> bool:
    return user.get("role") == "viewer"


def get_clients() -> pd.DataFrame:
    return query_df("SELECT * FROM clients ORDER BY client_name")


def get_client_by_name(client_name: str) -> Dict:
    df = query_df("SELECT * FROM clients WHERE client_name = ?", [client_name])
    if df.empty:
        raise ValueError(f"Cliente não encontrado: {client_name}")
    return df.iloc[0].to_dict()


def get_client_by_id(client_id: str) -> Dict:
    df = query_df("SELECT * FROM clients WHERE client_id = ?", [client_id])
    if df.empty:
        raise ValueError(f"Cliente não encontrado: {client_id}")
    return df.iloc[0].to_dict()


def insert_ticket(client: Dict, requester: str, message: str, classification: Dict) -> str:
    ticket_id = str(uuid.uuid4())[:8].upper()
    _insert_ticket_with_id(ticket_id, datetime.now(), client, requester, message, classification, "Aberto")
    return ticket_id


def _insert_ticket_with_id(
    ticket_id: str,
    created_at: datetime,
    client: Dict,
    requester: str,
    message: str,
    classification: Dict,
    status: str,
    admin_response: Optional[str] = None,
    responded_by: Optional[str] = None,
    responded_at: Optional[datetime] = None,
) -> None:
    ensure_ticket_response_columns()

    try:
        execute(
            """
            INSERT INTO tickets (
                ticket_id, created_at, client_id, client_name, requester, original_message,
                product, category, priority, sentiment, business_impact, sla_hours,
                responsible_team, summary, next_action, suggested_response,
                region_detected, business_objective, status,
                admin_response, responded_by, responded_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ticket_id,
                created_at,
                client["client_id"],
                client["client_name"],
                requester,
                message,
                classification["product"],
                classification["category"],
                classification["priority"],
                classification["sentiment"],
                classification["business_impact"],
                classification["sla_hours"],
                classification["responsible_team"],
                classification["summary"],
                classification["next_action"],
                classification["suggested_response"],
                classification["region_detected"],
                classification["business_objective"],
                status,
                admin_response,
                responded_by,
                responded_at,
            ],
        )
    except Exception as exc:
        # Demo safety: if a fixed seed ticket already exists, do not crash the app.
        # User-created tickets use random IDs and should not hit this path.
        msg = str(exc).lower()
        if "constraint" in msg or "duplicate" in msg or "primary key" in msg or "unique" in msg:
            return
        raise


def get_tickets() -> pd.DataFrame:
    ensure_ticket_response_columns()
    return query_df("SELECT * FROM tickets ORDER BY created_at DESC")


def get_tickets_for_user(user: Dict) -> pd.DataFrame:
    ensure_ticket_response_columns()
    if user.get("role") in ("admin", "viewer"):
        return get_tickets()

    if user.get("role") == "client":
        return query_df(
            """
            SELECT *
            FROM tickets
            WHERE client_id = ?
            ORDER BY created_at DESC
            """,
            [user["client_id"]],
        )

    return pd.DataFrame()


def update_ticket_status(ticket_id: str, status: str) -> None:
    execute("UPDATE tickets SET status = ? WHERE ticket_id = ?", [status, ticket_id])


def save_ticket_response(ticket_id: str, response: str, responder_name: str, new_status: str) -> None:
    ensure_ticket_response_columns()
    execute(
        """
        UPDATE tickets
        SET admin_response = ?,
            responded_by = ?,
            responded_at = ?,
            status = ?
        WHERE ticket_id = ?
        """,
        [response, responder_name, datetime.now(), new_status, ticket_id],
    )


def _seed_ticket_exists(ticket_id: str) -> bool:
    return int(fetch_scalar("SELECT COUNT(*) FROM tickets WHERE ticket_id = ?", [ticket_id], default=0)) > 0


def _seed_one(ticket_id: str, client_name: str, requester: str, message: str, days_ago: int, status: str) -> None:
    if _seed_ticket_exists(ticket_id):
        return

    try:
        from classifier import classify_ticket
    except Exception:
        from src.classifier import classify_ticket

    client = get_client_by_name(client_name)
    classification = classify_ticket(message, client)
    created_at = datetime.now() - timedelta(days=days_ago, hours=days_ago % 7, minutes=(days_ago * 13) % 60)

    admin_response = None
    responded_by = None
    responded_at = None
    if status in ("Resolvido", "Aguardando cliente"):
        admin_response = (
            "Olá! Recebemos sua solicitação, analisamos o cenário e direcionamos o caso para a equipe responsável. "
            "Seguiremos acompanhando o atendimento para garantir evolução dentro do SLA."
        )
        responded_by = "Juan Vitor"
        responded_at = created_at + timedelta(hours=max(int(classification["sla_hours"]), 1))

    _insert_ticket_with_id(ticket_id, created_at, client, requester, message, classification, status, admin_response, responded_by, responded_at)


def seed_demo_tickets() -> None:
    """Cria massa demonstrativa apenas quando a tabela estiver vazia.

    Importante para demo/Streamlit Cloud:
    se já existe qualquer ticket no banco, pulamos o seed para evitar colisão
    de IDs fixos em reinicializações ou deploys.
    """
    ensure_ticket_response_columns()

    existing_tickets = int(fetch_scalar("SELECT COUNT(*) FROM tickets", default=0) or 0)
    if existing_tickets > 0:
        return

    demo_tickets = [
        # Vivo — 8 tickets
        ("FCT-VIVO-001", "Vivo", "Ana Planejamento", "Após a atualização do portal, o mapa de cobertura da região de Campinas deixou de exibir torres LTE e 5G. A equipe de planejamento não consegue validar a expansão prevista para esta semana.", 1, "Aberto"),
        ("FCT-VIVO-002", "Vivo", "Carlos Operações", "As camadas de fibra metropolitana não carregam no ArcGIS Enterprise e o NOC não consegue cruzar incidentes com áreas de cobertura.", 3, "Em análise"),
        ("FCT-VIVO-003", "Vivo", "Marina Campo", "Equipe de campo reportou falha de sincronização no Field Maps ao atualizar pontos de manutenção de antenas.", 5, "Aguardando cliente"),
        ("FCT-VIVO-004", "Vivo", "Rafael Rede", "Precisamos revisar permissões de grupos no portal para separar equipes de planejamento, campo e operação.", 8, "Resolvido"),
        ("FCT-VIVO-005", "Vivo", "Juliana BI", "Dashboard de indicadores de expansão 5G está com refresh atrasado desde ontem e impacta reunião de planejamento.", 11, "Em análise"),
        ("FCT-VIVO-006", "Vivo", "Pedro Engenharia", "Camadas de torres e antenas aparecem com simbologia incorreta em algumas regiões do Sudeste.", 16, "Resolvido"),
        ("FCT-VIVO-007", "Vivo", "Luiza Telecom", "Solicito orientação sobre publicação de novo Web Map para análise de cobertura indoor.", 23, "Resolvido"),
        ("FCT-VIVO-008", "Vivo", "Bruno NOC", "Mapa operacional de incidentes de rede móvel parou de atualizar em tempo real durante janela crítica.", 27, "Escalado"),

        # Prefeitura do Recife — 7 tickets
        ("FCT-REC-001", "Prefeitura do Recife", "Operador COP", "O mapa de monitoramento das ocorrências do Centro de Operações deixou de atualizar em tempo real e está impactando a resposta operacional da prefeitura.", 0, "Aberto"),
        ("FCT-REC-002", "Prefeitura do Recife", "João Segurança", "Dashboard de ocorrências por bairro não carrega os dados da madrugada e a equipe precisa acompanhar eventos críticos.", 2, "Em análise"),
        ("FCT-REC-003", "Prefeitura do Recife", "Mariana COP", "Usuários do turno noturno não conseguem acessar o portal para registrar camadas de eventos urbanos.", 4, "Aguardando cliente"),
        ("FCT-REC-004", "Prefeitura do Recife", "Paulo Operações", "Precisamos de treinamento rápido para operadores do COP criarem filtros de ocorrências por tipo de evento.", 6, "Resolvido"),
        ("FCT-REC-005", "Prefeitura do Recife", "Lívia Defesa Civil", "Camada de áreas de risco deixou de exibir polígonos durante acompanhamento de chuva forte.", 9, "Escalado"),
        ("FCT-REC-006", "Prefeitura do Recife", "Rogério Dados", "Gostaria de confirmar como alterar legenda do mapa de efetivo policial por bairro.", 18, "Resolvido"),
        ("FCT-REC-007", "Prefeitura do Recife", "Fernanda Gestão", "Indicadores de tempo de resposta no dashboard estão divergentes do relatório consolidado.", 24, "Em análise"),

        # Eletrobras Chesf — 6 tickets
        ("FCT-CHESF-001", "Eletrobras Chesf", "Analista de Ativos", "Nossa equipe de operação não consegue visualizar ativos da rede elétrica no ArcGIS Enterprise após a atualização do portal.", 1, "Aberto"),
        ("FCT-CHESF-002", "Eletrobras Chesf", "Carlos Manutenção", "Camadas de linhas de transmissão não carregam em alguns mapas usados para planejamento de manutenção.", 7, "Em análise"),
        ("FCT-CHESF-003", "Eletrobras Chesf", "Patrícia Energia", "Dashboard de ativos críticos está desatualizado e impacta reunião operacional com a equipe de manutenção.", 12, "Aguardando cliente"),
        ("FCT-CHESF-004", "Eletrobras Chesf", "Roberto GIS", "Solicito apoio para organizar permissões de acesso por equipes regionais no portal.", 15, "Resolvido"),
        ("FCT-CHESF-005", "Eletrobras Chesf", "Daniel Operação", "Serviço de mapa usado para inspeção de subestações está indisponível.", 21, "Escalado"),
        ("FCT-CHESF-006", "Eletrobras Chesf", "Renata Planejamento", "Preciso de orientação para alterar simbologia de ativos no Web Map sem afetar dashboards publicados.", 29, "Resolvido"),

        # BP — 6 tickets
        ("FCT-BP-001", "BP", "Coordenador Campo", "As equipes de campo não conseguem sincronizar os pontos coletados no Field Maps desde ontem. Isso está atrasando a logística de campo e gerando retrabalho.", 2, "Aberto"),
        ("FCT-BP-002", "BP", "Marcos Operações", "Formulário do Survey123 para vistoria de campo não está salvando todas as respostas.", 5, "Em análise"),
        ("FCT-BP-003", "BP", "Luciana Logística", "Dashboard de rotas e consumo de combustível não atualiza desde ontem e prejudica análise operacional.", 10, "Aguardando cliente"),
        ("FCT-BP-004", "BP", "Eduardo Campo", "Alguns pontos coletados offline aparecem duplicados após sincronização.", 14, "Resolvido"),
        ("FCT-BP-005", "BP", "Camila Dados", "Gostaria de agendar treinamento sobre coleta offline no Field Maps para novas equipes.", 20, "Resolvido"),
        ("FCT-BP-006", "BP", "Fábio Operações", "Mapa de áreas operacionais está lento para carregar em tablets usados em campo.", 28, "Em análise"),

        # Starbucks — 5 tickets
        ("FCT-STAR-001", "Starbucks", "Gerente Expansão", "Estamos avaliando novos pontos de loja no Sudeste, mas o dashboard com dados de mobilidade urbana e potencial de consumo não atualiza desde ontem. A análise de expansão está parada.", 3, "Aberto"),
        ("FCT-STAR-002", "Starbucks", "Ana Estratégia", "Precisamos de uma demonstração sobre como criar filtros no dashboard de expansão e compartilhar a visualização com outras áreas.", 8, "Resolvido"),
        ("FCT-STAR-003", "Starbucks", "Bruno Analytics", "Web Map de clusters de varejo não exibe algumas camadas de demografia.", 13, "Em análise"),
        ("FCT-STAR-004", "Starbucks", "Carla Expansão", "Gostaria de saber onde encontro a documentação para alterar a cor da legenda em um Web Map.", 22, "Resolvido"),
        ("FCT-STAR-005", "Starbucks", "Diretoria", "Estamos insatisfeitos com o suporte e queremos avaliar o cancelamento do contrato se não houver plano de ação.", 30, "Escalado"),

        # Natura — 4 tickets
        ("FCT-NAT-001", "Natura", "Analista Sustentabilidade", "O dashboard de rastreabilidade da cadeia sustentável não atualizou os dados desta semana e precisamos validar indicadores para uma reunião executiva.", 4, "Aberto"),
        ("FCT-NAT-002", "Natura", "Bianca Cadeia", "Gostaríamos de agendar uma reunião para revisar o dashboard de rastreabilidade e melhorar filtros e indicadores.", 11, "Resolvido"),
        ("FCT-NAT-003", "Natura", "Felipe Logística", "Camada hospedada com origem dos insumos não está refletindo atualizações do último ETL.", 17, "Em análise"),
        ("FCT-NAT-004", "Natura", "Juliana ESG", "Preciso confirmar se é possível alterar o nome de uma camada hospedada sem impactar o dashboard publicado.", 26, "Resolvido"),
    ]

    for args in demo_tickets:
        try:
            _seed_one(*args)
        except Exception:
            # Seed demo must never block the live app.
            # If one demo row fails, the user must still be able to open tickets.
            continue
