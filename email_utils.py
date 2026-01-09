import win32com.client as win32
import os
import pandas as pd
import tempfile

def send_email_log(subject, dataset_logs, sender_email, receiver_email, *_args, **_kwargs):
    """
    Envia e-mail via Outlook com o usuário logado no Windows,
    incluindo o log e uma planilha Excel com os dados dos datasets.
    """

    # Monta a tabela HTML para o corpo do e-mail
    html_rows = ""
    for log in dataset_logs:
        html_rows += f"""
        <tr>
            <td>{log['name']}</td>
            <td>{log['status']}</td>
            <td>{log['start']}</td>
            <td>{log['end']}</td>
        </tr>
        """

    html_body = f"""
    <html>
        <body>
            <h2>Relatório de Atualização dos Datasets - Power BI</h2>
            <table border="1" cellpadding="5" cellspacing="0">
                <thead>
                    <tr>
                        <th>Dataset</th>
                        <th>Status</th>
                        <th>Início</th>
                        <th>Fim</th>
                    </tr>
                </thead>
                <tbody>
                    {html_rows}
                </tbody>
            </table>
        </body>
    </html>
    """

    # Cria o e-mail no Outlook
    outlook = win32.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)
    mail.To = receiver_email
    mail.Subject = subject
    mail.HTMLBody = html_body

    # Anexa log se fornecido
    attachment_path = _kwargs.get("attachment_path")
    if attachment_path and os.path.exists(attachment_path):
        mail.Attachments.Add(os.path.abspath(attachment_path))

    # Cria planilha Excel temporária com os dados
    if dataset_logs:
        df = pd.DataFrame(dataset_logs)
        nome_arquivo = f"dataset_logs_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        temp_excel = os.path.join(tempfile.gettempdir(), nome_arquivo)
        df.to_excel(temp_excel, index=False, engine="openpyxl")
        mail.Attachments.Add(temp_excel)

    mail.Send()
    print("📧 E-mail enviado via Outlook.")
