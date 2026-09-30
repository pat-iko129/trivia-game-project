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
import pandas as pd                           # to print tables nicely
import datetime                               # so we can print table w/ times
import numpy as np

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
          user='appclient',
          # Find port in MAMP or MySQL Workbench GUI or with
          # SHOW VARIABLES WHERE variable_name LIKE 'port';
          port='3306',
          password='clientpw',
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

# Function that uses sql command to get the player's username and password
def get_login():
    uid = input('UID: ')
    pword = getpass()

    # Use mysql command to authenticate the inserted password
    sql = """
            SELECT authenticate('%s', '%s'); 
            """ % (uid, pword)

    cursor1 = conn.cursor()
    cursor1.execute(sql)
    rows = cursor1.fetchall()

    return rows[0][0], uid

def check_client(uid):
    sql = f"""
            SELECT is_admin FROM user_info WHERE user_id='{uid}';
           """
    
    cursor = conn.cursor()
    cursor.execute(sql)
    is_client = cursor.fetchall()

    return is_client

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
            ORDER BY %s DESC 
            LIMIT 5;
            """ %(ranking, ranking)

    cursor2 = conn.cursor()
    cursor2.execute(sql)
    leaderboard  = cursor2.fetchall()  
    
    return leaderboard

def get_players_ranking(ans, uid):
    # In our query file, we use a temporary table to store the ranked version of
    # our leaderboard, but it wasn't working in python so we just put the select 
    # statement directly inside the code, so it is a bit messier than the 
    # queries listed in queries.sql 
    sql = f"""
        SELECT 
            l.total_rank, 
            l.user_id, 
            u.username, 
            l.num_games_played, 
            l.num_quest_answered, 
            l.total_score
        FROM 
            (SELECT
                    DENSE_RANK() OVER (ORDER BY
                                        {ans} DESC
                                ) total_rank,
                    user_id,
                    num_games_played,
                    num_quest_answered,
                    total_score
                FROM leaderboard
                ORDER BY total_rank ASC) AS l LEFT JOIN 
            (SELECT
                    DENSE_RANK() OVER (ORDER BY
                                        {ans} DESC
                                ) total_rank,
                    user_id,
                    num_games_played,
                    num_quest_answered,
                    total_score
                FROM leaderboard
                ORDER BY total_rank ASC) AS r NATURAL JOIN 
                user_info as u
            ON l.user_id = r.user_id
        WHERE 
            r.total_score = 
            (SELECT DISTINCT MIN(r2.total_score) as min_total
            FROM leaderboard AS r2 
            WHERE r2.total_score > 
                (SELECT total_score FROM leaderboard WHERE user_id='{uid}')
            GROUP BY l.user_id) 
            OR r.user_id='{uid}'
        ORDER BY {ans} ASC LIMIT 2; 
    """

    cursor = conn.cursor()
    cursor.execute(sql)
    
    return cursor.fetchall()  
    

def play_game(uid):
    """
    Function to prompt the user with questions, checks their answers, and
    awards them points
    """
    tprint('Let\'s start playing!', font='graceful')
    category = get_categories()
    difficult = get_difficulty()
    num_quest = get_num_quests()

    # Note that we are only getting one question at a time (Limit=1) since it is
    # easier this way to keep track of the number of points earned and then add
    # into the score later
    for _ in range(num_quest):
        # If both category and difficulty are random
        if category=='Random' and difficult=='random':
            sql = f"""
            SELECT question_id, question, correct_answer, difficulty, A, B, C, D
            FROM trivia_questions_indexed
            ORDER BY RAND()
            LIMIT 1;
            """
        # If only category is random
        elif category=='Random' and not difficult=='random':
            sql = f"""
            SELECT question_id, question, correct_answer, difficulty, A, B, C, D
            FROM trivia_questions_indexed
            difficulty='{difficult}'
            ORDER BY RAND()
            LIMIT 1;
            """
        # If category is not random but difficulty is random
        elif category!='Random' and difficult=='random':
            sql = f"""
            SELECT question_id, question, correct_answer, difficulty, A, B, C, D
            FROM trivia_questions_indexed
            WHERE category='{category}'
            ORDER BY RAND()
            LIMIT 1;
            """
        else:
            sql = f"""
                SELECT question_id, question, correct_answer, difficulty, 
                A, B, C, D
                FROM trivia_questions_indexed
                WHERE category='{category}' AND difficulty='{difficult}'
                ORDER BY RAND()
                LIMIT 1;
                """ 
        
        question_data = conn.cursor()
        question_data.execute(sql)
        question_data = question_data.fetchall()

        # Print out the questions and possible answers in the command line
        ans, correct_answer, difficulty, qid = get_question(question_data)
        
        poss = None
        if difficulty == 'easy': poss=1
        elif difficulty == 'medium': poss=2
        elif difficulty == 'hard': poss=3

        earned = 0
        # We need to update leaderboard and submission history tables
        if ans.lower() == correct_answer.lower():
            earned = poss
            print("Congratulations, you answered it correctly!")
        else:
            print(f"Sorry, your answer was incorrect :( ")
            print(f"The correct answer is {correct_answer}")
        
        # Call the procedure to update the leaderboard and submission histories
        cursor = conn.cursor()
        cursor.callproc('sp_update_game', 
                        (uid, qid, ans.upper(), earned, poss, num_quest))
        
        conn.commit()

def get_cols(table_name):
    # Get the column names to make the dataframe
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

def view_submissions(uid, print_output=True):
    """
    Function to view player's private leaderboard/stats
    """
    # Get the players submission history based on their uid
    sql = """
        SELECT *
        FROM submission_history
        WHERE user_id='%s'; 
        """ %(uid)
    
    cursor = conn.cursor()
    cursor.execute(sql)
    submissions = cursor.fetchall()

    columns = get_cols('submission_history')
    for i in range(len(columns)):
        columns[i] = columns[i][0]

    # Print out the previous submissions of the user. Prints out an empty 
    # table with only column names if the user has no submissions
    data = pd.DataFrame(submissions, columns=columns)
    if print_output==True:
        print(data.to_markdown(tablefmt="grid", index=False))

    return data

def view_statistics(uid):
    # Call the function defined in setup-routines to calculate the average
    # time in seconds between submissions/games
    sql = f"""
        SELECT avg_submit_interval('{uid}'); 
        """
     
    cursor = conn.cursor()
    cursor.execute(sql)
    avg_times = cursor.fetchall()

    sql = f"""
        SELECT num_quest_answered, total_score 
        FROM leaderboard
        WHERE user_id='{uid}'; 
        """
     
    cursor = conn.cursor()
    cursor.execute(sql)
    quest_points = cursor.fetchall()

    # Get the player's favorite category, could be multiple categories if 
    # there are ties
    sql = f"""
            SELECT category 
            FROM 
                (SELECT count(category) AS category_counts, category
                    FROM trivia_questions NATURAL JOIN submission_history
                    WHERE user_id='{uid}'
                    GROUP BY category
                    ORDER BY count(category) DESC) AS count_table1
            WHERE category_counts = 
                (SELECT MAX(category_counts) 
                FROM
                    (SELECT count(category) AS category_counts, category
                    FROM trivia_questions NATURAL JOIN submission_history
                    WHERE user_id='{uid}'
                    GROUP BY category
                    ORDER BY count(category) DESC) AS count_table2);
           """
    
    cursor = conn.cursor()
    cursor.execute(sql)
    fav_cat = cursor.fetchall()

    favorite_categories = []
    for i in fav_cat:
        favorite_categories.append(i[0])

    if len(favorite_categories) == 0:
        favorite_categories="N/A"

    data = view_submissions(uid, print_output=False)
    
    dshape = data.shape[0]
    ccorrect = 0
    for i in range(data.shape[0]):
        if data['points_earned'][i] == data['points_possible'][i]: 
            ccorrect += 1
    if dshape == 0:
        percentage = 0
    else:
        percentage = np.round(ccorrect/dshape*100, 2)

    print(f"Average time between submissions (secs): {avg_times[0][0]} s")
    print(f"Total number of questions answered: {quest_points[0][0]}")
    print(f"Percentage of questions answered correctly: {percentage}%")
    print(f"Total points accumulated: {quest_points[0][1]}")
    print(f"Favorite Categories: {favorite_categories}")
    
# ----------------------------------------------------------------------
# Command-Line Functionality
# ----------------------------------------------------------------------
# Function to prompt the user to log in. If the provided user id and password
# are correct, then the user can continue. We only give the player 5 attempts
# Otherwise we print an apology letter and kick them out of the application.
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
        is_client = check_client(uid) # returns 0 if the player is a client
        if rows==1 and is_client[0][0]==0:
            print("Login Successful! Have Fun!")

            # Get the username so we can print it out
            uname = get_uname(uid)
            
            break
        # If the person trying to log in is not a client, then print an apology
        # message and quit out of the application, since they are not allowed to
        # login
        elif rows==1 and is_client[0][0]==1:
            print("Sorry, you are not a client. You cannot login.")
            exit()
        elif rows==0: 
            login_counts -=1
            print("Incorrect password, please try again.")
            print(f"You have {login_counts} attempts remaining")

    return uid, uname

def get_question(question_data):
    qid = question_data[0][0]
    question = question_data[0][1]
    correct_answer = question_data[0][2]
    difficulty = question_data[0][3]
    A = question_data[0][4]
    B = question_data[0][5]
    C = question_data[0][6]
    D = question_data[0][7]

    print(f"\n {question}, difficult: {difficulty}")
    print(f"\n (A) {A}")
    print(f"\n (B) {B}")
    print(f"\n (C) {C}")
    print(f"\n (D) {D}")

    ans = ''
    answered = False
    while answered==False:
        ans = input('Your Answer: ')[0]
        if ans.lower() in ['a', 'b', 'c', 'd']:
            answered=True
        else:
            print("Unknown input")

    return ans, correct_answer, difficulty, qid

def get_num_quests():
    print("How many questions would you like to answer?")
    
    return int(input('Number of questions: '))

def get_categories():
    sql = """SELECT DISTINCT category FROM trivia_questions;"""
    
    cursor = conn.cursor()
    cursor.execute(sql)
    categories = cursor.fetchall()
    print(categories)
    categories.append(('Random', ))
    retval = {}

    answered = False
    while answered == False:
        print("Please choose your category:")
        count = 0
        for i in categories:
            print(f'  ({count}) - {i[0]}')
            count += 1
        
        ans = input('Enter a category: ')

        if type(ans)!=int and int(ans) not in range(count):
            print("Unknown Option")
        else:
            answered = True
            ans = categories[int(ans)][0]

    return ans

def get_difficulty():
    diff = ['easy', 'medium', 'hard']
    retval = {}

    answered = False
    while answered == False:
        print("Please choose your difficulty:")
        count = 1
        for i in diff:
            print(f'  ({i[0].lower()}) - {i} ({count} points)')
            retval[i[0].lower()] = i
            count += 1
        print('  (r) - random')
        
        ans = input('Enter your difficulty: ')[0].lower()
        retval['r'] = 'random'

        if ans not in retval.keys():
            print("Unknown Option")
        else:
            answered = True
            ans = retval[ans]

    return ans

def view_leaderboard(uid):
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
    window = get_players_ranking(ans, uid)
    
    # Get column names
    columns = get_cols('leaderboard')
    columns.insert(1, ('username',))
    for i in range(len(columns)):
        columns[i] = columns[i][0]

    columns.insert(0, 'rank')

    # Print out the previous submissions of the user. Prints out an empty 
    # table with only column names if the user has no submissions
    data = pd.DataFrame(result, columns=columns)

    if uid not in data['user_id'].values:
        window0 = []
        window1 = []
        for i in window[0]:
            window0.append(i)
        for i in window[1]:
            window1.append(i)

        s = pd.Series(['...', '...', '...', '...' ,'...','...'],
                      index=columns)

        # Appending empty series to df
        data = data.append(s,ignore_index=True)

        data.loc[len(data)] = window1
        data.loc[len(data)] = window0

    print(data.to_markdown(tablefmt="grid", index=False))

def show_options(uid):
    while True:
        print('\n\n What would you like to do? ')
        print('     (s) - start game')
        print('     (l) - see leaderboard')
        print('     (c) - see my statistics')
        print('     (p) - see previous submissions')
        print('     (q) - quit')
        print()
        ans = input('Enter an option: ')[0].lower()
        if ans == 's':
            play_game(uid)
        elif ans == 'l':
            view_leaderboard(uid)
        elif ans == 'p':
            view_submissions(uid)
        elif ans == 'c':
            view_statistics(uid)
        elif ans == 'q':
            quit_ui()
        else:
            print('Unknown option.')

def quit_ui():
    """
    Quits the program, printing a good bye message to the user.
    """
    tprint("Thank you for playing!", font='graceful')
    tprint("See you again soon!", font='graceful')
    exit()


# Main function to start up the program
def main():
    # Print a welcome message
    tprint("Welcome to CS121 Trivia", font='graceful')
    
    # The player must login before they can do anything
    uid, uname = login()
    print(f"Your username is {uname}")

    show_options(uid)

if __name__ == '__main__':
    # This conn is a global object that other functinos can access.
    # You'll need to use cursor = conn.cursor() each time you are
    # about to execute a query with cursor.execute(<sqlquery>)
    conn = get_conn()
    main()