import streamlit as st
import pandas as pd
import math
from typing import Tuple, Optional
from utils.processamento import processa_df_venda_agrupado
from utils.moeda import formatar_moeda_brasileira
from utils.sessao import inicializar_app

# ---------------- CONFIGURAÇÃO INICIAL ----------------
st.set_page_config(page_title="Indicadores de Vendas", layout="wide")
inicializar_app()
st.title("📊 Indicadores Gerais de Vendas")

# ---------------- CARREGAMENTO E VERIFICAÇÃO ----------------
if "df_vendas_agrupado" not in st.session_state:
    processa_df_venda_agrupado()

df: Optional[pd.DataFrame] = st.session_state.get("df_vendas_agrupado")

if not isinstance(df, pd.DataFrame) or df.empty:
    st.error("❌ O DataFrame 'df_vendas_agrupado' não está disponível ou está vazio.")
    st.stop()

df_vendas_agrupado: pd.DataFrame = df.copy()

# ---------------- FILTRAGEM OPCIONAL ----------------
ignore_99999 = st.checkbox("Ignorar cliente não identificado (ID 99999)", value=True)
if ignore_99999:
    df_vendas_agrupado = df_vendas_agrupado[df_vendas_agrupado["Cliente"] != 99999]

# ---------------- AGRUPAMENTO TEMPORAL ----------------

@st.cache_data
def agrupar_tabelas_temporais(df: pd.DataFrame) -> Tuple[pd.DataFrame, ...]:
    """Agrupa dados por variações temporais padrão."""

    def agrupar(coluna: str) -> pd.DataFrame:
        if coluna not in df.columns:
            return pd.DataFrame()

        soma_vendas = df.groupby(coluna)["TotalVenda"].sum()
        quant_clientes = df.groupby(coluna)["Cliente"].nunique()
        media_por_venda = df.groupby(coluna)["TotalVenda"].mean()

        agrupado = pd.DataFrame({
            coluna: soma_vendas.index,
            "TotalVenda": soma_vendas.values,
            "QuantClientes": quant_clientes.values,
            "QuantVendas": df.groupby(coluna)["Controle"].count().values,
            "MediaPorCliente": soma_vendas.values / quant_clientes.replace(0, pd.NA).fillna(1).values,
            "MediaPorVenda": media_por_venda.values
        })

        return agrupado

    anual     = agrupar("Ano")
    semestre  = agrupar("Semestre")
    trimestre = agrupar("Trimestre")
    mensal    = agrupar("MesPeriodo").rename(columns={"MesPeriodo": "Mês"})
    semanal   = agrupar("SemanaInicioDt").rename(columns={"SemanaInicioDt": "Semana"})
    dia_sem   = agrupar("DiaSemana")
    diario    = agrupar("Dia").rename(columns={"Dia": "Data"})

    if "Semana" in semanal.columns and "Data" in df.columns:
        meses_semanais = (
            df.groupby("SemanaInicioDt")["Data"]
              .agg(lambda x: "-".join(sorted(set(x.dt.strftime("%b")))))
              .reset_index(name="Meses")
              .rename(columns={"SemanaInicioDt": "Semana"})
        )
        semanal = semanal.merge(meses_semanais, on="Semana", how="left")

    return anual, semestre, trimestre, mensal, semanal, dia_sem, diario

# ---------------- EXIBIÇÃO DE TABELAS ----------------

def exibir_tabela(df: pd.DataFrame, titulo: Optional[str] = None) -> None:
    """Exibe um DataFrame formatado com valores monetários."""
    if df.empty:
        st.info(f"Nenhum dado disponível para '{titulo}'.")
        return

    df = df.reset_index(drop=True)

    if titulo == "Dia da Semana" and "DiaSemana" in df.columns:
        df["DiaSemana"] = pd.Categorical(
            df["DiaSemana"],
            categories=[
                "segunda-feira", "terça-feira", "quarta-feira",
                "quinta-feira", "sexta-feira", "sábado", "domingo"
            ],
            ordered=True
        )
        df = df.sort_values("DiaSemana")

    df["TotalVenda"] = df["TotalVenda"].map(formatar_moeda_brasileira)
    df["MediaPorCliente"] = df["MediaPorCliente"].map(formatar_moeda_brasileira)

    if titulo:
        st.markdown(f"### 📈 {titulo}")
    st.dataframe(df.style.hide(axis="index"), use_container_width=True)

# ---------------- KPIs GERAIS ----------------

total_clientes = df_vendas_agrupado["Cliente"].nunique()
total_vendas = df_vendas_agrupado["TotalVenda"].sum()

# DEBUG opcional (seguro)
st.text(f"DEBUG :: total_clientes = {total_clientes} ({type(total_clientes).__name__})")
st.text(f"DEBUG :: total_vendas = {total_vendas} ({type(total_vendas).__name__})")

# Tratamento seguro para divisão
try:
    total_clientes = float(total_clientes)
    total_vendas = float(total_vendas)

    if math.isnan(total_clientes) or math.isnan(total_vendas) or total_clientes == 0:
        ticket_medio = 0
    else:
        ticket_medio = total_vendas / total_clientes
except Exception as e:
    st.error(f"Erro ao calcular ticket médio: {e}")
    ticket_medio = 0

col1, col2, col3 = st.columns(3)
col1.metric("Total de Clientes", total_clientes)
col2.metric("Total Vendido", formatar_moeda_brasileira(total_vendas))
col3.metric("Média de Vendas/Cliente", formatar_moeda_brasileira(ticket_medio))

# ---------------- TABELAS DETALHADAS ----------------

tabelas = agrupar_tabelas_temporais(df_vendas_agrupado)
nomes = [
    "Ano", "Semestre", "Trimestre", "Mês",
    "Semana", "Dia da Semana", "Data"
]

for nome, df_tab in zip(nomes, tabelas):
    with st.expander(f"Detalhamento por {nome}"):
        exibir_tabela(df_tab, titulo=nome)
