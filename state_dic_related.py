#!/usr/bin/env python
##################################################################
# Copyright (c) 2015
# Nov 2015 - 
# Version 0.1, Last change on Nov 03, 2015    
##################################################################

# All functions needed to manipulate state dictionary


"""
Format of state dictionary:

state_dic = { session_id :{   "state" : session_state,
                              "waiting" : { req_id : req_transport}
                            } }

state dictionary contains:
    session_id      - The session id for the running app
    session_state   - The state of each session; such as Idle, pendding
    req_id          - The request id of the request waiting to response
    req_transport   - The transport object of the request waiting to
                    response 
"""

#----------------------------------------------------------------------
# Routines related to state_dic
#----------------------------------------------------------------------      
def set_state( state_dic, session_id, state ):
    """
    Set the state for specific session_id
    """
    try:
        state_dic[ session_id ]["state"] = state
    except:
        state_dic[ session_id ]= {"state" : state,"waiting" : { }}
        

def get_state( state_dic, session_id ):
    """
    Get the state for specific session_id
    """

    try:
        return state_dic[ session_id ]["state"]
    except:
        return
    

def set_wait_req( state_dic, session_id, req_id, req_transport ):
    """
    Set the waiting requests for specific session_id
    """

    try:
        state_dic[ session_id ]["waiting"][req_id] = req_transport
    except:
        state_dic[ session_id ]= {"waiting":{ req_id:req_transport } }
        
    
def get_wait_req( state_dic, session_id ):
    """
    Get the waiting requests for specific session_id
    """

    try:
        return state_dic[ session_id ]["waiting"]
    except:
        return  


def get_wait_req_transport( state_dic, session_id, req_id ):
    """
    Get the waiting transport request for specific session_id
    """

    try:
        return state_dic[ session_id ]["waiting"][req_id]
    except:
        return

    
def pop_wait_req( state_dic, session_id ):
    """
    pop a waiting request for specific session_id
    ( return req_id and corresponding req_transport in a tuple
      and remove them from dictionary )
    """

    try:
        return state_dic[ session_id ]["waiting"].popitem()
    except:
        return

def has_session_id( state_dic, session_id ):
    """
    Define if the state has specific session_id
    """

    return state_dic.has_key( session_id )
