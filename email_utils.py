import win32com.client as win32
import os

def send_email_log(subject, dataset_logs, sender_email, receiver_email, *_args, **_kwargs):
    """
    Envia e-mail via Outlook com o usuário logado no Windows,
    incluindo o log como anexo, se fornecido via 'attachment_path'.
    """

    # Monta tabela HTML dos datasets
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

    # Cria e-mail no Outlook
    outlook = win32.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)
    mail.To = receiver_email
    mail.Subject = subject
    mail.HTMLBody = html_body

    # Anexa log se fornecido
    attachment_path = _kwargs.get("attachment_path")
    if attachment_path and os.path.exists(attachment_path):
        mail.Attachments.Add(os.path.abspath(attachment_path))

    mail.Send()
    print("📧 E-mail enviado via Outlook.")
