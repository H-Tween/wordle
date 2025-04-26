from prefect import flow, task
from prefect.blocks.system import Secret
from sqlalchemy import create_engine, text
from datetime import datetime

# Get the database URL from Prefect block
secret_block = Secret.load("database-url")

# The URL for the database is stored in a secret block in prefect.
DATABASE_URL = secret_block.get()

# Sets up the database connection, essentially saying here is my database, get ready to create a connection.
engine = create_engine(DATABASE_URL)

# Gets a random word for the daily wordle
@task
def get_random_word():
    # Creates a live session with the database.
    with engine.connect() as conn:
        # This gets a word from the database which isn't the same as the daily word (A previously used word).
        result = conn.execute(text("""
            SELECT word
            FROM valid_words
            WHERE word NOT IN (SELECT word FROM daily_word)
            ORDER BY RAND()
            LIMIT 1
        """))
        word = result.scalar()

        # If the database doesn't get a word from the database, this means all the words have been selected, so it returns none.
        if word is None:
            print("All words used! Resetting...")

            # The daily word database needs to be cleared to allow for a fresh reset of words.
            conn.execute(text("DELETE FROM daily_word"))

            # Get new word randomly to reset the first selection statement by putting the first word into daily_word.
            result = conn.execute(text("""
                SELECT word 
                FROM valid_words 
                ORDER BY RAND() 
                LIMIT 1
            """))
            word = result.scalar()

        print(f"Selected word: {word}")
        return word

# Stores the daily word in the database for a record and also to stop duplication (the same word being picked again until all words have been gone through)
@task
def store_daily_word(word: str):
    # Gets the current data to be stored alongside the daily word so the wordle script can pull the daily word from the database.
    today = datetime.utcnow().date()
    # Opens a transactional connection so the database can be altered.
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO daily_word (date, word)
            VALUES (:date, :word)
            ON DUPLICATE KEY UPDATE word = :word
        """),
        {"date": today, "word": word}
        )
        print(f"Stored word for {today}: {word}")

@flow
def daily_word_update():
    word = get_random_word()
    store_daily_word(word)

# Test locally (Prefect will run the flow statement, not the main statement to run the script).
if __name__ == "__main__":
    daily_word_update()