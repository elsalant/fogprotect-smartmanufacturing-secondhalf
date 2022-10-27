#
# Copyright 2022 IBM Corp.
# SPDX-License-Identifier: Apache-2.0
#

from fybrik_python_logging import init_logger, logger, DataSetID, ForUser
from abm.config import Config
from abm.connector import GenericConnector
from abm.ticket import ABMTicket
from abm.jwt import decrypt_jwt
from abm.opa_requests_utils import opa_get_actions
from abm.kafka_utils import logToKafka
import http.server
import json
import os
import socketserver
from http import HTTPStatus
import pyarrow.flight as fl
import yaml

JWT_KEY = os.getenv("JWT_KEY") if os.getenv("JWT_KEY") else 'realm_access.roles'
TEST = True
CM_SITUATION_PATH = '/etc/confmap/situationstatus.yaml'
TESTING_SITUATION_STATUS = 'safe'

class ABMHttpHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        self.config_path = server.config_path
        self.workdir = server.workdir
        socketserver.BaseRequestHandler.__init__(self, request, client_address, server)

    '''
    do_GET() gets the asset name from the URL.
    for instance, if the URL is localhost:8080/userdata
    then the asset name is userdata.
    Obtain the dataset associated with the asset name, and
    return it to client.
    '''
    def do_GET(self):
        logger.info('do_GET called')
        action, policy = self.runtimeEval()
        logger.info('do_GET: action = ' + action)
        if (action == 'BlockResource'):
            self.send_response(HTTPStatus.FORBIDDEN)
            self.end_headers()
            self.wfile.write(b'Request blocked!')
            logToKafka(self, 'BlockURL', policy, self.headers.get('Host'))
            return
        with Config(self.config_path) as config:
            asset_name = self.path.lstrip('/')
            logger.debug('do_GET: asset_name = ' + asset_name)
            try:
                asset_conf = config.for_asset(asset_name)
                connector = GenericConnector(asset_conf, logger, self.workdir)
            except ValueError:
                logger.error('asset not found or malformed configuration')
                self.send_response(HTTPStatus.NOT_FOUND)
                self.end_headers()
                return
            batches = connector.get_dataset()
            if batches:
                self.send_response(HTTPStatus.OK)
                self.end_headers()
                for batch in batches:
                    for line in batch:
                        self.wfile.write(line + b'\n')
            else:
                self.send_response(HTTPStatus.BAD_REQUEST)
                self.end_headers
        logToKafka(self, 'AllowURL', policy, self.headers.get('Host'))


# Have the same routine for PUT and POST
    def do_WRITE(self):
        logger.info('write requested')
        action, policy = self.runtimeEval()
        logger.info('do_WRITE: action = ' + action)
        if (action == 'BlockResource'):
            self.send_response(HTTPStatus.FORBIDDEN)
            self.end_headers()
            logToKafka(self, 'BlockURL', policy, self.headers.get('Host'))
            return('Request blocked!')
        with Config(self.config_path) as config:
            asset_name = self.path.lstrip('/')
            try:
                asset_conf = config.for_asset(asset_name)
                connector = GenericConnector(asset_conf, logger, self.workdir)
            except ValueError:
                logger.error('asset ' + asset_name + ' not found or malformed configuration')
                self.send_response(HTTPStatus.NOT_FOUND)
                self.end_headers()
                self.wfile.write(b'Request blocked!')
                return
            # Change to allow for chunking
            read_length = self.headers.get('Content-Length')
            if connector.write_dataset(self.rfile, int(read_length)):
                self.send_response(HTTPStatus.OK)
            else:
                self.send_response(HTTPStatus.BAD_REQUEST)
            self.end_headers()
        logToKafka(self, 'AllowURL', policy, self.headers.get('Host'))

    def do_PUT(self):
        self.do_WRITE()

    def do_POST(self):
        self.do_WRITE()

    # runtimeEval() will get the role value from the JWT and the situationStatus from the
    # environment variable (from a k8s configmap) and call out to OPA to reassess the policy in order to
    # check if the endpoint is blocked.
    def runtimeEval(self):
        # Extract key from JWT
        jwtKeyValue = decrypt_jwt(self.headers.get('Authorization'), JWT_KEY)
        logger.info('jwtKeyValue = ' + str(jwtKeyValue))
        # FogProtect: Get the value of the external set SITUATION_STATUS variable (mounted from a configmap)
 #       situationStatus = os.getenv('SITUATION_STATUS') if os.getenv('SITUATION_STATUS') else 'ERROR - SITUATION_STATUS UNDEFINED'
        situationStatus = getSituationStatus()
        logger.info('situationStatus = ' + situationStatus)
        # Call OPA to get runtime policy evaluation
        actionDict = opa_get_actions(jwtKeyValue, situationStatus, self.path)
        # The Policy Mgr creates a list of dictionaries with the return action.  Get the dictionary that contains 'action'
        dictLists = actionDict['result']['rule']
        actionIndex = -1
        matchingPolicy =''
        for i in range(len(dictLists)):
            if 'action' in dictLists[i]:
                actionIndex = i
                matchingPolicy = dictLists[i]
                break
        try:
            action = actionDict['result']['rule'][actionIndex]['action']
        except:   # no matching rule
            action = 'NO POLICY ACTION'
#For FogProtect - log to Kafka

        return(action, matchingPolicy)

def getSituationStatus():
    if not TEST:
        try:
            with open(CM_SITUATION_PATH, 'r') as stream:
                cmReturn = yaml.safe_load(stream)
                situationStatus = cmReturn['situation-status']
        except Exception as e:
            errorStr = 'Error reading from file! ' + CM_SITUATION_PATH
            raise ValueError(errorStr)
    else:
        situationStatus = TESTING_SITUATION_STATUS
    logger.info('situationStatus being returned as ' + situationStatus)
    return situationStatus

class ABMHttpServer(socketserver.TCPServer):
    def __init__(self, server_address, RequestHandlerClass,
                 config_path, workdir):
        self.config_path = config_path
        self.workdir = workdir
        socketserver.TCPServer.__init__(self, server_address,
                                        RequestHandlerClass)

class ABMFlightServer(fl.FlightServerBase):
    def __init__(self, config_path: str, port: int, workdir: str, *args, **kwargs):
        super(ABMFlightServer, self).__init__(
                "grpc://0.0.0.0:{}".format(port), *args, **kwargs)
        self.config_path = config_path
        self.workdir = workdir

    '''
    Return a list of locations which can serve a client
    request for a dataset, given a flight ticket.
    The location list may be empty to indicate that the client
    should contact the same server that server its
    get_flight_info() request.
    '''
    def _get_locations(self):
        locations = []
        local_address = os.getenv("MY_POD_IP")
        if local_address:
            locations += "grpc://{}:{}".format(local_address, self.port)
        return locations

    '''
    Given a list of tickets and a list of locations,
    return a list of endpoints returned by get_flight_info.
    '''
    def _get_endpoints(self, tickets, locations):
        endpoints = []
        i = 0
        for ticket in tickets:
            if locations:
                endpoints.append(fl.FlightEndpoint(ticket.toJSON(), [locations[i]]))
                i = (i + 1) % len(locations)
            else:
                endpoints.append(fl.FlightEndpoint(ticket.toJSON(), []))
        return endpoints

    '''
    Serve arrow flight do_get requests
    '''
    def do_get(self, context, ticket: fl.Ticket):
        ticket_info: ABMTicket = ABMTicket.fromJSON(ticket.ticket)

        logger.info('retrieving dataset',
            extra={'ticket': ticket.ticket,
                   DataSetID: ticket_info.asset_name,
                   ForUser: True})

        with Config(self.config_path) as config:
            asset_conf = config.for_asset(ticket_info.asset_name)
        connector = GenericConnector(asset_conf, logger, self.workdir)
        # determine schema using the Airbyte 'discover' operation
        schema = connector.get_schema()
        # read dataset using the Airbyte 'read' operation
        batches = connector.get_dataset_batches(schema)

        # return dataset as arrow flight record batches
        return fl.GeneratorStream(schema, batches)

    '''
    Serve arrow-flight get_flight_info requests.
    Determine dataset schema.
    Return flight info with single ticket for entire dataset.
    '''
    def get_flight_info(self, context, descriptor):
        asset_name = json.loads(descriptor.command)['asset']
        logger.info('getting flight information',
            extra={'command': descriptor.command,
                   DataSetID: asset_name,
                   ForUser: True})

        with Config(self.config_path) as config:
            asset_conf = config.for_asset(asset_name)
            # given the asset configuration, let us determine the schema
            connector = GenericConnector(asset_conf, logger, self.workdir)
            schema = connector.get_schema()
        locations = self._get_locations()

        tickets = [ABMTicket(asset_name)]
        endpoints = self._get_endpoints(tickets, locations)
        return fl.FlightInfo(schema, descriptor, endpoints, -1, -1)

class ABMServer():
    def __init__(self, config_path: str, port: int, loglevel: str, workdir: str, *args, **kwargs):
        with Config(config_path) as config:
            init_logger(loglevel, config.app_uuid, 'airbyte-module')

        server = ABMHttpServer(("0.0.0.0", port), ABMHttpHandler,
                               config_path, workdir)
        server.serve_forever()
