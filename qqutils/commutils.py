import logging
from typing import List
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os

logger = logging.getLogger(__name__)


def send_mail(
        subject: str ,
        body: str,
        recipients: List[str],
        you: str,
        your_password: str,
        *,
        cc: List[str] = None,
        bcc: List[str] = None,
        attachments=None,
        smtp_server='smtp.gmail.com',
        smtp_port=0,
):
    logger.info(f"sending mail to {recipients} (cc:{cc}, bcc:{bcc}) on behalf of '{you}' via <{smtp_server}>, subject: '{subject}', {len(attachments or [])} attachments:{attachments}")
    msg = MIMEMultipart()
    msg['From'] = you
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = subject
    if cc:
        msg['Cc'] = ', '.join(cc)
    if bcc:
        msg['Bcc'] = ', '.join(bcc)
    msg.attach(MIMEText(body, 'html'))

    for attachment in attachments or []:
        with open(attachment, "rb") as f:
            attachment_basename = os.path.basename(attachment)
            part = MIMEApplication(f.read(), Name=attachment)
            part['Content-Disposition'] = f'attachment; filename="{attachment_basename}"'
            msg.attach(part)

    server = smtplib.SMTP_SSL(smtp_server, smtp_port)
    server.login(you, your_password)
    text = msg.as_string()
    server.sendmail(you, recipients, text)
    server.quit()
