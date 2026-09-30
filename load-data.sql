-- SQLBook: Code
-- SQL with load statements to load your database

-- Load the trivia data from the cleaned up csv file into questions table
LOAD DATA LOCAL INFILE './data/trivia_questions_combined.csv' 
INTO TABLE trivia_questions 
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE './data/trivia_questions_combined.csv' 
INTO TABLE trivia_questions_indexed
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;


-- Load user info csv
LOAD DATA LOCAL INFILE './data/accounts.csv' 
INTO TABLE user_info 
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

-- Load user info csv
LOAD DATA LOCAL INFILE './data/leaderboard.csv' 
INTO TABLE leaderboard
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

-- Load user info csv
LOAD DATA LOCAL INFILE './data/submission_history.csv' 
INTO TABLE submission_history
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

