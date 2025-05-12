from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, timedelta
import os
import enchant
from sqlalchemy import create_engine, text
from prefect.blocks.system import Secret

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Needed for sessions (24 random bytes)

# Get the database URL from Prefect block
secret_block = Secret.load("database-url")

# The URL for the database is stored in a secret block in prefect.
DATABASE_URL = secret_block.get()

# Sets up the database connection, essentially saying here is my database, get ready to create a connection.
engine = create_engine(DATABASE_URL)

# Initialize dictionary checker
dictionary = enchant.Dict("en_GB")

# Select a new word daily
def get_daily_word():
    # Get current data to then be used to get the daily word.
    today = datetime.utcnow().date()
    # This gets a word from the database which isn't the same as the daily word (A previously used word).
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT word 
            FROM daily_word 
            WHERE date = :date
            """),
            {"date": today}
        )
        # Used to fetch the whole row of the daily word
        row = result.fetchone()
        # Returns the first column which is the daily word if the daily word exists, otherwise it returns None
        return row[0] if row else None

# Check guess feedback
def evaluate_guess(guess, target):
    # Set the beginning of the guess (Assume all character guesses are wrong, then they can be updated to correct if correct)
    result = ["absent"] * 5
    # Set the target word (daily word) to list of characters to be checked individually
    target_chars = list(target)
    # Set the guessed word (users guessed word) to list of characters to be checked individually
    guess_chars = list(guess)

    # First check - mark correct (green) letters
    for i in range(5):
        # If the letter guesses is the same as the daily word
        if guess_chars[i] == target_chars[i]:
            # Set the element in the array to correct
            result[i] = "correct"
            # Replaces the letter guessed with None to prevent the same letter being marked as correct again
            # Example, in the word "karma" and guessed "urban", because I guessed 'a', both A's would be marked correct even though there is only one A.
            target_chars[i] = None

    # Second check: mark present (yellow) letters
    for i in range(5):
        # If the letter is absent (no correct letters) and the letter is in the target character array
        if result[i] == "absent" and guess_chars[i] in target_chars:
            # Set the letter to present (yellow)
            result[i] = "present"
            # Finds the first occurrence of the letter guessed and marks that index as None to stop it being used again.
            # This is the same as Line 57, it prevents duplicate presents (yellow boxes)
            target_chars[target_chars.index(guess_chars[i])] = None

    return result

# Calculate time until the word updates in GMT timezone (UK) for display after the game finishes.
def get_time_until_next_word():
    now = datetime.utcnow()
    midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return int((midnight - now).total_seconds())


@app.route("/", methods=["GET", "POST"])
def index():
    # Get the daily word
    target = get_daily_word()
    # Initialise session variables, guesses to store the players guesses and current_input to store what the player is currently typing
    if "guesses" not in session:
        session["guesses"] = []
    if "current_input" not in session:
        session["current_input"] = ""

    # Set the messaging returning to empty and difficulty to normal.
    message = ""
    difficulty = session.get("difficulty", "normal")

    # Changes the amount of rows depending on difficulty
    difficulty_map = {
        "easy": 8,
        "normal": 6,
        "hard": 4
    }

    # Gets the current difficulty to set the maximum amount of guesses. It defaults to 6 (Normal)
    # This happens every time the game starts as it will always be default normal.
    max_guesses = difficulty_map.get(difficulty, 6)

    # For row animation
    animate_row = None

    # Processing a users submission
    # If the user submits the form (POST) and the player still has guesses left
    if request.method == "POST" and len(session["guesses"]) < max_guesses:
        # Gets the users input and sets all characters to lower
        guess = session["current_input"].lower()
        # Makes sure the guess is 5 letters
        # Currently redundant code as the player can't submit the form unless all 5 letters are entered as well as the next letters entered can't be submitted
        if len(guess) != 5:
            message = "Guess must be exactly 5 letters."
        # Checks if the guess is a real word
        elif not dictionary.check(guess):
            message = f"'{guess}' is not a recognized English word."
        else:
            # Gets the absent, present and correct letters.
            feedback = evaluate_guess(guess, target)
            # Appends the guess to the board
            session["guesses"].append((guess, feedback))
            # Sets the row which is going to be animated
            session["animate_row"] = len(session["guesses"]) - 1
            # Resets the users input for the next input
            session["current_input"] = ""
            session.modified = True
            # Checks if the word was guessed
            if guess == target:
                message = "You got it! 🎉"
            # Checks if the user ran out of guesses
            elif len(session["guesses"]) >= max_guesses:
                message = f"Out of guesses! The word was '{target}'."


    # elif len(session["guesses"]) >= max_guesses:
    #     message = f"Out of guesses! The word was '{target}'."

    # Deletes the animated row after using it.
    animate_row = session.pop("animate_row", None)
    # Sets the game_over to True if the player uses all their guesses or the last guess was correct
    game_over = len(session["guesses"]) >= max_guesses or (session["guesses"] and session["guesses"][-1][0] == target)
    # Gets the time until next daily word if the game is finished, otherwise it does nothing (Used for displaying next daily word time)
    next_word_time = get_time_until_next_word() if game_over else None

    # Renders the HTML template.
    return render_template(
        "index.html",
        guesses=session["guesses"],
        message=message,
        current_input=session["current_input"],
        animate_row=animate_row,
        game_over=game_over,
        difficulty = difficulty,
        max_guesses = max_guesses,
        next_word_time=next_word_time
    )

# Handle keyboard input from user
@app.route("/type", methods=["POST"])
def type_letter():
    # Initialise the current_input for the session
    if "current_input" not in session:
        session["current_input"] = ""

    # Get the current inputted key from the user
    key = request.form.get("key")
    # If the user backspaces, remove the letter from the current_input
    if key == "BACKSPACE":
        session["current_input"] = session["current_input"][:-1]
    # If the user presses enter it POSTS the request (code=307 ensures it stays a POST method)
    elif key == "ENTER":
        return redirect(url_for("index"), code=307)
    # Adds a letter to the current_input if the current_input is less than 5 characters and the key pressed is a letter from A-Z
    elif len(session["current_input"]) < 5 and key.isalpha():
        session["current_input"] += key.lower()

    session.modified = True
    return redirect(url_for("index"))

# Resets the board
@app.route("/reset")
def reset():
    session.pop("guesses", None)
    session.pop("current_input", None)
    return redirect(url_for("index"))

# Resets the board with difficulty level
@app.route("/set_difficulty/<level>")
def set_difficulty(level):
    if level in ["easy", "normal", "hard"]:
        session["difficulty"] = level
        session.pop("guesses", None)
        session.pop("current_input", None)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
