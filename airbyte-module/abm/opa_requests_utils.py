#
# Copyright 2021 IBM Corp.
# SPDX-License-Identifier: Apache-2.0
#
import requests
import logging
import json
import yaml
import urllib.parse as urlparse
from .OPAConfig import *

logger = logging.getLogger(__name__)

# get the runtime evaluation of the OPA policies based on role, and the asset (extracted from passed_url)
def opa_get_actions(role, situationStatus, passed_url):
    opaEndpt = OPAConfig.policy_endpoint
    # The assumption is that the if there are query parameters (query_string), then this is prefixed by a "?"
    parsed_url = urlparse.urlparse(passed_url)
    asset = parsed_url[1] + parsed_url[2]

    # If we have passed parameters, asset will end in a '/' which needs to be stripped off
    asset.strip('/')
    logger.debug(f"stripped asset: {asset}")
    asset_name = asset.replace('/', '.').replace('_', '-')

    # TODO: role is being put into the header as a string - it should go in as a list for Rego.  What we are doing
    #  now requires the Rego to do a substring search, rather than search in a list
    opa_query_body = get_opa_query_body(asset_name, role, situationStatus)
    logger.info('opa_query_body = ' + opa_query_body)
    opa_url = get_opa_url()
    url_string = opa_url + opaEndpt
    header = {"Content-Type": "application/json"}
    logger.debug(f"url_string: {url_string} asset_name: {asset_name} opa_query_body: {opa_query_body}")

    try:
        response = requests.post(url_string, data=opa_query_body, headers=header)
    except:
        logger.error(f"could not connect to OPA for url: {url_string} data: {opa_query_body}")
        raise
    try:
        return_string = response.json()
    except Exception as e:
        logger.error(f"could not convert response to JSON for url: {url_string} data: {opa_query_body}")
        raise

    logger.debug(f"return_string: {str(return_string)}")

    return return_string


# Example code to create Rego policy reconstructing returned information from the Policy Manager
# The information from the Policy Manager will go into a configmap.  The Helm chart for this program
# must mount the configmap in order to be able to read from it.  Converts the information in the configmap into Rego.
# The created Rego is finally loaded into OPA as a policy update
def _build_rego_rules(action_list):
    # We can assume that in this case, all evaluation needs to be done at runtime,
    # and hence the columns field returned to the module is empty.
    rule_out = ''
    for i_dict in action_list:
        if i_dict['action']['columns'] != '""':
            cols = ',"columns":' + i_dict['action']['columns']
        else:
            cols = ''
        if i_dict['action']['name'] == 'FilterPred':
            rego_statement = ',"regoStatement": "q=data.' + get_partial_policy_package() + '.' + get_partial_policy_name() + '==\'true\', input=' + str(
                i_dict['action']['partial_eval']['inputs']) \
                            + ', unknowns=' + str(i_dict['action']['partial_eval']['unknowns']) + '"'
            rule_name = 'rule'
        else:
            rego_statement = ''
            rule_name = "rule"
        rule_out += rule_name + '[{"name":"' + i_dict['policy'] + '", "action":"' + i_dict['action'][
            'name'] + '"' + cols + rego_statement + '}] { \n\t' \
                    + "\n\t".join(i_dict['action']['runtime_eval']) \
                    + "\n}\n\n"

    return rule_out


def configmap_to_policy():
    logger.info(f"reading policy from file in path: {OPAConfig.configmap_path}")

    with open(OPAConfig.configmap_path, 'r') as stream:
        configmap_return = yaml.safe_load(stream)
    policy = configmap_return['data']
    # Reconstruct the rule(s) in Rego
    rego_rules = _build_rego_rules(policy)

    policy_headers = get_policy_headers()
    policy_boilerplate = get_configmap_policy_boilerplate()
    rego_out = policy_headers + policy_boilerplate + rego_rules

    # Set the policies in OPA
    opa_url = get_opa_url()
    url_string = opa_url + OPAConfig.set_policy_endpoint
    header = {"Content-Type": "application/json"}

    logger.info(f"sending the policy to the OPA sidecar, to the URL: {url_string}")
    r = requests.put(url_string, data=rego_out, headers=header)
    if r.reason != 'OK':
        error_message = f"failed to send policy to the OPA sidecar. Reason: {r.reason}"
        logger.error(error_message)
        raise Exception(error_message)


def get_opa_url():
    return 'http://' + OPAConfig.address + ":" + str(OPAConfig.port)


def get_opa_query_body(asset_name, role, situationStatus):
    return '{ \"input\": { \
            \"situationStatus\": \"' + situationStatus + '\", \
            \"request\": { \
            \"operation\": \"READ\", \
            \"role\": \"' + str(role) + '\", \
            \"asset\": { \
            \"namespace\": \"' + OPAConfig.asset_namespace + '\", \
            \"name\": \"' + asset_name + '\" \
            }  \
            }  \
            }  \
            }'


def get_configmap_policy_boilerplate():
    return 'filters[output] {\n' \
           '\tcount(rule)==0\n' \
           '\toutput = {"name": "Deny by default", "action": "Deny"}\n' \
           '}\n\n' \
           'filters[output] {\n' \
           '\tcount(rule)>0\n' \
           '\toutput = rule[_]\n' \
           '}\n\n'


def get_policy_headers():
    return 'package ' + get_partial_policy_package() + '\n\n' + 'import data.kubernetes.assets\n\n'


def get_partial_policy_package():
    return 'katalog.example'


def get_partial_policy_name():
    return 'partialPolicy'
