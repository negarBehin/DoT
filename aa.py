#!/usr/bin/env python
##################################################################
# Copyright (c) 2015
# Oct 2015 - 
# Version 0.1, Last change on Nov 02, 2015    
##################################################################

# All functions needed to implement AA server 

import datetime

from twisted.internet import reactor, protocol

from aa_server_db import *
from libDiameter import *
from diam_related import *

from constants import *
   
#----------------------------------------------------------------------
# AA class
#----------------------------------------------------------------------  
class AA:
    """
    The AA class
    """
    
    #------------------------------------------------------------------
    # handle received requests
    #------------------------------------------------------------------
    def handle_req_received( self, req, req_transport ):
        """
        Handle aa request which is received from
        Dot Client server( AAR ).
        """
        req_avps = return_request_avps( req )

        session_id          = req_avps[ "Session-Id" ]
        app_id              = req_avps[ "Auth-Application-Id" ]
        origin_host         = req_avps[ "Origin-Host" ]
        origin_realm        = req_avps[ "Origin-Realm" ]
        dest_realm          = req_avps[ "Destination-Realm" ]
        auth_request_type   = req_avps[ "Auth-Request-Type" ]
        auth_session_state  = req_avps[ "Auth-Session-State" ]
        user_name           = req_avps[ "User-Name" ]
        user_pass           = req_avps[ "Password" ]


        print
        print "received 'aa' request from Dot Client Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with username = %s "%user_name+\
              "and app_id = %s"%app_id
        print "-"*64
        
        # Connect to user db and Check if user existance
        conn = connect_user_db()
        user_existed = exist_user( conn, user_name, user_pass )

        # if user existance is false, return the aa response with
        # not successful result code
        if not user_existed:
            result_code = AA_UNKNOWN_USER
            aa_response = self.create_aa_response( session_id, app_id,
                                                   origin_host,
                                                   origin_realm,
                                                   dest_realm,
                                                   auth_request_type,
                                                   auth_session_state,
                                                   user_name,
                                                   user_pass,
                                                   result_code )
            req_transport.write( aa_response )
            return            

        # if user existance is true
        result_code = AA_SUCCESS
        session_existed = exist_session( conn, user_name, user_pass,
                                         app_id )

        # if session is exist in db, set the session_id in response to
        # retrieved session_id from db
        if session_existed:
            session_id      = session_existed
        else:
            insert_app_session_id( conn, user_name, user_pass,
                                   app_id, session_id )
        result_code = AA_SUCCESS
        aa_response = self.create_aa_response( session_id, app_id,
                                               origin_host,
                                               origin_realm,
                                               dest_realm,
                                               auth_request_type,
                                               auth_session_state,
                                               user_name,
                                               user_pass, result_code )
        req_transport.write( aa_response )

    #------------------------------------------------------------------
    # creating responses
    #------------------------------------------------------------------
    def create_aa_response(  self, session_id, app_id,
                             origin_host, origin_realm, dest_realm,
                             auth_request_type,
                             auth_session_state,
                             user_name, user_pass,
                             result_code  ):
        """
        Create aa response which is sent to
        Dot Client server( AAR ).
        """

         # add required AVPs to avps list object
        res_avps=[]
        res_avps.append(encodeAVP("Session-Id",session_id))
        res_avps.append(encodeAVP("Auth-Application-Id",app_id))
        res_avps.append(encodeAVP("Auth-Request-Type",auth_request_type))
        res_avps.append(encodeAVP("Origin-Host",origin_host))
        res_avps.append(encodeAVP("Origin-Realm",origin_realm))
        res_avps.append(encodeAVP("Destination-Realm",dest_realm))
        res_avps.append(encodeAVP("User-Name",user_name))
        res_avps.append(encodeAVP("Auth-Session-State",auth_session_state))
        res_avps.append(encodeAVP("Result-Code",result_code))       

        # in Failur cases Error-Message, Error-Reporting-Host
        # and Failed-AVP should be set

        # create header and set required settings for ARR
        arr = HDRItem()
        arr.cmd = dictCOMMANDname2code('AA')
        initializeHops( arr )
        res = createRes( arr, res_avps)

        print
        print "Send 'aa' response to Dot Client Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with result_code = %s "%result_code+\
              ", username = %s "%user_name+\
              ", app_id = %s "%app_id
        print "and finalized session_id = %s "%session_id
        print "-"*64
        
        return res.decode("hex")
    
    #------------------------------------------------------------------
    # Running the server
    #------------------------------------------------------------------        
    def run_server(self):
        """
        Run the AA server.
        """
        factory = ServerFactory( self )
        reactor.listenTCP( AA_PORT,factory )
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
    aa = AA()
    aa.run_server()
