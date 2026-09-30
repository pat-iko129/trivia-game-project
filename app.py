"""
Python code for Final Project 2023, providing code to interact with the trivia
game and database
"""
import sys                                    # print errors to sys.stderr
import mysql.connector                        # connect to sql
import mysql.connector.errorcode as errorcode # error handling
from art import tprint                        # print opening message
import pandas as pd

# Debugging flag to print errors when debugging that shouldn't be visible
# to an actual client. Set to False when done testing.
DEBUG = True

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

def view_leaderboard(curr_user_id):
    """
    Allows the player to view the first 5 players in the leaderboard, along with
    their current ranking and stats. In addition, we allow the user to see the 
    player one rank above them and their points so they know how many points 
    until they reach the next rank
    """
    sql = """SELECT * 
             FROM submission_history
             ORDER BY total_score DESC
             LIMIT 5;"""
    sql1 = f"""SELECT *
               FROM submission_history
               WHERE user_id = {curr_user_id} - 1
               ORDER BY total_score DESC;"""
    cursor = conn.cursor()
    cursor.execute(sql)
    top_five = cursor.fetchall()
    cursor.execute(sql1)
    prior = cursor.fetchall()

    leaderboard = top_five + prior

    print("""player | games played | questioned answered | total score 
         | max possible score""")
    for row in leaderboard:
        (user_id, num_games_played, num_quest_answered,
         total_score, max_possible_score) = row
        print(' ', user_id, num_games_played, num_quest_answered,
              total_score, max_possible_score)

def remove_players(remove_user_id):
    """
    Functionality only for admins, in case they want to remove players that 
    """
    # must check if person using app is admin
    sql = f"DELETE FROM user_info WHERE user_id = {remove_user_id}"
    cursor = conn.cursor()
    cursor.execute(sql)

def play_game():
    """
    Function to prompt the user with questions, checks their answers, and
    awards them points
    """
    num_qs_options = [5, 10, 15, 20]
    num_qs = int(input("How many questions would you like (5, 10, 15, 20): "))
    while num_qs not in num_qs_options:
        num_qs = int(input("How many questions would you like (5, 10, 15, 20): "))
    
    collect_qs = f"""SELECT *
                     FROM trivia_questions
                     LIMIT {num_qs}"""
    
    cursor = conn.cursor()
    cursor.execute(collect_qs)
    game_qs = cursor.fetchall()

    valid_game_ans = ["A", "B", "C", "D"]
    point_sys = {"easy" : 1,
                 "medium" : 2, 
                 "difficult" : 3}

    for row in game_qs:
        (q_id, cat, q_type, diff, q, c_ans, a, b, c, d) = row
        points_earned = 0

        # T/F Question Prompt
        if q_type.equals('boolean'):
            print(f"Category: {cat}")
            print(f"Question: {q}")
            print(f"A: {a}")
            print(f"B: {b}")
            print(f"C: {c}")
            print(f"D: {d}")
            u_ans = input("Type A, B, C, or D: ").upper().strip()
            while u_ans not in valid_game_ans:
                # did not raise error to allow for continued play
                print("Not a valid answer.")
                u_ans = input("Type A, B, C, or D: ").upper().strip()
        
        # MC Question Prompt
        elif q_type.equals('multiple'):
            print(f"Category: {cat}")
            print(f"Question: {q}")
            print(f"A: {a}")
            print(f"B: {b}")
            u_ans = input("Type A or B: ").upper().strip()
            while u_ans not in valid_game_ans:
                # did not raise error to allow for continued play
                print("Not a valid answer.")
                u_ans = input("Type A or B: ").upper().strip()
        
        # Error in Data and Not Correct Question Type
        else:
            raise Exception("Not question_type available.")
        
        if u_ans.equals(c_ans):
            points_earned = point_sys[diff]
            print(f"Correct. You earned {points_earned}")
        else:
            print("Incorrect.")
        
        # need to make function/procedure !!
        # adds submission to submission_history
        # add_submission(u_id, date, q_id, u_ans, points_earned, point_sys[diff])
    

def view_private():
    """
    Function to view player's private leaderboard/stats
    """
    # how to check players user_id
    sql = """SELECT *
             FROM submission_history
             WHERE user_id = """
    
    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.fetchall()

# ----------------------------------------------------------------------
# Command-Line Functionality
# ----------------------------------------------------------------------
def show_opening_options():
    """
    Display options users can choose from in the application on start up. This
    is different from the options that the user can choose from later to play 
    the game.
    """
    print('What would you like to do? ')
    print('  (l) - login')
    print('  (s) - see leaderboard')
    print('  (q) - quit')
    print()
    while True:
        ans = input('Enter an option: ')[0].lower()
        if ans == 'q':
            quit_ui()
        elif ans == 'l':
            print('Login functionality unimplemented.')
        else:
            print('Unknown option.')

def show_options():
    print('What would you like to do? ')
    print('  (s) - start game')
    print('  (l) - see full leaderboard')
    print('  (p) - see private leaderboard')
    print('  (q) - quit')
    print()

    while True:
        ans = input('Enter an option: ')[0].lower()
        if ans == 's':
            play_game()
        elif ans == 'l':
            view_leaderboard()
        elif ans == 'p':
            view_private()
        elif ans == 'q':
            quit_ui()
        else:
            print('Unknown option.')

# You may choose to support admin vs. client features in the same program, or
# separate the two as different client and admin Python programs using the same
# database.
def show_admin_options():
    """
    Displays options specific for admins, such as adding new data <x>,
    modifying <x> based on a given id, removing <x>, etc.
    """
    print('What would you like to do? ')
    print('  (f) - see full leaderboard')
    print('  (r) - remove players')
    print('  (q) - quit')
    print()
    while True:
        ans = input('Enter an option: ')[0].lower()
        if ans == 'f':
            view_leaderboard()
        elif ans == 'r':
            remove_players()
        elif ans == 'q':
            quit_ui()
        else:
            print('Unknown option.')

def quit_ui():
    """
    Quits the program, printing a good bye message to the user.
    """
    print('Good bye!')
    exit()


# Main function to start up the program
def main():
    # Print a welcome message
    tprint("Welcome to CS121 Trivia", font='graceful')
    show_opening_options()

    # temp = []
    # for i in range(60):
    # sql = """
    # SELECT * FROM user_info;
    # """ 

    # cursor = conn.cursor()
    # cursor.execute(sql)
    # rows = cursor.fetchall()

    # print(rows)

    # temp = pd.DataFrame(temp)
    # temp.to_csv('temp.csv')

if __name__ == '__main__':
    # This conn is a global object that other functinos can access.
    # You'll need to use cursor = conn.cursor() each time you are
    # about to execute a query with cursor.execute(<sqlquery>)
    conn = get_conn()
    main()