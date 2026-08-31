import logging
import sys
from datetime import datetime
from core.config import LOCAL_TIMEZONE
from core.otrs_service import extrair_dados_otrs
from core.data_processor import limpar_dataframe, preparar_dashboard_data
from core.dashboard_renderer import gerar_e_salvar_dashboard

# Configuração do Logging Estruturado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(module)s] - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def executar():
    agora_local = datetime.now(LOCAL_TIMEZONE)
    ano_atual = agora_local.year
    data_filtro = f"{ano_atual}-01-01"
    periodo_referencia = f"Jan/{ano_atual} até o presente"

    logger.info(f"Iniciando processamento para o período acumulado desde: {data_filtro}")

    try:
        # 1. Extração
        logger.info("Conectando ao OTRS e extraindo dados...")
        df_bruto = extrair_dados_otrs(data_filtro)
        
        if df_bruto.empty:
            logger.warning("A extração foi concluída, mas retornou 0 chamados.")
        else:
            logger.info(f"Dados extraídos com sucesso. Linhas: {len(df_bruto)}")

        # 2. Limpeza e Validação
        logger.info("Iniciando limpeza e normalização do DataFrame...")
        df_limpo = limpar_dataframe(df_bruto)
        logger.info(f"Colunas processadas com sucesso: {df_limpo.columns.tolist()}")

        # 3. Regras de Negócio
        logger.info("Calculando KPIs e estruturando dados para a Dashboard...")
        dashboard_data = preparar_dashboard_data(df_limpo, agora_local, ano_atual, periodo_referencia)

        # 4. Renderização
        logger.info("Renderizando HTML e injetando dados...")
        gerar_e_salvar_dashboard(dashboard_data)
        logger.info("Pipeline concluído com sucesso!")

    except Exception as e:
        logger.error(f"Falha crítica na execução do pipeline: {str(e)}", exc_info=True)
        sys.exit(1) # Marca o passo como "Failed" no GitHub Actions

if __name__ == "__main__":
    executar()