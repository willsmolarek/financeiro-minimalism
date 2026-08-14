from datetime import date
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import pymongo
import bcrypt

st.set_page_config(
    page_title="Dashboard Financeiro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização do app
CSS = """
<style>
    #MainMenu, footer { visibility: hidden; }
    button[data-testid="stSidebarNavSeparator"] { display: none; }
    [data-testid="stHeader"] { background-color: transparent !important; }
    [data-testid="stSidebarCollapseButton"] { color: #1A1A2E !important; }
    html, body, [class*="css"] { color: #1A1A2E; }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    .login-header {
        text-align: center;
        margin-bottom: 1.5rem;
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
        h1 { font-size: 1.5rem !important; }
        div[data-testid="column"] { min-width: 100% !important; flex: 1 1 100% !important; }
    }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# Conexão MongoDB Atlas
@st.cache_resource
def get_db_client():
    return pymongo.MongoClient(st.secrets["mongo"]["uri"])

client = get_db_client()
db = client["financeiro_db"]
usuarios_coll = db["usuarios"]
transacoes_coll = db["transacoes"]


# Auxiliares de Auth
def gerar_hash(senha: str) -> str:
    return bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verificar_senha(senha: str, hash_salvo: str) -> bool:
    return bcrypt.checkpw(senha.encode('utf-8'), hash_salvo.encode('utf-8'))

def criar_usuario(nome: str, cpf: str, data_nasc: str, email: str, senha: str) -> tuple[bool, str]:
    email = email.strip().lower()
    cpf = cpf.strip()
    
    if usuarios_coll.find_one({"email": email}):
        return False, "Este e-mail já está cadastrado."
    if usuarios_coll.find_one({"cpf": cpf}):
        return False, "Este CPF já está cadastrado."
    
    usuarios_coll.insert_one({
        "nome": nome.strip(),
        "cpf": cpf,
        "data_nascimento": data_nasc,
        "email": email,
        "senha": gerar_hash(senha)
    })
    return True, "Conta criada com sucesso!"

def autenticar_usuario(email: str, senha: str):
    email = email.strip().lower()
    user = usuarios_coll.find_one({"email": email})
    if user and verificar_senha(senha, user["senha"]):
        return user
    return None


# Controle de Sessão
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario_email = ""
    st.session_state.usuario_nome = ""

# Manter login no F5 via query params
if not st.session_state.autenticado and "session_email" in st.query_params:
    email_salvo = st.query_params["session_email"]
    user = usuarios_coll.find_one({"email": email_salvo})
    if user:
        st.session_state.autenticado = True
        st.session_state.usuario_email = email_salvo
        st.session_state.usuario_nome = user.get("nome", email_salvo)


# Flow de Login / Cadastro
if not st.session_state.autenticado:
    _, col_central, _ = st.columns([1, 1.8, 1])

    with col_central:
        st.markdown("""
            <div class="login-header">
                <h1>Dashboard Financeiro</h1>
                <p>Acesse sua conta para gerenciar suas finanças.</p>
            </div>
        """, unsafe_allow_html=True)

        tab_entrar, tab_cadastrar = st.tabs(["Entrar", "Criar Conta"])

        with tab_entrar:
            with st.form("form_login"):
                email = st.text_input("E-mail")
                senha = st.text_input("Senha", type="password")
                
                if st.form_submit_button("Entrar", use_container_width=True):
                    user = autenticar_usuario(email, senha)
                    if user:
                        st.session_state.autenticado = True
                        st.session_state.usuario_email = email.strip().lower()
                        st.session_state.usuario_nome = user.get("nome", email)
                        st.query_params["session_email"] = email.strip().lower()
                        st.success("Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("E-mail ou senha incorretos.")

        with tab_cadastrar:
            with st.form("form_cadastro"):
                novo_nome = st.text_input("Nome Completo")
                novo_cpf = st.text_input("CPF (somente números)", max_chars=14)
                nova_data_nasc = st.date_input("Data de Nascimento", value=date(2000, 1, 1))
                novo_email = st.text_input("E-mail")
                nova_senha = st.text_input("Senha", type="password")
                confirma_senha = st.text_input("Confirmar Senha", type="password")

                if st.form_submit_button("Cadastrar", use_container_width=True):
                    if not all([novo_nome.strip(), novo_cpf.strip(), novo_email.strip(), nova_senha.strip()]):
                        st.warning("Preencha todos os campos obrigatórios.")
                    elif nova_senha != confirma_senha:
                        st.error("As senhas não coincidem. Digite novamente.")
                    elif len(nova_senha) < 6:
                        st.warning("A senha deve ter pelo menos 6 caracteres.")
                    else:
                        ok, msg = criar_usuario(novo_nome, novo_cpf, str(nova_data_nasc), novo_email, nova_senha)
                        if ok:
                            st.success(f"{msg} Você já pode fazer login na aba 'Entrar'.")
                        else:
                            st.error(msg)

    st.markdown('<div class="rodape-app">Feito por Will Smolarek</div>', unsafe_allow_html=True)
    st.stop()


# Gerenciamento de Transações
COLUNAS = ["Data", "Tipo", "Descrição", "Valor"]

def carregar_dados() -> pd.DataFrame:
    query = {"usuario": st.session_state.usuario_email}
    docs = list(transacoes_coll.find(query, {"_id": 0, "usuario": 0}))
    
    if docs:
        df = pd.DataFrame(docs)
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce")
        for col in COLUNAS:
            if col not in df.columns:
                df[col] = None
        return df[COLUNAS]

    df = pd.DataFrame(columns=COLUNAS)
    df["Data"] = pd.to_datetime(df["Data"])
    df["Valor"] = pd.to_numeric(df["Valor"])
    return df

def salvar_dados(df: pd.DataFrame) -> None:
    email = st.session_state.usuario_email
    transacoes_coll.delete_many({"usuario": email})
    
    if not df.empty:
        df_salvar = df.copy()
        df_salvar["Data"] = pd.to_datetime(df_salvar["Data"]).dt.strftime("%Y-%m-%d")
        df_salvar["usuario"] = email
        transacoes_coll.insert_many(df_salvar.to_dict(orient="records"))

if "transacoes" not in st.session_state:
    st.session_state.transacoes = carregar_dados()


# Sidebar (Perfil e Novo Lançamento)
with st.sidebar:
    st.markdown(f"👤 **{st.session_state.usuario_nome}**")
    st.caption(f"E-mail: {st.session_state.usuario_email}")
    
    if st.button("Sair da Conta", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.usuario_email = ""
        st.session_state.usuario_nome = ""
        st.session_state.pop("transacoes", None)
        if "session_email" in st.query_params:
            del st.query_params["session_email"]
        st.rerun()

    st.divider()
    st.markdown("### Novo Lançamento")

    with st.form("form_transacao", clear_on_submit=True):
        tipo = st.radio("Tipo", ["Receita", "Despesa"], horizontal=True)
        valor = st.number_input("Valor (R$)", min_value=0.0, step=10.0, format="%.2f")
        descricao = st.text_input("Descrição", placeholder="Ex: Salário, Aluguel...")
        data_transacao = st.date_input("Data", value=date.today())

        if st.form_submit_button("Adicionar", use_container_width=True):
            if valor <= 0:
                st.warning("Informe um valor maior que zero.")
            elif not descricao.strip():
                st.warning("Informe uma descrição.")
            else:
                nova_linha = pd.DataFrame([{
                    "Data": pd.to_datetime(data_transacao),
                    "Tipo": tipo,
                    "Descrição": descricao.strip(),
                    "Valor": valor
                }])
                st.session_state.transacoes = pd.concat([st.session_state.transacoes, nova_linha], ignore_index=True)
                salvar_dados(st.session_state.transacoes)
                st.success("Lançamento adicionado!")
                st.rerun()

    st.divider()

    if not st.session_state.transacoes.empty:
        if st.button("Limpar todo o histórico", use_container_width=True):
            df_vazio = pd.DataFrame(columns=COLUNAS)
            df_vazio["Data"] = pd.to_datetime(df_vazio["Data"])
            st.session_state.transacoes = df_vazio
            salvar_dados(df_vazio)
            st.rerun()


# Painel Principal
df = st.session_state.transacoes.copy()
if not df.empty:
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

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
    f"R$ {saldo_periodo:,.2f}"
)

st.divider()


# Tabela de Transações
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
        df_salvar = df_editado[~df_editado["Excluir"]].drop(columns=["Excluir"])
        df_salvar["Data"] = pd.to_datetime(df_salvar["Data"])

        st.session_state.transacoes = df_salvar
        salvar_dados(df_salvar)

        st.success("Alterações salvas com sucesso!")
        st.rerun()

st.divider()


# Projeções e Juros Compostos
st.subheader("Projeção Financeira")

col_a, col_b = st.columns([1, 2])

with col_a:
    aporte_mensal = st.number_input(
        "Aporte mensal (R$)",
        min_value=0.0,
        value=500.0,
        step=50.0,
        format="%.2f"
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
            line={"color": "#37474F", "width": 3},
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
        yaxis={"title": "Patrimônio (R$)", "showgrid": True, "gridcolor": "#E0E0E0", "zeroline": False, "color": "#444444"},
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

st.markdown('<div class="rodape-app">Feito por Will Smolarek</div>', unsafe_allow_html=True)