import pytest
import pandas as pd
from core.data_processor import limpar_dataframe

# Criamos um dataframe simulando a extração bruta do OTRS para teste
@pytest.fixture
def mock_df_bruto():
    return pd.DataFrame({
        'DataCriacao': ['2026-01-01 10:00:00', '2026-01-02 11:00:00'],
        'Fila': ['SESUITE-N1', 'SESUITE-N2'],
        'Tipo': ['Incidente', 'Requisição'],
        'Estado': ['novo', 'aberto'],
        'ProprietarioNome': ['João', 'Maria'],
        'Servico': ['Acesso', 'Hardware']
    })

def test_limpeza_normaliza_colunas(mock_df_bruto):
    """Garante que as colunas são convertidas para minúsculo e sem acento."""
    df_limpo = limpar_dataframe(mock_df_bruto)
    colunas = df_limpo.columns.tolist()
    
    assert 'datacriacao' in colunas
    assert 'proprietarionome' in colunas

def test_limpeza_converte_datas(mock_df_bruto):
    """Garante que a coluna datacriacao virou um objeto datetime do Pandas."""
    df_limpo = limpar_dataframe(mock_df_bruto)
    assert pd.api.types.is_datetime64_any_dtype(df_limpo['datacriacao'])

def test_falha_sem_coluna_data():
    """Garante que o sistema bloqueia o avanço se o OTRS parar de mandar a data de criação."""
    df_invalido = pd.DataFrame({'Fila': ['N1'], 'Tipo': ['Incidente']})
    
    with pytest.raises(KeyError) as excinfo:
        limpar_dataframe(df_invalido)
    assert 'datacriacao' in str(excinfo.value)