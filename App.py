"""
Dashboard Financeiro Pessoal — Minimalista (com LocalStorage por dispositivo)
Streamlit + Plotly + Pandas + LocalStorage

Como rodar:
    pip install streamlit plotly pandas streamlit-local-storage
    streamlit run app.py
"""

from datetime import date
import json
import os
import time

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_local_storage import LocalStorage

# ----------------------------------------------------------------------------
# CONFIGURAÇÃO GERAL E ARMAZENAMENTO LOCAL
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Financeiro",
    layout="wide",
    initial_sidebar_state="expanded",
)

local_store = LocalStorage()

COR_RECEITA = "#2E7D32"
COR_DESPESA = "#B71C1C"
COR_SALDO = "#1A1A2E"
COR_LINHA = "#37474F"
COR_FUNDO_GRID = "#E0E0E0"

CSS = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    button[data-testid="stSidebarNavSeparator"] { display: none; }
    [data-testid="stHeader"] { background-color: transparent !important; }
    [data-testid="stSidebarCollapseButton"] { color: #1A1A2E !important; }
    html, body, [class*="css"] { color: #1A1A2E; }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* Cards de KPI */
    div[data-testid="stMetric"] {
        background-color: #F5F5F7;
        border: 1px solid #E0E0E0;
        border-radius: 10px;
        padding: 18px 20px;
    }
    div[data-testid="stMetricLabel"] { font-size: 0.85rem; color: #6B6B76; }
    div[data-testid="stMetricValue"] { font-size: 1.5rem; font-weight: 600; color: #1A1A2E; word-break: break-word; }

    h1, h2, h3 { font-weight: 600; color: #1A1A2E; }
    p, span, label, .stCaption, [data-testid="stCaptionContainer"] { color: #444444; }

    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: #FAFAFA; border-right: 1px solid #EAEAEA; }
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p { color: #1A1A2E !important; }

    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] textarea {
        background-color: #FFFFFF !important;
        color: #1A1A2E !important;
        border: 1px solid #D0D0D0 !important;
        border-radius: 6px !important;
    }
    section[data-testid="stSidebar"] input:focus,
    section[data-testid="stSidebar"] textarea:focus {
        border: 1px solid #37474F !important;
        box-shadow: 0 0 0 1px #37474F !important;
        color: #1A1A2E !important;
        background-color: #FFFFFF !important;
    }

    /* Campo de Valor (R$) maior e mais legivel, para nao ser atrapalhado
       pelo texto pequeno "Press Enter to submit form" do Streamlit */
    section[data-testid="stSidebar"] div[data-testid="stNumberInput"] input {
        font-size: 1.35rem !important;
        font-weight: 600 !important;
        height: 3rem !important;
        padding: 0.4rem 0.75rem !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stNumberInput"] {
        margin-bottom: 0.35rem;
    }
    /* Dica "Press Enter to submit form" menor e discreta */
    div[data-testid="InputInstructions"] {
        font-size: 0.65rem !important;
        opacity: 0.55;
    }

    section[data-testid="stSidebar"] button[data-testid="stNumberInputStepUp"],
    section[data-testid="stSidebar"] button[data-testid="stNumberInputStepDown"] {
        background-color: #FFFFFF !important;
        border: 1px solid #D0D0D0 !important;
    }
    section[data-testid="stSidebar"] button[data-testid="stNumberInputStepUp"] svg,
    section[data-testid="stSidebar"] button[data-testid="stNumberInputStepDown"] svg { fill: #1A1A2E !important; }

    div[data-baseweb="select"] > div { background-color: #FFFFFF !important; color: #1A1A2E !important; border: 1px solid #D0D0D0 !important; }

    /* Botões */
    .stButton > button,
    .stFormSubmitButton > button,
    div[data-testid="stFormSubmitButton"] > button,
    section[data-testid="stSidebar"] .stButton > button,
    section[data-testid="stSidebar"] .stFormSubmitButton > button {
        background-color: #1A1A2E !important;
        color: #FFFFFF !important;
        border: 1px solid #1A1A2E !important;
        border-radius: 6px !important;
    }
    .stButton > button *,
    .stFormSubmitButton > button *,
    div[data-testid="stFormSubmitButton"] > button *,
    section[data-testid="stSidebar"] .stButton > button *,
    section[data-testid="stSidebar"] .stFormSubmitButton > button * { color: #FFFFFF !important; fill: #FFFFFF !important; }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover,
    div[data-testid="stFormSubmitButton"] > button:hover,
    section[data-testid="stSidebar"] .stButton > button:hover,
    section[data-testid="stSidebar"] .stFormSubmitButton > button:hover {
        background-color: #37474F !important;
        border: 1px solid #37474F !important;
        color: #FFFFFF !important;
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] label { color: #1A1A2E !important; }
    div[data-testid="stDataFrame"] { border: 1px solid #E0E0E0; border-radius: 8px; }
    hr { border-color: #EAEAEA; }

    .rodape-app {
        text-align: center;
        color: #9E9E9E;
        font-size: 0.8rem;
        padding-top: 1.5rem;
        padding-bottom: 0.5rem;
    }

    @media (max-width: 768px) {
        .block-container { padding-left: 1rem; padding-right: 1rem; padding-top: 1.2rem; }
        div[data-testid="stMetric"] { padding: 14px 16px; }
        div[data-testid="stMetricValue"] { font-size: 1.2rem; }
        div[data-testid="stMetricLabel"] { font-size: 0.78rem; }
        h1 { font-size: 1.5rem !important; }
        h3 { font-size: 1.1rem !important; }
        div[data-testid="column"] { min-width: 100% !important; flex: 1 1 100% !important; }
        div[data-testid="stDataFrame"] { font-size: 0.85rem; }
    }

    @media (max-width: 480px) {
        .block-container { padding-left: 0.6rem; padding-right: 0.6rem; }
        h1 { font-size: 1.25rem !important; }
        div[data-testid="stMetricValue"] { font-size: 1.05rem; }
        .stButton > button, .stFormSubmitButton > button { font-size: 0.9rem; padding: 0.5rem 0.75rem; }
    }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# PERSISTÊNCIA DE DADOS (LOCALSTORAGE / NAVEGADOR)
# ----------------------------------------------------------------------------
colunas = ["Data", "Tipo", "Descrição", "Valor"]

def carregar_dados() -> pd.DataFrame:
    raw_data = local_store.getItem("transacoes_locais")

    if raw_data:
        try:
            dados = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
            df = pd.DataFrame(dados)
            if not df.empty:
                df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
                df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce")
                for c in colunas:
                    if c not in df.columns:
                        df[c] = None
                return df[colunas]
        except Exception:
            pass

    df = pd.DataFrame(columns=colunas)
    df["Data"] = pd.to_datetime(df["Data"])
    df["Valor"] = pd.to_numeric(df["Valor"])
    return df


def salvar_dados(df: pd.DataFrame) -> None:
    df_salvar = df.copy()
    if not df_salvar.empty:
        df_salvar["Data"] = pd.to_datetime(df_salvar["Data"]).dt.strftime("%Y-%m-%d")
        local_store.setItem("transacoes_locais", json.dumps(df_salvar.to_dict(orient="records")))
    else:
        local_store.setItem("transacoes_locais", json.dumps([]))


# O componente do streamlit-local-storage busca os dados do navegador de forma
# assíncrona: na primeira execução do script (ex: logo após um F5), o valor
# retornado ainda pode ser o "default" vazio, porque o JS do navegador não
# teve tempo de responder. Se carregarmos a tabela nesse instante, ela vem
# vazia e o app "esquece" os lançamentos até que algo mais force uma releitura.
# Por isso, sincronizamos explicitamente uma vez por sessão, dando um pequeno
# tempo para o componente responder e então recarregando os dados.
if "ls_sincronizado" not in st.session_state:
    st.session_state.ls_sincronizado = False

if not st.session_state.ls_sincronizado:
    time.sleep(0.3)
    local_store.refreshItems()
    st.session_state.transacoes = carregar_dados()
    st.session_state.ls_sincronizado = True
    st.rerun()

if "transacoes" not in st.session_state:
    st.session_state.transacoes = carregar_dados()


# ----------------------------------------------------------------------------
# SIDEBAR — LANÇAMENTO RÁPIDO
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Novo Lançamento")

    with st.form("form_transacao", clear_on_submit=True):
        tipo = st.radio("Tipo", ["Receita", "Despesa"], horizontal=True)
        valor = st.number_input("Valor (R$)", min_value=0.0, step=10.0, format="%.2f")
        descricao = st.text_input("Descrição", placeholder="Ex: Salário, Aluguel...")
        data_transacao = st.date_input("Data", value=date.today())

        enviado = st.form_submit_button("Adicionar", use_container_width=True)

        if enviado:
            if valor <= 0:
                st.warning("Informe um valor maior que zero.")
            elif not descricao.strip():
                st.warning("Informe uma descrição.")
            else:
                nova = pd.DataFrame([{
                    "Data": pd.to_datetime(data_transacao),
                    "Tipo": tipo,
                    "Descrição": descricao.strip(),
                    "Valor": valor,
                }])
                st.session_state.transacoes = pd.concat([st.session_state.transacoes, nova], ignore_index=True)
                salvar_dados(st.session_state.transacoes)
                st.success("Lançamento adicionado!")
                st.rerun()

    st.divider()

    if not st.session_state.transacoes.empty:
        if st.button("Limpar todo o histórico", use_container_width=True):
            df_vazio = pd.DataFrame(columns=colunas)
            df_vazio["Data"] = pd.to_datetime(df_vazio["Data"])
            st.session_state.transacoes = df_vazio
            salvar_dados(df_vazio)
            st.rerun()


# ----------------------------------------------------------------------------
# CÁLCULOS E FILTROS PRINCIPAIS
# ----------------------------------------------------------------------------
df = st.session_state.transacoes.copy()

if not df.empty:
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

# ----------------------------------------------------------------------------
# CABEÇALHO + KPIs COM FILTRO DE PERÍODO
# ----------------------------------------------------------------------------
st.title("Dashboard Financeiro Pessoal")
st.caption("Visão geral simples e objetiva das suas finanças.")

periodo = st.radio(
    "Filtrar período:",
    ["Hoje", "Mês Atual", "Ano Atual", "Total"],
    index=3,
    horizontal=True
)

hoje = pd.Timestamp.now().normalize()

if not df.empty:
    if periodo == "Hoje":
        df_kpi = df[df["Data"].dt.date == hoje.date()]
    elif periodo == "Mês Atual":
        df_kpi = df[(df["Data"].dt.month == hoje.month) & (df["Data"].dt.year == hoje.year)]
    elif periodo == "Ano Atual":
        df_kpi = df[df["Data"].dt.year == hoje.year]
    else:
        df_kpi = df
else:
    df_kpi = df

total_receitas = df_kpi.loc[df_kpi["Tipo"] == "Receita", "Valor"].sum() if not df_kpi.empty else 0.0
total_despesas = df_kpi.loc[df_kpi["Tipo"] == "Despesa", "Valor"].sum() if not df_kpi.empty else 0.0
saldo_periodo = total_receitas - total_despesas

saldo_total_historico = (
    df.loc[df["Tipo"] == "Receita", "Valor"].sum() - df.loc[df["Tipo"] == "Despesa", "Valor"].sum()
    if not df.empty else 0.0
)

col1, col2, col3 = st.columns(3)
col1.metric("Total de Recebimentos", f"R$ {total_receitas:,.2f}")
col2.metric("Total de Gastos", f"R$ {total_despesas:,.2f}")
col3.metric(
    "Saldo no Período" if periodo != "Total" else "Saldo Atual Disponível",
    f"R$ {saldo_periodo:,.2f}",
    delta=None,
)

st.divider()


# ----------------------------------------------------------------------------
# HISTÓRICO DE TRANSAÇÕES (EDIÇÃO E EXCLUSÃO)
# ----------------------------------------------------------------------------
st.subheader("Histórico de Transações")

if df.empty:
    st.info("Nenhuma transação registrada ainda. Use o formulário na barra lateral.")
else:
    df_editor = df.sort_values("Data", ascending=False).copy()
    df_editor["Data"] = pd.to_datetime(df_editor["Data"], errors="coerce").dt.date
    df_editor["Excluir"] = False

    df_editor = df_editor[["Excluir", "Data", "Tipo", "Descrição", "Valor"]]

    st.caption("Altere os dados diretamente na tabela abaixo ou marque 'Excluir' nas linhas que deseja remover.")

    df_editado = st.data_editor(
        df_editor,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        column_config={
            "Excluir": st.column_config.CheckboxColumn("Excluir", default=False),
            "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY", required=True),
            "Tipo": st.column_config.SelectboxColumn("Tipo", options=["Receita", "Despesa"], required=True),
            "Descrição": st.column_config.TextColumn("Descrição", required=True),
            "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", min_value=0.01, required=True),
        },
        key="editor_transacoes",
    )

    if st.button("Salvar Alterações", use_container_width=True):
        df_salvar = df_editado[df_editado["Excluir"] == False].drop(columns=["Excluir"])
        df_salvar["Data"] = pd.to_datetime(df_salvar["Data"])

        st.session_state.transacoes = df_salvar
        salvar_dados(df_salvar)

        st.success("Alterações salvas com sucesso!")
        st.rerun()

st.divider()


# ----------------------------------------------------------------------------
# PROJEÇÃO FINANCEIRA
# ----------------------------------------------------------------------------
st.subheader("Projeção Financeira")

col_a, col_b = st.columns([1, 2])

with col_a:
    aporte_mensal = st.number_input(
        "Aporte mensal (R$)",
        min_value=0.0,
        value=500.0,
        step=50.0,
        format="%.2f",
    )
    anos_projecao = st.slider("Anos de projeção", min_value=1, max_value=30, value=30)
    taxa_mensal = 0.01

    st.caption(f"Taxa fixa: **1% ao mês** (juros compostos) · Aporte inicial: **R$ {saldo_total_historico:,.2f}**")

with col_b:
    meses_total = anos_projecao * 12
    patrimonio = saldo_total_historico
    valores_anuais = [patrimonio]

    for mes in range(1, meses_total + 1):
        patrimonio = patrimonio * (1 + taxa_mensal) + aporte_mensal
        if mes % 12 == 0:
            valores_anuais.append(patrimonio)

    anos_eixo = list(range(0, anos_projecao + 1))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=anos_eixo,
            y=valores_anuais,
            mode="lines",
            line={"color": COR_LINHA, "width": 3},
            fill="tozeroy",
            fillcolor="rgba(55, 71, 79, 0.08)",
            hovertemplate="Ano %{x}<br>Patrimônio: R$ %{y:,.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        autosize=True,
        height=380,
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        xaxis={"title": "Anos", "showgrid": False, "zeroline": False, "color": "#444444"},
        yaxis={"title": "Patrimônio (R$)", "showgrid": True, "gridcolor": COR_FUNDO_GRID, "zeroline": False, "color": "#444444"},
        font={"family": "Arial, sans-serif", "size": 13, "color": "#333333"},
        hoverlabel={"bgcolor": "#1A1A2E", "font_color": "#FFFFFF"},
    )

    st.plotly_chart(fig, use_container_width=True, config={"responsive": True, "displayModeBar": False})

idx_5 = min(5, anos_projecao)
idx_10 = min(10, anos_projecao)

col_x, col_y, col_z = st.columns(3)
col_x.metric(f"Patrimônio em {idx_5} anos", f"R$ {valores_anuais[idx_5]:,.2f}")
col_y.metric(f"Patrimônio em {idx_10} anos", f"R$ {valores_anuais[idx_10]:,.2f}")
col_z.metric(f"Patrimônio em {anos_projecao} anos", f"R$ {valores_anuais[-1]:,.2f}")

# ----------------------------------------------------------------------------
# RODAPÉ
# ----------------------------------------------------------------------------
st.markdown('<div class="rodape-app">Feito por Will Smolarek</div>', unsafe_allow_html=True)