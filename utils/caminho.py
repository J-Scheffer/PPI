import pandas as pd
from typing import Union, IO, Optional
import os

def caminho_valido(path: Optional[Union[str, IO]]) -> bool:
    """Verifica se o caminho é uma string válida e aponta para um arquivo existente."""
    return isinstance(path, str) and os.path.isfile(path)