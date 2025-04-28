# wordle
Dissertation Project

### Steps to run
1. The database must be running in google cloud (This is how the daily word is retrieved)
2. Run main.py locally

### Steps to update the database

1. The database must be running in google cloud (This is how the daily word is retrieved)
2. A prefect worker has to be running to pick up the work from prefect. (Script for updating the database with the daily word)
3. Must be signed into the same prefect account locally to run it locally.
