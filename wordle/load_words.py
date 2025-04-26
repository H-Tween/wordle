from sqlalchemy import create_engine, text
from prefect.blocks.system import Secret

# Get the database URL from Prefect block
secret_block = Secret.load("database-url")

# The URL for the database is stored in a secret block in prefect.
DATABASE_URL = secret_block.get()

# Sets up the database connection, essentially saying here is my database, get ready to create a connection.
engine = create_engine(DATABASE_URL)

# Function for initialising the database
def load_words():
    # Removes spaces and converts the words to lowercase in words.txt and only keeps the words if they are exactly 5 letters
    with open("words.txt") as f:
        words = [line.strip().lower() for line in f if len(line.strip()) == 5]

    if not words:
        raise ValueError("No 5-letter words found in words.txt")

    print(f"Preparing to insert {len(words)} words...")

    # Inserts the words into the valid_words table
    with engine.begin() as conn:
        print(f"Inserting {len(words)} words...")
        conn.execute(text("""
            DELETE 
            FROM valid_words 
            WHERE CHAR_LENGTH(word) != 5
        """))

        conn.execute(
            text("""
            INSERT 
            IGNORE 
            INTO valid_words (word) 
            VALUES (:word)
        """),
        [{"word": w} for w in words]
        )

    print("All valid words loaded into database.")

if __name__ == "__main__":
    load_words()