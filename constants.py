#!/usr/bin/env python
#######################################################################
# Copyright (c) 2015
# Oct 2015 - 
# Version 0.1, Last change on Oct 15, 2015    
#######################################################################

# All required constants which are used in other modules

#======================================================================
# Server Addresses
#======================================================================

DOT_HOST = 'localhost'
DOT_PORT = 5000

AA_HOST = 'localhost'
AA_PORT = 5001

PROV_HOST = 'localhost'
PROV_PORT = 5002

RCS_HOST = 'localhost'
RCS_PORT = 5003

MTR_HOST = 'localhost'
MTR_PORT = 5004

# ** Should be retrive from plan file - it might be different for
# each session_id
MTR_TCP_PRX_HOST = 'localhost'
MTR_TCP_PRX_PORT = 5005
MTR_UDP_PRX_HOST = 'localhost'
MTR_UDP_PRX_PORT = 6005

PY_HOST = 'localhost'
PY_PORT = 5006

BUFFER_SIZE = 1024

#======================================================================
# Server requests
#======================================================================

USER_START_REQ = "Start"
USER_TERMINATE_REQ = "Terminate"

#======================================================================
# Server States
#======================================================================

##IDLE = 0
##OPEN = 1

# Dot Client

##PENDING_I = 2
##PENDING_P = 3
##PENDING_D = 4
##PENDING_T = 5

IDLE_D = 0
PENDING_DI = 1
PENDING_DP = 2
PENDING_DD = 3
OPEN_D = 4 
PENDING_DT = 5

# Provisioning

##PENDING_R = 6
##PENDING_M = 7
IDLE_P = 6
IDLE_PP = 7
PENDING_PR = 8
PENDING_PM = 9
OPEN_P = 10
PENDING_PRR = 11
PENDING_PMM = 12
PENDING_PNU = 13

# Resource Control

IDLE_R = 14
OPEN_R = 15
PENDING_RPP = 16
PENDING_RME = 17
PENDING_RPY = 18
PENDING_RPL = 19
PENDING_RNU = 20

# Metering

IDLE_M = 21
PENDING_MG = 22
PENDING_MA = 23
OPEN_M = 24
PENDING_MUU = 25
PENDING_MAT = 26
PENDING_MPC = 27
PENDING_MAC = 28

# Payment

IDLE_PY = 29

#======================================================================
# Server timeout in receiving the response or request
#======================================================================

##WAITING_FOR_AA_RES = 20
##WAITING_FOR_PROV_RES = 20
##WAITING_FOR_USER_REQ = 10

# Dot Client
WAITING_DI = 10
WAITING_DP = 10
WAITING_DD = 10 
WAITING_DT = 10

# Provisioning
WAITING_PR = 10
WAITING_PM = 10
WAITING_PRR = 10
WAITING_PMM = 10

# Resource Control
WAITING_RME = 10
WAITING_RPY = 10

# Metering
WAITING_MG = 10
WAITING_MA = 10
WAITING_MUU = 10
WAITING_MAT = 10

#======================================================================
# Diam Messages
#======================================================================

AUTHENTICATE_ONLY = 1
NO_STATE_MAINTAINED  = 1


ACCOUNTING_REQUEST = 271
AA_REQUEST = 265

#======================================================================
# DoT Messages
#======================================================================

#------------------------------------
# Request types
#------------------------------------

PROV_REQ = 1
METER_REQUEST = 2
UPDATE_REQUEST = 3
PAY_REQUEST = 4
TERMINATE_REQUEST = 5

#------------------------------------
# Request actions
#------------------------------------

REQ_ACT = "Dot-Requested-Action"
REQ_TYPE = "Request-Type"
SESSION_ID = "Session-Id"
REQ_ID = "Request-Id"
RES_CODE = "Result-Code"

# Provisioning
PROV_APP_TOPO = 1
APP_RESOURCE_ALLOCATION = 2
START_IOT_APP = 3

# Metering
START_APP_METERING = 4
GET_APP_SPECIFICATION = 5
START_METERING_AGENTS = 6
PUBLISH_USAGE_UPDATE = 7
SEND_COMMIT_VOTES = 8
COMMIT_METERING_TOKENS = 9
COMMIT_APP_METERING = 10
TERMINATE_APP_METERING = 11
STOP_METERING_AGENTS = 12

# payment
START_BILL_PAYMENT = 13
LOCK_USER_CREDIT = 14

#------------------------------------
# Update Requests
#------------------------------------

# Confirmation-Mode
NOTIFY_ONLY = 0
USER_ACTION_REQUIRED = 1

# Allocation-Unit
CREDIT = 0
SUBSCRIPTION_TIME = 1

#======================================================================
# Commands and avps dictionaries' path 
#======================================================================

DICT_DIAMETER_PATH = "Dictionary/dictDiameter.xml"
DICT_DOT_PATH = "Dictionary/dictDoT.xml"
DICT_MERGE_PATH = "Dictionary/mergeDict.xml"

#======================================================================
# Server response for timeout and result codes
#======================================================================
AA_SUCCESS = 2001
AA_UNKNOWN_USER = 5006

SUCCESS = 2001
