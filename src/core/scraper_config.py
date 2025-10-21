# core/scraper_config.py
from pydantic import BaseModel


class ScraperTimeouts(BaseModel):
    """Timeout configurations for web scraping (shared across all ISPs)"""

    login_wait: int = 5
    page_load_wait: int = 7
    element_wait: int = 2
    post_action_delay: float = 0.5


# Shared timeout configuration
timeouts = ScraperTimeouts()
