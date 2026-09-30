-- Small SQL file to create users and grant permissions

-- Drop the users if they already exist so when the file is sourced from the 
-- command line we will not get errors
DROP USER IF EXISTS 'appclient'@'localhost';
DROP USER IF EXISTS 'appadmin'@'localhost';

-- Create admin and client users
CREATE USER 'appadmin'@'localhost' IDENTIFIED BY 'adminpw';
CREATE USER 'appclient'@'localhost' IDENTIFIED BY 'clientpw';

-- Grant all privileges to the admin
GRANT ALL PRIVILEGES ON *.* TO 'appadmin'@'localhost' WITH GRANT OPTION;
-- Grant only the select, insert, trigger, update, and execute privileges to the
-- client user
GRANT SELECT, INSERT, TRIGGER, UPDATE, EXECUTE ON *.* TO 
'appclient'@'localhost' IDENTIFIED BY 'clientpw';

-- Flush all privileges
FLUSH PRIVILEGES;