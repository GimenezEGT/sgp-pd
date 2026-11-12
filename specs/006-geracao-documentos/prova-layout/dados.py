"""Dados fictícios da prova de layout (nada vem dos arquivos de docs/modelos)."""

TITULO = "Entrada de Projeto"
PRODUTO = "Produto de Teste Alfa"
VERSAO = "01"
FORM_VERSAO = "05"
REFERENCIA = "PSG 20 - Pesquisa e Desenvolvimento de Produtos"

# Rótulos dos tópicos do modelo de formulário da Entrada (estrutura do seed da feature 004).
TOPICOS = [
    "Amostras",
    "Funcionalidade",
    "Apresentações",
    "Armazenamento",
    "Automação",
    "Classificação de uso",
    "Tipo de usuário",
    "Filtros primário e secundário (se aplicável)",
    "Classificação de Uso",
    "Requisitos de desempenho",
    "Requisitos regulatórios",
    "Gerenciamento de risco",
    "Outros dados pertinentes",
]

COLUNAS = ["Nº", "Item de teste", "Condição", "Valor (mg/L)", "Observação"]


def linhas(n=120):
    out = []
    for i in range(1, n + 1):
        valor = f"{i * 1.25:.2f}".replace(".", ",")
        out.append([f"{i:03d}", f"Item fictício {i:03d}", "2 a 8 °C" if i % 2 else "15 a 25 °C", valor, "—"])
    return out


def colunas_capa():
    numerados = [(i + 1, t) for i, t in enumerate(TOPICOS)]
    return numerados[:6], numerados[6:]
