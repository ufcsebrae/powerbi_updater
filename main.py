import json
import sys
import time
import difflib
from powerbi import (
    get_access_token,
    get_group_and_dataset_ids,
    refresh_dataset,
    get_refresh_history
)
from email_utils import send_email_log
from logger_utils import setup_logger

# Inicializa logger e armazena o caminho do log
logger, log_file_path = setup_logger()

# Carrega configurações
with open("config.json") as f:
    config = json.load(f)

token = get_access_token()

if not token:
    logger.error("❌ Falha ao obter token de acesso.")
    exit()

workspace_name = config["workspace_name"]
all_datasets = config["datasets"]
datasets_lower = {ds.lower(): ds for ds in all_datasets}

# Permitir nome via argumento ou input
if len(sys.argv) > 1:
    dataset_input = " ".join(sys.argv[1:]).strip()
else:
    dataset_input = input("Digite o nome do dataset (ou pressione Enter para todos): ").strip()

# Define datasets a processar
if dataset_input:
    dataset_key = dataset_input.lower()
    dataset_name = datasets_lower.get(dataset_key)

    if not dataset_name:
        similares = difflib.get_close_matches(dataset_input, all_datasets, n=1, cutoff=0.4)
        if similares:
            sugestao = similares[0]
            confirm = input(f"⚠️ Dataset '{dataset_input}' não encontrado. Você quis dizer '{sugestao}'? (s/n): ").strip().lower()
            if confirm == "s":
                dataset_name = sugestao
            else:
                logger.info("❌ Operação cancelada pelo usuário.")
                exit()
        else:
            logger.error(f"❌ Dataset '{dataset_input}' não encontrado nem similar.")
            exit()

    dataset_names = [dataset_name]
else:
    dataset_names = all_datasets
    logger.info("🔁 Nenhum nome informado — executando todos os datasets.")

# Descobre ID do workspace uma vez só
group_id, _ = get_group_and_dataset_ids(token, workspace_name, dataset_names[0])
logger.info(f"📂 Workspace '{workspace_name}' encontrado com ID: {group_id}\n")

dataset_logs = []

# Loop por cada dataset
for dataset_name in dataset_names:
    logger.info(f"➡️ Atualizando dataset: {dataset_name}")

    try:
        _, dataset_id = get_group_and_dataset_ids(token, workspace_name, dataset_name)

        status_code, result = refresh_dataset(group_id, dataset_id, token)
        logger.info(f"🚀 Atualização solicitada (status HTTP: {status_code})")

        if status_code == 202:
            logger.info("⏳ Aguardando conclusão da atualização...")

            while True:
                status, history = get_refresh_history(group_id, dataset_id, token)

                if status != 200:
                    logger.error(f"❌ Erro ao consultar histórico: {history}")
                    break

                refresh = history.get("value", [])[0]
                refresh_status = refresh["status"]
                start_time = refresh["startTime"]
                end_time = refresh.get("endTime", "⏳ Em andamento")

                logger.info(f"🕒 Status: {refresh_status} | Início: {start_time}")

                if refresh_status in ["Completed", "Failed"]:
                    logger.info(f"🏁 Finalizado: {refresh_status} | Início: {start_time} | Fim: {end_time}\n")
                    dataset_logs.append({
                        "name": dataset_name,
                        "status": refresh_status,
                        "start": start_time,
                        "end": end_time
                    })
                    break
                else:
                    time.sleep(10)
        else:
            logger.warning(f"⚠️ Atualização não aceita. Detalhes: {result}")
            dataset_logs.append({
                "name": dataset_name,
                "status": "Erro na solicitação",
                "start": "-",
                "end": "-"
            })

    except Exception as e:
        logger.exception(f"❌ Erro ao processar {dataset_name}: {e}")
        dataset_logs.append({
            "name": dataset_name,
            "status": f"Erro: {e}",
            "start": "-",
            "end": "-"
        })

# Envia e-mail com os logs
send_email_log(
    subject="Relatório de Atualização Power BI",
    dataset_logs=dataset_logs,
    sender_email="",
    receiver_email="cesargl@sebraesp.com.br",
    smtp_server="", smtp_port=0, smtp_user="", smtp_password="",
    attachment_path=log_file_path
)

logger.info("✅ Todas as atualizações processadas e e-mail enviado.")
