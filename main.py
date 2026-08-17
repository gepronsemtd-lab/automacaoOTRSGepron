from datetime import datetime
from core.config import LOCAL_TIMEZONE
from core.otrs_service import extrair_dados_otrs
from core.data_processor import limpar_dataframe, preparar_dashboard_data
from core.dashboard_renderer import gerar_e_salvar_dashboard

def executar():
    agora_local = datetime.now(LOCAL_TIMEZONE)
    ano_atual = agora_local.year
    data_filtro = f"{ano_atual}-01-01"
    periodo_referencia = f"Jan/{ano_atual} até o presente"

    print(f"Iniciando processamento para o período acumulado desde: {data_filtro}")

    try:
        # 1. Extração
        df_bruto = extrair_dados_otrs(data_filtro)
        print(f"Dados extraídos com sucesso. Linhas encontradas: {len(df_bruto)}")

        # 2. Limpeza
        df_limpo = limpar_dataframe(df_bruto)
        print(f"Colunas processadas: {df_limpo.columns.tolist()}")

        # 3. Regras de Negócio e KPIs
        dashboard_data = preparar_dashboard_data(df_limpo, agora_local, ano_atual, periodo_referencia)

        # 4. Renderização e Salvamento do Arquivo HTML
        gerar_e_salvar_dashboard(dashboard_data)

    except Exception as e:
        print(f"Erro crítico durante a execução: {e}")

if __name__ == "__main__":
    executar()