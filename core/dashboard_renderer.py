import json
import os
import shutil 
from .config import OUTPUT_DIR, OUTPUT_FILE, TEMPLATE_FILE, ASSETS_DIR, OUTPUT_ASSETS_DIR

def gerar_e_salvar_dashboard(dashboard_data, template_path=TEMPLATE_FILE):
    # Lê o arquivo HTML limpo
    with open(template_path, "r", encoding="utf-8") as f:
        html_template = f.read()

    # Injeta os dados na variável window.DASHBOARD_DATA
    html_final = html_template.replace(
        '"DATA_PLACEHOLDER"',
        json.dumps(dashboard_data, ensure_ascii=False),
    )

    # Cria diretório de saída
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Copia a pasta templates/assets para dist/assets
    if os.path.exists(ASSETS_DIR):
        shutil.copytree(ASSETS_DIR, OUTPUT_ASSETS_DIR, dirs_exist_ok=True)

    # Salva o arquivo html final
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_final)

    print(f"Dashboard gerado com sucesso em: {OUTPUT_FILE}")
