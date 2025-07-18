import pandas as pd

def formatar_moeda_brasileira(valor: float) -> str:
    """Formata valor numérico como moeda brasileira."""
    if pd.isnull(valor) or not isinstance(valor, (int, float)):
        return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
