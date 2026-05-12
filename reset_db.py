import asyncio
from app.db.session import engine, init_db
from sqlalchemy import text

async def reset_database():
    print("[Reset] Connecting to database...")
    try:
        async with engine.begin() as conn:
            print("[Reset] Dropping table 'meetings'...")
            await conn.execute(text("DROP TABLE IF EXISTS meetings CASCADE"))
            print("[Reset] Table dropped successfully.")
        
        print("[Reset] Re-initializing database...")
        await init_db()
        print("[Reset] Database reset complete!")
    except Exception as e:
        print(f"[Reset] Error: {e}")

if __name__ == "__main__":
    asyncio.run(reset_database())
