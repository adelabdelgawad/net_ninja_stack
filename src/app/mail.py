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


# Updated HTML template aligned with ResultSchema field names
# Updated HTML template with centered text and proper coloring
html_template_string = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Line Results Report</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background-color: #f5f5f5; 
        }
        .table-container { 
            margin: 20px auto; 
            max-width: 1400px; 
            background-color: white; 
            padding: 20px; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
        }
        h1 { 
            color: #333; 
            text-align: center; 
            margin-bottom: 20px; 
        }
        table { 
            width: 100%; 
            border-collapse: collapse; 
        }
        th, td { 
            border: 1px solid #dddddd; 
            text-align: center; 
            vertical-align: middle;
            padding: 12px; 
        }
        th { 
            background-color: #ffa500; 
            color: white; 
            font-weight: bold; 
        }
        .header-row th { 
            text-align: center; 
            vertical-align: middle;
        }
        .data-row td { 
            text-align: center; 
            vertical-align: middle;
        }
        /* High usage: > 90% - Red background */
        tr.high-usage td { 
            background-color: #ffcccc !important; 
        }
        /* Medium usage: 75-90% - Yellow background */
        tr.medium-usage td { 
            background-color: #ffeb99 !important; 
        }
        /* Normal usage: < 75% - White background */
        tr.normal-usage td { 
            background-color: #ffffff !important; 
        }
        /* Hover effect */
        tbody tr:hover td { 
            opacity: 0.8; 
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="table-container">
        <h1>Internet Lines Usage Report</h1>
        <table>
            <thead>
                <tr class="header-row">
                    <th colspan="4">Line Information</th>
                    <th colspan="2">Speed Test</th>
                    <th colspan="5">Quota & Balance</th>
                </tr>
                <tr>
                    <th>Number</th>
                    <th>Name</th>
                    <th>ISP</th>
                    <th>Description</th>
                    <th>Download (Mbps)</th>
                    <th>Upload (Mbps)</th>
                    <th>Used</th>
                    <th>Usage %</th>
                    <th>Remaining (GB)</th>
                    <th>Renewal Date</th>
                    <th>Balance (LE)</th>
                </tr>
            </thead>
            <tbody>
                {% for item in data %}
                    {% set usage_percentage = item.usage_percentage if item.usage_percentage is not none else 0 %}
                    {% if usage_percentage > 90 %}
                        {% set row_class = "data-row high-usage" %}
                    {% elif usage_percentage > 75 %}
                        {% set row_class = "data-row medium-usage" %}
                    {% else %}
                        {% set row_class = "data-row normal-usage" %}
                    {% endif %}
                    <tr class="{{ row_class }}">
                        <td>{{ item.number if item.number is not none else 'N/A' }}</td>
                        <td>{{ item.name if item.name is not none else 'N/A' }}</td>
                        <td>{{ item.isp if item.isp is not none else 'N/A' }}</td>
                        <td>{{ item.description if item.description is not none else 'N/A' }}</td>
                        <td>{{ item.download if item.download is not none else 'N/A' }}</td>
                        <td>{{ item.upload if item.upload is not none else 'N/A' }}</td>
                        <td>{{ item.used if item.used is not none else 'N/A' }}</td>
                        <td><strong>{{ "%.1f"|format(item.usage_percentage) if item.usage_percentage is not none else '0.0' }}%</strong></td>
                        <td>{{ item.remaining if item.remaining is not none else 'N/A' }}</td>
                        <td>{{ item.renewal_date if item.renewal_date is not none else 'N/A' }}</td>
                        <td>{{ item.balance if item.balance is not none else 'N/A' }}</td>
                    </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
"""


async def send_email(
    subject: str,
    recipients_list: List[str],
    sender: str,
    line_results: List[ResultSchema],
) -> bool:
    """
    Compose and send an email with an HTML body using SMTP.

    Args:
        subject: Email subject line
        recipients_list: List of recipient email addresses
        sender: Sender email address
        line_results: List of ResultSchema objects to include in the email

    Returns:
        bool: True if email sent successfully, False otherwise

    Raises:
        aiosmtplib.SMTPException: If there is an error sending the email.
    """
    logger.info("Preparing to send email.")

    if not line_results:
        logger.error("No results found to send in email")
        raise ValueError("No Results Found")

    # Retrieve SMTP and email configurations
    smtp_host = settings.email.server
    smtp_port = settings.email.port
    smtp_user = settings.email.username
    smtp_password = settings.email.password
    sender_alias = settings.email.sender_alias
    cc_records = settings.email.cc_address

    # Load the template
    env = Environment()
    template = env.from_string(html_template_string)

    # Convert ResultSchema objects to dictionaries for template rendering
    context_data = {"data": [line.model_dump() for line in line_results]}

    # Render the template with the context data
    html_body = await render_html(template, context_data)

    logger.debug(
        f"Recipients: {recipients_list}, Type: {type(recipients_list)}"
    )

    # Create a multipart email message
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = formataddr((sender_alias, sender))
    message["To"] = ", ".join(recipients_list)
    if cc_records:
        message["CC"] = cc_records

    # Attach the HTML body to the email
    message.attach(MIMEText(html_body, "html"))

    try:
        # Send the email using aiosmtplib with correct settings for port 587
        await aiosmtplib.send(
            message,
            hostname=smtp_host,
            port=smtp_port,
            use_tls=False,  # For port 587, use STARTTLS not direct TLS
            start_tls=True,  # Enable STARTTLS for port 587
            username=smtp_user,
            password=smtp_password.get_secret_value(),
        )
        logger.info(
            f"Email sent successfully to {len(recipients_list)} recipients"
        )
        return True
    except aiosmtplib.SMTPException as smtp_error:
        logger.error(f"SMTP error while sending email: {smtp_error}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while sending email: {e}")
        raise
