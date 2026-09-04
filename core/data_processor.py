import pandas as pd
import unicodedata
import re

def normalize_column(column_name: str) -> str:
    normalized = unicodedata.normalize('NFKD', str(column_name))
    normalized = ''.join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r'[^a-z0-9_]', '', normalized.lower().replace(' ', '_'))

def percentual(parte, total):
    return round((parte / total * 100), 1) if total else 0

def limpar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df.rename(columns={col: normalize_column(col) for col in df.columns}, inplace=True)
    if 'datacriacao' not in df.columns:
        raise KeyError('A coluna datacriacao não foi encontrada no arquivo CSV.')
    df['datacriacao'] = pd.to_datetime(df['datacriacao'])

    if 'estado' in df.columns:
        mapa_estados = {
            'closed successful': 'Fechado c/ Sucesso',
            'closed unsuccessful': 'Fechado s/ Sucesso',
            'new': 'Novo',
            'open': 'Aberto',
            'pending reminder': 'Lembrete Pendente',
            'merged': 'Mesclado',
            'removed': 'Removido'
        }
        df['estado'] = df['estado'].str.lower().map(lambda x: mapa_estados.get(x, str(x).title()))
        
    if 'proprietarionome' in df.columns:
        df['proprietarionome'] = df['proprietarionome'].apply(
            lambda x: " ".join(str(x).strip().split()[:2]) if pd.notna(x) and str(x).strip() else "Não informado"
        )
    
    if 'servico' in df.columns:
        df['servico'] = df['servico'].apply(
            lambda x: re.sub(r'(?i)^(se\s*)?suite\s*-\s*', '', str(x)).strip() if pd.notna(x) else "Não informado"
        )

    return df

def preparar_dashboard_data(df, agora_local, ano_atual, periodo_referencia):

    total_tickets = len(df)
    n1_count = len(df[df["fila"] == "SESUITE-N1"])
    n2_count = len(df[df["fila"] == "SESUITE-N2"])
    n3_count = len(df[df["fila"] == "SESUITE-N3"])

    n1_percent = percentual(n1_count, total_tickets)
    n2_percent = percentual(n2_count, total_tickets)
    n3_percent = percentual(n3_count, total_tickets)

    tipo_counts = df["tipo"].fillna("Não informado").value_counts().to_dict()
    fila_counts = df["fila"].fillna("Não informado").value_counts().to_dict()
    estado_counts = df["estado"].fillna("Não informado").value_counts().to_dict()

    top_analistas = df["proprietarionome"].fillna("Não informado").value_counts().head(10)
    top_servicos = df["servico"].fillna("Não informado").value_counts().head(10)

    meses = pd.period_range(
        start=f"{ano_atual}-01",
        end=agora_local.strftime("%Y-%m"),
        freq="M",
    )

    labels_meses = [mes.strftime("%b/%Y") for mes in meses]
    indice_meses = [mes.strftime("%Y-%m") for mes in meses]

    def serie_mensal(dataframe):
        if dataframe.empty:
            return [0 for _ in indice_meses]

        serie = (
            dataframe.assign(mes=dataframe["datacriacao"].dt.strftime("%Y-%m"))
            .groupby("mes")
            .size()
            .reindex(indice_meses, fill_value=0)
        )
        return serie.astype(int).tolist()

    dashboard_data = {
        "updated": agora_local.strftime("%d/%m/%Y %H:%M:%S"),
        "period": periodo_referencia,
        "kpis": [
            {"label": "Total", "value": total_tickets, "color": "blue", "icon": "list-checks"},
            {"label": "N1", "value": n1_count, "color": "green", "icon": "check-circle"},
            {"label": "N2", "value": n2_count, "color": "amber", "icon": "clock"},
            {"label": "N3", "value": n3_count, "color": "red", "icon": "alert-triangle"},
        ],
        "progress": {
            "items": [
                {"label": "SESUITE-N1", "value": n1_count, "percent": n1_percent, "color": "green"},
                {"label": "SESUITE-N2", "value": n2_count, "percent": n2_percent, "color": "amber"},
                {"label": "SESUITE-N3", "value": n3_count, "percent": n3_percent, "color": "red"},
            ]
        },
        "charts": {
            "tipos": {
                "labels": list(tipo_counts.keys()),
                "values": list(tipo_counts.values()),
            },
            "filas": {
                "labels": list(fila_counts.keys()),
                "values": list(fila_counts.values()),
            },
            "estados": {
                "labels": list(estado_counts.keys()),
                "values": list(estado_counts.values()),
            },
            "analistas": {
                "labels": top_analistas.index.tolist(),
                "values": top_analistas.astype(int).tolist(),
            },
            "servicos": {
                "labels": top_servicos.index.tolist(),
                "values": top_servicos.astype(int).tolist(),
            },
            "timeline": {
                "labels": labels_meses,
                "total": serie_mensal(df),
                "n1": serie_mensal(df[df["fila"] == "SESUITE-N1"]),
                "n2": serie_mensal(df[df["fila"] == "SESUITE-N2"]),
                "n3": serie_mensal(df[df["fila"] == "SESUITE-N3"]),
            },
        },
    }

    records_columns = [
        "numerochamado",
        "fila",
        "estado",
        "proprietarionome",
        "servico",
        "titulo",
        "tipo",
        "prioridade",
        "datacriacao",
        "datamodificacao",
        "gerencia",
    ]

    records = (
        df[[col for col in records_columns if col in df.columns]]
        .fillna("Não informado")
        .assign(
            datacriacao=lambda base: base["datacriacao"].astype(str) if "datacriacao" in base.columns else "",
            datamodificacao=lambda base: base["datamodificacao"].astype(str) if "datamodificacao" in base.columns else "",
        )
        .to_dict(orient="records")
    )

    dashboard_data["records"] = records
    dashboard_data["filters"] = {
        "niveis": sorted(df["fila"].dropna().unique().tolist()) if "fila" in df.columns else [],
        "gerencias": sorted(df["gerencia"].dropna().unique().tolist()) if "gerencia" in df.columns else [],
        "executores": sorted(df["proprietarionome"].dropna().unique().tolist()) if "proprietarionome" in df.columns else [],
        "status": sorted(df["estado"].dropna().unique().tolist()) if "estado" in df.columns else [],
    }

    return dashboard_data
