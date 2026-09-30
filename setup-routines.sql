-- SQLBook: Code
-- SQL for stored routines and triggers

-- Drop procedures and functions if they already exist so we do not get errors
DROP PROCEDURE IF EXISTS sp_update_game;
DROP PROCEDURE IF EXISTS  sp_delete;
DROP TRIGGER IF EXISTS trg_delete;
DROP FUNCTION IF EXISTS avg_submit_interval;

-- Create a procedure that inserts a new submission into the submission history
-- table and updates the values on the leaderboard corresponding to the given 
-- user after each question is answered
DELIMITER !
CREATE PROCEDURE sp_update_game(uid CHAR(5), qid CHAR(7), ans CHAR(10), 
                                earned INT, poss INT, num_quest INT)
BEGIN 
    -- Insert submission into the submission history table with the user's id, 
    -- the current timestamp, the question id, the user's answer, the number of 
    -- points earned by the player, and the points possible for the question
    INSERT INTO submission_history VALUES 
                (uid, CURRENT_TIMESTAMP, qid, ans, earned, poss);

    -- Update the values in the leaderboard reflecting the changes made after 
    -- a question is answered
    UPDATE leaderboard 
        SET num_games_played = num_games_played+1,
        num_quest_answered = num_quest_answered+num_quest/2, 
        total_score = total_score + earned
        WHERE user_id=uid;
END !
DELIMITER ;

DELIMITER !

-- Create the trigger that is called after deleting on account
-- This trigger will update the removed_players table and also delete the user
-- from the leaderboard
CREATE TRIGGER trg_delete AFTER DELETE ON user_info FOR EACH ROW
BEGIN
    -- We also want to add the player and their stats into the removed players
    -- table so that we have a record of who broke the rules if needed later
    INSERT INTO removed_players 
    (user_id, username, num_quest_answered, total_score) 
    SELECT user_id, OLD.username as username, num_quest_answered, total_score
    FROM leaderboard
    WHERE user_id=OLD.user_id;

    -- Delete the user from the leaderboard since he/she has broken the rule
    -- and we no longer want them listed. We can keep them in submission history
    -- because that is only available to the admin and not the players
    DELETE FROM leaderboard WHERE user_id=OLD.user_id;

END!

DELIMITER ;

-- Create a function that calculates the average time between submissions for a 
-- given user, result is given in seconds
DELIMITER !
CREATE FUNCTION avg_submit_interval (uid CHAR(5)) 
RETURNS DOUBLE DETERMINISTIC
BEGIN
    -- Make variable declarations
    DECLARE count INT DEFAULT NULL;
    DECLARE min, max TIMESTAMP DEFAULT NULL;
    DECLARE avg_interval DOUBLE DEFAULT NULL;

    -- Get the min, max, and count of submitted timestamps in the submission_
    -- history table for the given user
    SELECT 
        MIN(submitted_timestamp), 
        MAX(submitted_timestamp), 
        COUNT(submitted_timestamp)
    INTO min, max, count
    FROM submission_history 
    WHERE user_id = uid;

    -- If the number of submitted timestamps is less than 2 (i.e. player only 
    -- played one game), then we return null. Otherwise, we return the average
    -- interval by calculating the max-min unix timestamp and divide by the 
    -- total number of timestamps.
    IF count < 2 THEN
        SET avg_interval = NULL;
    ELSE 
        SET avg_interval=(UNIX_TIMESTAMP(max) - UNIX_TIMESTAMP(min))/(count -1);
    END IF;
    RETURN avg_interval;

END !
DELIMITER ;
