-- This file contains all queries that are used in the python app-client and 
-- app-admin scripts

-- First drop some of the temporary tables that are created in this file so we
-- prevent the possibility of errors occuring when this file is run. Note that 
-- we use temporary tables in this code to make the code slightly cleaner, but 
-- in the python code, it was quite difficult to make temporary tables, so they
-- were just included as subqueries instead
DROP TABLE IF EXISTS ranked_leaderboard;
DROP TABLE IF EXISTS count_table;

-- This query calls the function authenticate written in setup-routines.sql and
-- checks whether the given user id and password are valid/in the database. 
-- Returns 1 if it is, and 0 if not. The example below is in the database, so 
-- it will return a 1
SELECT authenticate('QPOSD', 'qpassword1'); 

-- Query to get the username (different from user id) from a given user_id
-- Expected output: james2
SELECT username
FROM user_info
WHERE user_id='QPOSD'; 

-- Create a temporary to store the ranked version of the leaderboard. Here we
-- are using dense_rank so everybody that has the same total score will have 
-- the same rank, and that the rank increments like 1, 2, 3, ... instead of by 
-- how many people have that rank (like 1, 1, 3, 3, 3, 6, ...)
CREATE TEMPORARY TABLE ranked_leaderboard
    SELECT
        DENSE_RANK() OVER 
            (ORDER BY total_score DESC) total_rank,
        user_id,
        num_games_played,
        num_quest_answered,
        total_score
    FROM leaderboard
    ORDER BY total_rank ASC;

-- Query to select the top five players and their stats with the highest 
-- total_score (note this is a variable the players can choose in the python 
-- script)
SELECT 
    total_rank AS rank, 
    user_id, 
    username, 
    num_games_played, 
    num_quest_answered, 
    total_score
FROM user_info NATURAL JOIN ranked_leaderboard
ORDER BY total_score DESC 
LIMIT 5;

-- Query to get the window ranking for a given player, i.e. look in the 
-- leaderboard and get the player's ranking along with the ranking of another 
-- player that has ranking one larger than the user's ranking. This is slightly
-- complicated because there may be many people with the same ranking, so we 
-- cannot just get the row above (though this in mysql is also a little 
-- complicated) and we also do not know the score of the player when querying, 
-- so we cannot just get the player with score + 1
SELECT 
    l.total_rank, 
    l.user_id, 
    u.username, 
    l.num_games_played, 
    l.num_quest_answered, 
    l.total_score
FROM 
    ranked_leaderboard AS l LEFT JOIN 
    ranked_leaderboard AS r NATURAL JOIN 
    user_info as u
ON l.user_id = r.user_id
WHERE 
    r.total_score = 
    (SELECT DISTINCT MIN(r2.total_score) as min_total
    FROM leaderboard AS r2 
    WHERE r2.total_score > 
        (SELECT total_score FROM leaderboard WHERE user_id='QPOSD')
    GROUP BY l.user_id) 
    OR r.user_id='QPOSD'
    -- only get the player's and one ofthe other ones
ORDER BY total_score ASC LIMIT 2; 

-- Get one question id, question, correct answer, difficult, and answer choices
-- A, B, C, D from the trivia questions database for a random category and 
-- specified difficulty
SELECT question_id, question, correct_answer, difficulty, A, B, C, D
FROM trivia_questions_indexed
WHERE difficulty='easy'
ORDER BY RAND()
LIMIT 1;

-- Get one question id, question, correct answer, difficult, and answer choices
-- A, B, C, D from the trivia questions database for a random category and 
-- random difficulty
SELECT question_id, question, correct_answer, difficulty, A, B, C, D
FROM trivia_questions_indexed
ORDER BY RAND()
LIMIT 1;

-- Get one question id, question, correct answer, difficult, and answer choices
-- A, B, C, D from the trivia questions database for specified category and 
-- specified difficulty
SELECT question_id, question, correct_answer, difficulty, A, B, C, D
FROM trivia_questions_indexed
WHERE category='Animals' AND difficulty='easy'
ORDER BY RAND()
LIMIT 1;

-- Get one question id, question, correct answer, difficult, and answer choices
-- A, B, C, D from the trivia questions database for specified category but 
-- random difficulty
SELECT question_id, question, correct_answer, difficulty, A, B, C, D
FROM trivia_questions_indexed
WHERE category='Animals'
ORDER BY RAND()
LIMIT 1;

-- Query to get the column names for a given table. In this example, we are 
-- using the table leaderboard, but can be specified in python script
SELECT COLUMN_NAME 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME='leaderboard';

-- Query to get the submission history based on a given uid. In this example, 
-- we are using QPOSD, but can be specified in python script
SELECT *
FROM submission_history
WHERE user_id='QPOSD'; 

-- Call the avg_submit_interval function to calculate the average time between
-- question submissions in seconds. The result is used when displaying user 
-- stats. In this example, we are using QPOSD, but can be specified in python 
-- script
SELECT avg_submit_interval('QPOSD')

-- Get the number of questions answered and total score of a given user. In 
-- this example, we are using QPOSD, but can be specified in python script
SELECT num_quest_answered, total_score 
FROM leaderboard
WHERE user_id='QPOSD'; 

-- Create temporary table that groups the submissions based on category counts, 
-- will be used to give stats to the user of their favorite categories
CREATE TEMPORARY TABLE count_table
    SELECT COUNT(category) AS category_counts, category
    FROM trivia_questions NATURAL JOIN submission_history
    WHERE user_id='BHDQC'
    GROUP BY category
    ORDER BY COUNT(category) DESC;

SELECT * FROM count_table;

-- Get all the categories that have the category count equaling the max number
-- of category counts. This allows us to get all the names of categories that 
-- have the same number of category counts that are maximum, allowing for ties
SELECT category 
FROM count_table
WHERE category_counts = 
    (SELECT MAX(category_counts) 
     FROM count_table);

-- Query to get the full leaderboard. Note that this option is only available to
-- the admin, and that clients are only allowed to see the top 5 plus their own
-- ranking
SELECT user_id, username, num_games_played, num_quest_answered, total_score
FROM user_info NATURAL JOIN leaderboard 
ORDER BY total_score DESC;

-- Query to delete a user from the user_info database. This query/option is 
-- again only available to the admin if a a player breaks a rule and has to be
-- removed from the game. Note that this delete statement will call the 
-- trigger, which will also delete the user from the leaderboard and add their 
-- information to the removed_players table
DELETE FROM user_info WHERE user_id='BHDQC';

-- Query to view the players that have been removed
SELECT *
FROM removed_players
