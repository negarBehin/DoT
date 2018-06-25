#!/usr/bin/env python
##################################################################
# Copyright (c) 2015
# Oct 2015 - 
# Version 0.1, Last change on Oct 29, 2015    
##################################################################

# All functions needed to implement Metering server 

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
# Metering class
#----------------------------------------------------------------------  
class Metering:
    """
    The metering class
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
        
        # received metering start request from prov ( SAMR request )
        if req_action == START_APP_METERING:
            self.handle_mtr_start_metering_request( req_avps,
                                                    transport )

        # received publish usage update request from metering proxy
        # (** PUUR from metering Proxy )    
        elif req_action == PUBLISH_USAGE_UPDATE and state == OPEN_M:
            self.handle_mtr_pub_usage_update_request( req_avps,
                                                      transport )
            
        # received commit metering request from RCS ( CAMR request )    
        elif req_action == COMMIT_APP_METERING:
            self.handle_mtr_commit_request( req_avps, transport )

        # received terminate request from Prov ( TAMR request ) 
        elif req_action == TERMINATE_APP_METERING:
            self.handle_mtr_terminate_metering_request( req_avps,
                                                        transport )

##        elif not req_action and
##            return_command_name( req ) == ACCOUNTING_REQUEST:
##            self.handle_accounting_request( req_avps, transport )
            
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

        # received get app spec response from RCS ( GASA )
        if res_action == GET_APP_SPECIFICATION and state == PENDING_MG:
            self.handle_mtr_get_spec_response( res_avps )
            
        # received start metering response from metering Proxy ( SMAA )
        elif res_action == START_METERING_AGENTS and state == PENDING_MA:
            self.handle_mtr_start_meter_agents_response( res_avps )

        # received commit metering response from Metering Proxy ( CMTA )
        elif res_action == COMMIT_METERING_TOKENS and state == PENDING_MPC:
            self.handle_commit_metering_tokens_response( res_avps )

        # received publish usage update from RCS ( PUUA )
        elif res_action == PUBLISH_USAGE_UPDATE and state == PENDING_MUU:
            self.handle_mtr_pub_usage_update_response( res_avps )            

        # received stop metering response from metering Proxy ( PMAA )
        elif res_action == STOP_METERING_AGENTS and state == PENDING_MAT:
            self.handle_mtr_stop_meter_agents_response( res_avps )
            
    #------------------------------------------------------------------
    # handle received requests
    #------------------------------------------------------------------
    def handle_mtr_start_metering_request( self, req_avps,
                                           req_transport ):
        """
        Handle the metering start request( SAMR ); change the state to
        PENDING_MG and send GASR to RCS.
        """
        
        session_id = get_session_id_from_avps( req_avps )

        print
        print "Received 'SAMR' request from Provisioning Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with Session-Id = %s "%session_id+\
              "and Request-Id = %s"%get_request_id_from_avps(req_avps)
        print "-"*64
        
        # set state and send a GASR request to Resource Control
        set_state( session_id, PENDING_MG )

        req_id = get_request_id_from_avps( req_avps )
        set_wait_req( session_id, req_id, req_transport )
            
        gasr = self.create_mtr_get_spec_request( req_avps )                
        self.send_to_rcs( gasr )

    def handle_mtr_pub_usage_update_request( self, req_avps,
                                             req_transport ):
        """
        Handle the publishing usage update request which is received
        from Metering Proxy ( PUUR from proxy  ).
        """

        session_id = get_session_id_from_avps( req_avps )
        
        print
        print "Received 'PUUR' request from Metering Proxy "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with Session-Id = %s "%session_id+\
              "and Request-Id = %s"%get_request_id_from_avps(req_avps)
        print "-"*64
   
        # Set state and Send PUUR to RCS
        set_state( session_id, PENDING_MUU )
        req_id = get_request_id_from_avps( req_avps )
        set_wait_req( session_id, req_id, req_transport )

        
        app_usage = req_avps[ "App-Usage" ]

        
        puur_resource_ctrl = self.create_mtr_pub_usage_update_request(\
                                                    req_avps, app_usage )
        self.send_to_rcs( puur_resource_ctrl )
        
    
    def handle_mtr_commit_request(  self, req_avps, req_transport ):
        """
        Handle the commit app metering request which is received
        from Resource Control Server ( CAMR ).
        """
        session_id = get_session_id_from_avps( req_avps )

        print
        print "Received 'CAMR' request from Resource Control Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with Session-Id = %s "%session_id+\
              "and Request-Id = %s"%get_request_id_from_avps(req_avps)
        print "-"*64
        
        # set state and send a CMTR request to Metering Proxy
        # ( It should send to relate Metering Proxies )
        # Now we assume we have just one proxy
        
        set_state( session_id, PENDING_MPC )

        req_id = get_request_id_from_avps( req_avps )
        set_wait_req( session_id, req_id, req_transport )
        
        cmtr_request =self.create_commit_metering_tokens_request(
                                                            req_avps )
        self.send_to_mtr_proxy( cmtr_request ) 

        
    def handle_mtr_terminate_metering_request(  self, req_avps,
                                                req_transport ):
        """
        Handle the terminate app metering request which is received
        from Provisioning Server ( TAMR ).
        """
        session_id = get_session_id_from_avps( req_avps )

        print
        print "Received 'TAMR' request from Provisioning Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with Session-Id = %s "%session_id+\
              "and Request-Id = %s"%get_request_id_from_avps(req_avps)
        print "-"*64
        
        # set state and send a PMAR request to Metering Proxy
        # ( It should send to relate Metering Proxies )
        # Now we assume we have just one proxy
        
        set_state( session_id, PENDING_MAT )

        req_id = get_request_id_from_avps( req_avps )
        set_wait_req( session_id, req_id, req_transport )
        
        pmar_request =self.create_mtr_stop_meter_agents_request(
                                                            req_avps )
        self.send_to_mtr_proxy( pmar_request )
        

    def handle_accounting_request( req_avps, transport ):
        pass

    #------------------------------------------------------------------
    # handle received responses
    #------------------------------------------------------------------
    def handle_mtr_get_spec_response( self, res_avps ):
        """
        Handle getting app specification response which is
        received from resource control server( GASA ).
        """

        session_id = get_session_id_from_avps( res_avps )

        print
        print "Received 'GASA' response from Resource Control Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the result_code "+\
              "= %s, "%get_result_code_from_avps( res_avps )+\
              "Session-Id = %s "%session_id
        print "and Request-Id = %s"%get_request_id_from_avps(res_avps)
        print "-"*64
        
        # set state and send a SMAR request to Metering Proxy
        set_state( session_id, PENDING_MA )

        smar = self.create_mtr_start_meter_agents_request( res_avps )
        self.send_to_mtr_proxy( smar )
        
    
    def handle_mtr_start_meter_agents_response(  self, res_avps ):
        """
        Handle start metering agents response which is
        received from metering Proxy( SMAA ).
        """

        session_id = get_session_id_from_avps( res_avps )
        
        print
        print "Received 'SMAA' response from Metering Proxy "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the result_code "+\
              "= %s, "%get_result_code_from_avps( res_avps )+\
              "Session-Id = %s "%session_id
        print "and Request-Id = %s"%get_request_id_from_avps(res_avps)
        print "-"*64        

        # Sets the state and sends SAMA response to Provisioning Server
        # Should wait for all proxies related to the running
        # session - now we assume thet we have only one proxy

        set_state( session_id, OPEN_M )
        ( samr_req_id, samr_transport ) = pop_wait_req( session_id )
        sama = self.create_mtr_start_metering_response( res_avps,
                                                        samr_req_id )               
        samr_transport.write( sama )

        
    def handle_mtr_stop_meter_agents_response(  self, res_avps ):
        """
        Handle stop metering agents response which is
        received from metering Proxy( PMAA ).
        """

        session_id = get_session_id_from_avps( res_avps )
        
        print
        print "Received 'PMAA' response from Metering Proxy "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the result_code "+\
              "= %s, "%get_result_code_from_avps( res_avps )+\
              "Session-Id = %s "%session_id
        print "and Request-Id = %s"%get_request_id_from_avps(res_avps)
        print "-"*64        

        # Should wait for all proxies related to the running
        # session - now we assume thet we have only one proxy
        # Sets state and send TAMA to provisioning Server
        set_state( session_id, IDLE_M )
        ( tamr_req_id, tamr_transport ) = pop_wait_req( session_id )
        tama = self.create_mtr_terminate_metering_response( res_avps,
                                                        tamr_req_id )               
        tamr_transport.write( tama )

        
    def handle_commit_metering_tokens_response(  self, res_avps ):
        """
        Handle commit metering tokens response which is
        received from Metering Proxy( CMTA ).
        """

        session_id = get_session_id_from_avps( res_avps )
        
        print
        print "Received 'CMTA' response from Metering Proxy "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the result_code "+\
              "= %s, "%get_result_code_from_avps( res_avps )+\
              "Session-Id = %s "%session_id
        print "and Request-Id = %s"%get_request_id_from_avps(res_avps)
        print "-"*64

        # Should wait for all proxies related to the running
        # session - now we assume thet we have only one proxy
        # Sets state and sends CAMA to Resource Control server
        set_state( session_id, OPEN_M )
        ( camr_req_id, camr_transport ) = pop_wait_req( session_id )
        cama = self.create_mtr_commit_response( res_avps,
                                                camr_req_id )               
        camr_transport.write( cama )

        
    def handle_mtr_pub_usage_update_response( self, res_avps ):
        """
        Handle publish usage update response which is
        received from resource control server( PUUA ).
        """
        
        session_id = get_session_id_from_avps( res_avps )
        
        print
        print "Received 'PUUA' response from Resource Control Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the result_code "+\
              "= %s, "%get_result_code_from_avps( res_avps )+\
              "Session-Id = %s "%session_id
        print "and Request-Id = %s"%get_request_id_from_avps(res_avps)
        print "-"*64

        # set state and send PUUA( of proxy ) response to Metering proxy
        set_state( session_id, OPEN_M )

        ( puur_req_id, puur_transport ) = pop_wait_req( session_id )

        puua_proxy = self.create_mtr_pub_usage_update_response(res_avps,
                                                               puur_req_id )               
        puur_transport.write( puua_proxy )
        
    #------------------------------------------------------------------
    # create requests
    #------------------------------------------------------------------
    def create_mtr_get_spec_request( self, avps ):
        """
        Create a request for getting app specification from resource
        control server( GASR ).
        """
        # add required AVPs to request avps object
        req_avps=[]
        for avp in [ "Session-Id", "Origin-Host",
                     "Origin-Realm", "Destination-Realm",
                     "User-Name" ]:
            req_avps.append(encodeAVP( avp, avps[avp]))

        req_id = create_req_id()
        req_avps.append(encodeAVP("Request-Id",req_id))
        req_avps.append(encodeAVP("Request-Type",METER_REQUEST))
        req_avps.append(encodeAVP("Dot-Requested-Action",
                                  GET_APP_SPECIFICATION)) 

        # create header and set command
        gasr = HDRItem()
        gasr.cmd = dictCOMMANDname2code('DoT-Request')
        initializeHops( gasr )
        request = createReq( gasr, req_avps )

        print
        print "Send 'GASR' request to Resource Control Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%req_id
        print "-"*64
        
        return request.decode("hex")
    
    def create_mtr_start_meter_agents_request( self, avps ):
        """
        Create a request for starting metering agents which is sent
        to Metering Proxy( SMAR ).
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
                                  START_METERING_AGENTS ))

        # create header and set command
        smar = HDRItem()
        smar.cmd = dictCOMMANDname2code('DoT-Request')
        initializeHops( smar )
        request = createReq( smar, req_avps )

        print
        print "Send 'SMAR' request to Metering Proxy "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%req_id
        print "-"*64
        
        return request.decode("hex")

    def create_mtr_stop_meter_agents_request( self, avps ):
        """
        Create a request for stoping metering agents which is sent
        to Metering Proxy( PMAR ).
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
                                  STOP_METERING_AGENTS ))

        # create header and set command
        pmar = HDRItem()
        pmar.cmd = dictCOMMANDname2code('DoT-Request')
        initializeHops( pmar )
        request = createReq( pmar, req_avps )

        print
        print "Send 'PMAR' request to Metering Proxy "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%req_id
        print "-"*64
        
        return request.decode("hex")
    
    def create_commit_metering_tokens_request( self, avps ):
        """
        Create Commit Metering Tokens request which is sent
        to Metering Proxy( CMTR ).
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
                                   COMMIT_METERING_TOKENS ))

        # create header and set required settings for CMTR
        cmtr = HDRItem()
        cmtr.cmd = dictCOMMANDname2code('DoT-Request')
        initializeHops( cmtr )
        req = createReq( cmtr, req_avps )

        print
        print "Send 'CMTR' request to Metering Proxy Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%req_id
        print "-"*64
        
        return req.decode("hex")


    def create_mtr_pub_usage_update_request( self, avps, app_usage ):
        """
        Create a request for publishing usage update which is sent
        to Resource Control server( PUUR ).
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
                                  PUBLISH_USAGE_UPDATE ))
        req_avps.append(encodeAVP("App-Usage", app_usage ))
        
        # create header and set command
        puur = HDRItem()
        puur.cmd = dictCOMMANDname2code('DoT-Request')
        initializeHops( puur )
        request = createReq( puur, req_avps )

        print
        print "Send 'PUUR' request to Resource Control Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              ", Request-Id = %s "%req_id
        print "and App-Usage = %s"%app_usage
        print "-"*64
        
        return request.decode("hex")
    
    #------------------------------------------------------------------
    # creating responses
    #------------------------------------------------------------------
    def create_mtr_start_metering_response( self, avps, req_id ):
        """
        Create a response of start metering request which is sent
        to provisioning server server( SAMA ).
        """
        
        # add required AVPs to response avps object
        res_avps=[]
        for avp in [ "Session-Id", "Origin-Host",
                     "Origin-Realm","Destination-Realm",
                     "User-Name" ]:
            res_avps.append(encodeAVP( avp, avps[avp]))

        res_avps.append(encodeAVP( "Request-Id", req_id ))
        res_avps.append(encodeAVP( "Result-Code", SUCCESS ))
        res_avps.append(encodeAVP( "Request-Type", METER_REQUEST ))
        res_avps.append(encodeAVP( "Dot-Requested-Action",
                                   START_APP_METERING ))
        # create header and set command
        sama = HDRItem()
        sama.cmd = dictCOMMANDname2code('DoT-Answer')
        initializeHops( sama )
        response = createRes(sama,res_avps)

        print
        print "Send 'SAMA' response to Provisioning Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%req_id
        print "-"*64
        
        return response.decode("hex")


    def create_mtr_terminate_metering_response( self, avps, req_id ):
        """
        Create a response of terminate app metering request which is sent
        to Provisioning server( TAMA ).
        """

        # add required AVPs to response avps object
        res_avps=[]
        for avp in [ "Session-Id", "Origin-Host",
                     "Origin-Realm","Destination-Realm",
                     "User-Name" ]:
            res_avps.append(encodeAVP( avp, avps[avp]))

        res_avps.append(encodeAVP( "Request-Id", req_id ))
        res_avps.append(encodeAVP( "Result-Code", SUCCESS ))
        res_avps.append(encodeAVP( "Request-Type", METER_REQUEST ))
        res_avps.append(encodeAVP( "Dot-Requested-Action",
                                   TERMINATE_APP_METERING ))
        
        # create header and set command
        tama = HDRItem()
        tama.cmd = dictCOMMANDname2code('DoT-Answer')
        initializeHops( tama )
        response = createRes( tama, res_avps )

        print
        print "Send 'TAMA' response to Provisioning Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%req_id
        print "-"*64
        
        return response.decode("hex")
    
    def create_mtr_commit_response( self, avps, req_id ):
        """
        Create a response of commit metering request which is sent
        to Resource Control server( CAMA ).
        """
        
        # add required AVPs to response avps object
        res_avps=[]
        for avp in [ "Session-Id", "Origin-Host",
                     "Origin-Realm","Destination-Realm",
                     "User-Name", "App-Usage" ]:
            res_avps.append(encodeAVP( avp, avps[avp]))

        res_avps.append(encodeAVP( "Request-Id", req_id ))
        res_avps.append(encodeAVP( "Result-Code", SUCCESS ))
        res_avps.append(encodeAVP( "Request-Type", METER_REQUEST ))
        res_avps.append(encodeAVP( "Dot-Requested-Action",
                                   COMMIT_APP_METERING ))
        res_avps.append(encodeAVP("Billable-Artifact",
                                  avps["Billable-Artifact"] ))
        # create header and set command
        cama = HDRItem()
        cama.cmd = dictCOMMANDname2code('DoT-Answer')
        initializeHops( cama )
        response = createRes(cama,res_avps)

        print
        print "Send 'CAMA' response to Resource Control Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%req_id
        print "-"*64
        
        return response.decode("hex")
    

    def create_mtr_pub_usage_update_response( self, avps,
                                              req_id ):
        """
        Create the publishing usage update response which is sent to
        Metering Proxy ( ** PUUA of Proxy ).
        """
        
        # add required AVPs to response avps object
        res_avps=[]
        for avp in [ "Session-Id", "Origin-Host",
                     "Origin-Realm","Destination-Realm",
                     "User-Name" ]:
            res_avps.append(encodeAVP( avp, avps[avp]))

        res_avps.append(encodeAVP( "Request-Id", req_id ))
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
        print "Send 'PUUA' response to Metering Proxy "+\
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
            pass
            # Should be sent to UDP server
        

    # Send a message to Resource Control Server 
    send_to_rcs = lambda self, msg: self.send_to( msg, RCS_HOST, RCS_PORT )
    send_to_mtr_proxy = lambda self, msg: self.send_to( msg, MTR_TCP_PRX_HOST,
                                                        MTR_TCP_PRX_PORT )
    
    #------------------------------------------------------------------
    # Running the server
    #------------------------------------------------------------------        
    def run_server(self):
        """
        Run the metering server.
        """
        factory = ServerFactory( self )
        reactor.listenTCP( MTR_PORT,factory )
        reactor.run()       

#----------------------------------------------------------------------
# Server protocol
#---------------------------------------------------------------------- 
class ServerProtocol(protocol.Protocol):
    """
    The Server protocol is used for listening to
    receive messages from other servers
    """
    
    def __init__(self, factory, metering):
        """
        initialization of ServerProtocol class
        """
        self.metering = metering
        
    def dataReceived(self, data):
        """
        As soon as data received to the server, this function is called.
        """
        self.metering.handle_req_received( data, self.transport )
        #self.transport.write( response )
        #self.transport.loseConnection()

#----------------------------------------------------------------------
# Server Factory
#----------------------------------------------------------------------
class ServerFactory(protocol.ServerFactory):
    
    def __init__(self, metering):
        """
        initialization of ServerFactory class
        """
        self.metering = metering
        
    def buildProtocol(self, addr):
        """
        return the ServerProtocol as its factory
        """
        return ServerProtocol(self, self.metering)
    
#----------------------------------------------------------------------
# Client protocol
#---------------------------------------------------------------------- 
class ClientProtocol(protocol.Protocol):
    """
    The client protocol is used when the metering server act as a
    client to send message for other servers
    """
    
    def __init__(self, factory, metering, message):
        """
        initialization of ClientProtocol class
        """
        self.message = message
        self.metering = metering
        
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
        self.metering.handle_res_received( data )
        #self.transport.loseConnection()

#----------------------------------------------------------------------
# Client Factory
#---------------------------------------------------------------------- 
class ClientFactory(protocol.ClientFactory):
    
    def __init__(self, metering, message):
        """
        initialization of ClientFactory class
        """
        self.message = message
        self.metering = metering
        
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
####        reactor.stop()
        
    def buildProtocol(self, addr):
        """
        return the ClientProtocol as its factory
        """
        return ClientProtocol(self, self.metering, self.message)

#----------------------------------------------------------------------
# run-time execution
#---------------------------------------------------------------------- 
if __name__ == '__main__':
    metering = Metering()
    metering.run_server()
