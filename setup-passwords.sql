-- File for Password Management section of Final Project

-- Drop procedures and functions if they already exist so we do not get errors
DROP PROCEDURE IF EXISTS sp_add_user;
DROP FUNCTION IF EXISTS authenticate;
DROP FUNCTION IF EXISTS make_salt;


-- (Provided) This function generates a specified number of characters for 
-- using as a salt in passwords.
DELIMITER !
CREATE FUNCTION make_salt(num_chars INT) 
RETURNS VARCHAR(20) NOT DETERMINISTIC
BEGIN
    DECLARE salt VARCHAR(20) DEFAULT '';
    -- Don't want to generate more than 20 characters of salt.
    SET num_chars = LEAST(20, num_chars);
    -- Generate the salt!  Characters used are ASCII code 32 (space)
    -- through 126 ('z').
    WHILE num_chars > 0 DO
        SET salt = CONCAT(salt, CHAR(32 + FLOOR(RAND() * 95)));
        SET num_chars = num_chars - 1;
    END WHILE;
    RETURN salt;
END !
DELIMITER ;


-- [Problem 1a]
-- Adds a new user to the user_info table, using the specified password (max
-- of 20 characters). Salts the password with a newly-generated salt value,
-- and then the salt and hash values are both stored in the table.

DELIMITER !
CREATE PROCEDURE sp_add_user(new_user_id CHAR(5), new_username VARCHAR(20), 
                            admin_bol TINYINT, password VARCHAR(20))
BEGIN
    DECLARE new_salt CHAR(8);
    DECLARE salted_pw VARCHAR(38);
    DECLARE pw_hash BINARY(64);

    SET new_salt = make_salt(8);

    SET pw_hash = SHA2(CONCAT(password, new_salt), 256);
 
    INSERT INTO user_info(user_id, username, is_admin, salt, password_hash)
    VALUES (new_user_id, new_username, admin_bol, new_salt, pw_hash);

    -- When adding a user, we also need to add them into the leaderboard
    -- Note that when they are first added, the number of games played, number
    -- of questions answered, and total score are all 0
    INSERT INTO leaderboard VALUES (new_user_id, 0, 0, 0);
END !
DELIMITER ;

-- [Problem 1b]
-- Authenticates the specified username and password against the data
-- in the user_info table.  Returns 1 if the user appears in the table, and the
-- specified password hashes to the value for the user. Otherwise returns 0.
DELIMITER !
CREATE FUNCTION authenticate(check_user_id CHAR(5), password VARCHAR(20))
RETURNS TINYINT DETERMINISTIC
BEGIN
    -- DECLARE check_salt CHAR(8);
    DECLARE salted_pw VARCHAR(28);
    DECLARE pw_hash BINARY(64);
    DECLARE check_salt CHAR(8);

    SELECT salt INTO check_salt 
    FROM user_info
    WHERE user_id = check_user_id;

    SET pw_hash = SHA2(CONCAT(password, check_salt), 256);
    
    -- If the user id that we are checking exists in the table, then return true
    IF  EXISTS    (SELECT user_id 
                   FROM user_info
                   WHERE user_id=check_user_id) AND
        pw_hash = (SELECT password_hash
                   FROM user_info
                   WHERE user_id = check_user_id)  THEN
        RETURN TRUE;
    ELSE 
        RETURN FALSE;
    END IF;
END !
DELIMITER ;

-- [Problem 1c]
-- Add at least two users into your user_info table so that when we run this 
-- file, we will have examples users in the database.

CALL sp_add_user('QPOSD', 'james2', 0, 'qpassword1');
CALL sp_add_user('1KF2J', 'mario243', 0, 'passwords');
CALL sp_add_user('O2I5J', 'player2', 0, '1password1');
CALL sp_add_user('Q9EM2', 'saras02', 1, 'adminpass');
CALL sp_add_user('WE3L9', 'pat190', 1, 'admin2');

-- Example to check if the accounts made above are actually in the database
SELECT authenticate('QPOSD', 'qpassword1'); -- Returns 1
SELECT authenticate('QPOSD', 'randpassword'); -- Returns 0
SELECT authenticate('ASIFL', 'mypassword') -- Returns 0