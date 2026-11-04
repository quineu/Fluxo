import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(
    page_title="Fluxo Familiar",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .main { background-color: #0f172a; color: #f8fafc; }
    .stMetric { background-color: #1e293b; padding: 15px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 10px; }
    h1, h2, h3 { color: #f8fafc !important; }
    </style>
""", unsafe_allow_html=True)

EXCEL_FILE = 'fluxo Familiar.xlsx'

@st.cache_data(ttl=5)
def load_data():
    if os.path.exists(EXCEL_FILE):
        return pd.read_excel(EXCEL_FILE, sheet_name='Fluxo Familiar')
    return None

df_raw = load_data()

if df_raw is None:
    st.error("⚠️ Erro: O arquivo 'fluxo Familiar.xlsx' não foi encontrado no repositório do GitHub. Envie o arquivo junto com o app.py.")
    st.stop()

try:
    col_desc = df_raw.columns[0]
    df_clean = df_raw.dropna(subset=[col_desc]).copy()
    df_clean.set_index(col_desc, inplace=True)

    df_transposed = df_clean.T
    df_transposed.index = pd.to_datetime(df_transposed.index, errors='coerce')
    valid_dates = [d for d in df_transposed.index if pd.notnull(d)]
except Exception as e:
    st.error(f"Erro ao processar estrutura da planilha: {e}")
    st.stop()

st.title("💰 Fluxo Familiar")

if formatted_dates := [d.strftime('%b / %Y') for d in valid_dates]:
    selected_month_str = st.selectbox("📅 Mês de Referência", formatted_dates, index=0)
    selected_date = valid_dates[formatted_dates.index(selected_month_str)]
    mes_data = df_transposed.loc[selected_date]
else:
    st.error("Nenhuma data válida encontrada.")
    st.stop()

# Métricas com valores seguros
saldo_global = float(mes_data.get('Saldo Global', 0) or 0)
investimentos_total = float(mes_data.get('Investimentos', 0) or 0)
saldo_no_mes = float(mes_data.get('Saldo no mês', 0) or 0)
despesas_totais = float(mes_data.get('Despesas Totais', 0) or 0)

st.markdown(f"### 📌 Resumo: {selected_month_str}")
st.metric(label="💵 Saldo Global Acumulado", value=f"R$ {saldo_global:,.2f}")
st.metric(label="📈 Investimentos", value=f"R$ {investimentos_total:,.2f}")

col_m1, col_m2 = st.columns(2)
with col_m1:
    st.metric(label="Entrada no Mês", value=f"R$ {saldo_no_mes:,.2f}")
with col_m2:
    st.metric(label="Despesas Totais", value=f"R$ {abs(despesas_totais):,.2f}")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["📊 Visão", "💵 Entradas", "📉 Despesas", "✏️ Lançar"])

with tab1:
    st.subheader("Evolução Patrimonial")
    try:
        fig_evolucao = go.Figure()
        fig_evolucao.add_trace(go.Scatter(
            x=df_transposed.index, y=df_transposed['Saldo Global'],
            mode='lines+markers', name='Saldo Global', line=dict(color='#38bdf8', width=3)
        ))
        fig_evolucao.update_layout(
            template='plotly_dark', height=280,
            margin=dict(l=10, r=10, t=20, b=10),
            xaxis_title='', yaxis_title='R$'
        )
        st.plotly_chart(fig_evolucao, use_container_width=True)
    except Exception:
        st.info("Gráfico indisponível para os dados atuais.")

with tab2:
    st.subheader("Entradas do Mês")
    entradas_keys = [
        'Neu Fixo', 'Neu Comissões licenças', 'Neu comissões serviços', 
        'Reembolsos Neu', 'Alini', 'Entrada adicionais diversas'
    ]
    for k in entradas_keys:
        val = mes_data.get(k, 0)
        if pd.notnull(val) and float(val) > 0:
            st.markdown(f"✅ **{k}**: R$ {float(val):,.2f}")

with tab3:
    st.subheader("Despesas do Mês")
    gastos_keys = [
        'Aluguel e condomínio', 'Darf Neu', 'Darf Alini', 'Luz e telefone', 
        'Diarista', 'Psicologa Alini e Neu', 'Personal Alini e Neu', 
        'Plano de saude', 'Maju e Ozzy', 'Acordo C6', 
        'Cartão BTG Neu', 'Cartão Santander Neu', 'Cartão Santander Alini'
    ]
    for k in gastos_keys:
        val = mes_data.get(k, 0)
        if pd.notnull(val) and float(val) != 0:
            st.markdown(f"🔻 **{k}**: R$ {abs(float(val)):,.2f}")

with tab4:
    st.subheader("✏️ Atualização Rápida")
    categorias_disponiveis = df_raw[col_desc].dropna().tolist()
    cat_selecionada = st.selectbox("Categoria / Item", categorias_disponiveis)
    
    val_atual = df_raw.loc[df_raw[col_desc] == cat_selecionada, selected_date].values
    val_default = float(val_atual[0]) if len(val_atual) > 0 and pd.notnull(val_atual[0]) else 0.0
    
    novo_valor = st.number_input("Novo Valor (R$)", value=val_default, step=100.0, format="%.2f")
    
    if st.button("💾 Atualizar Valor", type="primary", use_container_width=True):
        try:
            df_raw[selected_date] = pd.to_numeric(df_raw[selected_date], errors='coerce').fillna(0.0)
            df_raw.loc[df_raw[col_desc] == cat_selecionada, selected_date] = float(novo_valor)
            
            with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl', mode='w') as writer:
                df_raw.to_excel(writer, sheet_name='Fluxo Familiar', index=False)
                
            st.cache_data.clear()
            st.success("✅ Atualizado com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")
