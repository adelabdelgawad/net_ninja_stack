import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Any, Dict, List

import aiosmtplib
from jinja2 import Environment, Template

from core.config import get_settings
from db.schema import ResultSchema

logger = logging.getLogger(__name__)

settings = get_settings()


async def render_html(template: Template, context: Dict[str, Any]) -> str:
    """
    Render HTML content using a Jinja2 template and context data.

    Args:
        template (Template): The Jinja2 template to render.
        context (Dict[str, Any]): The context data for rendering the template.

    Returns:
        str: The rendered HTML content.
    """
    try:
        html_content = template.render(context)
        logger.debug("HTML content successfully rendered.")
        return html_content
    except Exception as e:
        logger.error(f"Error rendering HTML content: {e}")
        raise


# Define your HTML template as a string (this could be a simplified or full version)
html_template_string = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dynamic Table</title>
    <style>
        body { font-family: Arial, sans-serif; }
        .table-container { margin: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #dddddd; text-align: left; padding: 8px; }
        th { background-color: #ffa500; color: white; text-align: center; }
        .header-row th { text-align: center; }
        .data-row td { text-align: center; }
        .high-usage { background-color: #ffcccc !important; }
        .low-balance { background-color: #ffeb99 !important; }
    </style>
</head>
<body>
    <div class="table-container">
        <table>
            <thead>
                <tr class="header-row">
                    <th colspan="4">LineBase Information</th>
                    <th colspan="2">Speedtest</th>
                    <th colspan="4">Quota Results</th>
                </tr>
                <tr>
                    <th>Number</th>
                    <th>Name</th>
                    <th>ISP</th>
                    <th>Description</th>
                    <th>Download</th>
                    <th>Upload</th>
                    <th>Used</th>
                    <th>Remaining</th>
                    <th>Renewal Date</th>
                    <th>Balance</th>
                </tr>
            </thead>
            <tbody>
                {% for item in data %}
                    {% set usage_percentage = item.usage_percentage if item.usage_percentage is not none else 0 %}
                    <tr class="data-row" 
                        style="{% if usage_percentage > 90 %}background-color: #ffcccc;{% elif usage_percentage > 75 %}background-color: #ffeb99;{% endif %}">
                        <td>{{ item.line_number if item.line_number is not none else '' }}</td>
                        <td>{{ item.name if item.name is not none else '' }}</td>
                        <td>{{ item.isp_name if item.isp_name is not none else '' }}</td>
                        <td>{{ item.description if item.description is not none else '' }}</td>
                        <td>{{ item.download_speed }} Mbps</td>
                        <td>{{ item.upload_speed }} Mbps</td>
                        <td>{{ item.data_used }} ({{ item.usage_percentage }}%)</td>
                        <td>{{ item.data_remaining }} GB</td>
                        <td>{{ item.renewal_date }}</td>
                        <td>{{ item.balance }} LE</td>
                    </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
"""


async def send_email(
    line_results: List[ResultSchema], recipients_list: List[str]
) -> None:
    """
    Compose and send an email with an HTML body using SMTP.

    Args:
        lines (List[Line]): List of Line objects to include in the email.

    Raises:
        aiosmtplib.SMTPException: If there is an error sending the email.
    """
    logger.info("Preparing to send email.")

    if not line_results:
        raise Exception("No Results Found")

    # Retrieve SMTP and email configurations from environment variables
    smtp_host = settings.email.server
    smtp_port = settings.email.port
    smtp_user = settings.email.username
    smtp_password = settings.email.password
    sender_elias = settings.email.sender_alias
    email_subject = settings.email.subject
    cc_records = settings.email.cc_address

    # Load the template from the string
    env = Environment()
    template = env.from_string(html_template_string)

    # Convert LineResult objects to dictionaries for template rendering
    context_data = {"data": [line.model_dump() for line in line_results]}

    # Render the template with the context data
    html_body = await render_html(template, context_data)

    # Create a multipart email message
    message = MIMEMultipart("alternative")
    message["Subject"] = email_subject
    message["From"] = formataddr((sender_elias, smtp_user))
    message["To"] = ", ".join(recipients_list)
    if cc_records:
        cc_list = [rec.recipient for rec in cc_records]
        message["CC"] = ", ".join(cc_list)

    # Attach the HTML body to the email
    message.attach(MIMEText(html_body, "html"))

    try:
        # Send the email using aiosmtplib
        await aiosmtplib.send(
            message,
            hostname=smtp_host,
            port=smtp_port,
            use_tls=True,
            start_tls=False,
            username=smtp_user,
            password=smtp_password,
            validate_certs=False,
        )
        logger.info("Email sent successfully.")
        return True
    except aiosmtplib.SMTPException as smtp_error:
        logger.error(f"Failed to send email: {smtp_error}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred while sending email: {e}")
        raise
