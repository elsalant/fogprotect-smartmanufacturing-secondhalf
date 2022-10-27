#
# Copyright 2021 IBM Corp.
# SPDX-License-Identifier: Apache-2.0
#
import os

class OPAConfig:
    # the port on which the OPA server listens
    port = 8181

    # the address of the OPA server
  #  address = 'localhost'
    address = 'opa.fybrik-system'

    # the endpoint to send to in order to get the list of filters from the OPA server
    policy_endpoint = '/v1/data/dataapi/authz'

    # the enpoint to send to in order to update the policy in the OPA server.
    set_policy_endpoint = '/v1/policies/localEval'

    # the namespace in the cluster in which the assets reside.
    asset_namespace = 'default'

    # the path for the configmap file created by the fybrik-manager
    configmap_path = '/etc/conf/conf.yaml'


class FilterAction:
    BLOCK_URL = 'BlockURL'
    REDACT_COLUMN = 'RedactColumn'
    BLOCK_COLUMN = 'BlockColumn'
    FILTER = 'Filter'
    ALLOW = 'Allow'
    DENY = 'Deny'


class ResponseCode:
    ACCESS_DENIED_CODE = 403
    ERROR_CODE = 406
    VALID_RETURN = 200
