#
# Copyright 2022 IBM Corp.
# SPDX-License-Identifier: Apache-2.0
#
import yaml
from kubernetes import config, client
import base64
from fybrik_python_logging import init_logger, logger, DataSetID, ForUser

class Config:
    def __init__(self, config_path):
        self.logger = logger
        with open(config_path, 'r') as stream:
            self.values = yaml.safe_load(stream)

# If there is a Secret resource, decode and return each element in the secret asset as dictionary entry
    def decodeSecret(self,secretName, secretNamespace, logger) -> dict:
        try:
            config.load_incluster_config()  # in cluster
        except:
            config.load_kube_config()  # useful for testing outside of k8s
        v1 = client.CoreV1Api()
        secret = v1.read_namespaced_secret(secretName, secretNamespace)
        for k in secret.data: secret.data[k] = base64.b64decode(secret.data[k])
        return(secret.data)

    # return configuration for specific asset
    def for_asset(self, asset_name: str) -> dict:
 # For now, assume that the all secrets are in a Secrets resource specified by the key, SECRETS in the configmap.
 # Copy the contents of the Secrets resource into values, and then delete SECRETS from values
        for asset_info in self.values.get('data', []):
            if asset_name in asset_info['name']:
                asset_info.keys()
                try:
                    if 'secretPath' in asset_info['vault']['read']:
                        parseStr = asset_info['vault']['read']['secretPath']
 # secretPath is of the format: /v1/kubernetes-secrets/<secret name>?namespace=fybrik-airbyte-sample
                        secretNamespace = parseStr.split('=')[1]
                        secretName = (parseStr.split('?')[0]).split('/')[-1]
                        secretDict = self.decodeSecret(secretName, secretNamespace, logger)
                        for value, key in enumerate(secretDict):
                            secretDict[key] = secretDict[key].decode('ascii')
                        connection_name = asset_info['connection']['name']
                        logger.debug('connection name = '+ connection_name)
                        asset_info['connection'][connection_name]['provider'].update(secretDict)
                    return asset_info
                except Exception as e:
                    raise ValueError('for_asset: error decoding secret ' + str(e))
        raise ValueError(
            "Requested config for undefined asset: {}".format(asset_name))

    @property
    def app_uuid(self) -> str:
        return self.values.get('app-uuid', '')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
