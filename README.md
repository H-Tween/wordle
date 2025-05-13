# Wordle
## This application can only be run by myself currently as it takes database credentials and Prefect credentials using my personal login. 

### Steps to run
1. The database must be running in google cloud (This is how the daily word is retrieved)
2. Run prefect cloud login (Used to get the cloud DB URL secret)
3. Run main.py locally

### Steps to update the database manually

1. The database must be running in google cloud (This is how the daily word is retrieved)
2. Run prefect cloud login (Used to get the cloud DB URL secret)
3. A prefect worker has to be running to pick up the work from prefect. (Script for updating the database with the daily word)
4. Must be signed into the same prefect account locally to run it locally.
5. Run daily_word_prefect_script.py
