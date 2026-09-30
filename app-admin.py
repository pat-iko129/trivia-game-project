"""
Python code for Final Project 2023, providing code to interact with the trivia
game and database

Collaborators: Saraswati Soedarmadji and Pat Mutia
Emails: ssoedarm@caltech.edu and pmutia@caltech.edu
"""
import sys                                    # print errors to sys.stderr
import mysql.connector                        # connect to sql
import mysql.connector.errorcode as errorcode # error handling
from art import tprint                        # print opening message
from getpass import getpass                   # to get the password without 
                                              # actually showing in command line
import pandas as pd

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


# Debugging flag to print errors when debugging that shouldn't be visible
# to an actual client. Set to False when done testing.
DEBUG = False

# ----------------------------------------------------------------------
# SQL Utility Functions
# ----------------------------------------------------------------------
def get_conn():
    """"
    Returns a connected MySQL connector instance, if connection is successful.
    If unsuccessful, exits.
    """
    try:
        conn = mysql.connector.connect(
          host='localhost',
          user='appadmin',
          # Find port in MAMP or MySQL Workbench GUI or with
          # SHOW VARIABLES WHERE variable_name LIKE 'port';
          port='3306',
          password='adminpw',
          database='triviadb'
        )
        print('Successfully connected.')
        return conn
    except mysql.connector.Error as err:
        # Remember that this is specific to _database_ users, not
        # application users. So is probably irrelevant to a client in your
        # simulated program. Their user information would be in a users table
        # specific to your database.
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR and DEBUG:
            sys.stderr('Incorrect username or password when connecting to DB.')
        elif err.errno == errorcode.ER_BAD_DB_ERROR and DEBUG:
            sys.stderr('Database does not exist.')
        elif DEBUG:
            sys.stderr(err)
        else:
            sys.stderr('An error occurred, please contact the administrator.')
        sys.exit(1)

# ----------------------------------------------------------------------
# Functions for Command-Line Options/Query Execution
# ----------------------------------------------------------------------

def get_login():
    uname = input('UID: ')
    pword = getpass()

    # Use mysql command to authenticate the inserted password
    sql = """
            SELECT authenticate('%s', '%s'); 
            """ % (uname, pword)

    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()

    return rows[0][0], uname

def get_uname(uid):
    # Get the username corresponding to the userid
    sql = """
            SELECT username
            FROM user_info
            WHERE user_id='%s'; 
            """ % (uid)

    cursor2 = conn.cursor()
    cursor2.execute(sql)
    uname = cursor2.fetchall()

    return uname[0][0]

def check_admin(uid):
    sql = f"""
            SELECT is_admin FROM user_info WHERE user_id='{uid}';
           """
    
    cursor = conn.cursor()
    cursor.execute(sql)
    is_admin = cursor.fetchall()

    return is_admin

def get_cols(table_name):
    # Helper function to get the column names to make the dataframe
    sql = """
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME='%s'
        """ %(table_name)
    
    cursor_cols = conn.cursor()
    cursor_cols.execute(sql)
    columns = cursor_cols.fetchall()
    columns = columns[0:int(len(columns)/2)]

    return columns

def get_leaderboard(ranking):
    """
    Allows the player to view the first 5 players in the leaderboard, along 
    with their current ranking and stats. In addition, we allow the user to 
    see the player one rank above them and their points so they know how many 
    points until they reach the next rank
    """
    sql = """
            SELECT total_rank AS rank, user_id, username, num_games_played, 
            num_quest_answered, total_score
            FROM user_info NATURAL JOIN 
                (SELECT
                    DENSE_RANK() OVER (ORDER BY
                                        %s DESC
                                ) total_rank,
                    user_id,
                    num_games_played,
                    num_quest_answered,
                    total_score
                FROM leaderboard
                ORDER BY total_rank ASC) AS ranked_leaderboard
            ORDER BY %s DESC;
            """ %(ranking, ranking)

    cursor2 = conn.cursor()
    cursor2.execute(sql)
    leaderboard  = cursor2.fetchall()  
    
    return leaderboard

def remove_players():
    """
    Functionality only for admins, in case they want to remove players that 
    broke the rules
    """
    # We will delete the user from the user_info table
    # This will use the trigger written in setup-routines.sql, since even with 
    # the update/delete cascade, it only deletes from the user_info table and 
    # not the leaderboard and submissions tables.
    print("What is the UID of the player you would like to remove?")
    uid = input("UID to Remove: ")

    # first check if the user even exists
    sql = f"""SELECT *
              FROM user_info
              WHERE user_id='{uid}'
           """
    cursor = conn.cursor()
    cursor.execute(sql)
    user = cursor.fetchall()

    if len(user)==0:
        print("Sorry, the user you would like to remove does not exist!")
    else:
        sql = """
                DELETE FROM user_info WHERE user_id='%s'
                """ %(uid)

        cursor2 = conn.cursor()
        cursor2.execute(sql)

        print(f"Player {uid} successfully removed.")

def view_removed_players():
    sql = """
            SELECT *
            FROM removed_players
    """
    
    cursor = conn.cursor()
    cursor.execute(sql)
    removed = cursor.fetchall()

    data = pd.DataFrame(removed, 
                        columns=['user_id', 'username', 'removed_timestamp', 
                                 'num_quest_answered', 'total_score'])
    print(data.to_markdown(tablefmt="grid", index=False))

# -------------------------------------------------------------------------
# Command-Line Functionality
# !! Note that the command line functionalities for the admin are different
# !! compared to those available to the client. 
# -------------------------------------------------------------------------

def login():
    # Prompt the user to log in
    print('Please log in')
    # Keep track of login attempts
    login_counts = 5;

    # Verify that the result from the authenticate function returns the value 1
    # If it does, then return login successful, otherwise print login failed and
    # ask for the password again. 
    while login_counts > 0:
        # If the player has reached maximum number of log in attempts, print 
        # apology message and exit
        if login_counts == 0:
            print("You have reached the maximum number of attempts, sorry!")
            exit()
        
        # Get the result and uid from the helper function
        rows, uid = get_login();
        is_admin = check_admin(uid) # returns 1 if they are an admin
        if rows==1 and is_admin[0][0]==1:
            print("Login Successful! Have Fun!")

            # Get the username so we can print it out
            uname = get_uname(uid)
            
            break
        # If the person trying to log in is not a client, then print an apology
        # message and quit out of the application, since they are not allowed to
        # login
        elif rows==1 and is_admin[0][0]==0:
            print("Sorry, you are not an admin. You cannot login.")
            exit()
        elif rows==0: 
            login_counts -=1
            print("Incorrect password, please try again.")
            print(f"You have {login_counts} attempts remaining")

    return uname

def view_leaderboard():
    print('\n How would you like to sort the leaderboard?')
    print('  (g) - number of games played')
    print('  (q) - number of questions answered')
    print('  (t) - total score')
    print()
    
    answered=False
    while answered==False:
        ans = input('Enter an option: ')[0].lower()
        
        if ans=='g':
            ans='num_games_played'
            answered = True
        elif ans=='q':
            ans='num_quest_answered'
            answered = True
        elif ans=='t':
            ans='total_score'
            answered = True
        else:
            print('Unknown Option')

    result = get_leaderboard(ans)
    
    # Get column names
    columns = get_cols('leaderboard')
    columns.insert(1, ('username',))
    for i in range(len(columns)):
        columns[i] = columns[i][0]

    columns.insert(0, 'rank')

    # Print out the previous submissions of the user. Prints out an empty 
    # table with only column names if the user has no submissions
    data = pd.DataFrame(result, columns=columns)
    print(data.to_markdown(tablefmt="grid", index=False))

# You may choose to support admin vs. client features in the same program, or
# separate the two as different client and admin Python programs using the same
# database.
def show_admin_options():
    """
    Displays options specific for admins, such as adding new data <x>,
    modifying <x> based on a given id, removing <x>, etc.
    """
    while True:
        print('\n \n What would you like to do? ')
        print('      (f) - see full leaderboard')
        print('      (r) - remove players')
        print('      (v) - view removed players')
        print('      (q) - quit')
        print()
        ans = input('Enter an option: ')[0].lower()
        if ans == 'f':
            view_leaderboard()
        elif ans == 'r':
            remove_players()
        elif ans == 'v':
            view_removed_players()
        elif ans == 'q':
            quit_ui()
        else:
            print('Unknown option.')

def quit_ui():
    """
    Quits the program, printing a good bye message to the user.
    """
    tprint('Thank you, Good bye!')
    exit()


# Main function to start up the program
def main():
    # Print a welcome message
    tprint("Welcome to CS121 Trivia", font='graceful')
    
    # The admin must login before anything can be done
    uname = login()
    print(f"Your username is {uname}")

    show_admin_options()

if __name__ == '__main__':
    # This conn is a global object that other functinos can access.
    # You'll need to use cursor = conn.cursor() each time you are
    # about to execute a query with cursor.execute(<sqlquery>)
    conn = get_conn()
    main()