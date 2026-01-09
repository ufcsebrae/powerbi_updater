import requests
import json
from msal import PublicClientApplication

AUTHORITY = "https://login.microsoftonline.com/organizations"
CLIENT_ID = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"  # ID público da Microsoft (client público padrão)
SCOPE = ["https://analysis.windows.net/powerbi/api/.default"]

def get_access_token():
    app = PublicClientApplication(CLIENT_ID, authority=AUTHORITY)
    flow = app.initiate_device_flow(scopes=SCOPE)
    if "user_code" not in flow:
        raise Exception("Falha ao iniciar o fluxo de autenticação.")
    
    print("Por favor autentique em: {}\nCódigo: {}".format(flow["verification_uri"], flow["user_code"]))
    
    result = app.acquire_token_by_device_flow(flow)
    return result.get("access_token", None)

def get_group_and_dataset_ids(token, workspace_name, dataset_name):
    headers = {"Authorization": f"Bearer {token}"}
    
    groups = requests.get("https://api.powerbi.com/v1.0/myorg/groups", headers=headers).json()["value"]
    group = next((g for g in groups if g["name"] == workspace_name), None)
    if not group:
        raise Exception("Workspace não encontrado.")

    datasets = requests.get(f"https://api.powerbi.com/v1.0/myorg/groups/{group['id']}/datasets", headers=headers).json()["value"]
    dataset = next((d for d in datasets if d["name"] == dataset_name), None)
    if not dataset:
        raise Exception("Dataset não encontrado.")
    
    return group["id"], dataset["id"]

def refresh_dataset(group_id, dataset_id, token):
    """
    Dispara a atualização de um dataset específico via API REST.
    """

    url = f"https://api.powerbi.com/v1.0/myorg/groups/{group_id}/datasets/{dataset_id}/refreshes"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.post(url, headers=headers)

    try:
        data = response.json()
    except ValueError:
        data = response.text  # se não for JSON, pega como texto

    return response.status_code, data

def get_refresh_history(group_id, dataset_id, token):
    """
    Retorna o histórico das atualizações (últimas 5 por padrão).
    Documentação: https://learn.microsoft.com/en-us/rest/api/power-bi/datasets/get-refresh-history-in-group
    """
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{group_id}/datasets/{dataset_id}/refreshes"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)
    try:
        return response.status_code, response.json()
    except ValueError:
        return response.status_code, response.text

def list_datasets_in_workspace(group_id, token):
    """
    Lista todos os datasets dentro de um workspace (por ID).
    Documentação: https://learn.microsoft.com/en-us/rest/api/power-bi/datasets/get-datasets-in-group
    """
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{group_id}/datasets"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)

    try:
        return response.status_code, response.json()
    except ValueError:
        return response.status_code, response.text
    
def get_group_id_by_name(token, workspace_name):
    import requests

    url = "https://api.powerbi.com/v1.0/myorg/groups"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Erro ao obter workspaces: {response.text}")

    workspaces = response.json().get("value", [])
    for workspace in workspaces:
        if workspace["name"].lower() == workspace_name.lower():
            return workspace["id"]

    raise Exception(f"Workspace '{workspace_name}' não encontrado.")
    
