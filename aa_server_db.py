#!/usr/bin/env python
##################################################################
# Copyright (c) 2015
# Sep 2015 - 
# Version 0.1, Last change on Sep 24, 2015    
##################################################################

# All functions needed to create db, save and retrieve data 

import sqlite3

#----------------------------------------------------------------------
# global variables
#----------------------------------------------------------------------

USER_DB_PATH = "DB/users.db"

#----------------------------------------------------------------------
# Database routines
#----------------------------------------------------------------------

def connect_db( file_path ):
    """
    Create a Connection object that represents the database.
    Data will be stored in the file_path
    """
   
    conn = sqlite3.connect( file_path )
    return conn

def connect_user_db():
    """
    Create a Connection object to users db
    """
    return connect_db( USER_DB_PATH )

#----------------------------------------------------------------------
# Apply changes to database
#----------------------------------------------------------------------

def create_user_table( conn ):
    """
    Create users table into users db.
    """    
    # create a Cursor object
    c = conn.cursor()
    try:
        # Create table and commit the changes
        c.execute('''CREATE TABLE users
                    (username text,
                    password text,
                    app_id text,
                    session_id text)''')
        conn.commit()
    except:
        return 'Table exists in db'
    

def insert_rows( conn, rows ):
    """
    Insert rows of data (username, password, app_id, session_id)
    into users db.
    """
    c = conn.cursor()
    # Insert input rows of data and commit the changes
    c.executemany("INSERT INTO users VALUES (?,?,?,?)", rows )
    conn.commit()


def insert_user_pass( conn, rows ):
    """
    Insert new username and password into users db.
    """
    c = conn.cursor()
    c.executemany('''INSERT INTO users VALUES (?,?,None,None)''', rows )
    conn.commit()


def insert_app_session_id( conn, username, password,
                           app_id, session_id ):
    """
    Insert app_id and session_id for specific user.
    """
    
    c = conn.cursor()
    # Update row of data and commit the changes
    c.execute('''UPDATE users SET app_id = ?,session_id=?
              WHERE username = ? and password = ?''',
              ( app_id, session_id, username, password ) )
    conn.commit()

def insert_row( conn, username, password,
                           app_id, session_id ):
    """
    Insert a new user.
    """
    
    c = conn.cursor()
    # Update row of data and commit the changes
    c.execute('''INSERT INTO users VALUES (?,?,?,?)''',
              ( username, password,app_id, session_id ) )
    conn.commit()    
#----------------------------------------------------------------------
# Retrieve data from database
#----------------------------------------------------------------------
def exist_user( conn, username, password ):
    """
    Check if the user with specific username and password exists in
    user db
    """    
    c = conn.cursor()
    # Select rows of data from db and Return the existance of the user
    c.execute('''SELECT * FROM users WHERE
                username = ? and password = ?''',
              ( username, password ) )
    if c.fetchone(): return True
    return False


    
# Return user info with specific session_id
def return_user_info( conn, session_id ):
    """
    Return user info with specific session_id
    """ 
    c = conn.cursor()
    # Select row of data from db and Return user info
    c.execute('''SELECT * FROM users WHERE session_id = ?''',
              ( session_id, ) )
    user = c.fetchone()
    return user

def exist_session( conn, username, password, app_id ):
    """
    Check if the session_id for specific username, password and
    app_id exists in user db
    """    

    c = conn.cursor()
    # Select session_id related to input data from db
    # and Return the existance of the user
    c.execute('''SELECT session_id FROM users WHERE
                username = ? and password = ? and app_id=?''',
              ( username, password, app_id ) )
    session_id = c.fetchone()
    if session_id: return session_id[0]
    return False

#----------------------------------------------------------------------
# Testing functions
#----------------------------------------------------------------------
def test_create_insert_db():
    """
    Test creating db and inserting data in it.
    """
    conn = connect_db( "DB/users.db" )
    create_user_table( conn )
    users = [('negar', 'nb1',None,None),
             ('samira', 'sm1',None,None),
             ('soheil', 'sq1',None,None)
             ]
    insert_rows(conn, users)
    conn.close()
    
def test_return_session_id():
    """
    test checking existance of user and session_id
    """
    conn = connect_db( "DB/users.db" )

    username = "negar"
    password = "nb1"
    app_id = "1059"
    session_id = "negar_1059_1234"

    if not exist_user( conn, username, password ):
        print "User is not in DB"
        response = "Not Success"

    else:    
        exist_session_id = exist_session( conn, username,
                                          password, app_id )        
        if exist_session_id:
            print "Session exist in db"
            response = exist_session_id

        else:            
            insert_app_session_id( conn, username, password,
                                   app_id, session_id )
            print "Session is inserted in db"
            response = session_id
    conn.close()
    return response

#----------------------------------------------------------------------
# Main function which called in runtime
#----------------------------------------------------------------------

def main():
    """
    Get the new record and save it to table.
    """
    
    print
    print "To add a new user to the database, please fill out "
    print "the following information:"
    print
    
    username = raw_input ( "Enter the user name:" )
    password = raw_input ( "Enter the password:" )
    app_id = int(raw_input ( "Enter the app_id:" ))

    conn = connect_db( "DB/users.db" )
    try:
        create_user_table( conn )
    except: pass
    insert_row(conn, username, password,app_id,None)

    c = conn.cursor()
    c.execute('''SELECT * FROM users''' )
    
    print
    print "The user has been just added to the database."
    print
    
    conn.close()

#----------------------------------------------------------------------
# Test in run-time
#----------------------------------------------------------------------
if __name__ == "__main__":
    main()
    #print "response:",test_return_session_id()
