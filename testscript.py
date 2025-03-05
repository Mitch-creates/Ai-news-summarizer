from sqlalchemy import create_engine, text
from database.db_operations import initialize_database, Base, engine
# Initialize database (ensure tables are created)
def test_database_setup():
    
    # Ensure tables are created
    Base.metadata.create_all(engine)
    
    with engine.connect() as connection:
        result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        tables = result.fetchall()
        print("Tables in the database:", tables)

if __name__ == "__main__":
    test_database_setup()