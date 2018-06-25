from libDiameter import *
from merge_dicts import merge_dictionaries

from constants import *

#----------------------------------------------------------------------
# Methods related to work with diameter
#----------------------------------------------------------------------

def create_req_id():
    """
    Create request id
    """
    return long( str(time.time()).replace(".","")[2:-1] )

def merge_load_dictionary( ):
    """
    Merge the input dictionaries and load the output file
    """
    
    in_files = ( DICT_DIAMETER_PATH, DICT_DOT_PATH )
    out_file = DICT_MERGE_PATH
    merge_dictionaries( in_files, out_file )
    LoadDictionary(out_file)

def get_request_type( request ):
    """
    Retrieve the request type from received message and
    return it
    """
    
    header = HDRItem()
    stripHdr(header,request.encode("hex"))
    avps_encode =splitMsgAVPs(header.msg)

    for avp in avps_encode:
        avp_decode = decodeAVP(avp)
        if avp_decode[0] == REQ_TYPE:
            return avp_decode[1]
    return

def get_request_action( request ):
    """
    Retrieve the request action from received message and
    return it
    """
    
    header = HDRItem()
    stripHdr(header,request.encode("hex"))
    avps_encode =splitMsgAVPs(header.msg)

    for avp in avps_encode:
        avp_decode = decodeAVP(avp)
        if avp_decode[0] == REQ_ACT:
            return avp_decode[1]
    return
    
def return_session_id( request ):
    """
    Return the session_id retrieved from the received request message
    """
    
    header = HDRItem()
    stripHdr(header,request.encode("hex"))
    avps_encode =splitMsgAVPs(header.msg)

    avps={}
    for avp in avps_encode:
        avp_decode = decodeAVP(avp)
        avps[ avp_decode[0] ] =  avp_decode[1]
    return avps

def return_request_avps( request ):
    """
    Return the avps retrieved from the received request message
    """
    
    header = HDRItem()
    stripHdr(header,request.encode("hex"))
    avps_encode =splitMsgAVPs(header.msg)

    avps={}
    for avp in avps_encode:
        avp_decode = decodeAVP(avp)
        avps[ avp_decode[0] ] =  avp_decode[1]
    return avps


def return_command_id( request ):
    """
    Return the command id retrieved from the received request message
    """
    
    header = HDRItem()
    stripHdr(header,request.encode("hex"))
    return header.cmd

#----------------------------------------------------------------------
# Get info from input avps
#----------------------------------------------------------------------

def get_request_action_from_avps( avps ):
    """
    Retrieve the request action from the input avps
    """
    
    try:
        return avps[ REQ_ACT ]
    except:
        return

def get_session_id_from_avps( avps ):
    """
    Retrieve the session id from the input avps
    """
    
    try:
        return avps[ SESSION_ID ]
    except:
        return

def get_request_type_from_avps( avps ):
    """
    Retrieve the request type from the input avps
    """
    
    try:
        return avps[ REQ_TYPE ]
    except:
        return

def get_request_id_from_avps( avps ):
    """
    Retrieve the request id from the input avps
    """
    
    try:
        return avps[ REQ_ID ]
    except:
        return

def get_result_code_from_avps( avps ):
    """
    Retrieve the result code from the input avps
    """
    
    try:
        return avps[ RES_CODE ]
    except:
        return
    
#----------------------------------------------------------------------
# importing time
#----------------------------------------------------------------------
    
# load the merged dictionary to libDiameter when this module is imported
merge_load_dictionary()
