#!/usr/bin/env python
##################################################################
# Copyright (c) 2015
# Jan 06 - 
# Version 0.1, Last change on Jan 10, 2016    
##################################################################

# All functions needed to implement Metering Agent

from twisted.internet import defer
from twisted.internet import reactor

import txthings.resource as resource
import txthings.coap as coap

import json, random, cbor
import os

class Agent(resource.CoAPResource):

    """
    The Metering Agent Class. It is a coap server which listen to coap
    defualt port.

    It contains render_GET which invoked by sending get request to this
    server.

    The format of data is received is json. Each json message includes:

        - session_id : The session_id of run service
        - u3 : Metered usage data( used_credit ) is sent to
               Metering agent by the rate of u3
        - request : which can be "start", "meter",...
    
    """

    def __init__(self):
        """
        Initializer of Metering Agent Class.
        """
        resource.CoAPResource.__init__(self)
        self.pause = False
        self.visible = True
        self.observable = True
        self.do_meter = 0
        self.u3 = None
        self.service_name = "service #1"
        self.update_credit_dic = {}


    def notify_used_credit(self):
        """
        Send the used credit to Metering Proxy by u3 rate.
        """
        if self.pause :
            return
        self.updatedState()
        if self.u3:
            reactor.callLater( self.u3, self.notify_used_credit )
        else:
            reactor.callLater( 10, self.notify_used_credit )

    def render_GET(self, request):
        """
        As soon as the get request received,
        this function is called.
        """
        info = cbor.loads( request.payload )

        # Start Request
        if info["request"] == "start":
            if not self.do_meter:
                print 
                print " -- Received start request from Metering Proxy -- "
                print " Metering Agent has started metering process."
                print
                self.u3 = info["u3"]
                self.session_id = info["session_id"]
                self.update_credit_dic[ "session_id" ] = self.session_id
                self.update_credit_dic[ "request" ] = "start"
                self.update_credit_dic[ "service_name" ] = self.service_name
                self.notify_used_credit()

            # Create Metering proxy response ( the first time, it is the start
            # response and further times, it also contains metered usage credit )
            # Send the response to Metering Proxy
            response = coap.Message(
                                code = coap.CONTENT,
                                payload = self.create_start_update_response()
                                )
            
            self.do_meter = 1
            return defer.succeed(response)

        # Commit Request
        elif info["request"] == "commit" :
            print 
            print " -- Received commit request from Metering Proxy -- "
            print " Metering Agent is going to commit the measured metering token."
            print
            self.pause = True
            self.session_id = info["session_id"]
            response = coap.Message(
                                code = coap.CONTENT,
                                payload = self.create_commit_response()
                                )            
            return defer.succeed(response)

        # Stop Request
        elif info["request"] == "stop" :
            print 
            print " -- Received Stop request from Metering Proxy -- "
            
            print
            self.session_id = info["session_id"]
            response = coap.Message(
                                code = coap.CONTENT,
                                payload = self.create_stop_response()
                                )            
            print " Metering Agent is going to stop....."
            reactor.callLater( 10, self.stop )
            return defer.succeed(response)        

    def stop(self):
        """
        Stop the metering Agent.
        """
        os._exit(0)
        
    def create_stop_response(self ):
        """
        Create the stop response send it to
        the proxy Server.
        """
        temp_stop_dic = {}
        temp_stop_dic[ "session_id" ] = self.session_id
        temp_stop_dic[ "service_name" ] = self.service_name

        temp_stop_dic[ "request" ] = "stop_response"
        print " Send stop response to the Metering Proxy"
        return cbor.dumps( temp_stop_dic )
    
    def create_commit_response(self ):
        """
        Create the commit response, commit the usage and send it to
        the proxy Server.
        """
        temp_commit_dic = {}
        temp_commit_dic[ "service_usage" ] = random.randint(1,5)
        temp_commit_dic[ "resource_usage" ] = random.randint(1,2)
        temp_commit_dic[ "session_id" ] = self.session_id
        temp_commit_dic[ "service_name" ] = self.service_name

        temp_commit_dic[ "request" ] = "commit_response"
        print " Send commit response with the last measured token:"
        print
        print temp_commit_dic
        print
        return cbor.dumps( temp_commit_dic )

    
    def create_start_update_response(self ):
        """
        Create the response which is sent to Metering Proxy.
        The first response is the response of "start metering agent"
        request, and further responses are related to informing
        used credit.
        """
        if self.do_meter:
            self.update_credit_dic[ "service_usage" ] = random.randint(1,5)
            self.update_credit_dic[ "resource_usage" ] = random.randint(1,2)

            # Send ACR request to Metering Proxy
            self.update_credit_dic[ "request" ] = "send_usage_update"
        else:
            print
            print " -- Sending Following metering tokens to "+\
                  "Metering Proxy -- "
            print
        
        print self.update_credit_dic
        return cbor.dumps( self.update_credit_dic )

        
#----------------------------------------------------------------------
# Creating resource tree and running the Metering agent ( Coap Server )
#---------------------------------------------------------------------- 
# Resource tree creation
root = resource.CoAPResource()

agent = Agent()
root.putChild('agent', agent)
endpoint = resource.Endpoint(root)

# Run the server on coap default port ( 5683 ) 
reactor.listenUDP(coap.COAP_PORT, coap.Coap(endpoint)) #, interface="::")
reactor.run()
