import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(
    page_title="Fluxo de Caixa Familiar",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS customizada para visual limpo e moderno
st.markdown("""
    <style>
    .main {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .metric-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Carregamento dos dados
@st.cache_data
def load_data():
    filepath = 'fluxo Familiar.xlsx'
    df = pd.read_excel(filepath, sheet_name='Fluxo Familiar')
    return df

try:
    df_raw = load_data()
except Exception as e:
    st.error(f"Erro ao carregar a planilha: {e}")
    st.stop()

# Tratamento dos dados para formato adequado (Colunas de datas)
col_desc = df_raw.columns[0]
date_cols = [c for c in df_raw.columns if c != col_desc]

# Limpando e formatando o dataframe principal
df_clean = df_raw.dropna(subset=[col_desc]).copy()
df_clean.set_index(col_desc, inplace=True)

# Transpondo para termos meses como linhas e categorias como colunas
df_transposed = df_clean.T
df_transposed.index = pd.to_datetime(df_transposed.index)

# Título do App
st.title("📊 Gestão de Fluxo de Caixa Familiar")
st.markdown("Painel interativo consolidado com todas as projeções de receitas, despesas, investimentos e saldo global.")

# Barra lateral para navegação e filtros
st.sidebar.header("⚙️ Filtros e Navegação")
formatted_dates = [d.strftime('%b / %Y') for d in df_transposed.index]
selected_month_str = st.sidebar.selectbox("Selecione o Mês de Referência", formatted_dates, index=0)
selected_date = df_transposed.index[formatted_dates.index(selected_month_str)]

# Dados do mês selecionado
mes_data = df_transposed.loc[selected_date]

# Extração de métricas principais do mês
saldo_inicial = mes_data.get('Saldo', 0)
despesas_totais = mes_data.get('Despesas Totais', 0)
saldo_no_mes = mes_data.get('Saldo no mês', 0)
saldo_global = mes_data.get('Saldo Global', 0)
investimentos_total = mes_data.get('Investimentos', 0)

# Exibição de KPIs em Cards no topo
st.markdown(f"### 📌 Resumo para: {selected_month_str}")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(label="Saldo Inicial / Mês", value=f"R$ {saldo_inicial:,.2f}")
with col2:
    st.metric(label="Saldo no Mês", value=f"R$ {saldo_no_mes:,.2f}", delta=f"R$ {despesas_totais:,.2f} desp")
with col3:
    st.metric(label="Despesas Totais", value=f"R$ {abs(despesas_totais):,.2f}")
with col4:
    st.metric(label="Investimentos Acumulados", value=f"R$ {investimentos_total:,.2f}")
with col5:
    st.metric(label="Saldo Global", value=f"R$ {saldo_global:,.2f}")

st.divider()

# Abas para organizar a visualização
tab1, tab2, tab3, tab4 = st.tabs(["📈 Visão Geral e Gráficos", "💵 Entradas & Receitas", "📉 Despesas & Gastos Fixos", "📋 Tabela Completa"])

with tab1:
    st.subheader("Evolução Temporal do Patrimônio e Saldo Global")
    
    # Gráfico de Linha - Saldo Global e Investimentos ao longo do tempo
    fig_evolucao = go.Figure()
    fig_evolucao.add_trace(go.Scatter(
        x=df_transposed.index, y=df_transposed['Saldo Global'],
        mode='lines+markers', name='Saldo Global', line=dict(color='#38bdf8', width=3)
    ))
    fig_evolucao.add_trace(go.Scatter(
        x=df_transposed.index, y=df_transposed['Investimentos'],
        mode='lines+markers', name='Investimentos', line=dict(color='#4ade80', width=3)
    ))
    fig_evolucao.update_layout(
        template='plotly_dark',
        xaxis_title='Mês',
        yaxis_title='Valor (R$)',
        hovermode='x unified'
    )
    st.plotly_chart(fig_evolucao, use_container_width=True)
    
    # Gráfico de Entradas vs Despesas por mês
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("Saldo Mensal Acumulado")
        fig_barra = px.bar(
            x=df_transposed.index, 
            y=df_transposed['Saldo no mês'],
            labels={'x': 'Mês', 'y': 'Saldo no Mês (R$)'},
            template='plotly_dark',
            color_discrete_sequence=['#818cf8']
        )
        st.plotly_chart(fig_barra, use_container_width=True)

with tab2:
    st.subheader(f"Detalhamento de Entradas — {selected_month_str}")
    entradas_keys = [
        'Neu Fixo', 'Neu Comissões licenças', 'Neu comissões serviços', 
        'Reembolsos Neu', 'Alini', 'Entrada adicionais diversas'
    ]
    df_entradas = pd.DataFrame({
        'Categoria': entradas_keys,
        'Valor (R$)': [mes_data.get(k, 0) for k in entradas_keys]
    }).fillna(0)
    
    col_t1, col_t2 = st.columns([2, 3])
    with col_t1:
        st.dataframe(df_entradas, hide_index=True, use_container_width=True)
    with col_t2:
        fig_pie_ent = px.pie(
            df_entradas[df_entradas['Valor (R$)'] > 0], 
            names='Categoria', values='Valor (R$)', 
            hole=0.4, template='plotly_dark'
        )
        st.plotly_chart(fig_pie_ent, use_container_width=True)

with tab3:
    st.subheader(f"Detalhamento de Despesas e Gastos Fixos — {selected_month_str}")
    gastos_keys = [
        'Aluguel e condomínio', 'Darf Neu', 'Darf Alini', 'Luz e telefone', 
        'Diarista', 'Psicologa Alini e Neu', 'Personal Alini e Neu', 
        'Plano de saude', 'Maju e Ozzy', 'Acordo C6', 
        'Cartão BTG Neu', 'Cartão Santander Neu', 'Cartão Santander Alini'
    ]
    df_gastos = pd.DataFrame({
        'Categoria': gastos_keys,
        'Valor (R$)': [abs(mes_data.get(k, 0)) for k in gastos_keys]
    }).fillna(0)
    
    col_g3, col_g4 = st.columns([2, 3])
    with col_g3:
        st.dataframe(df_gastos, hide_index=True, use_container_width=True)
    with col_g4:
        fig_pie_gastos = px.pie(
            df_gastos[df_gastos['Valor (R$)'] > 0], 
            names='Categoria', values='Valor (R$)', 
            hole=0.4, template='plotly_dark'
        )
        st.plotly_chart(fig_pie_gastos, use_container_width=True)

with tab4:
    st.subheader("Planilha Consolidada Completa")
    st.dataframe(df_raw, use_container_width=True)