"""
GeoCS 360 — Módulo de classificação por regras de negócio.
# [FUTURE-AI] Este módulo pode ser substituído ou complementado por um LLM
# sem alterar a interface ou a estrutura do sistema. A função classify_ticket()
# mantém o mesmo contrato de entrada/saída independente da implementação interna.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class ClientProfile:
    client_name: str
    sector: str
    business_context: str
    criticality: str
    default_sla_hours: int
    main_products: str


# ─────────────────────────────────────────────────────────────
# KEYWORD MAPS
# ─────────────────────────────────────────────────────────────
PRODUCT_KEYWORDS: Dict[str, List[str]] = {
    "ArcGIS Dashboards": [
        "dashboard", "painel", "indicador", "tempo real",
        "monitoramento", "cop", "centro de operações", "noc",
        "mapa de cobertura", "visualização",
    ],
    "ArcGIS Field Maps": [
        "field maps", "campo", "coleta", "sincron", "offline",
        "equipe de campo", "pontos",
    ],
    "ArcGIS Enterprise": [
        "enterprise", "portal", "servidor", "publicar",
        "camadas", "camada", "serviço", "login", "acesso",
        "usuários", "torres", "antenas", "fibra", "lte", "5g",
        "cobertura", "rede",
    ],
    "ArcGIS Online": [
        "online", "web map", "mapa web", "compartilhar",
        "grupo", "camada hospedada",
    ],
    "ArcGIS Survey123": [
        "survey", "formulário", "pesquisa", "vistoria",
        "coleta de formulário",
    ],
    "ArcGIS Experience Builder": [
        "experience", "aplicativo", "app", "experiência", "interface",
    ],
}

CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "Falha técnica": [
        "erro", "falha", "não abre", "não carrega", "não funciona",
        "fora do ar", "travando", "indisponível", "bug",
    ],
    "Atualização de dados": [
        "não atualiza", "desatualizado", "dados antigos",
        "atualização", "carga", "refresh", "etl",
    ],
    "Acesso e permissões": [
        "login", "senha", "acesso", "permissão", "usuário",
        "perfil", "autenticação",
    ],
    "Sincronização de campo": [
        "sincron", "offline", "campo", "coleta", "upload", "download",
    ],
    "Agendamento / Treinamento": [
        "reunião", "treinamento", "demonstração",
        "capacitação", "agenda", "apresentação",
    ],
    "Insatisfação / Retenção": [
        "cancelar", "insatisfeito", "contrato", "não atende",
        "reclamação", "churn", "renovação",
    ],
    "Visualização de camadas": [
        "camada", "mapa", "web map", "não carrega", "não exibe",
        "renderizar", "deixou de exibir",
    ],
    "Operação crítica": [
        "ocorrência", "emergência", "operação", "manutenção",
        "rede elétrica", "segurança", "cop", "5g", "lte",
        "cobertura", "rede móvel",
    ],
}

NEGATIVE_WORDS = [
    "urgente", "parado", "atrasando", "crítico", "insatisfeito",
    "cancelar", "fora do ar", "não funciona", "falha", "erro",
    "impactando", "prejuízo", "não consegue", "deixou de",
    "não exibe", "não visualiza", "parada", "interrompido",
    "bloqueado", "retrabalho",
]
POSITIVE_WORDS = [
    "obrigado", "ótimo", "excelente", "gostaria", "interesse", "melhorar",
]

# Termos que disparam prioridade Crítica
CRITICAL_TERMS = [
    "segurança pública", "energia", "rede elétrica",
    "centro de operações", "ocorrências", "tempo real",
    "infraestrutura", "operação crítica", "ambulância",
    "defesa civil", "telecom", "rede móvel", "fibra",
    "antenas", "torres", "5g", "cobertura", "noc",
    "emergência", "incidente crítico",
]

# Termos que disparam prioridade Alta
HIGH_TERMS = [
    "campo", "produção", "logística", "expansão", "lojas",
    "sustentabilidade", "rastreabilidade", "tomada de decisão",
    "operação", "dados parados", "planejamento de rede",
    "manutenção", "outage", "indisponibilidade",
    "clientes impactados", "não atualiza", "análise parada",
    "reunião executiva", "desde ontem", "equipe bloqueada",
]

# Termos que indicam baixa complexidade/baixa urgência
LOW_TERMS = [
    "documentação", "onde encontro", "como faço", "confirmar se é possível",
    "alterar cor", "legenda", "simbologia", "nome de uma camada",
    "orientação", "dúvida", "consulta", "sem urgência", "quando possível",
]

# ─────────────────────────────────────────────────────────────
# EQUIPES RESPONSÁVEIS
# ─────────────────────────────────────────────────────────────
TEAM_BY_PRODUCT: Dict[str, str] = {
    "ArcGIS Dashboards":         "BI/GIS Dashboards Team",
    "ArcGIS Field Maps":         "Field Operations Support",
    "ArcGIS Enterprise":         "GIS Enterprise Support",
    "ArcGIS Online":             "Customer Success Support",
    "ArcGIS Survey123":          "Forms & Field Data Team",
    "ArcGIS Experience Builder": "Customer Success Support",
    "Plataforma ArcGIS":         "Customer Success Support",
}

TEAM_BY_CATEGORY: Dict[str, str] = {
    "Acesso e permissões":    "Access Management",
    "Insatisfação / Retenção": "Customer Success Manager",
}

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def normalize(text: str) -> str:
    return text.lower().strip()


def score_keywords(text: str, keywords: List[str]) -> int:
    t = normalize(text)
    return sum(1 for kw in keywords if kw in t)


def choose_by_keywords(
    text: str,
    mapping: Dict[str, List[str]],
    default: str,
) -> Tuple[str, int]:
    scores = [(label, score_keywords(text, kws)) for label, kws in mapping.items()]
    scores.sort(key=lambda x: x[1], reverse=True)
    if scores and scores[0][1] > 0:
        return scores[0]
    return default, 0


def classify_sentiment(text: str) -> str:
    neg = score_keywords(text, NEGATIVE_WORDS)
    pos = score_keywords(text, POSITIVE_WORDS)
    if neg >= 2:
        return "Negativo"
    if neg == 1 and pos == 0:
        return "Levemente negativo"
    if pos > neg:
        return "Positivo"
    return "Neutro"


def estimate_priority(
    text: str,
    client: ClientProfile,
    category: str,
) -> Tuple[str, str, int]:
    """
    Retorna (prioridade, razão, sla_horas).
    [FUTURE-AI] Esta função pode ser aumentada com scoring semântico via LLM.
    """
    t = normalize(text)
    critical_hits = score_keywords(t, CRITICAL_TERMS)
    high_hits     = score_keywords(t, HIGH_TERMS)
    negative_hits = score_keywords(t, NEGATIVE_WORDS)

    # Crítica — cliente crítico com impacto operacional
    if client.criticality == "Crítica" and (
        critical_hits > 0
        or category in ["Falha técnica", "Atualização de dados", "Sincronização de campo", "Operação crítica", "Visualização de camadas"]
    ):
        return "Crítica", "Cliente de operação crítica com impacto direto em serviço essencial ou infraestrutura.", 1

    # Crítica — risco de retenção
    if "cancelar" in t and ("insatisfeito" in t or "contrato" in t):
        return "Crítica", "Sinal de risco de retenção — possível churn detectado.", 1

    # Crítica — termos de infraestrutura crítica
    if critical_hits > 0:
        return "Crítica", "Mensagem contém termos associados a operação crítica ou infraestrutura essencial.", 1

    # Alta — impacto operacional
    if high_hits > 0 or negative_hits >= 2:
        return "Alta", "Chamado pode impactar operação, campo, decisão estratégica ou produtividade.", 2

    # Média — agendamento ou treinamento
    if category == "Agendamento / Treinamento":
        return "Média", "Solicitação importante, sem sinal de incidente operacional imediato.", 6

    # Baixa — dúvida simples / orientação / documentação, sem sinais de urgência
    low_hits = score_keywords(t, LOW_TERMS)
    if low_hits > 0 and critical_hits == 0 and high_hits == 0 and negative_hits == 0:
        return "Baixa", "Solicitação simples de orientação, documentação ou ajuste visual, sem impacto operacional imediato.", 24

    if category == "Suporte Geral" and critical_hits == 0 and high_hits == 0 and negative_hits == 0:
        return "Baixa", "Solicitação geral sem indícios de criticidade, urgência ou impacto operacional.", 24

    # Média — padrão
    sla = min(client.default_sla_hours, 6) if client.default_sla_hours <= 6 else 6
    return "Média", "Solicitação sem indícios de criticidade elevada.", sla


def extract_entities(text: str) -> Dict[str, str]:
    region_match = re.search(
        r"\b(sudeste|nordeste|norte|sul|centro-oeste|recife|campinas|brasília|"
        r"belo horizonte|porto alegre|fortaleza|são paulo|rio de janeiro|"
        r"curitiba|salvador|manaus|campo)\b",
        text.lower(),
    )
    objective = "Não identificado"
    t = text.lower()
    if any(w in t for w in ["expansão", "loja", "mercado", "pontos de loja"]):
        objective = "Expansão e localização de unidades"
    elif any(w in t for w in ["campo", "logística", "combustível", "produção"]):
        objective = "Eficiência operacional no campo"
    elif any(w in t for w in ["segurança", "ocorrência", "cop", "cidade"]):
        objective = "Gestão urbana e resposta a eventos críticos"
    elif any(w in t for w in ["sustentabilidade", "origem", "cadeia", "rastreabilidade"]):
        objective = "Sustentabilidade e rastreabilidade"
    elif any(w in t for w in ["telecom", "5g", "lte", "fibra", "antenas", "torres", "cobertura", "rede móvel"]):
        objective = "Planejamento, cobertura e operação de rede telecom"
    elif any(w in t for w in ["energia", "ativos", "rede elétrica", "manutenção"]):
        objective = "Gestão de ativos e manutenção"

    return {
        "regiao_mencionada": region_match.group(0).title() if region_match else "Não identificada",
        "objetivo_negocio": objective,
    }


def build_summary(client: ClientProfile, product: str, category: str, text: str) -> str:
    clean = " ".join(text.split())
    if len(clean) > 180:
        clean = clean[:177] + "..."
    return (
        f"{client.client_name} relata {category.lower()} relacionado a {product}. "
        f"Contexto: {client.business_context}. Mensagem: {clean}"
    )


def suggested_next_action(priority: str, category: str, product: str) -> str:
    team = TEAM_BY_PRODUCT.get(product, "Customer Success Support")
    if priority == "Crítica":
        return f"Escalar imediatamente para {team} e acionar o CSM responsável pela conta."
    if category == "Agendamento / Treinamento":
        return "Encaminhar ao CSM para agendamento de reunião de capacitação ou demonstração."
    if category == "Insatisfação / Retenção":
        return "Acionar CSM e liderança para plano de retenção e alinhamento de expectativas."
    return f"Criar ticket e direcionar para {team} conforme SLA sugerido."


def build_suggested_response(
    client: ClientProfile,
    product: str,
    category: str,
    priority: str,
    sla_hours: int,
) -> str:
    """
    Gera resposta empática e profissional para envio ao cliente.
    [FUTURE-AI] Este bloco pode ser gerado por LLM com base no contexto completo.
    """
    sla_text = "em até 1 hora" if sla_hours <= 1 else f"em até {sla_hours} horas"
    team = TEAM_BY_PRODUCT.get(product, "Customer Success Support")
    return (
        f"Olá, time {client.client_name}.\n\n"
        f"Recebemos sua solicitação relacionada a {product} e classificamos o caso como prioridade {priority}. "
        f"Entendemos o impacto que isso pode gerar na sua operação e queremos garantir uma resolução ágil.\n\n"
        f"O chamado foi direcionado ao {team} com previsão de primeiro retorno {sla_text}. "
        f"Nosso time de Customer Success acompanhará o andamento para garantir visibilidade e evolução do atendimento.\n\n"
        f"Qualquer atualização, entraremos em contato imediatamente. Obrigado pela confiança."
    )


# ─────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────
def classify_ticket(text: str, client_row: dict) -> Dict[str, str | int]:
    """
    Recebe a mensagem e o perfil do cliente, retorna dict de classificação.
    Contrato de saída estável — compatível com substituição por LLM no futuro.
    """
    client = ClientProfile(
        client_name=client_row["client_name"],
        sector=client_row["sector"],
        business_context=client_row["business_context"],
        criticality=client_row["criticality"],
        default_sla_hours=int(client_row["default_sla_hours"]),
        main_products=client_row["main_products"],
    )

    product, product_score = choose_by_keywords(text, PRODUCT_KEYWORDS, "Plataforma ArcGIS")
    if product_score == 0 and client.main_products:
        product = client.main_products.split(",")[0].strip()

    category, _ = choose_by_keywords(text, CATEGORY_KEYWORDS, "Suporte Geral")
    sentiment    = classify_sentiment(text)
    priority, priority_reason, sla_hours = estimate_priority(text, client, category)
    entities     = extract_entities(text)

    # Equipe por categoria sobrescreve equipe por produto em casos específicos
    responsible_team = TEAM_BY_CATEGORY.get(
        category,
        TEAM_BY_PRODUCT.get(product, "Customer Success Support"),
    )

    business_impact = priority_reason
    if client.sector in ["Setor público", "Energia", "Telecom"]:
        business_impact += (
            " O segmento do cliente exige resposta rápida por envolver "
            "serviço público, infraestrutura ou operação essencial."
        )

    return {
        "product":            product,
        "category":           category,
        "priority":           priority,
        "sentiment":          sentiment,
        "business_impact":    business_impact,
        "sla_hours":          sla_hours,
        "responsible_team":   responsible_team,
        "summary":            build_summary(client, product, category, text),
        "next_action":        suggested_next_action(priority, category, product),
        "suggested_response": build_suggested_response(client, product, category, priority, sla_hours),
        "region_detected":    entities["regiao_mencionada"],
        "business_objective": entities["objetivo_negocio"],
    }
