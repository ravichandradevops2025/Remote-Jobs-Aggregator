import os
import asyncpg
from typing import Optional
from supabase import create_client, Client

# Global database connection
_db_pool: Optional[asyncpg.Pool] = None
_supabase: Optional[Client] = None

async def get_database():
    global _db_pool
    
    if os.getenv("SUPABASE_URL"):
        # Use Supabase
        global _supabase
        if not _supabase:
            _supabase = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            )
        return SupabaseAdapter(_supabase)
    else:
        # Use direct PostgreSQL connection
        if not _db_pool:
            database_url = os.getenv("DATABASE_URL")
            _db_pool = await asyncpg.create_pool(database_url)
        return PostgresAdapter(_db_pool)

class SupabaseAdapter:
    def __init__(self, client: Client):
        self.client = client
    
    async def fetch_all(self, query: str, params: list = None):
        # For now, use basic Supabase queries
        response = self.client.table('jobs').select('*').execute()
        return response.data
    
    async def fetch_one(self, query: str, params: list = None):
        response = self.client.table('jobs').select('*').limit(1).execute()
        return response.data[0] if response.data else None
    
    async def execute(self, query: str, params: list = None):
        # For inserts, use Supabase SDK
        pass

class PostgresAdapter:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def fetch_all(self, query: str, params: list = None):
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *(params or []))
    
    async def fetch_one(self, query: str, params: list = None):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *(params or []))
    
    async def execute(self, query: str, params: list = None):
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *(params or []))

async def create_tables():
    """Create database tables if they don't exist"""
    db = await get_database()
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS jobs (
        id VARCHAR(255) PRIMARY KEY,
        title VARCHAR(500) NOT NULL,
        company VARCHAR(255) NOT NULL,
        description TEXT,
        apply_url VARCHAR(1000) NOT NULL UNIQUE,
        location VARCHAR(255),
        remote BOOLEAN DEFAULT false,
        salary_min INTEGER,
        salary_max INTEGER,
        domain VARCHAR(50) DEFAULT 'Other',
        source VARCHAR(100) NOT NULL,
        source_job_id VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_jobs_domain ON jobs(domain);
    CREATE INDEX IF NOT EXISTS idx_jobs_remote ON jobs(remote);
    CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);
    CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
    """
    
    await db.execute(create_table_sql)