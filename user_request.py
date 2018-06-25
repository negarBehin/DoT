#!/usr/bin/env python
##################################################################
# Copyright (c) 2015
# Oct 2015 - 
# Version 0.1, Last change on Nov 03, 2015    
##################################################################

# Tcp client which sends the user request to DoT client


import json

from twisted.internet import reactor, protocol
from constants import *
    
#------------------------------------------------------------------
# user request routins
#------------------------------------------------------------------        
def create_user_request( request ):
    """
    Create request which is sent to DotClient server.
    """
    userDic = {}
    userDic["request"] = request
    userDic["username"] = raw_input ( "Enter the user name:" )
    userDic["password"] = raw_input ( "Enter the password:" )
    userDic["app_id"] = int(raw_input ( "Enter the app_id:" ))

    if request == USER_START_REQ:
        userDic["email"] = raw_input ( "Enter the user email:" )
        userDic["topo_url"] = raw_input ( "Enter the topology url:" )

    req = json.dumps( userDic )
    return req


def send_request_to_dot( req ):
    """
    Send request to DotClient server.
    """
    factory = ClientFactory( req )
    reactor.connectTCP( DOT_HOST, DOT_PORT, factory )
    reactor.run()


def main():
    """
    Get user inputs and send the request.Called by executing the
    module.
    """
    
    # Get the required info from user
    ok_input = 0
    while not ok_input:        
        data = raw_input ( "Enter 'S' to send " +\
                           "Start request or 'T' for "+\
                           " Terminate request:" )
        data = data.upper()
        if data not in ['S','T']:
            continue
        else:
            ok_input = 1
            if data == 'S' : request = USER_START_REQ
            else : request = USER_TERMINATE_REQ
    
    # Create the request according to user inputs and send it to Dot
    req = create_user_request( request )
    send_request_to_dot( req )
    
#----------------------------------------------------------------------
# Client protocol
#---------------------------------------------------------------------- 
class ClientProtocol(protocol.Protocol):
    """
    The client protocol is used to send message for Dot Client server
    """
    
    def __init__( self, factory, message ):
        """
        initialization of ClientProtocol class
        """
        self.message = message
        
    def connectionMade( self ):
        """
        As soon as the connection is made, this function is called and
        send the message to the server.
        """
        self.transport.write( self.message )
        
    def dataReceived(self, data):
        """
        As soon as data received, this function is called.
        """
        print
        print data
        print
        self.transport.loseConnection()

#----------------------------------------------------------------------
# Client Factory
#---------------------------------------------------------------------- 
class ClientFactory(protocol.ClientFactory):
    
    def __init__(self,message):
        """
        initialization of ClientFactory class
        """
        self.message = message
        
    def clientConnectionFailed( self, connector, reason ):
        """
        As soon as connection was failed, this function is called.
        """
        #print "Connection failed!"
        reactor.stop()
    
    def clientConnectionLost( self, connector, reason ):
        """
        As soon as connection was lost, this function is called.
        """
        #print "Connection lost!"
        reactor.stop()
        
    def buildProtocol( self, addr ):
        """
        return the ClientProtocol as its protocol
        """
        return ClientProtocol( self, self.message )
    
#----------------------------------------------------------------------
# run-time execution
#---------------------------------------------------------------------- 
if __name__ == '__main__':
    main()

