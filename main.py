import json
import time
from powerbi import (
    get_access_token,
    get_group_and_dataset_ids,
    refresh_dataset,
    get_refresh_history
)
from email_utils import send_email_log  # certifique-se de que esse arquivo existe

# Carrega configurações
with open("config.json") as f:
    config = json.load(f)

token = get_access_token()

if not token:
    print("❌ Falha ao obter token de acesso.")
    exit()

workspace_name = config["workspace_name"]
dataset_names = config["datasets"]

# Descobre ID do workspace uma vez só
group_id, _ = get_group_and_dataset_ids(token, workspace_name, dataset_names[0])
print(f"📂 Workspace '{workspace_name}' encontrado com ID: {group_id}\n")

dataset_logs = []

# Loop por cada painel
for dataset_name in dataset_names:
    print(f"➡️ Atualizando dataset: {dataset_name}")

    try:
        _, dataset_id = get_group_and_dataset_ids(token, workspace_name, dataset_name)

        status_code, result = refresh_dataset(group_id, dataset_id, token)
        print(f"🚀 Atualização solicitada (status HTTP: {status_code})")

        if status_code == 202:
            print("⏳ Aguardando conclusão da atualização...")

            while True:
                status, history = get_refresh_history(group_id, dataset_id, token)

                if status != 200:
                    print("❌ Erro ao consultar histórico:", history)
                    break

                refresh = history.get("value", [])[0]
                refresh_status = refresh["status"]
                start_time = refresh["startTime"]
                end_time = refresh.get("endTime", "⏳ Em andamento")

                print(f"🕒 Status: {refresh_status} | Início: {start_time}")

                if refresh_status in ["Completed", "Failed"]:
                    print(f"🏁 Finalizado: {refresh_status} | Início: {start_time} | Fim: {end_time}\n")
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
            print("⚠️ Atualização não aceita. Detalhes:", result)
            dataset_logs.append({
                "name": dataset_name,
                "status": "Erro na solicitação",
                "start": "-",
                "end": "-"
            })

    except Exception as e:
        print(f"❌ Erro ao processar {dataset_name}: {e}")
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
    sender_email="",  # pode deixar vazio
    receiver_email="cesargl@sebraesp.com.br",
    smtp_server="", smtp_port=0, smtp_user="", smtp_password=""
)

print("✅ Todas as atualizações processadas e e-mail enviado.")
