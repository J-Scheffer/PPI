import streamlit as st
import pandas as pd
from typing import Optional
from utils.processamento import (
    carregar_df_cadastro,
    carregar_df_vendas,
    processa_df_venda_agrupado,
)
from utils.moeda import formatar_moeda_brasileira
from utils.sessao import inicializar_app, validar_df

# ---------------- CONFIGURAÇÃO INICIAL ----------------
st.set_page_config(page_title="Indicadores de Vendas", layout="wide")
inicializar_app()
st.title("📊 Indicadores de Vendas")

# ---------------- FUNÇÕES AUXILIARES ----------------

@st.cache_data
def calcular_vendas_por_localizacao(df: pd.DataFrame, campo: str) -> pd.DataFrame:
    """
    Agrupa o número de vendas e o valor total por campo de localização (ex: Bairro).
    """
    if campo not in df.columns or "Controle" not in df.columns or "TotalVenda" not in df.columns:
        print(f"⚠️ Campo '{campo}' não encontrado no DataFrame.")
        return pd.DataFrame(columns=[campo, "Vendas", "ValorTotal"])

    df_filtrado = df.dropna(subset=[campo, "Controle", "TotalVenda"])
    print(f"🔍 Agrupando por: {campo} (total de registros: {len(df_filtrado)})")

    df_grouped = (
        df_filtrado
        .groupby(campo, as_index=False)
        .agg(
            Vendas=("Controle", "nunique"),
            ValorTotal=("TotalVenda", "sum")
        )
        .sort_values("Vendas", ascending=False, ignore_index=True)
    )

    df_grouped["ValorTotalFormatado"] = df_grouped["ValorTotal"].map(formatar_moeda_brasileira)
    return df_grouped

# ---------------- CARREGAMENTO DE DADOS ----------------

df_cadastro = validar_df("df_cadastro", carregar_df_cadastro)
df_vendas_agrupado = validar_df("df_vendas_agrupado", processa_df_venda_agrupado)

# ---------------- MÉTRICAS GERAIS ----------------

st.subheader("📈 Métricas Gerais")

media_itens = df_vendas_agrupado["QuantidadeItens"].mean() if "QuantidadeItens" in df_vendas_agrupado.columns else 0
st.metric("🛍️ Itens por Venda (média)", f"{media_itens:.2f}")

# ---------------- VENDAS POR LOCALIZAÇÃO ----------------

st.markdown("---")
st.subheader("📍 Vendas por Local de Entrega")

coluna_local = "Bairro"  # Campo padrão para localização

if not coluna_local:
    st.warning("⚠️ Nenhuma coluna relacionada a bairro ou local de entrega foi encontrada.")
else:
    st.markdown(f"**Campo analisado:** `{coluna_local}`")
    df_bairro = calcular_vendas_por_localizacao(df_vendas_agrupado, coluna_local)

    if df_bairro.empty:
        st.warning("⚠️ Não há dados suficientes para agrupar por esse campo.")
    else:
        st.dataframe(
            df_bairro[[coluna_local, "Vendas", "ValorTotalFormatado"]],
            use_container_width=True
        )
