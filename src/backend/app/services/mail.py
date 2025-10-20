from jinja2 import Environment
import os
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
import aiosmtplib
from jinja2 import Template
from db.schema import LineResult, Line
from db.crud import read_email_recipients, read_last_result
# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def get_env_variable(key: str, default: str = "") -> str:
    """
    Retrieve an environment variable or return a default value if not found.

    Args:
        key (str): The environment variable key.
        default (str, optional): The default value to return if the key is not found. Defaults to "".

    Returns:
        str: The value of the environment variable or the default value.
    """
    value = os.getenv(key, default)
    if not value:
        logger.warning(f"Environment variable '{key}' is not set.")
    return value


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
    lines: List[Line] = None
) -> None:
    """
    Compose and send an email with an HTML body using SMTP.

    Args:
        lines (List[Line]): List of Line objects to include in the email.

    Raises:
        aiosmtplib.SMTPException: If there is an error sending the email.
    """
    logger.info("Preparing to send email.")

    if not lines:
        raise Exception("No Lines Found")

    line_results: List[LineResult] = [await read_last_result(line.id) for line in lines if lines]

    if not line_results:
        raise Exception("No Results Found")

    # Retrieve SMTP and email configurations from environment variables
    smtp_host = get_env_variable("SMTP_HOST")
    smtp_port_str = get_env_variable(
        "SMTP_PORT", "587")  # Default to 587 if not set
    try:
        smtp_port = int(smtp_port_str)
    except ValueError:
        logger.error(f"Invalid SMTP_PORT value: '{
                     smtp_port_str}'. Must be an integer.")
        raise

    smtp_user = get_env_variable("SMTP_USER")
    smtp_password = get_env_variable("SMTP_PASSWORD")
    sender_elias = get_env_variable("SENDER_ALIAS")
    email_subject = get_env_variable("SUBJECT", "No Subject")
    recipient_records = await read_email_recipients(1)
    cc_records = await read_email_recipients(2)

    if recipient_records:
        recipients = [rec.recipient for rec in recipient_records]

        # Load the template from the string
        env = Environment()
        template = env.from_string(html_template_string)

        # Convert LineResult objects to dictionaries for template rendering
        context_data = {
            "data": [line.model_dump() for line in line_results]
        }

        # Render the template with the context data
        html_body = await render_html(template, context_data)

        # Create a multipart email message
        message = MIMEMultipart("alternative")
        message["Subject"] = email_subject
        message["From"] = formataddr((sender_elias, smtp_user))
        message["To"] = ", ".join(recipients)
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
                validate_certs=False  # Consider setting to True in production
            )
            logger.info("Email sent successfully.")
            return True
        except aiosmtplib.SMTPException as smtp_error:
            logger.error(f"Failed to send email: {smtp_error}")
            raise
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while sending email: {e}")
            raise
    else:
        logger.error("No recipients found.")
        return False
