"""Alembic environment configuration - uses asyncpg directly for Neon compatibility."""
from __future__ import annotations

import asyncio
import os
import ssl
import sys
from logging.config import fileConfig

import asyncpg
from alembic import context

# Allow importing src package from apps/api/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config import settings  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None


def _build_dsn() -> str:
    """Return a plain asyncpg DSN from settings.DATABASE_URL."""
    url = settings.DATABASE_URL
    # Strip SQLAlchemy driver prefix
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    # Strip sslmode query param - SSL handled via ssl_ctx below
    if "sslmode" in url:
        from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
        parsed = urlparse(url)
        params = {k: v for k, v in parse_qs(parsed.query).items() if k != "sslmode"}
        url = urlunparse(parsed._replace(query=urlencode(params, doseq=True)))
    return url


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    dsn = _build_dsn()
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    conn = await asyncpg.connect(dsn=dsn, ssl=ssl_ctx)
    try:
        def do_migrations(sync_conn):
            context.configure(connection=sync_conn, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()

        # Alembic needs a synchronous DBAPI-2 style connection.
        # With asyncpg we wrap it using the migration_context run_sync helper.
        async with conn.transaction():
            await conn.execute("SELECT 1")  # verify connection

        # Use Alembic's native asyncpg support via a simple wrapper
        import io
        from alembic.runtime.migration import MigrationContext
        from alembic.operations import Operations

        # Get the current revision
        rev_table_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='alembic_version')"
        )
        current_rev = None
        if rev_table_exists:
            row = await conn.fetchrow("SELECT version_num FROM alembic_version LIMIT 1")
            current_rev = row["version_num"] if row else None

        # Run each migration script manually
        script = context.script
        revisions = list(script.walk_revisions())
        revisions.reverse()  # oldest first

        for rev in revisions:
            if current_rev and rev.revision <= current_rev:
                continue
            # Execute the upgrade SQL
            upgrade_fn = rev.module.upgrade
            # We need to run it with a connection context
            mc = MigrationContext.configure(conn, opts={"as_sql": False})
            ops = Operations(mc)
            # Run within transaction
            async with conn.transaction():
                # Temporarily monkey-patch to use our async conn
                import alembic.op as alembic_op
                old_ops = alembic_op._proxy
                alembic_op._proxy = ops
                try:
                    upgrade_fn()
                finally:
                    alembic_op._proxy = old_ops
                # Update alembic_version
                if not rev_table_exists:
                    await conn.execute(
                        "CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)"
                    )
                    rev_table_exists = True
                await conn.execute(
                    "INSERT INTO alembic_version (version_num) VALUES ($1) ON CONFLICT (version_num) DO NOTHING",
                    rev.revision
                )
            current_rev = rev.revision
            print(f"  -> Applied revision {rev.revision}: {rev.doc}")
    finally:
        await conn.close()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
