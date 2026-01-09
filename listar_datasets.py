import json
from powerbi import get_access_token, get_group_and_dataset_ids, list_datasets_in_workspace

with open("config.json") as f:
    config = json.load(f)

token = get_access_token()

if token:
    group_id, _ = get_group_and_dataset_ids(token, config["workspace_name"], config["datasets"][0])
    status, data = list_datasets_in_workspace(group_id, token)

    if status == 200:
        print(f"📋 Datasets no workspace '{config['workspace_name']}':\n")
        for ds in data.get("value", []):
            print(f"✅ {ds['name']} | ID: {ds['id']}")
    else:
        print("❌ Erro ao buscar datasets:", data)
else:
    print("❌ Falha na autenticação.")
