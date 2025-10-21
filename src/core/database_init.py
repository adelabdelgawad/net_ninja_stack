# core/database_init.py
import logging
import sys
from pathlib import Path

from core.config import settings

logger = logging.getLogger(__name__)


async def check_and_initialize_database() -> bool:
    """
    Check if database exists and initialize if needed.

    Returns:
        True if database was newly created, False if it already existed.
    """
    db_path = Path("app.db")

    if not db_path.exists():
        logger.warning(f"⚠️  Database file not found: {db_path}")
        logger.info("🔧 Initializing database for the first time...")

        # Delete old encryption key if exists (fresh start)
        secret_key_path = Path(".secret.key")
        if secret_key_path.exists():
            logger.info("🔑 Removing old encryption key for fresh start...")
            secret_key_path.unlink()
            logger.info("✓ Old encryption key removed")

        try:
            # Import and run setup
            from db.setup_database import setup_database

            await setup_database()

            logger.info("✅ Database initialized successfully!")
            logger.info(f"📁 Database location: {db_path.absolute()}")
            logger.info(
                "🔑 New encryption key will be generated on first password encryption"
            )
            logger.info(
                "ℹ️  Please add your ISP lines to the database before running again."
            )
            logger.info(
                "ℹ️  You can use the admin interface or database management tools."
            )
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            logger.error(
                "Please run 'python setup_database.py' manually to set up the database."
            )
            sys.exit(1)
    else:
        logger.info(f"✓ Database found: {db_path}")
        return False


async def encrypt_unencrypted_passwords():
    """Encrypt any unencrypted passwords in the database"""
    from db.database import get_session
    from db.models.line_model import LineModel
    from services.line_service import LineService

    lines = await LineService.get_all_lines()

    async with get_session() as session:
        line_model = LineModel(session)

        for line in lines:
            # Check if password is encrypted
            if line.portal_password and not line.portal_password.startswith(
                "gAAAAA"
            ):
                # Encrypt and update the password in the line object
                line.set_password(line.portal_password)
                # Update the record in the DB
                await line_model.update(
                    line.id, {"portal_password": line.portal_password}
                )
                logger.info(f"Encrypted password for line: {line.name}")
