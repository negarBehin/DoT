#!/usr/bin/env python
##################################################################
# Copyright (c) 2015
# Oct 2015 - 
# Version 0.1, Last change on Oct 29, 2015    
##################################################################

# All functions needed to implement Resource Control server 

import datetime

import state_dic_related as states

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
used for saving plan and topology of specific session.
"""
plan_topo_dic = {}


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
# Routines related to plan_topo_dic
#----------------------------------------------------------------------

def set_plan_topo_dic( session_id, plan_uri, topo_uri ):
    """
    Set plan uri and topo uri for specific session_id.
    """
    plan_topo_dic[ session_id ] = { "plan_uri" : plan_uri,
                                    "topo_uri" : topo_uri } 

def get_plan_topo_dic( session_id ):
    """
    Get the plan and topo for the specific session_id.
    """
    try:
        return plan_topo_dic[ session_id ]
    except:
        return

def get_plan( session_id ):
    """
    Get the plan for the specific session_id.
    """
    try:
        return plan_topo_dic[ session_id ][ "plan_uri" ]
    except:
        return

def get_topo( session_id ):
    """
    Get the topo for the specific session_id.
    """
    try:
        return plan_topo_dic[ session_id ][ "topo_uri" ]
    except:
        return

"""
used for saving credit info of specific session.
"""
credit_dic = {}

#----------------------------------------------------------------------
# Routines related to credit_dic
#----------------------------------------------------------------------

# ** Its value should be retrived from plan and set to dictionary
def set_credit_dic( session_id, #last_usage = 0,
                    primary_credit = 500,
                    # In the first use, it's equal to primary_credit
                    #current_credit = 500,
                    # It's a percentage of primary_credit
                    credit_threshold = 0.35 ):
    """
    Set list of agents for specific session_id.
    """
    credit_dic[ session_id ] = {
                    "last_usage" : 0,
                    "primary_credit" :primary_credit,
                    "current_credit" : primary_credit,
                    "credit_threshold" :credit_threshold*primary_credit
                    }

def update_credit_dic( session_id, app_usage ):
    """
    update the credit dictionary.
    """

    credit_dic[session_id]["last_usage"] += app_usage
    credit_dic[session_id]["current_credit"] -= app_usage

def met_credit_threshold( session_id ):
    """
    Define if the credit threshold has been met met or no.
    """

    return credit_dic[session_id]["current_credit"]<=\
           credit_dic[session_id]["credit_threshold"]
    
def allocate_credit( session_id ):
    """
    Allocate more credit to user.
    """
    credit_dic[session_id]["current_credit"] += \
                            credit_dic[session_id]["primary_credit"]

def return_current_credit( session_id ):
    """
    return current credit.
    """
    return credit_dic[session_id]["current_credit"]

def return_total_usage( session_id):
    """
    return the total usage of the user
    from starting the application
    """
    return credit_dic[session_id]["last_usage"]
#----------------------------------------------------------------------
# ResourceControl class
#----------------------------------------------------------------------  
class ResourceControl:
    """
    The Resource Control class
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
        state = get_state( session_id )

        # Received resource alloc request from provisioning
        if req_action == APP_RESOURCE_ALLOCATION and \
           ( not state or state == IDLE_R ):
            self.handle_prov_resource_alloc_request( req_avps,
                                                     transport )
        
        # Received get app specification request from metering
        elif req_action == GET_APP_SPECIFICATION and state == OPEN_R:
            self.handle_mtr_get_spec_request( req_avps, transport )

        # Received publish usage update request from metering   
        elif req_action == PUBLISH_USAGE_UPDATE and state == OPEN_R:
            self.handle_mtr_pub_usage_update_request( req_avps,
                                                      transport )

        # Received terminate request from provisioning
        elif not req_action and state == OPEN_R and \
             get_request_type_from_avps( req_avps )== TERMINATE_REQUEST:
                self.handle_rcs_terminate_request( req_avps, transport )
        else:
            print "The message is not allowed to request in this state!"
            
    #------------------------------------------------------------------
    # response received handler
    #------------------------------------------------------------------        
    def handle_res_received(self, res):
        """
        As soon as response received from other servers ,
        this function is called.
        """

        res_avps = return_request_avps( res )
        res_action = get_request_action_from_avps( res_avps )
        session_id = get_session_id_from_avps( res_avps )
        state = get_state( session_id )

        # Received commit app response from metering
        if res_action == COMMIT_APP_METERING and state == PENDING_RME:
            self.handle_mtr_commit_response( res_avps )
        
        # Received start bill response from payment
        elif res_action == START_BILL_PAYMENT and state == PENDING_RPY:
            self.handle_pay_start_bill_response( res_avps )

        # Received lock user credit response from payment   
        elif  res_action == LOCK_USER_CREDIT :
            if state == PENDING_RPP:
                interrogation = "first"
            elif state == PENDING_RPL:
                interrogation = "intermediate"
            else:
                return
            self.handle_pay_lock_credit_response( res_avps,
                                                  interrogation )
        # Received update notification response from Provisioning ( NUAA )
        elif not res_action and state == PENDING_RNU and \
             get_request_type_from_avps( res_avps )== UPDATE_REQUEST:
            self.handle_update_notification_response( res_avps )
            
    #------------------------------------------------------------------
    # handle received requests
    #------------------------------------------------------------------
    def handle_prov_resource_alloc_request( self, req_avps,
                                            req_transport ):
        """
        Handle the resource allocation request which is received from
        Provisioning server ( ARAR ).
        """

        session_id = get_session_id_from_avps( req_avps )

        print
        print "Received 'ARAR' request from Provisioning Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with Session-Id = %s "%session_id+\
              "and Request-Id = %s"%get_request_id_from_avps(req_avps)
        print "-"*64
        
        # Reserve resources based on the app plan
        plan_uri = req_avps[  "App-Topology" ]
        topo_uri = req_avps[  "Subscription-Plan" ]

        set_plan_topo_dic( session_id, plan_uri, topo_uri )
        self.reserve_resources( session_id, plan_uri, topo_uri )

        # set state and waiting request and send a LUCA request to Payment
        # Server for lucking the credit
        set_state( session_id, PENDING_RPP )
        
        req_id = get_request_id_from_avps( req_avps )
        set_wait_req( session_id, req_id, req_transport )

        lucr_request = self.create_pay_lock_credit_request( req_avps )               
        self.send_to_pay( lucr_request )


    def handle_mtr_get_spec_request(  self, req_avps, req_transport ):
        """
        Handle the get specification request which is received from
        Metering server ( GASR ).
        """
        
        session_id = get_session_id_from_avps( req_avps )

        print
        print "Received 'GASR' request from Metering Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with Session-Id = %s "%session_id+\
              "and Request-Id = %s"%get_request_id_from_avps(req_avps)
        print "-"*64
        
        plan_uri = get_plan( session_id )   
        # send GASA response to Metering

        gasa = self.create_mtr_get_spec_response( req_avps,
                                                  plan_uri )               
        req_transport.write( gasa )
        
    
    def handle_mtr_pub_usage_update_request( self, req_avps,
                                             req_transport ):
        """
        Handle the publishing usage update request which is received
        from Metering server ( PUUR ).
        """

        session_id = get_session_id_from_avps( req_avps )
        
        print
        print "Received 'PUUR' request from Metering Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with Session-Id = %s "%session_id+\
              "and Request-Id = %s"%get_request_id_from_avps(req_avps)
        print "-"*64
           
        # send PUUA( of Metering ) response to Metering Server
        puua = self.create_mtr_pub_usage_update_response(req_avps)               
        req_transport.write( puua )

        # Update credit and usage according to received app_usage
        app_usage = req_avps[ "App-Usage" ]
        update_credit_dic( session_id, app_usage )
        if met_credit_threshold(session_id):
            set_state( session_id, PENDING_RPL )
            lucr_request = self.create_pay_lock_credit_request( req_avps )               
            self.send_to_pay( lucr_request )
            
    def handle_rcs_terminate_request( self, req_avps, req_transport ):
        """
        Handle the terminate request ( release alloc resource request )
        which is received from Provisioning server ( ARRR ).
        """

        session_id = get_session_id_from_avps( req_avps )
        
        print
        print "Received 'ARRR' request from Provisioning Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with Session-Id = %s "%session_id+\
              "and Request-Id = %s"%get_request_id_from_avps(req_avps)
        print "-"*64

        # Release the allocated resources to the application
        self.release_alloc_resources()
        print
        print "The resources allocated to the application "+\
              "with Session-Id = %s "%session_id
        print "and Request-Id = %s "%get_request_id_from_avps(req_avps)+\
              "has been released."
        print "-"*64

        # set state and send CAMR request to Metering
        set_state( session_id, PENDING_RME )
        
        req_id = get_request_id_from_avps( req_avps )
        set_wait_req( session_id, req_id, req_transport )

        camr_request = self.create_mtr_commit_request( req_avps )               
        self.send_to_mtr( camr_request )

        
    #------------------------------------------------------------------
    # handle received responses
    #------------------------------------------------------------------
    def handle_mtr_commit_response(  self, res_avps  ):
        """
        Handle metering commit response which is received from
        Metering server( CAMA ).
        """

        session_id = get_session_id_from_avps( res_avps )
        
        print
        print "Received 'CAMA' response from Metering Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the result_code "+\
              "= %s, "%get_result_code_from_avps( res_avps )+\
              "Session-Id = %s "%session_id
        print "and Request-Id = %s"%get_request_id_from_avps(res_avps)
        print "-"*64

        # set state and send SBPR request to Payment
        set_state( session_id, PENDING_RPY )

        app_usage = res_avps[ "App-Usage" ]
        update_credit_dic( session_id, app_usage )
            
        sbpr_request = self.create_pay_start_bill_request( res_avps )               
        self.send_to_pay( sbpr_request )

    def handle_pay_start_bill_response(  self, res_avps  ):
        """
        Handle start bill response which is received from
        Payment server( SBPA ).
        """

        session_id = get_session_id_from_avps( res_avps )
        
        print
        print "Received 'SBPA' response from Payment Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the result_code "+\
              "= %s, "%get_result_code_from_avps( res_avps )+\
              "Session-Id = %s "%session_id
        print "and Request-Id = %s"%get_request_id_from_avps(res_avps)
        print "-"*64        

        # set state and send ARRA to prov
        set_state( session_id, IDLE_R )
        ( arrr_req_id, arrr_transport ) = pop_wait_req( session_id )
        arra = self.create_rcs_terminate_response( res_avps,
                                                   arrr_req_id )               
        arrr_transport.write( arra )

    def handle_pay_lock_credit_response(  self, res_avps, interrogation  ):
        """
        Handle lock user credit response which is received from
        Payment server( LUCA ).
        """
        
        # set state and send ARAA to prov
        session_id = get_session_id_from_avps( res_avps )

        print
        print "Received 'LUCA' response from Payment Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the result_code "+\
              "= %s, "%get_result_code_from_avps( res_avps )+\
              "Session-Id = %s "%session_id
        print "and Request-Id = %s"%get_request_id_from_avps(res_avps)
        print "-"*64
        

        set_state( session_id, OPEN_R )
        
        if interrogation == "first":
            ( arar_req_id, arar_transport ) = pop_wait_req( session_id )
            araa = self.create_prov_resource_alloc_response( res_avps,
                                                             arar_req_id)               
            arar_transport.write( araa )

        elif interrogation == "intermediate":
          
            allocate_credit( session_id )
            set_state( session_id, PENDING_RNU )

            print
            print "*"*64
            print "Credit Threshold is met:"
            print "More credit has been allocated to user.The current "
            print "credit for session_id = %s is "%session_id+\
                  "%s"%return_current_credit( session_id )
            print
            print "An update notification will be sent to user "+\
                  "with username = %s"%res_avps[ "User-Name" ]
            print "to notify him that the more credit allocation "+\
                  "has been established!"
            print "*"*64

            nuar = self.create_update_notification_request( res_avps )
            self.send_to_prov( nuar )
            
    def handle_update_notification_response( self, res_avps ):
        """
        Handle update notification response which is received from
        Provisioning server( NUAA ).
        """

        session_id = get_session_id_from_avps( res_avps )
        
        print
        print "Received 'NUAA' response from Provisioning Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the result_code "+\
              "= %s, "%get_result_code_from_avps( res_avps )+\
              "Session-Id = %s "%session_id
        print "and Request-Id = %s"%get_request_id_from_avps(res_avps)
        print "-"*64
        
        set_state( session_id, OPEN_R )
        
    #------------------------------------------------------------------
    # create requests
    #------------------------------------------------------------------
    def create_update_notification_request(  self, avps ):
        """
        Create update notification message which is sent
        to Provisioning server( NUAR ).

        It is for "pay-per-use" and "automatic update" mode.
        """

        # add required AVPs to request avps object
        req_avps=[]
        for avp in [ "Session-Id", "Origin-Host",
                     "Origin-Realm", "Destination-Realm",
                     "User-Name" ]:
            req_avps.append(encodeAVP( avp, avps[avp]))
            
        req_id = create_req_id()
        req_avps.append(encodeAVP("Request-Id", req_id ))
        req_avps.append(encodeAVP("Request-Type", UPDATE_REQUEST ))

        req_avps.append(encodeAVP("Allocation-Unit", CREDIT ))
        req_avps.append(encodeAVP("Confirmation-Mode", NOTIFY_ONLY ))
 
        # create header and set required settings for NUAR
        nuar = HDRItem()
        nuar.cmd = dictCOMMANDname2code('DoT-Request')
        initializeHops( nuar )
        req = createReq( nuar, req_avps )

        print
        print "Send 'NUAR' request to Provisioning Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%req_id
        print "-"*64
        
        return req.decode("hex")


    def create_mtr_commit_request(  self, avps  ):
        """
        Create commit app metering request which is sent
        to Metering server( CAMR ).
        """
        
        # add required AVPs to request avps object
        req_avps=[]
        for avp in [ "Session-Id", "Origin-Host",
                     "Origin-Realm", "Destination-Realm",
                     "User-Name" ]:
            req_avps.append(encodeAVP( avp, avps[avp]))
        req_id = create_req_id()
        req_avps.append(encodeAVP( "Request-Id", req_id  ))
        req_avps.append(encodeAVP( "Request-Type", METER_REQUEST ))
        req_avps.append(encodeAVP( "Dot-Requested-Action",
                                   COMMIT_APP_METERING ))

        # create header and set required settings for CAMR
        camr = HDRItem()
        camr.cmd = dictCOMMANDname2code('DoT-Request')
        initializeHops( camr )
        req = createReq( camr, req_avps )

        print
        print "Send 'CAMR' request to Metering Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%req_id
        print "-"*64
        
        return req.decode("hex")

    def create_pay_start_bill_request(  self, avps  ):
        """
        Create start bill request which is sent
        to Payment server( SBPR ).
        """

        session_id = avps["Session-Id"]
        # add required AVPs to request avps object
        req_avps=[]
        for avp in [ "Session-Id", "Origin-Host",
                     "Origin-Realm", "Destination-Realm",
                     "User-Name" ]:
            req_avps.append(encodeAVP( avp, avps[avp]))
        req_id = create_req_id()
        req_avps.append(encodeAVP( "Request-Id", req_id  ))
        req_avps.append(encodeAVP( "Request-Type", PAY_REQUEST ))
        req_avps.append(encodeAVP( "Dot-Requested-Action",
                                   START_BILL_PAYMENT ))
        req_avps.append(encodeAVP( "App-Usage",
                                   return_total_usage(
                                       session_id )))
        req_avps.append(encodeAVP("Billable-Artifact",
                                  avps["Billable-Artifact"] ))

        # create header and set required settings for SBPR
        sbpr = HDRItem()
        sbpr.cmd = dictCOMMANDname2code('DoT-Request')
        initializeHops( sbpr )
        req = createReq( sbpr, req_avps )

        print
        print "Send 'SBPR' request to Payment Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%session_id+\
              "and Request-Id = %s"%req_id
        print "-"*64
        
        return req.decode("hex")

    def create_pay_lock_credit_request(  self, avps ):
        """
        Create lock user credit request which is sent
        to Payment server( LUCR ).
        """

        # add required AVPs to request avps object
        req_avps=[]
        for avp in [ "Session-Id", "Origin-Host",
                     "Origin-Realm", "Destination-Realm",
                     "User-Name" ]:
            req_avps.append(encodeAVP( avp, avps[avp]))

        if avps.has_key("App-Topology") and avps.has_key("Subscription-Plan"):
            plan = avps["Subscription-Plan"]
            topo = avps["App-Topology"]            
        else:
            session_id = avps[ "Session-Id" ]
            plan = get_plan( session_id )
            topo = get_topo( session_id )              
        req_avps.append(encodeAVP( "Subscription-Plan", plan ))
        req_avps.append(encodeAVP( "App-Topology", topo ))
            
        req_id = create_req_id()
        req_avps.append(encodeAVP("Request-Id", req_id ))
        req_avps.append(encodeAVP("Request-Type", PAY_REQUEST ))
        req_avps.append(encodeAVP("Dot-Requested-Action",
                                  LOCK_USER_CREDIT ))

        # create header and set required settings for ARAR
        lucr = HDRItem()
        lucr.cmd = dictCOMMANDname2code('DoT-Request')
        initializeHops( lucr )
        req = createReq( lucr, req_avps )

        print
        print "Send 'LUCR' request to Payment Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%req_id
        print "-"*64
        
        return req.decode("hex")
    
    #------------------------------------------------------------------
    # creating responses
    #------------------------------------------------------------------
    def create_prov_resource_alloc_response( self, avps,
                                             req_id ):
        """
        Create the resource allocation response which is sent to
        Provisioning server ( ARAA ).
        """

        # add required AVPs to response avps object
        res_avps=[]
        for avp in [ "Session-Id", "Origin-Host",
                     "Origin-Realm","Destination-Realm",
                     "User-Name" ]:
            res_avps.append(encodeAVP( avp, avps[avp]))

        res_avps.append(encodeAVP( "Request-Id", req_id ))
        res_avps.append(encodeAVP( "Result-Code", SUCCESS ))
        res_avps.append(encodeAVP( "Request-Type", PROV_REQ ))
        res_avps.append(encodeAVP( "Dot-Requested-Action",
                                   APP_RESOURCE_ALLOCATION ))
        
        # create header and set command
        araa = HDRItem()
        araa.cmd = dictCOMMANDname2code('DoT-Answer')
        initializeHops( araa )
        response = createRes(araa,res_avps)

        print
        print "Send 'ARAA' response to Provisioning Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%req_id
        print "-"*64
        
        return response.decode("hex")
    

    def create_mtr_get_spec_response(  self, avps, plan_uri ):
        """
        Create the get specification response which is sent to
        Metering server ( GASA ).
        """
        
        # add required AVPs to response avps object
        res_avps=[]
        for avp in [ "Session-Id", "Origin-Host",
                     "Origin-Realm","Destination-Realm",
                     "Request-Id", "User-Name" ]:
            res_avps.append(encodeAVP( avp, avps[avp]))

        res_avps.append(encodeAVP( "Result-Code", SUCCESS ))
        res_avps.append(encodeAVP( "Request-Type", METER_REQUEST ))
        res_avps.append(encodeAVP( "Dot-Requested-Action",
                                   GET_APP_SPECIFICATION ))
        res_avps.append(encodeAVP( "Subscription-Plan", plan_uri ))
        
        # create header and set command
        gasa = HDRItem()
        gasa.cmd = dictCOMMANDname2code('DoT-Answer')
        initializeHops( gasa )
        response = createRes( gasa, res_avps )

        print
        print "Send 'GASA' response to Metering Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%avps["Request-Id"]
        print "-"*64
        
        return response.decode("hex")

    
    def create_mtr_pub_usage_update_response( self, avps ):
        """
        Create the publishing usage update response which is sent to
        Metering Server ( PUUA of Metering ).
        """
        
        # add required AVPs to response avps object
        res_avps=[]
        for avp in [ "Session-Id", "Origin-Host",
                     "Origin-Realm","Destination-Realm",
                     "Request-Id", "User-Name" ]:
            res_avps.append(encodeAVP( avp, avps[avp]))

        res_avps.append(encodeAVP( "Result-Code", SUCCESS ))
        res_avps.append(encodeAVP( "Request-Type", METER_REQUEST ))
        res_avps.append(encodeAVP( "Dot-Requested-Action",
                                   PUBLISH_USAGE_UPDATE ))
        
        # create header and set command
        puua = HDRItem()
        puua.cmd = dictCOMMANDname2code('DoT-Answer')
        initializeHops( puua )
        response = createRes( puua, res_avps )

        print
        print "Send 'PUUA' response to Metering Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%avps["Request-Id"]
        print "-"*64
        
        return response.decode("hex")
    
    
    def create_rcs_terminate_response( self, avps,
                                             req_id):
        """
        Create the terminate response (release alloc resource response)
        which is sent to Provisioning server ( ARRA ).
        """
        # add required AVPs to response avps object
        res_avps=[]
        for avp in [ "Session-Id", "Origin-Host",
                     "Origin-Realm","Destination-Realm",
                     "User-Name" ]:
            res_avps.append(encodeAVP( avp, avps[avp]))

        res_avps.append(encodeAVP( "Request-Id", req_id ))
        res_avps.append(encodeAVP( "Result-Code", SUCCESS ))
        res_avps.append(encodeAVP( "Request-Type", TERMINATE_REQUEST ))
        
        # create header and set command
        arra = HDRItem()
        arra.cmd = dictCOMMANDname2code('DoT-Answer')
        initializeHops( arra )
        response = createRes(arra,res_avps)

        print
        print "Send 'ARRA' response to Provisioning Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%req_id
        print "-"*64
        
        return response.decode("hex")

    #------------------------------------------------------------------
    # Sending message to other servers
    #------------------------------------------------------------------
    def send_to( self, message, host, port, tcp = True ):
        """
        Send a message to other servers.
        """
        
        factory = ClientFactory( self, message )
        if tcp:
            reactor.connectTCP( host, port, factory )
        else:
            reactor.connectUDP( host, port, factory )

        
    # Send a message to provisioning Server 
    send_to_prov = lambda self, msg: self.send_to( msg,
                                                   PROV_HOST,
                                                   PROV_PORT )
    # Send a message to Metering Server 
    send_to_mtr = lambda self, msg: self.send_to( msg,
                                                  MTR_HOST,
                                                  MTR_PORT )
    # Send a message to Payment Server 
    send_to_pay = lambda self, msg: self.send_to( msg,
                                                  PY_HOST,
                                                  PY_PORT )
    
    #------------------------------------------------------------------
    # Resource Control responsibilities
    #------------------------------------------------------------------
    def parse_plan_topology( self, plan_uri, topo_uri ):
        pass
    def reserve_resources( self, session_id, plan_uri, topo_uri ):
        # ** It should be retrieve values from plan and set dic
        # according to them
        set_credit_dic( session_id )
                        
    def charge_credit( self, last_usage ):
        pass
    def check_credit_threshold( self ):
        pass
    def release_alloc_resources( self ):
        pass
    def create_billable_artiface(self ):
        pass
    #------------------------------------------------------------------
    # Running the server
    #------------------------------------------------------------------        
    def run_server(self):
        """
        Run the Resource Control server.
        """
        factory = ServerFactory( self )
        reactor.listenTCP( RCS_PORT,factory )
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
# Client protocol
#---------------------------------------------------------------------- 
class ClientProtocol(protocol.Protocol):
    """
    The client protocol is used when the dot server act as a
    client to send message for other servers
    """
    
    def __init__(self, factory, dot_server, message):
        """
        initialization of ClientProtocol class
        """
        self.message = message
        self.dot_server = dot_server
        
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
        self.dot_server.handle_res_received( data )
        self.transport.loseConnection()

#----------------------------------------------------------------------
# Client Factory
#---------------------------------------------------------------------- 
class ClientFactory(protocol.ClientFactory):
    
    def __init__(self, dot_server, message):
        """
        initialization of ClientFactory class
        """
        self.message = message
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
        return ClientProtocol(self, self.dot_server, self.message)

#----------------------------------------------------------------------
# run-time execution
#---------------------------------------------------------------------- 
if __name__ == '__main__':
    resource_control = ResourceControl()
    resource_control.run_server()
