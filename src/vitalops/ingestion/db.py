import psycopg
from vitalops.shared.config.settings import settings


def get_conn():
    return psycopg.connect(
        settings.database_url.replace("postgresql+psycopg://", "postgresql://")
    )
