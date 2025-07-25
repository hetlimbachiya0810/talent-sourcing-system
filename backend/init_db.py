import asyncio
import logging
from db.database import init_db



async def main():
    try:
        """Initialize the database tables asynchronously"""
        print("Creating database tables...")
        await init_db()
        print("Tables created successfully!")
    except Exception as e:
        logging.error(f"Error creating tables: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())