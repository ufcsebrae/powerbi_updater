# Power BI Updater

Este projeto automatiza a atualização de múltiplos datasets em um workspace do Power BI, monitora o status de cada atualização e envia um relatório por e-mail ao final do processo.

## Sumário

- [Visão Geral](#visão-geral)
- [Arquivos e Componentes](#arquivos-e-componentes)
  - [config.json](#configjson)
  - [powerbi.py](#powerbipy)
  - [listar_datasets.py](#listar_datasetspy)
  - [main.py](#mainpy)
  - [email_utils.py](#email_utilspy)
- [Fluxo da Aplicação](#fluxo-da-aplicação)
- [Pré-requisitos](#pré-requisitos)
- [Como Executar](#como-executar)
- [Observações](#observações)

---

## Visão Geral

A aplicação realiza as seguintes tarefas:

1. **Autentica** o usuário via Microsoft Device Code Flow.
2. **Obtém IDs** do workspace e dos datasets configurados.
3. **Dispara a atualização** de cada dataset via API REST do Power BI.
4. **Monitora o status** de cada atualização até a conclusão.
5. **Registra logs** do status de cada dataset.
6. **Envia um e-mail** com um relatório em HTML dos resultados.

---

## Arquivos e Componentes

### [config.json](config.json)

Arquivo de configuração contendo:
- `workspace_name`: Nome do workspace do Power BI.
- `datasets`: Lista dos nomes dos datasets a serem atualizados.

Exemplo:
```json
{
  "workspace_name": "UFC",
  "datasets": [
    "Recursos aplicados na atividade fim NOVEMBRO",
    "monitoramento_CREDENCIAMENTO",
    ...
  ]
}
```

---

### [powerbi.py](powerbi.py)

Módulo responsável por toda a integração com a API do Power BI.

**Principais funções:**

- `get_access_token()`: Autentica o usuário e retorna um token de acesso.
- `get_group_and_dataset_ids(token, workspace_name, dataset_name)`: Busca os IDs do workspace e do dataset pelo nome.
- `refresh_dataset(group_id, dataset_id, token)`: Dispara a atualização de um dataset específico.
- `get_refresh_history(group_id, dataset_id, token)`: Consulta o histórico de atualizações de um dataset.
- `list_datasets_in_workspace(group_id, token)`: Lista todos os datasets de um workspace.

---

### [listar_datasets.py](listar_datasets.py)

Script utilitário para listar todos os datasets presentes no workspace configurado.

**Fluxo:**
1. Lê as configurações do arquivo `config.json`.
2. Autentica o usuário.
3. Obtém o ID do workspace.
4. Lista e imprime todos os datasets do workspace.

---

### [main.py](main.py)

Script principal da aplicação. Realiza o processo completo de atualização e envio de relatório.

**Fluxo:**
1. Lê as configurações do arquivo `config.json`.
2. Autentica o usuário.
3. Obtém o ID do workspace.
4. Para cada dataset:
   - Obtém o ID do dataset.
   - Dispara a atualização.
   - Monitora o status até finalizar (Completed ou Failed).
   - Registra o log do resultado.
5. Ao final, chama [`send_email_log`](email_utils.py) para enviar o relatório por e-mail.

---

### [email_utils.py](email_utils.py)

Módulo responsável pelo envio de e-mails via Outlook.

**Função principal:**

- `send_email_log(subject, dataset_logs, sender_email, receiver_email, ...)`: 
  - Monta uma tabela HTML com os logs de atualização dos datasets.
  - Envia o e-mail usando o Outlook instalado no Windows.

---

## Fluxo da Aplicação

1. **Configuração:** O usuário define o workspace e os datasets em [config.json](config.json).
2. **Execução:** O usuário executa [main.py](main.py).
3. **Autenticação:** O script solicita autenticação via navegador (Device Code Flow).
4. **Atualização:** Cada dataset é atualizado sequencialmente, com monitoramento do status.
5. **Relatório:** Ao final, um e-mail é enviado com o resumo das atualizações.

---

## Pré-requisitos

- Python 3.8+
- Pacotes:
  - `requests`
  - `msal`
  - `pywin32` (para integração com Outlook)
- Conta Microsoft com acesso ao workspace do Power BI.
- Outlook instalado e configurado no Windows.

Instale as dependências com:
```sh
pip install requests msal pywin32
```

---

## Como Executar

1. Edite o arquivo [config.json](config.json) com o nome do workspace e os datasets desejados.
2. Execute o script principal:
   ```sh
   python main.py
   ```
3. Siga as instruções de autenticação exibidas no terminal.
4. Aguarde a conclusão do processo e o recebimento do e-mail de relatório.

---

## Observações

- O envio de e-mail utiliza o Outlook instalado no Windows. Certifique-se de estar logado com a conta correta.
- O script [listar_datasets.py](listar_datasets.py) pode ser usado para listar rapidamente todos os datasets de um workspace.
- O token de acesso é válido por tempo limitado; caso expire, será necessário autenticar novamente.
- O script trata erros de autenticação, atualização e consulta de status, registrando falhas no relatório final.

---

## Estrutura dos Arquivos

```
config.json
email_utils.py
listar_datasets.py
main.py
powerbi.py
__pycache__/