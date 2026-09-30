-- SQLBook: Code
-- DDl for the trivia database

-- Drop the tables if they already exist in the database so we do not get errors
DROP TABLE IF EXISTS submission_history;
DROP TABLE IF EXISTS leaderboard;
DROP TABLE IF EXISTS removed_players;
DROP TABLE IF EXISTS trivia_questions_indexed;
DROP TABLE IF EXISTS trivia_questions;
DROP TABLE IF EXISTS user_info;

-- Create a table to store the questions data downloaded and cleaned up from 
-- the open trivia website. The primary key of this table is question_id, which 
-- is unique for each question
CREATE TABLE trivia_questions (
    question_id    CHAR(7),               -- ID for each question, each 7 chars 
    category       VARCHAR(100) NOT NULL, -- Question category (sports, etc ...)
    question_type  VARCHAR(10)  NOT NULL, -- Specifies multiple or True/False
    difficulty     VARCHAR(10)  NOT NULL, -- Specifies easy/medium/hard 
    question       TEXT         NOT NULL, -- The actual question
    correct_answer CHAR(1)      NOT NULL, -- The id (A, B, C, D) of correct ans
    A              VARCHAR(100) NOT NULL, -- Answer choice a
    B              VARCHAR(100) NOT NULL, -- Answer choice b 
    C              VARCHAR(100) NOT NULL, -- Answer choice c 
    D              VARCHAR(100) NOT NULL, -- Answer choice d 

    PRIMARY KEY (question_id)
);

CREATE TABLE trivia_questions_indexed (
    question_id    CHAR(7),               -- ID for each question, each 7 chars 
    category       VARCHAR(100) NOT NULL, -- Question category (sports, etc ...)
    question_type  VARCHAR(10)  NOT NULL, -- Specifies multiple or True/False
    difficulty     VARCHAR(10)  NOT NULL, -- Specifies easy/medium/hard 
    question       TEXT         NOT NULL, -- The actual question
    correct_answer CHAR(1)      NOT NULL, -- The id (A, B, C, D) of correct ans
    A              VARCHAR(100) NOT NULL, -- Answer choice a
    B              VARCHAR(100) NOT NULL, -- Answer choice b 
    C              VARCHAR(100) NOT NULL, -- Answer choice c 
    D              VARCHAR(100) NOT NULL, -- Answer choice d 

    PRIMARY KEY (question_id)
);

-- Table containing the user information
CREATE TABLE user_info (
    user_id CHAR(5), 
    -- Usernames are up to 20 characters.
    username VARCHAR(20),
    -- Salt will be 8 characters all the time, so we can make this 8.
    is_admin TINYINT NOT NULL,
    salt CHAR(8) NOT NULL,
    -- We use SHA-2 with 256-bit hashes.  MySQL returns the hash
    -- value as a hexadecimal string, which means that each byte is
    -- represented as 2 characters.  Thus, 256 / 8 * 2 = 64.
    -- We can use BINARY or CHAR here; BINARY simply has a different
    -- definition for comparison/sorting than CHAR.
    password_hash BINARY(64) NOT NULL, 

    PRIMARY KEY (user_id)
);

-- This table includes stats of all users that will be used to display the 
-- public leaderboard. User ids in this case are all unique, so we can simply 
-- use that as our primary key
-- Note that number of games played and number of questions answered are not 
-- the same, since a game can contain multiple questions (kind of like a round)
CREATE TABLE leaderboard (
    user_id            CHAR(5) REFERENCES user_info(user_id),
    num_games_played   INTEGER DEFAULT 0, -- total number of games player played
    num_quest_answered INTEGER DEFAULT 0, -- total number of questions answered
    total_score        INTEGER DEFAULT 0, -- total accumulated points by user

    PRIMARY KEY (user_id)
);

-- This table includes submissions for the single player 
-- It will be used to display the player's private stats/leaderboard
CREATE TABLE submission_history (
    user_id              CHAR(5) REFERENCES user_info(user_id),
    submitted_timestamp  DATETIME NOT NULL, -- Date when score was submitted
    question_id          CHAR(7) NOT NULL 
                         REFERENCES trivia_questions(question_id) 
                         ON UPDATE CASCADE 
                         ON DELETE CASCADE, -- id of question answered, foreign
    user_answer          CHAR(1),           -- Choices A,B,C,D that user input
    points_earned        INTEGER NOT NULL,  -- Points earned for the question
    points_possible      INTEGER NOT NULL,  -- Total number questions answered

    -- Here we are using both user_id and submitted_timestamp as the primary 
    -- key, since a single user may have multiple submissions, but they cannot
    -- have multiple submissions at the same time (up to milliseconds)
    PRIMARY KEY (user_id, submitted_timestamp)
);

-- Table to keep track of players that have been removed by the admin
CREATE TABLE removed_players(
    user_id             CHAR(5) REFERENCES user_info(user_id), 
    username            VARCHAR(20) REFERENCES user_info(username)
                            ON DELETE CASCADE 
                            ON UPDATE CASCADE,
    removed_timestamp   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, 
    num_quest_answered  INTEGER NOT NULL, -- The number of questions answered
                                          -- by the player, this is not a 
                                          -- foreign key because an entry is not 
                                          -- put into the table until the player
                                          -- is removed 
    total_score         INTEGER NOT NULL, -- total score of player before being
                                          -- removed, not a foreign key for same
                                          -- reason as above

    PRIMARY KEY (user_id)
);

-- Create an index on the category for trivia_questions_indexed
CREATE INDEX id_correct_answer ON trivia_questions_indexed(correct_answer);

-- Commands used to test the efficiency of indexes
-- SET profiling=1;
-- SELECT * FROM trivia_questions WHERE correct_answer='A';
-- SELECT * FROM trivia_questions_indexed WHERE correct_answer='A';

-- SHOW PROFILES;

-- EXPLAIN SELECT * FROM trivia_questions_indexed WHERE correct_answer='D';