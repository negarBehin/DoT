#!/usr/bin/env python
##################################################################
# Copyright (c) 2015
# Dec 2015 - 
# Version 0.1, Last change on Jan 10, 2016    
##################################################################

# All functions needed to implement Metering Proxy server 

from twisted.internet import reactor, protocol, task
from libDiameter import *
from diam_related import *
from constants import *


import txthings.coap as coap
import txthings.resource as resource
import state_dic_related as states
import json, datetime, cbor

import subprocess

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


"""
used for saving ugase data for each session.
"""
usages_dic = {}
#----------------------------------------------------------------------
# Routines related to agents_dic
#----------------------------------------------------------------------


"""
used for saving agents info related to each session.
"""
agents_dic = {}
#----------------------------------------------------------------------
# Routines related to agents_dic
#----------------------------------------------------------------------

def set_agents_dic( session_id, list_of_agents ):
    """
    Set list of agents for specific session_id.
    """
    agents_dic[ session_id ] = { "service_usage" : 0,
                                 "resource_usage" :0,
                                 "total_service_usage" : 0,
                                 "total_resource_usage" :0,
                                 # can be list of agents with key of agent
                                 # address and values such az u3,...
                                 "list_of_agents": list_of_agents,
                                 "waiting_list_for_agents":[],
                                 # ** Its default is 60 s , should be replaced
                                 # by the defined value in plan
                                 "aggregation_threshold": 50,
                                 # detail_agents contains usage information about
                                 # each agent separately:
                                 #{ agent_address_port :
                                 #  {
                                 #  "service_name":service_name,
                                 #  "total_service_usage":
                                 #      total_service_usage_of_agent,
                                 #  "total_resource_usage":
                                 #      total_resource_usage_of_agent
                                 #  }
                                 #}
                                 "detail_agents":{}}


def set_aggregation_threshold( session_id, aggregation_threshold ):
    """
    Set the aggregation threshold for the session
    """

    agents_dic[session_id]["aggregation_threshold"] = \
                                                aggregation_threshold

def get_aggregation_threshold( session_id ):
    """
    Get the aggregation threshold of the session
    """

    return agents_dic[session_id]["aggregation_threshold"]

def get_list_of_agents( session_id ):
    """
    Get the list of agents associated with the specific session id
    """

    return agents_dic[session_id]["list_of_agents"]

def get_total_service_usage( session_id ):
    """
    Get the total service usage of the session
    """

    return agents_dic[session_id]["total_service_usage"]

def get_total_resource_usage( session_id ):
    """
    Get the total resource usage of the session
    """

    return agents_dic[session_id]["total_resource_usage"]

def add_waiting_agent( session_id, agent ):
    """
    Add an agent to waiting list
    """

    agents_dic[session_id]["waiting_list_for_agents"].append( agent )

def remove_waiting_agent( session_id, agent ):
    """
    Remove an agent from waiting list
    """
    agents_dic[session_id]["waiting_list_for_agents"].remove( agent )
    
def is_waiting_agents_empty( session_id ):
    """
    Set list of agents for specific session_id.
    """

    return not bool(len(
        agents_dic[session_id]["waiting_list_for_agents"] ))

def update_usage( session_id, service_usage, resource_usage ):
    """
    update the service and resource usage.
    """

    agents_dic[session_id]["service_usage"] += service_usage
    agents_dic[session_id]["resource_usage"] += resource_usage

def refresh_credit( session_id ):
    """
    refresh the usage.
    """

    service_usage = agents_dic[session_id]["service_usage"]
    agents_dic[session_id]["service_usage"] = 0
    
    resource_usage = agents_dic[session_id]["resource_usage"]
    agents_dic[session_id]["resource_usage"] = 0
    
    agents_dic[session_id]["total_service_usage"] += service_usage
    agents_dic[session_id]["total_resource_usage"] += resource_usage

    service_resource_usage = service_usage + resource_usage                          
    return service_resource_usage


def add_detail_agents( session_id, agent_address_port,
                       related_service_name ):
    """
    Add an agent to detail agents( which stores the
    additional data about agents )
    """

    temp_dic = {}
    temp_dic[ agent_address_port ]={"service_name":related_service_name,
                                    "total_service_usage":0,
                                    "total_resource_usage":0 }
    agents_dic[ session_id ]["detail_agents"].update( temp_dic )

def update_detail_agents_usage( session_id, agent_address_port,
                                service_usage, resource_usage ):
    """
    update the usages of an agent in detail agents( which stores the
    additional data about agents )
    """

    agents_dic[ session_id ]["detail_agents"][agent_address_port]["total_service_usage"]  += service_usage
    agents_dic[ session_id ]["detail_agents"][agent_address_port]["total_resource_usage"]  += resource_usage

def get_detail_agents_service_usage( session_id, agent_address_port ):
    """
    get the total service usage of an agent 
    """

    return agents_dic[ session_id ]["detail_agents"][agent_address_port]["total_service_usage"]

def get_detail_agents_resource_usage( session_id, agent_address_port ):
    """
    get the total resource usage of an agent 
    """

    return agents_dic[ session_id ]["detail_agents"][agent_address_port]["total_resource_usage"]

def get_detail_agents_service_name( session_id, agent_address_port ):
    """
    get the service name related to the agent 
    """

    return agents_dic[ session_id ]["detail_agents"][agent_address_port]["service_name"]
#----------------------------------------------------------------------
# Metering Proxy Coap class
#----------------------------------------------------------------------  
endpoint = resource.Endpoint(None)
protocol_coap = coap.Coap(endpoint)

class MeteringPrxCoap:
    """
    The coap metering proxy class
    """

    def __init__(self, ptr, metering, transport, req_avps,
                 req_type, agentDic, agent_host,
                 agent_port = coap.COAP_PORT ):
        self.ptr = ptr
        self.transport = transport
        self.avps = req_avps
        self.metering = metering
        self.agentDic = agentDic
        self.agent_host = agent_host
        self.agent_port = agent_port
        if req_type == "start":
            reactor.callLater( 1, self.send_agent_start_request )
        elif req_type == "commit":
            reactor.callLater( 1, self.send_agent_commit_request )
        elif req_type == "stop":
            reactor.callLater( 1, self.send_agent_stop_request )        
 
    #------------------------------------------------------------------
    # Send Coap Requests
    #------------------------------------------------------------------
    def send_agent_start_request(self):
        
        payload = cbor.dumps( self.agentDic )
        request = coap.Message( code=coap.GET )
        request.payload = payload
        
        #Send request to "coap://agent_host:agent_port/agent"
        request.opt.uri_path = ('agent',)
        request.opt.observe = 1
        request.remote = ( self.agent_host, self.agent_port )

        # Send the request to Metering agent( coap server )
        # Set the callback functions
        d = protocol_coap.request( request,
                                   observeCallback =\
                                   self.handle_update_credit_request )
        d.addCallback( self.handle_smar_coap_response )
        d.addErrback( self.noResponse )
        
    def send_agent_commit_request(self):
        
        payload = cbor.dumps( self.agentDic )
        request = coap.Message( code=coap.GET )
        request.payload = payload
        
        #Send request to "coap://agent_host:agent_port/agent"
        request.opt.uri_path = ('agent',)
        #request.opt.observe = 1
        request.remote = ( self.agent_host, self.agent_port )

        # Send the request to Metering agent( coap server )
        # Set the callback functions
        d = protocol_coap.request( request )
        d.addCallback( self.handle_commit_coap_response )
        d.addErrback( self.noResponse )

    def send_agent_stop_request(self):
        
        payload = cbor.dumps( self.agentDic )
        request = coap.Message( code=coap.GET )
        request.payload = payload
        
        #Send request to "coap://agent_host:agent_port/agent"
        request.opt.uri_path = ('agent',)
        #request.opt.observe = 1
        request.remote = ( self.agent_host, self.agent_port )

        # Send the request to Metering agent( coap server )
        # Set the callback functions
        d = protocol_coap.request( request )
        d.addCallback( self.handle_stop_coap_response )
        d.addErrback( self.noResponse )
        
    #------------------------------------------------------------------
    # Handle Coap Responses
    #------------------------------------------------------------------        
    def handle_smar_coap_response(self, response):
        """
        Handle the start metering agents response which
        is received from Metering Agent.
        """        
        accounting_info = cbor.loads( response.payload )
        session_id = accounting_info["session_id"]
        related_service_name = accounting_info["service_name"]

        agent_address = response.remote[ 0 ]
        agent_port = response.remote[ 1 ]
        
        # Inform metering proxy 
        self.metering.handle_agent_start_response(
                                                self.avps,
                                                session_id,
                                                agent_address,
                                                agent_port,
                                                related_service_name )
        
    def handle_commit_coap_response(self, response):
        
        usage_commit_res = cbor.loads( response.payload )
        
        session_id = usage_commit_res["session_id"]
        service_usage = usage_commit_res[ "service_usage" ]
        resource_usage = usage_commit_res[ "resource_usage" ]

        agent_address = response.remote[ 0 ]
        agent_port = response.remote[ 1 ]
        agent_address_port = "%s:%s"%( agent_address, agent_port )

        # Update the usage values of specific agent in dictionary
        update_detail_agents_usage( session_id, agent_address_port,
                                service_usage, resource_usage )
        
        # Update the usage values off all agents in dictionary
        update_usage( session_id, service_usage, resource_usage )
        
        self.metering.handle_agent_commit_response(
                                                self.avps,
                                                session_id,
                                                agent_address,
                                                agent_port )
        
    def handle_stop_coap_response(self, response):

        stop_res = cbor.loads( response.payload )
        
        session_id = stop_res["session_id"]

        agent_address = response.remote[ 0 ]
        agent_port = response.remote[ 1 ]
        agent_address_port = "%s:%s"%( agent_address, agent_port )

        self.metering.handle_agent_stop_response(
                                                self.avps,
                                                session_id,
                                                agent_address,
                                                agent_port )

    def handle_update_credit_request(self, request):
        
        usage_update_req = cbor.loads( request.payload )
        print 'Received measured token: %s' %usage_update_req
       
        session_id = usage_update_req["session_id"]
        service_usage = usage_update_req[ "service_usage" ]
        resource_usage = usage_update_req[ "resource_usage" ]

        agent_address = request.remote[ 0 ]
        agent_address_port = "%s:%s"%( agent_address, self.agent_port )

        # Update the usage values of specific agent in dictionary
        update_detail_agents_usage( session_id, agent_address_port,
                                service_usage, resource_usage )
        
        # Update the usage values off all agents in dictionary
        update_usage( session_id, service_usage, resource_usage )
        
            
    def noResponse(self, failure):
        print 'Failed to fetch resource:'
        print failure
        

#----------------------------------------------------------------------
# Metering Proxy class
#----------------------------------------------------------------------  
class MeteringPrx:
    """
    The Tcp metering proxy class
    """

    #------------------------------------------------------------------
    # request received handler
    #------------------------------------------------------------------
    def handle_req_received(self, req, transport):
        """
        As soon as request received through Tcp from other servers ,
        this function is called.
        """

        req_avps = return_request_avps( req )
        req_action = get_request_action_from_avps( req_avps )
        session_id = get_session_id_from_avps( req_avps )
        state = get_state( session_id )
        
        # Received start metering agents request from metering server
        # ( SMAR request )
        if req_action == START_METERING_AGENTS:
            self.handle_mtr_start_meter_agents_request( req_avps,
                                                    transport )

        # Received Commit Metering Tokens request from Metering Server
        # ( CMTR request )    
        elif req_action == COMMIT_METERING_TOKENS:
            self.handle_commit_metering_tokens_request( req_avps, transport )     

        # Received Stop Metering Agents request from Metering Server
        # ( CMTR request )    
        elif state == OPEN_M and req_action == STOP_METERING_AGENTS:
            self.handle_mtr_stop_meter_agents_request( req_avps, transport )
            
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

        # Received publish usage update from Metering
        # ( ** PUUA from metering )
        if res_action == PUBLISH_USAGE_UPDATE and state == PENDING_MUU:
            self.handle_mtr_pub_usage_update_response( res_avps )
            
    #------------------------------------------------------------------
    # handle received requests
    #------------------------------------------------------------------
    def handle_mtr_start_meter_agents_request( self, req_avps,
                                              req_transport ):
        """
        Handle the start metering agents request which
        is received from Metering server ( SMAR ).
        """

        self.pause = False
        session_id = get_session_id_from_avps( req_avps )

        print
        print "Received 'SMAR' request from Metering Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with Session-Id = %s "%session_id+\
              "and Request-Id = %s"%get_request_id_from_avps(req_avps)
        print "-"*64
        
        # set state and send a start agent request to all agents
        set_state( session_id, PENDING_MA )

        req_id = get_request_id_from_avps( req_avps )
        set_wait_req( session_id, req_id, req_transport )

        # ** Should be Retrieved from plan
        agent_addresses = [ "127.0.0.1:5683" , "127.0.0.1:5684" ]
        agent_names = [ "metering_agent.py", "metering_agent_2.py" ]
        set_agents_dic( session_id, agent_addresses )
        
        for i in range( len( agent_addresses ) ):

            agent = agent_addresses[ i ]
            agent_add, agent_port = agent.split( ":" )
            # It's just a test code which is used to run the agent code
            agent_name = agent_names[ i ]
            command = "python %s"%agent_name
            subprocess.Popen(["start", "cmd", "/k",command], shell=True)
            
            # ** u3 for each agent should be retrieved from plan
            u3 = 1
        
            # Create a dictionary contains required info for starting
            # the agent
            agentDic = {}
            agentDic["session_id"] = session_id
            agentDic["request"] = "start"
            agentDic["u3"] = u3
            #agentDic["unit_price"] = unit_price
            #agentDic["usage_price"] = usage_price
            #agentDic["service_ip"] = service_ip
            #agentDic["service_port"] = service_port
            #agentDic["timebased"] = timebased

            req_type = "start"
            client = MeteringPrxCoap( protocol_coap, self,
                                      req_transport, req_avps,
                                      req_type,
                                      agentDic, agent_add, int( agent_port ) )
            add_waiting_agent( session_id, agent )


    def handle_commit_metering_tokens_request( self, req_avps,
                                               req_transport ):
        """
        Handle the Commit Metering Tokens request which is received
        from Metering Server ( CMTR ).
        """

        session_id = get_session_id_from_avps( req_avps )

        print
        print "Received 'CMTR' request from Metering Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with Session-Id = %s "%session_id+\
              "and Request-Id = %s"%get_request_id_from_avps(req_avps)
        print "-"*64

        # set state and send a commit request to all agents
        set_state( session_id, PENDING_MAC )

        req_id = get_request_id_from_avps( req_avps )
        set_wait_req( session_id, req_id, req_transport )

        agent_addresses = get_list_of_agents( session_id )

        for i in range( len( agent_addresses ) ):

            agent = agent_addresses[ i ]
            agent_add, agent_port = agent.split( ":" )

            # Create a dictionary contains commit request
            agentDic = {}
            agentDic["session_id"] = session_id
            agentDic["request"] = "commit"

            req_type = "commit"
            client = MeteringPrxCoap( protocol_coap, self,
                                      req_transport, req_avps,
                                      req_type,
                                      agentDic, agent_add, int( agent_port ) )
            add_waiting_agent( session_id, agent )

    def handle_mtr_stop_meter_agents_request(  self, req_avps,
                                                req_transport ):
        """
        Handle the stop metering agents request which is received
        from Metering Server ( PMAR ).
        """
        session_id = get_session_id_from_avps( req_avps )

        print
        print "Received 'PMAR' request from Metering Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with Session-Id = %s "%session_id+\
              "and Request-Id = %s"%get_request_id_from_avps(req_avps)
        print "-"*64
        
        # set state and send a stop request to All Metering Agents
        set_state( session_id, PENDING_MAT )

        req_id = get_request_id_from_avps( req_avps )
        set_wait_req( session_id, req_id, req_transport )
        
        agent_addresses = get_list_of_agents( session_id )

        for i in range( len( agent_addresses ) ):

            agent = agent_addresses[ i ]
            agent_add, agent_port = agent.split( ":" )

            # Create a dictionary contains commit request
            agentDic = {}
            agentDic["session_id"] = session_id
            agentDic["request"] = "stop"

            req_type = "stop"
            client = MeteringPrxCoap( protocol_coap, self,
                                      req_transport, req_avps,
                                      req_type,
                                      agentDic, agent_add, int( agent_port ) )
            add_waiting_agent( session_id, agent )
            
    #------------------------------------------------------------------
    # handle received responses
    #------------------------------------------------------------------
    def handle_agent_start_response( self,  res_avps, session_id,
                                     agent_address, agent_port,
                                     related_service_name ):
        """
        Handle the start agent response which
        is received from Metering agents.
        """

        print
        print "Received 'Start' response from Metering Agent ( "+\
              "%s:%s )"%( agent_address, agent_port )
        print "at %s "%datetime.datetime.now().strftime("%H:%M:%S:%f")+\
              "with the Session-Id = %s "%session_id
        print "-"*64
        
        # should remove the agent from list
        # Check the list if empty send SMAA to metering server

        agent_address_port = "%s:%s"%( agent_address, agent_port )
        add_detail_agents( session_id, agent_address_port,
                           related_service_name )

        remove_waiting_agent( session_id, agent_address_port )

        if is_waiting_agents_empty( session_id ) :
            
            # set state and send a SMAA response to Metering server
            set_state( session_id, OPEN_M )

            ( smaa_req_id, smaa_transport ) = pop_wait_req( session_id )
            smaa = self.create_mtr_start_meter_agents_response( res_avps,
                                                         smaa_req_id )
            smaa_transport.write( smaa )

            # Set the timer to aggregation_threshold value
            # for the session_id
            aggregation_threshold = get_aggregation_threshold( \
                                                            session_id )
            loop = task.LoopingCall(self.handle_aggregation_threshold_met,
                                    res_avps, session_id )
            loop.start(aggregation_threshold,False)


    def handle_agent_commit_response( self, res_avps, session_id,
                                      agent_address, agent_port ):
        """
        Handle the commit metering agent response which
        is received from Metering Agents.
        """

        print
        print "Received 'Commit' response from Metering Agent ( "+\
              "%s:%s )"%( agent_address, agent_port )
        print "at %s "%datetime.datetime.now().strftime("%H:%M:%S:%f")+\
              "with the Session-Id = %s "%session_id
        print "-"*64
        
        # should remove the agent from list
        # Check the list if empty send CMTA to metering server

        agent_address_port = "%s:%s"%( agent_address, agent_port )
        remove_waiting_agent( session_id, agent_address_port )

        if is_waiting_agents_empty( session_id ) :
            
            # set state and send a CMTA response to Metering server
            # Pause the metering proxy to not send a new usage package to
            # Metering after commiting
            self.pause = True
            set_state( session_id, OPEN_M )

            ( cmta_req_id, cmta_transport ) = pop_wait_req( session_id )
            cmta = self.create_commit_metering_tokens_response(
                                                res_avps, cmta_req_id )
            
            cmta_transport.write( cmta )

    def handle_agent_stop_response( self, res_avps, session_id,
                                      agent_address, agent_port ):
        """
        Handle the stop metering agent response which
        is received from Metering Agents.
        """

        print
        print "Received 'Stop' response from Metering Agent ( "+\
              "%s:%s )"%( agent_address, agent_port )
        print "at %s "%datetime.datetime.now().strftime("%H:%M:%S:%f")+\
              "with the Session-Id = %s "%session_id
        print "-"*64
        
        # should remove the agent from list
        # Check the list if empty send PMAA to metering server

        agent_address_port = "%s:%s"%( agent_address, agent_port )
        remove_waiting_agent( session_id, agent_address_port )

        if is_waiting_agents_empty( session_id ) :
            
            # set state and send a PMAA response to Metering server
            set_state( session_id, IDLE_M )

            ( pmar_req_id, pmar_transport ) = pop_wait_req( session_id )
            pmaa = self.create_mtr_stop_meter_agents_response(
                                                res_avps, pmar_req_id )
            
            pmar_transport.write( pmaa )
            
    def handle_mtr_pub_usage_update_response( self, res_avps ):
        """
        Handle publish usage update response which is
        received from Metering server( ** PUUA from metering ).
        """

        print
        print "Received 'PUUA' response from Metering Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the result_code "+\
              "= %s, "%get_result_code_from_avps( res_avps )+\
              "Session-Id = %s "%get_session_id_from_avps( res_avps )
        print "and Request-Id = %s"%get_request_id_from_avps(res_avps)
        print "-"*64
        print

        session_id = get_session_id_from_avps( res_avps )
        set_state( session_id, OPEN_M )

    
    #------------------------------------------------------------------
    # creating requests
    #------------------------------------------------------------------
    def create_mtr_pub_usage_update_request( self, avps, app_usage ):
        """
        Create a request for publishing usage update which is sent
        to Metreing server( ** PUUR to Metering Server ).
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

        print "Send 'PUUR' request to Metering Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              ", Request-Id = %s "%req_id
        print "and App-Usage = %s"%app_usage
        print "="*64
        print
        
        return request.decode("hex")
    

    #------------------------------------------------------------------
    # creating responses
    #------------------------------------------------------------------
    def create_mtr_start_meter_agents_response( self, avps, req_id ):
        """
        Create a response of start metering agents request which is sent
        to Metering server( SMAA ).
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
                                   START_METERING_AGENTS ))
        
        # create header and set command
        smaa = HDRItem()
        smaa.cmd = dictCOMMANDname2code('DoT-Answer')
        initializeHops( smaa )
        response = createRes( smaa, res_avps )

        print
        print "Send 'SMAA' response to Metering Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%avps["Session-Id"]+\
              "and Request-Id = %s"%req_id
        print "-"*64
        
        return response.decode("hex")


    def create_commit_metering_tokens_response( self, avps, req_id ):
        """
        Create a response of commit metering tokens request which is sent
        to Metering server( CMTA ).
        """

        session_id = avps["Session-Id"]
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
                                   COMMIT_METERING_TOKENS ))
        
        last_service_resource_usage = refresh_credit( session_id )
        res_avps.append(encodeAVP("App-Usage",
                                  last_service_resource_usage ))

        # Create billable artifact in json format and Serialize it
        billable_artifact = {}
        for agent in get_list_of_agents( session_id ):
            agent_service_name = get_detail_agents_service_name(
                                                            session_id,
                                                            agent )
            billable_artifact[ agent_service_name ] = {}
            billable_artifact[ agent_service_name ]["service_ugase"] =\
                        get_detail_agents_service_usage(session_id,agent )
            billable_artifact[ agent_service_name ]["resource_usage"] =\
                        get_detail_agents_resource_usage(session_id,agent )
        res_avps.append(encodeAVP("Billable-Artifact",
                                  json.dumps( billable_artifact ) ))

        # create header and set command
        cmta = HDRItem()
        cmta.cmd = dictCOMMANDname2code('DoT-Answer')
        initializeHops( cmta )
        response = createRes( cmta, res_avps )

        print
        print "Send 'CMTA' response to Metering Server "+\
              "at %s"%datetime.datetime.now().strftime("%H:%M:%S:%f")
        print "with the Session-Id = %s "%session_id+\
              "and Request-Id = %s"%req_id
        print "-"*64
            
        return response.decode("hex")

    def create_mtr_stop_meter_agents_response( self, avps, req_id ):
        """
        Create a response of stop metering agents request which is sent
        to Metering server( PMAA ).
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
                                   STOP_METERING_AGENTS ))
        
        # create header and set command
        pmaa = HDRItem()
        pmaa.cmd = dictCOMMANDname2code('DoT-Answer')
        initializeHops( pmaa )
        response = createRes( pmaa, res_avps )

        print
        print "Send 'PMAA' response to Metering Server "+\
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
    send_to_mtr_proxy = lambda self, msg: self.send_to( msg, MTR_PRX_HOST,
                                                        MTR_PRX_PORT )

    #------------------------------------------------------------------
    # Handle aggregation threshold met
    #------------------------------------------------------------------
    
    def handle_aggregation_threshold_met( self, res_avps, session_id ):

        if self.pause: return
        
        print
        print "="*64
        print "Aggregation Threshold has been met "+\
              "at %s "%datetime.datetime.now().strftime("%H:%M:%S:%f")+\
              " for Session-Id = %s "%session_id
        print

        service_resource_usage = refresh_credit( session_id )

        if service_resource_usage != 0 :
            # set state and send a PUUR request to Metering Server
            set_state( session_id, PENDING_MUU )
            puur = self.create_mtr_pub_usage_update_request(
                                                    res_avps,
                                                    service_resource_usage )

            self.send_to_mtr( puur )

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
        
    # Send a message to Metering Server 
    send_to_mtr = lambda self, msg: self.send_to( msg, MTR_HOST, MTR_PORT )
    
        
    #------------------------------------------------------------------
    # Running the server
    #------------------------------------------------------------------        
    def run_server(self):
        """
        Run the metering server.
        """
        factory = ServerFactory( self )
        reactor.listenTCP( MTR_TCP_PRX_PORT, factory )


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
        self.transport.loseConnection()

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
        reactor.stop()
    
##    def clientConnectionLost(self, connector, reason):
##        """
##        As soon as connection was lost, this function is called.
##        """
##        print "Connection lost"
##        reactor.stop()
        
    def buildProtocol(self, addr):
        """
        return the ClientProtocol as its factory
        """
        return ClientProtocol(self, self.metering, self.message)

# this only runs if the module was *not* imported
if __name__ == '__main__':
    metering_prx_tcp = MeteringPrx()
    metering_prx_tcp.run_server()
    reactor.listenUDP( MTR_UDP_PRX_PORT , protocol_coap )
    reactor.run()
