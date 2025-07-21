import sys
import time
import difflib
import requests
from powerbi import (
    get_access_token,
    get_group_and_dataset_ids,
    refresh_dataset,
    get_refresh_history,
    get_group_id_by_name
)
from email_utils import send_email_log
from logger_utils import setup_logger

# Inicializa logger
logger, log_file_path = setup_logger()

# Solicita workspace (via argumento ou input)
if len(sys.argv) > 1:
    workspace_input = sys.argv[1].strip()
else:
    workspace_input = input("Digite o nome do workspace: ").strip()

if not workspace_input:
    logger.error("❌ Nome do workspace não informado.")
    sys.exit(1)

# Solicita nome do dataset (opcional)
if len(sys.argv) > 2:
    dataset_input = " ".join(sys.argv[2:]).strip()
else:
    dataset_input = input("Digite o nome do dataset (ou pressione Enter para atualizar todos): ").strip()

# Autentica
token = get_access_token()
if not token:
    logger.error("❌ Falha ao obter token de acesso.")
    sys.exit(1)

# Obtém o ID do workspace
group_id = get_group_id_by_name(token, workspace_input)
logger.info(f"📂 Workspace '{workspace_input}' encontrado com ID: {group_id}")

# Lista todos os datasets do workspace via API
datasets_url = f"https://api.powerbi.com/v1.0/myorg/groups/{group_id}/datasets"
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(datasets_url, headers=headers)

if response.status_code != 200:
    logger.error(f"❌ Falha ao obter datasets. Código {response.status_code}: {response.text}")
    sys.exit(1)

datasets_api = response.json().get("value", [])
all_datasets = {ds["name"]: ds["id"] for ds in datasets_api}
datasets_lower = {name.lower(): name for name in all_datasets.keys()}

# Define quais datasets atualizar
if dataset_input:
    key = dataset_input.lower()
    dataset_name = datasets_lower.get(key)

    if not dataset_name:
        sugestao = difflib.get_close_matches(dataset_input, all_datasets.keys(), n=1, cutoff=0.4)
        if sugestao:
            confirmar = input(f"⚠️ Dataset '{dataset_input}' não encontrado. Você quis dizer '{sugestao[0]}'? (s/n): ").strip().lower()
            if confirmar == "s":
                dataset_name = sugestao[0]
            else:
                logger.info("❌ Cancelado pelo usuário.")
                sys.exit(0)
        else:
            logger.error("❌ Nenhum dataset similar encontrado.")
            sys.exit(1)

    datasets_to_update = {dataset_name: all_datasets[dataset_name]}
else:
    logger.info("🔁 Nenhum nome informado — atualizando todos os datasets encontrados.")
    datasets_to_update = all_datasets

dataset_logs = []

# Loop de atualização
for dataset_name, dataset_id in datasets_to_update.items():
    logger.info(f"➡️ Atualizando dataset: {dataset_name}")
    try:
        status_code, result = refresh_dataset(group_id, dataset_id, token)
        logger.info(f"🚀 Atualização solicitada (HTTP {status_code})")

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
    subject=f"Atualização de datasets | Workspace: {workspace_input}",
    dataset_logs=dataset_logs,
    sender_email="",
    receiver_email="cesargl@sebraesp.com.br",
    smtp_server="", smtp_port=0, smtp_user="", smtp_password="",
    attachment_path=log_file_path
)

logger.info("✅ Atualizações concluídas e e-mail enviado.")
