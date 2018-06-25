#!/usr/bin/env python
##################################################################
# Copyright (c) 2015
# Oct 2015 - 
# Version 0.1, Last change on Oct 29, 2015    
##################################################################

# All functions needed to implement Provisioning server 

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
    
#----------------------------------------------------------------------
# Provisioning class
#----------------------------------------------------------------------  
class Provisioning:
    """
    The Provisioning class
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

        # Received provisioning application topo request from Dot Client
        # ( PATR )
        if req_action == PROV_APP_TOPO and \
           ( not state or state == IDLE_P ):
                self.handle_prov_app_topo_request( req_avps, transport )
        
        # Received start iot app request from Dot Client ( SIAR )
        elif req_action == START_IOT_APP and state == IDLE_PP:
            self.handle_prov_start_app_request( req_avps, transport )

        # Received update notification from Resource Control ( NUAR )   
        elif not req_action and state == OPEN_P and \
             get_request_type_from_avps( req_avps )== UPDATE_REQUEST:
                self.handle_update_notification_request( req_avps, transport )

        # Received terminate request from Dot Client ( TIAR )
        elif not req_action and state == OPEN_P and \
             get_request_type_from_avps( req_avps )== TERMINATE_REQUEST:
                self.handle_prov_terminate_request( req_avps, transport )
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

        # Received app resource allocation response from RCS ( ARAA )
        if res_action == APP_RESOURCE_ALLOCATION and state== PENDING_PR:
            self.handle_prov_resource_alloc_response( res_avps )
        
        # Received start app metering response from Metering ( SAMA )
        elif res_action == START_APP_METERING and state == PENDING_PM:
            self.handle_mtr_start_metering_response( res_avps )

        # Received terminate response from RCS( ARRA )  
        elif not res_action and state == PENDING_PRR and \
             get_request_type_from_avps( res_avps )== TERMINATE_REQUEST:
                self.handle_rcs_terminate_response( res_avps )

        # Received terminate metering response from Metering ( TAMA )   
        elif  res_action == TERMINATE_APP_METERING and \
             state == PENDING_PMM:
                self.handle_mtr_terminate_metering_response(res_avps)
                
        # Received update notification response from Dot Client ( NUAA )
        elif not res_action and state == PENDING_PNU and \
             get_request_type_from_avps( res_avps )== UPDATE_REQUEST:
            self.handle_update_notification_response( res_avps )
    
    #------------------------------------------------------------------
    # handle received requests
    #------------------------------------------------------------------
    def handle_prov_app_topo_request( self, req_avps, req_transport ):
        """
        Handle the provisioning application topology request which
        is received from Dot Client server ( PATR ).
        """
        
        print
        print "Received 'PATR' request from Dot Client Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with Session-Id = %s "%get_session_id_from_avps(req_avps)+\
              "and Request-Id = %s"%get_request_id_from_avps(req_avps)
        print "-"*64
        
        if self.is_plan_topolo_valid( None, None ):
            session_id = get_session_id_from_avps( req_avps )
            
            # set state and send a ARAR request to RCS
            set_state( session_id, PENDING_PR )

            req_id = get_request_id_from_avps( req_avps )
            set_wait_req( session_id, req_id, req_transport )
        
            arar_request = self.create_prov_resource_alloc_request(
                                                            req_avps )                
            self.send_to_rcs( arar_request )
            

    def handle_prov_start_app_request(  self, req_avps, req_transport ):
        """
        Handle the start iot app request which is received from
        Dot Client server ( SIAR ).
        """
        
        print
        print "Received 'SIAR' request from Dot Client Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with Session-Id = %s "%get_session_id_from_avps(req_avps)+\
              "and Request-Id = %s"%get_request_id_from_avps(req_avps)
        print "-"*64
        
        session_id = get_session_id_from_avps( req_avps )

        if self.start_app_services( session_id ):
            
            # set state and send a SAMR request to Metering
            set_state( session_id, PENDING_PM )

            req_id = get_request_id_from_avps( req_avps )
            set_wait_req( session_id, req_id, req_transport )
            
            samr = self.create_mtr_start_metering_request( req_avps )                
            self.send_to_metering( samr )
            
            
    def handle_update_notification_request( self, req_avps,
                                             req_transport ):
        """
        Handle the update notification request which is received
        from Resource Control server ( NUAR ).
        """

        session_id = get_session_id_from_avps( req_avps )
        print
        print "Received 'NUAR' request from Resource Control server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with Session-Id = %s "%get_session_id_from_avps(req_avps)+\
              "and Request-Id = %s"%get_request_id_from_avps(req_avps)
        print "-"*64
        
        
        set_state( session_id, PENDING_PNU )
        req_id = get_request_id_from_avps( req_avps )
        set_wait_req( session_id, req_id, req_transport )
            
        nuar = self.create_update_notification_request( req_avps )
        self.send_to_dot_client( nuar ) 
    
    def handle_prov_terminate_request( self, req_avps, req_transport ):
        """
        Handle the terminate request which is received from
        Dot Client server ( TIAR ).
        """

        print
        print "Received 'TIAR' request from Dot Client Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with Session-Id = %s "%get_session_id_from_avps(req_avps)+\
              "and Request-Id = %s"%get_request_id_from_avps(req_avps)
        print "-"*64
        
        # set state and send a ARRR request to RCS
        session_id = get_session_id_from_avps( req_avps )
        set_state( session_id, PENDING_PRR )

        req_id = get_request_id_from_avps( req_avps )
        set_wait_req( session_id, req_id, req_transport )
        
        arrr_request = self.create_rcs_terminate_request( req_avps )                
        self.send_to_rcs( arrr_request )   

    #------------------------------------------------------------------
    # handle received responses
    #------------------------------------------------------------------
    def handle_prov_resource_alloc_response(  self, res_avps ):
        """
        Handle app resource allocation response which is received from
        Resource Control server( ARAA ).
        """

        print
        print "Received 'ARAA' response from Resource Control Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the result_code "+\
              "= %s, "%get_result_code_from_avps( res_avps )+\
              "Session-Id = %s "%get_session_id_from_avps(res_avps)
        print "and Request-Id = %s"%get_request_id_from_avps(res_avps)
        print "-"*64
        
        session_id = get_session_id_from_avps( res_avps )

        # Set the state and Send PATA to Dot Client
        set_state( session_id, IDLE_PP )

        ( patr_req_id, patr_transport ) = pop_wait_req( session_id )

        pata = self.create_prov_app_topo_response( res_avps,
                                                   patr_req_id )               
        patr_transport.write( pata )

    def handle_mtr_start_metering_response(  self, res_avps ):
        """
        Handle start app metering response which is received from
        Metering server( SAMA ).
        """

        print
        print "Received 'SAMA' response from Metering Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the result_code "+\
              "= %s, "%get_result_code_from_avps( res_avps )+\
              "Session-Id = %s "%get_session_id_from_avps(res_avps)
        print "and Request-Id = %s"%get_request_id_from_avps(res_avps)
        print "-"*64

        # set state and send SIAA to dot client
        session_id = get_session_id_from_avps( res_avps )
        set_state( session_id, OPEN_P )

        ( siar_req_id, siar_transport ) = pop_wait_req( session_id )

        siaa = self.create_prov_start_app_response( res_avps,
                                                    siar_req_id )               
        siar_transport.write( siaa )
        
    def handle_rcs_terminate_response( self, res_avps ):
        """
        Handle terminate response which is received from
        Resource Control server( ARRA ).
        """

        session_id = get_session_id_from_avps( res_avps )

        print
        print "Received 'ARRA' response from Resource Control Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the result_code "+\
              "= %s, "%get_result_code_from_avps( res_avps )+\
              "Session-Id = %s "%session_id
        print "and Request-Id = %s"%get_request_id_from_avps(res_avps)
        print "-"*64
        
        # set state and send a TAMR request to Metering Server
        set_state( session_id, PENDING_PMM )

        tamr = self.create_mtr_terminate_metering_request( res_avps )
        self.send_to_metering( tamr )

    def handle_mtr_terminate_metering_response(  self, res_avps ):
        """
        Handle terminate app metering response which is received from
        Metering server( TAMA ).
        """

        print
        print "Received 'TAMA' response from Metering Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the result_code "+\
              "= %s, "%get_result_code_from_avps( res_avps )+\
              "Session-Id = %s "%get_session_id_from_avps(res_avps)
        print "and Request-Id = %s"%get_request_id_from_avps(res_avps)
        print "-"*64

        # set state and send TIAA to dot client
        session_id = get_session_id_from_avps( res_avps )
        set_state( session_id, IDLE_P )

        ( tiar_req_id, tiar_transport ) = pop_wait_req( session_id )

        tiaa = self.create_prov_terminate_response( res_avps,
                                                    tiar_req_id )               
        tiar_transport.write( tiaa )


    def handle_update_notification_response( self, res_avps ):
        """
        Handle update notification response which is received from
        Dot Client server( NUAA ).
        """

        session_id = get_session_id_from_avps( res_avps )
        
        print
        print "Received 'NUAA' response from Dot Client Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the result_code "+\
              "= %s, "%get_result_code_from_avps( res_avps )+\
              "Session-Id = %s "%session_id
        print "and Request-Id = %s"%get_request_id_from_avps(res_avps)
        print "-"*64
        
        # Set the state and send NUAA to Resource Control server
        set_state( session_id, OPEN_P )
        
        ( nuar_req_id, nuar_transport ) = pop_wait_req( session_id )
        
        nuaa = self.create_update_notification_response( res_avps,
                                                         nuar_req_id )
        nuar_transport.write( nuaa )
        
    #------------------------------------------------------------------
    # create requests
    #------------------------------------------------------------------
    def create_prov_resource_alloc_request(  self, avps ):
        """
        Create app resource allocation request which is sent
        to Resource Control server( ARAR ).
        """
        
        # add required AVPs to request avps object
        req_avps=[]
        for avp in [ "Session-Id", "Origin-Host",
                     "Origin-Realm", "Destination-Realm",
                     "App-Topology", "Subscription-Plan",
                     "User-Name" ]:
            req_avps.append(encodeAVP( avp, avps[avp]))
        req_id = create_req_id()
        req_avps.append(encodeAVP("Request-Id", req_id  ))
        req_avps.append(encodeAVP("Request-Type",PROV_REQ))
        req_avps.append(encodeAVP("Dot-Requested-Action",
                                  APP_RESOURCE_ALLOCATION ))

        # create header and set required settings for ARAR
        arar = HDRItem()
        arar.cmd = dictCOMMANDname2code('DoT-Request')
        initializeHops( arar )
        req = createReq( arar, req_avps )

        print
        print "Send 'ARAR' request to Resource Control Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%req_id
        print "-"*64
        
        return req.decode("hex")


    def create_mtr_start_metering_request(  self, avps ):
        """
        Create start app metering request which is sent
        to Metering server( SAMR ).
        """

        # add required AVPs to request avps object
        req_avps=[]
        for avp in [ "Session-Id", "Origin-Host",
                     "Origin-Realm", "Destination-Realm",
                     "User-Name" ]:
            req_avps.append(encodeAVP( avp, avps[avp]))

        req_id = create_req_id()
        req_avps.append(encodeAVP("Request-Id", req_id ))
        req_avps.append(encodeAVP("Request-Type",METER_REQUEST ))
        req_avps.append(encodeAVP("Dot-Requested-Action",
                                  START_APP_METERING ))

        # create header and set required settings for SAMR
        samr = HDRItem()
        samr.cmd = dictCOMMANDname2code('DoT-Request')
        initializeHops( samr )
        req = createReq( samr, req_avps )

        print
        print "Send 'SAMR' request to Metering Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%req_id
        print "-"*64
        
        return req.decode("hex")
    

    def create_rcs_terminate_request(  self, avps ):
        """
        Create app resource release request which is sent
        to Resource Control server( ARRR ).
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

        # create header and set required settings for ARRR
        arrr = HDRItem()
        arrr.cmd = dictCOMMANDname2code('DoT-Request')
        initializeHops( arrr )
        req = createReq( arrr, req_avps )

        print
        print "Send 'ARRR' request to Resource Control Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%req_id
        print "-"*64
        
        return req.decode("hex")

    def create_mtr_terminate_metering_request(  self, avps ):
        """
        Create terminate app metering request which is sent
        to Metering server( TAMR ).
        """

        # add required AVPs to request avps object
        req_avps=[]
        for avp in [ "Session-Id", "Origin-Host",
                     "Origin-Realm", "Destination-Realm",
                     "User-Name" ]:
            req_avps.append(encodeAVP( avp, avps[avp]))

        req_id = create_req_id()
        req_avps.append(encodeAVP("Request-Id", req_id ))
        req_avps.append(encodeAVP("Request-Type",METER_REQUEST ))
        req_avps.append(encodeAVP("Dot-Requested-Action",
                                  TERMINATE_APP_METERING ))

        # create header and set command
        tamr = HDRItem()
        tamr.cmd = dictCOMMANDname2code('DoT-Request')
        initializeHops( tamr )
        request = createReq( tamr, req_avps )

        print
        print "Send 'TAMR' request to Metering Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%req_id
        print "-"*64
        
        return request.decode("hex")

    def create_update_notification_request(  self, avps ):
        """
        Create update notification which is sent
        to Dot Client server( NUAR ).
        """
        # add required AVPs to request avps object
        req_avps=[]
        for avp in [ "Session-Id", "Origin-Host",
                     "Origin-Realm", "Destination-Realm",
                     "User-Name" , "Request-Type",
                     "Allocation-Unit", "Confirmation-Mode" ]:
            req_avps.append(encodeAVP( avp, avps[avp]))
            
        req_id = create_req_id()
        req_avps.append(encodeAVP("Request-Id", req_id ))

 
        # create header and set required settings for NUAR
        nuar = HDRItem()
        nuar.cmd = dictCOMMANDname2code('DoT-Request')
        initializeHops( nuar )
        req = createReq( nuar, req_avps )

        print
        print "Send 'NUAR' request to Dot Client Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%req_id
        print "-"*64
        
        return req.decode("hex")
    
    #------------------------------------------------------------------
    # creating responses
    #------------------------------------------------------------------
    def create_prov_app_topo_response( self, avps, req_id ):
        """
        Create the provisioning application topology response which
        is sent to Dot Client server ( PATA ).
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
                                   PROV_APP_TOPO ))
        
        # create header and set command
        pata = HDRItem()
        pata.cmd = dictCOMMANDname2code('DoT-Answer')
        initializeHops( pata )
        response = createRes( pata, res_avps )

        print
        print "Send 'PATA' response to Dot Client Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%req_id
        print "-"*64
        
        return response.decode("hex")
    

    def create_prov_start_app_response( self, avps, req_id ):
        """
        Create the start iot app response which is sent to
        Dot Client server ( SIAA ).
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
                                   START_IOT_APP ))
        
        # create header and set command
        siaa = HDRItem()
        siaa.cmd = dictCOMMANDname2code('DoT-Answer')
        initializeHops( siaa )
        response = createRes( siaa, res_avps )

        print
        print "Send 'SIAA' response to Dot Client Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%req_id
        print "-"*64
        
        return response.decode("hex")
    
    
    def create_update_notification_response(  self, avps,
                                              req_id ):
        """
        Create update notification response which is sent
        to Resource Control server( NUAA ).

        It is for "pay-per-use" and "automatic update" mode.
        """

        # add required AVPs to response avps object
        res_avps=[]
        for avp in [ "Session-Id", "Origin-Host",
                     "Origin-Realm","Destination-Realm",
                     "User-Name", "Request-Type",
                     "Allocation-Unit", "Confirmation-Mode" ]:
            res_avps.append(encodeAVP( avp, avps[avp]))


        res_avps.append(encodeAVP( "Request-Id", req_id ))
        res_avps.append(encodeAVP( "Result-Code", SUCCESS ))
       
        # create header and set command
        nuaa = HDRItem()
        nuaa.cmd = dictCOMMANDname2code('DoT-Answer')
        initializeHops( nuaa )
        response = createRes( nuaa, res_avps )

        print
        print "Send 'NUAA' response to Resource Control Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%req_id
        print "-"*64
        
        return response.decode("hex")

    def create_prov_terminate_response( self, avps, req_id ):
        """
        Create the terminate app response which is sent to
        Dot Client server ( TIAA ).
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
        tiaa = HDRItem()
        tiaa.cmd = dictCOMMANDname2code('DoT-Answer')
        initializeHops( tiaa )
        response = createRes( tiaa, res_avps )

        print
        print "Send 'TIAA' response to Dot Client Server "+\
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

        
    # Send a message to Resource Control Server 
    send_to_rcs = lambda self, msg: self.send_to( msg,
                                                  RCS_HOST,
                                                  RCS_PORT )
    # Send a message to Dot Client Server 
    send_to_dot_client = lambda self, msg: self.send_to( msg,
                                                         DOT_HOST,
                                                         DOT_PORT )
    # Send a message to Metering Server 
    send_to_metering = lambda self, msg: self.send_to( msg,
                                                       MTR_HOST,
                                                       MTR_PORT )
    
    #------------------------------------------------------------------
    # Provisioning responsibilities
    #------------------------------------------------------------------
    def is_plan_topolo_valid( self, plan_uri, topo_uri ):
        """
        Determine if the app plan and topo uri is valid or no.
        """
        
        return True
    
    def parse_plan_topology( self, plan_uri, topo_uri ):
        """
        Parse the app plan and topo to retrieve required information.
        """
        pass

    def start_app_services( self, session_id ):
        """
        Start the app services based on the app plan and topo.
        """
        plan_uri = get_plan( session_id )
        topo_uri = get_topo( session_id )
        self.parse_plan_topology( plan_uri, topo_uri )
        # Start the services based on the plan and topo
        return True
    
    #------------------------------------------------------------------
    # Running the server
    #------------------------------------------------------------------        
    def run_server(self):
        """
        Run the Provisioning server.
        """
        factory = ServerFactory( self )
        reactor.listenTCP( PROV_PORT,factory )
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
    provisioning = Provisioning()
    provisioning.run_server()
