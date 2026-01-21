import asyncpg
from pathlib import Path
import structlog

logger = structlog.get_logger()


class Database:
    """PostgreSQL database connection manager"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: asyncpg.Pool = None
    
    async def connect(self):
        """Create database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info("Database connection pool created")
        except Exception as e:
            logger.error("Failed to create database pool", error=str(e))
            raise
    
    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    async def is_connected(self) -> bool:
        """Check if database is connected"""
        if not self.pool:
            return False
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False
    
    async def run_migrations(self):
        """Run SQL migrations from migrations directory"""
        migrations_dir = Path(__file__).parent.parent / "migrations"
        
        if not migrations_dir.exists():
            logger.warning("Migrations directory not found", path=str(migrations_dir))
            return
        
        # Get all .sql files sorted
        migration_files = sorted(migrations_dir.glob("*.sql"))
        
        for migration_file in migration_files:
            logger.info("Running migration", file=migration_file.name)
            
            try:
                sql = migration_file.read_text()
                async with self.pool.acquire() as conn:
                    await conn.execute(sql)
                logger.info("Migration completed", file=migration_file.name)
            except Exception as e:
                logger.error("Migration failed", file=migration_file.name, error=str(e))
                # Continue with other migrations (tables might already exist)
    
    async def fetch(self, query: str, *args):
        """Execute query and fetch all results"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args):
        """Execute query and fetch single row"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetchval(self, query: str, *args):
        """Execute query and fetch single value"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    async def execute(self, query: str, *args):
        """Execute query without returning results"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
