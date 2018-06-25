#!/usr/bin/env python
##################################################################
# Copyright (c) 2015
# Oct 2015 - 
# Version 0.1, Last change on Nov 02, 2015    
##################################################################

# All functions needed to implement Dot Client server 


import json, datetime
import time
import state_dic_related as states
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from twisted.internet import reactor, protocol
from libDiameter import *
from diam_related import *
from constants import *



#----------------------------------------------------------------------
# global variables
#----------------------------------------------------------------------

"""
used for saving state and waiting req_id of specific session.
Details of this dictionary can be found in state_dic_related module.
"""
state_dic = {}


"""
user_email_dic is used for saving user email related to specific session
and notify the user through email

Format of user email dictionary:

user_email_dic = { session_id :{"username" : username,
                                "app_id" : app_id,
                                "email" : user_email,
                                "user_transport": user_transport
                                } }

user email dictionary contains:
    session_id      - The session id for the running app
    username        - The username
    app_id          - The application id which is submitted by user
    user_email      - The user email
    user_transport  - The transport of the user which can send data to
                      user through
"""
user_email_dic = {}

#----------------------------------------------------------------------
# Routines related to state_dic
#----------------------------------------------------------------------      

set_state               = lambda session_id, state:\
                                        states.set_state(
                                                        state_dic,
                                                        session_id,
                                                        state )
get_state               = lambda session_id:\
                                        states.get_state(
                                                        state_dic,
                                                        session_id )
set_wait_req            = lambda session_id, req_id, req_transport:\
                                        states.set_wait_req(
                                                        state_dic,
                                                        session_id,
                                                        req_id,
                                                        req_transport )
get_wait_req            = lambda session_id:\
                                        states.get_wait_req(
                                                        state_dic,
                                                        session_id )
get_wait_req_transport  = lambda session_id, req_id:\
                                        states.get_wait_req_transport(
                                                        state_dic,
                                                        session_id,
                                                        req_id )
pop_wait_req            = lambda session_id :\
                                        states.pop_wait_req(
                                                        state_dic,
                                                        session_id )
has_session_id          = lambda session_id:\
                                        states.has_session_id(
                                                        state_dic,
                                                        session_id )

#----------------------------------------------------------------------
# Routines related to user_email_dic
#----------------------------------------------------------------------
def set_user_email_dic( session_id, username, app_id, email,
                        user_transport ):
    """
    Set email,username, app_id and user transport for user that
    submitted application with specific session_id
    """
    user_email_dic[ session_id ] = { "username" : username,
                                     "app_id" : app_id,
                                     "email" : email,
                                     "user_transport": user_transport } 

def get_user_email_dic( session_id ):
    """
    Get email of user that submitted application with specific
    session_id
    """
    try:
        return user_email_dic[ session_id ]
    except:
        return

def get_username( session_id ):
    """
    Get username of the user that submitted application with
    specific session_id
    """
    try:
        return user_email_dic[ session_id ][ "username" ]
    except:
        return

def get_app_id( session_id ):
    """
    Get app_id of the application with specific session_id
    which is submitted by user 
    """
    try:
        return user_email_dic[ session_id ][ "app_id" ]
    except:
        return

def get_user_email( session_id ):
    """
    Get user email of the user that submitted application with
    specific session_id
    """
    try:
        return user_email_dic[ session_id ][ "email" ]
    except:
        return

def get_user_transport( session_id ):
    """
    Get user transport of the user that submitted application with
    specific session_id
    """
    try:
        return user_email_dic[ session_id ][ "user_transport" ]
    except:
        return
    
#----------------------------------------------------------------------
# DotClient class
#----------------------------------------------------------------------  
class DotClient:
    """
    The DotClient class
    """

    #------------------------------------------------------------------
    # request received handler
    #------------------------------------------------------------------
    def handle_req_received(self, req, transport):
        """
        As soon as request received from other servers ,
        this function is called.
        """

        # Determine if the request sent form user or other servers
        try:
            user_app_info = json.loads( req )
            sent_by_servers = False
        except:
            sent_by_servers = True

        #If the request sent by other servers (sent_by_servers == True)
        if sent_by_servers:
            req_avps = return_request_avps( req )
            req_action = get_request_action_from_avps( req_avps )
            session_id = get_session_id_from_avps( req_avps )
            state = get_state( session_id )

            # received update notification from Provisioning ( NUAR )   
            if not req_action and state == OPEN_D and \
                 get_request_type_from_avps( req_avps )== UPDATE_REQUEST:
                    self.handle_update_notification_request( req_avps, transport )
            else:
                print "The message is not allowed to request "+\
                      "in this state!"
            return
        
        #If the request sent by user (sent_by_servers == False)
        request = user_app_info["request"]
        username = str( user_app_info["username"] )
        password = str( user_app_info["password"] )
        app_id = int( user_app_info["app_id"] )

        if request == USER_START_REQ:
            email = str( user_app_info["email"] )
            topo_url = str( user_app_info["topo_url"] )
            self.handle_user_start_request( username, password, app_id,
                                            email, topo_url, topo_url,
                                            transport )
            
        elif request == USER_TERMINATE_REQ:
            self.handle_user_terminate_request( username, password,
                                                app_id, transport )

            
            # For START:
            # retrieve data from aa to see if there is session_id for this user
            # with this app id
            # If there is beforehand session_id, the state should be
            # idle for start request

            # For TERMINATE:
            # The state should be OPEN_D
    
    #------------------------------------------------------------------
    # response received handler
    #------------------------------------------------------------------       
    def handle_res_received(self, res, additional_info ):
        """
        As soon as response received from other servers ,
        this function is called.
        """

        res_avps = return_request_avps( res )
        res_action = get_request_action_from_avps( res_avps )
        session_id = get_session_id_from_avps( res_avps )
        state = get_state( session_id )

        # received AA response from AA server ( AAR )
        if not res_action and \
           not get_request_type_from_avps( res_avps ) and \
           return_command_id( res ) == AA_REQUEST:
                self.handle_aa_response( res_avps, additional_info )
       
        # received provision topo response from Prov ( PATA )
        elif res_action == PROV_APP_TOPO and state == PENDING_DP:
            self.handle_prov_app_topo_response( res_avps )

        # received start iot app response from Prov( SIAA )  
        elif res_action == START_IOT_APP and state == PENDING_DD:
            self.handle_prov_start_app_response( res_avps )

        # received terminate response from Prov ( TIAA )   
        elif not res_action and state == PENDING_DT and \
             get_request_type_from_avps( res_avps )== TERMINATE_REQUEST:
                self.handle_prov_terminate_response( res_avps,
                                                     additional_info )
   
    #------------------------------------------------------------------
    # handle received requests
    #------------------------------------------------------------------
    def handle_user_start_request( self, username, password, app_id,
                                   email, topo_url, sub_url,
                                   req_transport ):
        """
        Handle the start request which is received from user
        """
        print
        print "Received 'Start' request "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "from user with "+\
              "username = %s and app_id = %s"%( username, app_id )
        print "-"*64
        
        session_id = self.create_session_id( username, app_id )
        aa_request = self.create_aa_request(
                                        session_id = session_id,
                                        app_id = app_id,
                                        origin_host = "orghost.com",
                                        origin_realm = "orgrealm.com",
                                        dest_realm = "desrealm.com",
                                        user_name = username,
                                        user_pass = password )
        self.send_to_aa( aa_request, { "email":email,
                                       "session_id":session_id,
                                       "request":USER_START_REQ,
                                       "user_transport":req_transport,
                                       "app_topology":topo_url,
                                       "sub_plan":sub_url
                                       } )
    

    def handle_user_terminate_request(  self, username, password,
                                        app_id, req_transport ):
        """
        Handle the Terminate request which is received from user
        """
        print
        print "Received 'Terminate' request "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "from user with "+\
              "username = %s and app_id = %s"%( username, app_id )
        print "-"*64
        
        session_id = self.create_session_id( username, app_id )
        aa_request = self.create_aa_request(
                                        session_id = session_id,
                                        app_id = app_id,
                                        origin_host = "orghost.com",
                                        origin_realm = "orgrealm.com",
                                        dest_realm = "desrealm.com",
                                        user_name = username,
                                        user_pass = password )
        self.send_to_aa( aa_request, { "session_id":session_id,
                                       "request":USER_TERMINATE_REQ,
                                       "user_transport":req_transport
                                       } )
    
    def handle_update_notification_request( self, req_avps, req_transport ):
        """
        Handle the update notification request which is received
        from Provisioning server ( NUAR ).
        """

        session_id = get_session_id_from_avps( req_avps )
        
        print
        print "Received 'NUAR' request from Provisioning Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with Session-Id = %s "%session_id+\
              "and Request-Id = %s"%get_request_id_from_avps(req_avps)
        print "-"*64
        
        nuaa = self.create_update_notification_response( req_avps )
        req_transport.write( nuaa )   

        # Send a notification email to the user
        email = get_user_email( session_id )
        username = get_username( session_id )
        app_id = get_app_id( session_id )

        message = "Dear %s, As your credit for the "%username+\
                  "application with the '%s' id "%app_id+\
                  "is going to finish and your "+\
                  "application is running on 'Automatic Update' "+\
                  "mode, we have just charged you automatically."
        self.send_notification_email( email,
                                      username,
                                      app_id,
                                      message )
        
    #------------------------------------------------------------------
    # handle received responses
    #------------------------------------------------------------------
    def handle_aa_response( self, res_avps, additional_info ):
        """
        Handle AA response which is received from AA server ( AAA ).
        """
        request_type = additional_info[ "request" ]

        if request_type == USER_START_REQ:
            self.handle_start_aa_response( res_avps, additional_info )

        else:
            self.handle_terminate_aa_response( res_avps, additional_info )


    def handle_start_aa_response( self, res_avps, additional_info ):
        """
        Handle aa response which is received from AA server( AAR ).
        """

        print
        print "Received 'aa' response from aa Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the result_code = "+\
              "%s"%get_result_code_from_avps( res_avps )
        print "-"*64
        
        last_created_session_id = additional_info[ "session_id" ]
        session_id = get_session_id_from_avps( res_avps )
        state = get_state( session_id )

        # The session_id is not exist beforehand
        if last_created_session_id == session_id:
            req_transport = additional_info[ "user_transport" ]
            result_code = get_result_code_from_avps( res_avps )
            # AAR result code shows that Athentication was failed
            if result_code == AA_UNKNOWN_USER:
                usr_start_response = "Athentication was failed!"
                req_transport.write( usr_start_response )
                return            
        # Return an error message to user if he requested to start
        # the app which is running now
        elif state != None and state != IDLE_D:
            app_id = res_avps[ "Auth-Application-Id" ]
            usr_start_response = "Since the application with "+\
                                 "id='%i' is "%app_id+\
                                 "now running,The request of starting "+\
                                 "app is not accepted!"
            req_transport = additional_info[ "user_transport" ]
            req_transport.write( usr_start_response )
            return
        # set state, set user info and send a PATR request to prov
        set_state( session_id, PENDING_DP )
        set_user_email_dic( session_id, res_avps[ "User-Name" ],
                            res_avps[ "Auth-Application-Id" ],
                            additional_info[ "email" ],
                            additional_info[ "user_transport" ] )

        app_topology = additional_info[ "app_topology" ]
        sub_plan = additional_info[ "sub_plan" ]
                                      
        patr_request = self.create_prov_app_topo_request( res_avps,
                                                          app_topology,
                                                          sub_plan )
        self.send_to_prov( patr_request )


    def handle_terminate_aa_response( self, res_avps, additional_info ):
        """
        Handle aa response which is received from AA server( AAR ).
        """

        print
        print "Received 'aa' response from aa Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the result_code = "+\
              "%s"%get_result_code_from_avps( res_avps )
        print "-"*64
        
        last_created_session_id = additional_info[ "session_id" ]
        session_id = get_session_id_from_avps( res_avps )
        state = get_state( session_id )

        # The session_id is not exist beforehand
        if last_created_session_id == session_id:
            req_transport = additional_info[ "user_transport" ]
            result_code = get_result_code_from_avps( res_avps )
            # AAR result code shows that Athentication was failed
            if result_code == AA_UNKNOWN_USER:
                usr_start_response = "Athentication was failed!"
                req_transport.write( usr_start_response )
                return
            else:
                app_id = res_avps[ "Auth-Application-Id" ]
                usr_start_response = "There is no running "+\
                                     "application with id='%i' !"%app_id
                req_transport.write( usr_start_response )
                return
                
        # Return an error message to user if he requested to terminate
        # the app which is not running now( The state of app is not Open )
        elif state != OPEN_D:
            app_id = res_avps[ "Auth-Application-Id" ]
            usr_start_response = "There is no running "+\
                                 "application with id='%i' !"%app_id
            req_transport = additional_info[ "user_transport" ]
            req_transport.write( usr_start_response )
            return
        
        # set state, and send a TIAR request to prov
        set_state( session_id, PENDING_DT )                                      
        tiar_request = self.create_prov_terminate_request( res_avps )
        self.send_to_prov( tiar_request, additional_info )

    
    def handle_prov_app_topo_response( self, res_avps ):
        """
        Handle the provisioning application topology response which
        is received from Provisioning server ( PATA ).
        """
         
        # Check the result code; return if is not success
        result_code = get_result_code_from_avps( res_avps )
        if result_code != SUCCESS:
            print "The result code of PATA is not success!"
            return 

        print
        print "Received 'PATA' response from Provisioning Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the result_code = %s, "%result_code+\
              "Session-Id = %s "%get_session_id_from_avps(res_avps)
        print "and Request-Id = %s"%get_request_id_from_avps(res_avps)
        print "-"*64
        
        # set state and send SIAR request to prov
        session_id = get_session_id_from_avps( res_avps )            
        set_state( session_id, PENDING_DD )

        pata = self.create_prov_start_app_request( res_avps )               
        self.send_to_prov( pata )

    def handle_prov_start_app_response(  self, res_avps ):
        """
        Handle the start iot app response which is received from
        Provisioning server ( SIAA ).
        """

        session_id = get_session_id_from_avps( res_avps )

        user_transport = get_user_transport( session_id )
        result_code = get_result_code_from_avps( res_avps )

        print
        print "Received 'SIAA' response from Provisioning Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the result_code = %s, "%result_code+\
              "Session-Id = %s "%session_id
        print "and Request-Id = %s"%get_request_id_from_avps(res_avps)
        print "-"*64

        # AAR result code shows that Athentication was failed
        if result_code != SUCCESS:
            usr_start_response = "Starting Service was failed!"
            # set state to IDLE_D if stating service was failed.
            set_state( session_id, IDLE_D )
        else:
            usr_start_response = "The requested Service has "+\
                                 "been started successfully!"
            # set state to OPEN_D if service has been
            # startes successfully
            set_state( session_id, OPEN_D )

        print
        print "Send the response of 'start' request "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "to user with username = %s "%get_username( session_id )+\
              "and app_id = %s"%get_app_id( session_id )
        print "-"*64
        user_transport.write( usr_start_response )

                
    
    def handle_prov_terminate_response( self, res_avps,
                                        additional_info ):
        """
        Handle the terminate response which is received from
        Provisioning server ( TIAA ).
        """
        session_id = get_session_id_from_avps( res_avps )

        user_transport = additional_info[ "user_transport" ]
        result_code = get_result_code_from_avps( res_avps )

        print
        print "Received 'TIAA' response from Provisioning Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the result_code = %s, "%result_code+\
              "Session-Id = %s "%session_id
        print "and Request-Id = %s"%get_request_id_from_avps(res_avps)
        print "-"*64

        # Termination was failed
        if result_code != SUCCESS:
            usr_start_response = "Service Termination was failed!"
            # set state to IDLE_D if terminating service was failed.
            set_state( session_id, IDLE_D )
        # Termination has been done successfully
        else:
            usr_start_response = "The Service has "+\
                                 "been terminated successfully!"
            # set state to OPEN_D if service has been
            # terminated successfully
            set_state( session_id, IDLE_D )

        print
        print "Send the response of 'terminate' request "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "to user with username = %s "%get_username( session_id )+\
              "and app_id = %s"%get_app_id( session_id )
        print "-"*64
        user_transport.write( usr_start_response )
        
    #------------------------------------------------------------------
    # create requests
    #------------------------------------------------------------------
    def create_aa_request(  self, session_id, app_id,
                            origin_host, origin_realm, dest_realm,
                            user_name, user_pass,
                            auth_request_type = AUTHENTICATE_ONLY,
                            auth_session_state = NO_STATE_MAINTAINED ):
        """
        Create aa request which is sent to AA server( AAR ).
        """
        
        # add required AVPs to avps list object
        req_avps=[]
        req_avps.append(encodeAVP("Session-Id",session_id))
        req_avps.append(encodeAVP("Auth-Application-Id",app_id))
        req_avps.append(encodeAVP("Origin-Host",origin_host))
        req_avps.append(encodeAVP("Origin-Realm",origin_realm))
        req_avps.append(encodeAVP("Destination-Realm",dest_realm))
        req_avps.append(encodeAVP("Auth-Request-Type",auth_request_type))
        req_avps.append(encodeAVP("User-Name",user_name))
        req_avps.append(encodeAVP("Password",user_pass))
        req_avps.append(encodeAVP("Auth-Session-State",auth_session_state))

        # create header and set required settings for ARR
        arr = HDRItem()
        arr.cmd = dictCOMMANDname2code('AA')
        initializeHops( arr )
        req = createReq( arr, req_avps )

        print
        print "Send 'aa' request to aa Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "for the user with "+\
              "username = %s and app_id = %s"%( user_name, app_id )
        print "-"*64
        
        return req.decode("hex")
    

    def create_prov_app_topo_request( self, avps,
                                      app_topology,
                                      subscription_plan ):
        """
        Create the provisioning application topology request which
        is sent to Provisioning server ( PATR ).
        """

        # add required AVPs to request avps object
        req_avps=[]
        for avp in [ "Session-Id", "Origin-Host",
                     "Origin-Realm", "Destination-Realm",
                     "User-Name" ]:
            req_avps.append(encodeAVP( avp, avps[avp]))

        req_id = create_req_id()
        req_avps.append(encodeAVP("Request-Id",req_id))
        req_avps.append(encodeAVP("Request-Type",PROV_REQ))
        req_avps.append(encodeAVP("Dot-Requested-Action",
                                  PROV_APP_TOPO ))
        req_avps.append(encodeAVP("App-Topology",app_topology))
        req_avps.append(encodeAVP("Subscription-Plan",
                                  subscription_plan ) )

        # create header and set required settings for PATR
        patr = HDRItem()
        patr.cmd = dictCOMMANDname2code('DoT-Request')
        initializeHops( patr )
        req = createReq( patr, req_avps )

        print
        print "Send 'PATR' request to Provisioning Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%req_id
        print "-"*64
        
        return req.decode("hex")

    
    def create_prov_start_app_request(  self, avps ):
        """
        Create the start iot app request which is sent to
        Provisioning server ( SIAR ).
        """

        # add required AVPs to request avps object
        req_avps=[]
        for avp in [ "Session-Id", "Origin-Host",
                     "Origin-Realm", "Destination-Realm",
                     "User-Name" ]:
            req_avps.append(encodeAVP( avp, avps[avp]))

        req_id = create_req_id()
        req_avps.append(encodeAVP("Request-Id", req_id))
        req_avps.append(encodeAVP("Request-Type",PROV_REQ))
        req_avps.append(encodeAVP("Dot-Requested-Action",
                                  START_IOT_APP ))

        # create header and set required settings for PATR
        siar = HDRItem()
        siar.cmd = dictCOMMANDname2code('DoT-Request')
        initializeHops( siar )
        req = createReq( siar, req_avps )

        print
        print "Send 'SIAR' request to Provisioning Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with Session-Id = "+\
              "%s and Request-Id = %s"%( avps["Session-Id"], req_id )
        print "-"*64
        
        return req.decode("hex")
    
    def create_prov_terminate_request(  self, avps ):
        """
        Create terminate IoT app request which is sent
        to Provisioning server( TIAR ).
        """
        
        # add required AVPs to request avps object
        req_avps=[]
        for avp in [ "Session-Id", "Origin-Host",
                     "Origin-Realm", "Destination-Realm",
                     "User-Name" ]:
            req_avps.append(encodeAVP( avp, avps[avp]))
        req_id = create_req_id()
        req_avps.append(encodeAVP("Request-Id", req_id  ))
        req_avps.append(encodeAVP("Request-Type",TERMINATE_REQUEST))

        # create header and set required settings for TIAR
        tiar = HDRItem()
        tiar.cmd = dictCOMMANDname2code('DoT-Request')
        initializeHops( tiar )
        req = createReq( tiar, req_avps )

        print
        print "Send 'TIAR' request to Provisioning Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%req_id
        print "-"*64
        
        return req.decode("hex")
    
    #------------------------------------------------------------------
    # creating responses
    #------------------------------------------------------------------
    
    def create_update_notification_response(  self, avps ):
        """
        Create update notification response which is sent
        to Provisioning server( NUAA ).

        It is for "pay-per-use" and "automatic update" mode.
        """

        # add required AVPs to response avps object
        res_avps=[]
        for avp in [ "Session-Id", "Origin-Host",
                     "Origin-Realm","Destination-Realm",
                     "User-Name", "Request-Type",
                     "Allocation-Unit", "Confirmation-Mode" ]:
            res_avps.append(encodeAVP( avp, avps[avp]))

        req_id = avps["Request-Id"]
        res_avps.append(encodeAVP( "Request-Id", req_id ))
        res_avps.append(encodeAVP( "Result-Code", SUCCESS ))
       
        # create header and set command
        nuaa = HDRItem()
        nuaa.cmd = dictCOMMANDname2code('DoT-Answer')
        initializeHops( nuaa )
        response = createRes( nuaa, res_avps )

        print
        print "Send 'NUAA' response to Provisioning Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%req_id
        print "-"*64
        
        return response.decode("hex")

    #------------------------------------------------------------------
    # Sending message to other servers
    #------------------------------------------------------------------
    def send_to( self, message, host, port, user_additional_info = {},
                 tcp = True ):
        """
        Send a message to other servers.
        """
        
        factory = ClientFactory( self, message, user_additional_info )
        if tcp:
            reactor.connectTCP( host, port, factory )
        else:
            reactor.connectUDP( host, port, factory )
        

    # Send a message to AA Server 
    send_to_aa = lambda self, msg, info = {}: self.send_to( msg,
                                                            AA_HOST,
                                                            AA_PORT,
                                                            info,)

    # Send a message to Provisioning Server 
    send_to_prov = lambda self, msg, info = None: self.send_to( msg,
                                                   PROV_HOST,
                                                   PROV_PORT,
                                                   info )
    
    #------------------------------------------------------------------
    # Dot Client responsibilities
    #------------------------------------------------------------------
    def send_notification_email( self, email, username,
                                 app_id, message ):
        """
        Send an email to user for notifying about update
        """
        
        try:
            from_adres = "dot.mail.2017@gmail.com"
            dot_pass = "dotmail2017"
            to_adres = email

            email_body = MIMEMultipart('alternatief')
            email_body['Subject'] = "Notification Email from DoT"
            email_body['From'] = from_adres
            email_body['To'] = to_adres

            send_massage = MIMEText( message,"plain" )

            email_body.attach( send_massage )
            mail = smtplib.SMTP('smtp.gmail.com',587)
            mail.ehlo()

            mail.starttls()
            mail.login( from_adres, dot_pass )
            mail.sendmail( from_adres, to_adres, email_body.as_string() )
            mail.close()

            print
            print "*"*64
            print "Send update notification email to "+\
                  "'%s' email address "%email
            print "for '%s' "%username+\
                  "that submitted the application "+\
                  "with '%s' id."%app_id
            print "*"*64
        except:
            print "The update notification email could not be sent because "
            print "'%s' is not a valid email address!"%email
            
    def create_session_id( self, username, app_id ):
        """
        Create session_id
        """

        sub_time = str( time.time() )
        session_id = str( username ) + \
                     str( app_id ) + \
                     sub_time[sub_time.find(".")-5 : sub_time.find(".")]
    
        return session_id
    
    #------------------------------------------------------------------
    # Running the server
    #------------------------------------------------------------------        
    def run_server(self):
        """
        Run the DotClient server.
        """
        factory = ServerFactory( self )
        reactor.listenTCP( DOT_PORT,factory )
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
# Client protocol
#---------------------------------------------------------------------- 
class ClientProtocol(protocol.Protocol):
    """
    The client protocol is used when the dot server act as a
    client to send message for other servers
    """
    
    def __init__(self, factory, dot_server, message, additional_info ):
        """
        initialization of ClientProtocol class
        """
        self.message = message
        self.dot_server = dot_server
        self.additional_info = additional_info
        
    def connectionMade(self):
        """
        As soon as the connection is made, this function is called and
        send the message to the server.
        """
        self.transport.write(self.message)
        #self.transport.loseConnection()
        
    def dataReceived(self, data):
        """
        As soon as data received to the server, this function is called.
        """
        self.dot_server.handle_res_received(data, self.additional_info)
        self.transport.loseConnection()

#----------------------------------------------------------------------
# Client Factory
#---------------------------------------------------------------------- 
class ClientFactory(protocol.ClientFactory):
    
    def __init__(self, dot_server, message, additional_info ):
        """
        initialization of ClientFactory class
        """
        self.message = message
        self.additional_info = additional_info
        self.dot_server = dot_server
        
    def clientConnectionFailed(self, connector, reason):
        """
        As soon as connection was failed, this function is called.
        """
        print "Connection failed"
        #reactor.stop()
    
##    def clientConnectionLost(self, connector, reason):
##        """
##        As soon as connection was lost, this function is called.
##        """
##        print "Connection lost"
##        #reactor.stop()
        
    def buildProtocol(self, addr):
        """
        return the ClientProtocol as its factory
        """
        return ClientProtocol(self, self.dot_server, self.message,
                              self.additional_info )

#----------------------------------------------------------------------
# run-time execution
#---------------------------------------------------------------------- 
if __name__ == '__main__':
    dot_client = DotClient()
    dot_client.run_server()
