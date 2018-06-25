#!/usr/bin/env python
##################################################################
# Copyright (c) 2015
# Oct 2015 - 
# Version 0.1, Last change on Nov 02, 2015    
##################################################################

# All functions needed to implement Payment server 

import datetime, json

from twisted.internet import reactor, protocol

from libDiameter import *
from diam_related import *

from constants import *

#----------------------------------------------------------------------
# global variables
#----------------------------------------------------------------------

"""
Format of account dictionary:

account_dic =   { user_name:{   "user_account" : user_account_value,
                                "reserved_credits" :{
                                    session_id : {
                                        "reserved_val": reserved_value,
                                        "primary_credit":primary_credit_value
                                        }
                                                    }
                            }
                }

session dictionary contains:

    
    user_name           - The user name
    session_id          - The session_id of user application
    user_account_value  - The whole user accounting value
    reserved_value      - The reserved value for each session_id
    primary_credit_value- The value of primary credit which is retrieved
                          from plan
    
"""

account_dic = {}
#----------------------------------------------------------------------
# Routines related to account_dic
#----------------------------------------------------------------------

def set_user_account( user_name, user_account_value ):
    """
    Set user acoount value for the user with specific username
    """
    account_dic[ user_name ] = { "user_account" : user_account_value,
                                 "reserved_credits" : {}
                                 }

def set_primary_credit( user_name, session_id, primary_credit_value ):
    """
    Set a primary credit value for a user with specific username and
    running session_id
    """
    account_dic[ user_name ]["reserved_credits"][ session_id ]["primary_credit"] = \
                                                         primary_credit_value
    
def set_reserved_credit( user_name, session_id, reserved_value ):
    """
    Set a reserve value for a user with specific username and
    running session_id
    """
    if not account_dic[ user_name ]["reserved_credits"].has_key(session_id):
        account_dic[ user_name ]["reserved_credits"][ session_id ] ={}
    account_dic[ user_name ]["reserved_credits"][ session_id ]["reserved_val"] = \
                                                         reserved_value
    
def add_to_reserved_credit( user_name, session_id, reserved_value ):
    """
    Add a new reserve value to the last reserved value
    """
    account_dic[ user_name ]["reserved_credits"][ session_id ]["reserved_val"] += \
                                                         reserved_value

def get_reserved_credit( user_name, session_id ):
    """
    Get reserved value of the user that submitted application with
    specific session_id
    """
    return account_dic[ user_name ]["reserved_credits"][ session_id ]["reserved_val"]

def get_user_account_val( user_name ):
    """
    Get user account value 
    """
    return account_dic[ user_name ][ "user_account" ]


def is_session_id_exist( user_name, session_id ):
    """
    Determine if the session id is exist in dictionary or no
    """
    try:
        return account_dic[ user_name ]["reserved_credits"].has_key(
                                                            session_id )
    except:
        set_user_account( user_name, 10000 )
        return False
    
def deduct_used_credit( user_name, session_id, used_credit ):
    account_dic[ user_name ]["user_account"] -= used_credit
    set_reserved_credit( user_name, session_id, 0 )
    
#----------------------------------------------------------------------
# Payment class
#----------------------------------------------------------------------  
class Payment:
    """
    The Payment class
    """

    #------------------------------------------------------------------
    # request received handler
    #------------------------------------------------------------------
    def handle_req_received(self, req, transport):
        """
        As soon as request received from other servers ,
        this function is called.
        """
        
        req_avps = return_request_avps( req )
        req_action = get_request_action_from_avps( req_avps )
        session_id = get_session_id_from_avps( req_avps )

        # Received lock user credit request from RCS ( LUCR )
        if req_action == LOCK_USER_CREDIT:
            self.handle_pay_lock_credit_request( req_avps, transport )
        
        # Received start bill request from RCS ( SBPR )
        elif req_action == START_BILL_PAYMENT:
            self.handle_pay_start_bill_request( req_avps, transport )

        else:
            print "The request is not allowed for this server!"
    
    #------------------------------------------------------------------
    # handle received requests
    #------------------------------------------------------------------
    def handle_pay_start_bill_request( self, req_avps, req_transport ):
        """
        Handle start bill request which is received from
        Resource Control server( SBPR ).
        """

        session_id = get_session_id_from_avps( req_avps )
        
        print
        print "Received 'SBPR' request from Resource Control Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with Session-Id = %s "%session_id+\
              "and Request-Id = %s"%get_request_id_from_avps(req_avps)
        print "-"*64
        
        user_name = req_avps[  "User-Name" ]
        billable_artifact = json.loads( req_avps[  "Billable-Artifact" ] )
        total_service_usage = 0
        total_resource_usage = 0
             
        for service in billable_artifact.keys():
            service_ugase = billable_artifact[ service ]["service_ugase"]
            resource_usage = billable_artifact[ service ]["resource_usage"] 
            total_service_usage += service_ugase
            total_resource_usage += resource_usage
            
        print
        print "Received billable artifact for the user with the "
        print "user_name = '%s' and session_id = %s"%( user_name,
                                                       session_id ) 
        print 
        print "Total service usage: ",total_service_usage
        print "Total resource usage: ",total_resource_usage
        print "Total usage: ",total_resource_usage + total_service_usage
        print
        print
        print "%20s%20s%20s"%( "Service name", "Service usage",
                               "Resource usage" )
        print "%20s%20s%20s"%("="*15,"="*15,"="*15)
        
        for service in billable_artifact.keys():
            service_ugase = billable_artifact[ service ]["service_ugase"]
            resource_usage = billable_artifact[ service ]["resource_usage"] 
            print "%20s%20s%20s"%( service, service_ugase, resource_usage )

        #print
        #print "Based on the received billable artifact and application plan, "
        #print "the Payment server calculates credit amount, then deducts credit"
        #print "from the end user's account and refunds unused reserved credit "
        #print "to the user's account"
        #print

        app_usage = req_avps[ "App-Usage" ]

        refund_credit = get_reserved_credit( user_name, session_id ) - app_usage
        deduct_used_credit( user_name, session_id, app_usage )
        
        print 
        print "The payment server deducts the amount of '%s' from user "%app_usage
        print "and give back the amount of '%s', which had been locked,"%refund_credit
        print "to the user."
        print
       
        # Send the SBPR response(SBPA) to RCS
        sbpa = self.create_pay_start_bill_response( req_avps )
        req_transport.write( sbpa )

    def handle_pay_lock_credit_request( self, req_avps, req_transport ):
        """
        Handle lock user credit request which is received from
        Resource Control server( LUCR ).
        """

        session_id = get_session_id_from_avps( req_avps )
        
        print
        print "Received 'LUCR' request from Resource Control Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with Session-Id = %s "%session_id+\
              "and Request-Id = %s"%get_request_id_from_avps(req_avps)
        print "-"*64
        
        # Reserve credit based on the app plan
        plan_uri = req_avps[  "App-Topology" ]
        user_name = req_avps[  "User-Name" ]
        
        res_value = self.get_reserved_val_from_plan( plan_uri )
        self.lock_usr_credit( user_name, session_id, res_value )

        # Send the LUCR response(LUCA) to RCS
        luca = self.create_pay_lock_credit_response( req_avps )
        req_transport.write( luca )
        

    #------------------------------------------------------------------
    # creating responses
    #------------------------------------------------------------------
    def create_pay_lock_credit_response(  self, avps  ):
        """
        Creates lock user credit response which
        is sent to Resource Control server( LUCA ).
        """

        # add required AVPs to response avps object
        res_avps=[]
        for avp in [ "Session-Id", "Origin-Host",
                     "Origin-Realm","Destination-Realm",
                     "User-Name",
                     "Request-Type","Request-Id",
                     "Dot-Requested-Action" ]:
            res_avps.append(encodeAVP( avp, avps[avp]))

        res_avps.append(encodeAVP( "Result-Code", SUCCESS ))           

        # create header and set command
        luca = HDRItem()
        luca.cmd = dictCOMMANDname2code('DoT-Answer')
        initializeHops( luca )
        response = createRes(luca,res_avps)

        print
        print "Send 'LUCA' response to Resource Control Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%avps["Request-Id"]
        print "-"*64
        
        return response.decode("hex")
    

    def create_pay_start_bill_response(  self, avps  ):
        """
        Create start bill response which is sent to
        Resource Control server( SBPA ).
        """
        # add required AVPs to response avps object
        res_avps=[]
        for avp in [ "Session-Id", "Origin-Host",
                     "Origin-Realm","Destination-Realm",
                     "User-Name",
                     "Request-Type","Request-Id",
                     "Dot-Requested-Action" ]:
            res_avps.append(encodeAVP( avp, avps[avp]))

        res_avps.append(encodeAVP( "Result-Code", SUCCESS ))           

        # create header and set command
        sbpa = HDRItem()
        sbpa.cmd = dictCOMMANDname2code('DoT-Answer')
        initializeHops( sbpa )
        response = createRes(sbpa,res_avps)

        print
        print "Send 'SBPA' response to Resource Control Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%avps["Request-Id"]
        print "-"*64
        
        return response.decode("hex")
    
    #------------------------------------------------------------------
    # Payment responsibilities
    #------------------------------------------------------------------
    def get_reserved_val_from_plan( self, plan_uri ):
        """
        Parse the submitted plan and retrieve the value of
        reserved credit.
        """
        # The primary_credit, which should be retrieved from plan
        return 500

    def lock_usr_credit( self, user_name, session_id, credit ):
        """
        Lock the credit value from user account.
        """
        
        session_exist = is_session_id_exist( user_name, session_id )
        
        if not session_exist:
            set_reserved_credit( user_name, session_id, credit )
        else:
            add_to_reserved_credit( user_name, session_id, credit )
                
        
    def calculate_used_credit( self, user_name, session_id,
                               billable_artifacts ):
        """
        This function should calculate the amount of credit should
        be deducted from user, with the help of billable artifact and
        the application plan
        """
        return None
    
    #------------------------------------------------------------------
    # Running the server
    #------------------------------------------------------------------        
    def run_server(self):
        """
        Run the Payment server.
        """
        factory = ServerFactory( self )
        reactor.listenTCP( PY_PORT,factory )
        reactor.run()
    
#----------------------------------------------------------------------
# Server protocol
#---------------------------------------------------------------------- 
class ServerProtocol(protocol.Protocol):
    """
    The Server protocol is used for listening to
    receive messages from other servers
    """
    
    def __init__(self, factory, dot_server):
        """
        initialization of ServerProtocol class
        """
        self.dot_server = dot_server
        
    def dataReceived(self, data):
        """
        As soon as data received to the server, this function is called.
        """
        self.dot_server.handle_req_received( data, self.transport )
        #self.transport.write( response )
        #self.transport.loseConnection()

#----------------------------------------------------------------------
# Server Factory
#----------------------------------------------------------------------
class ServerFactory(protocol.ServerFactory):
    
    def __init__(self, dot_server):
        """
        initialization of ServerFactory class
        """
        self.dot_server = dot_server
        
    def buildProtocol(self, addr):
        """
        return the ServerProtocol as its factory
        """
        return ServerProtocol(self, self.dot_server)
    

#----------------------------------------------------------------------
# run-time execution
#---------------------------------------------------------------------- 
if __name__ == '__main__':
##    for user in [('negar', 1000),('samira', 300),('soheil', 300)]:
##       set_user_account( user[0], user[1] )     
    payment = Payment()
    payment.run_server()
