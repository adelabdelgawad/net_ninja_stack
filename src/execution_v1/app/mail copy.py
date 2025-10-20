import os
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import aiosmtplib
from email.utils import formataddr
from jinja2 import Environment, FileSystemLoader
from app.logger import logger
# Load environment variables from .env file
load_dotenv()


async def generate_html(data):
    file_loader = FileSystemLoader("templates")
    env = Environment(loader=file_loader)
    template = env.get_template("result.html")
    return template.render(data=data)


async def send_email(subject, recipient, cc, data):
    try:
        await logger.info("1", "Sending Email")
        # Email configuration from environment variables
        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = os.getenv("SMTP_PORT")
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        sender_email = os.getenv("SEND_EMAIL")
        # Create a multipart message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg['From'] = formataddr(("NetBOT", sender_email))
        msg["To"] = ", ".join(recipient)
        msg["CC"] = cc

        html_body = await generate_html(data)
        # Attach the HTML body
        msg.attach(MIMEText(html_body, "html"))

        # Send the email using aiosmtplib
        await aiosmtplib.send(
            msg,
            hostname=smtp_host,
            port=smtp_port,
            use_tls=True,
            start_tls=False,
            username=smtp_user,
            password=smtp_password,
        )
        await logger.info("1", "Sent Succeed")
        
    except Exception as e:
        await logger.error("1", str(e))



