from kubernetes import client, config
import yaml
import base64
import logging
import os
import time

from module.s3_utils import S3utils
from module.kafka_utils import createKafkaConsumer
from module.policyUtils import PolicyUtils

FLASK_PORT_NUM = 5559  # this application

ACCESS_DENIED_CODE = 403
ERROR_CODE = 406
VALID_RETURN = 200

TEST = False   # allows testing outside of Fybrik/Kubernetes environment
TESTING_SITUATION_STATUS = 'safe'

FIXED_SCHEMA_ROLE = 'missing role'
FIXED_SCHEMA_ORG  = 'missing org'

CM_SITUATION_PATH = '/etc/confmap/situationstatus.yaml'

logger = logging.getLogger(__name__)
cmDict = {}

def getSecretKeys(secret_name, secret_namespace):
    try:
        config.load_incluster_config()  # in cluster
    except:
        config.load_kube_config()   # useful for testing outside of k8s
    v1 = client.CoreV1Api()
    logger.info('secret_name = ' + secret_name + ' secret_namespace = ' + secret_namespace)
    secret = v1.read_namespaced_secret(secret_name, secret_namespace)
    accessKeyID = base64.b64decode(secret.data['access_key'])
    secretAccessKey = base64.b64decode(secret.data['secret_key'])
    return(accessKeyID.decode('ascii'), secretAccessKey.decode('ascii'))

def readConfig(CM_PATH):
    if not TEST:
        try:
            with open(CM_PATH, 'r') as stream:
                cmReturn = yaml.safe_load(stream)
        except Exception as e:
            raise ValueError('Error reading from file! ' + CM_PATH)
    else:
        cmDict = {'MSG_TOPIC': 'sm', 'KAFKA_HOST': 'kafka.fybrik-system:9092', 'VAULT_SECRET_PATH': None,
                  'SECRET_NSPACE': 'fybrik-system', 'SECRET_FNAME': 'credentials-els',
                  'S3_URL': 'http://s3.eu.cloud-object-storage.appdomain.cloud', 'SUBMITTER': 'EliotSalant',
                  'SAFE_BUCKET':'safe-bucket', 'UNSAFE_BUCKET':'unsafe-bucket'}
        return(cmDict)
    cmDict = cmReturn.get('data', [])
    logger.info(f'cmReturn = ', cmReturn)
    return(cmDict)

def main():
    global cmDict
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info(f"starting module!!")

    CM_PATH = '/etc/conf/conf.yaml' # from the "volumeMounts" parameter in templates/deployment.yaml
    cmDict = readConfig(CM_PATH)

    # Get the connection details for S3 connection and then fire up the S3 object
    try:
        secret_namespace = cmDict['SECRET_NSPACE']
        secret_fname = cmDict['SECRET_FNAME']
        safeBucketName = cmDict['SAFE_BUCKET']
        unsafeBucketName = cmDict['UNSAFE_BUCKET']
        manufacturing_topic = cmDict['MANUFACTURING_DATA_TOPIC']
        logging_topic = cmDict['LOG_TOPIC']
        kafka_host = cmDict['KAFKA_HOST']
        logger.info('secret_namespace = ' + str(secret_namespace) + ' secret_fname = ' + str(secret_fname) +
                ' safeBucketName = ' + str(safeBucketName) + ' unsafeBucketName = ' + str(unsafeBucketName))
        s3_URL = cmDict['S3_URL']
        logger.info('s3_URL = '+ str(s3_URL))
    except:
        logger.info('Error reading from ' + CM_PATH)
        print('--- CM_PATH contents')
        f = open(CM_PATH, 'r')
        content = f.read()
        print(content)
        f.close()
    keyId, secretKey = getSecretKeys(secret_fname, secret_namespace)
    s3Utils = S3utils(keyId, secretKey, s3_URL)
    consumer = createKafkaConsumer(manufacturing_topic, kafka_host)
    policyUtils = PolicyUtils()

# Listen on the Kafka manufacturing queue for ever. When a message comes in, determine the "Status" env and write to S3 bucket accordingly
    #while True:
    #    message_batch = kafkaUtils.consumer.poll()  # Ref: https://www.thebookofjoel.com/python-kafka-consumers
    #    kafkaUtils.consumer.commit()
    #    for topic_partition, partition_batch in message_batch.items():
    #        for message in partition_batch:
    for message in consumer:
        messageDict = message.value
        logger.info('Read from Kafka: ')
        filteredData = policyUtils.apply_policy(messageDict)
# The external variable, SITUATION_STATUS, is created from a config map and can be externally changed.
# The value of this env determines to which bucket to write
        situationStatus = getSituationStatus()
        if TEST:
            situationStatus = 'safe'
        assert(situationStatus)
        if situationStatus.lower() == 'safe' or situationStatus == 'level0':
            bucketName = safeBucketName
        else:
            bucketName = unsafeBucketName

        # Convert filterData to a dataframe in order to export as Parquet
        s3Utils.write_to_S3(bucketName, messageDict)
    logging.info('--> finished reading from Kafka')

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
if __name__ == "__main__":
    main()