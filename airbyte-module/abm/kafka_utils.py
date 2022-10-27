#
# Copyright 2021 IBM Corp.
# SPDX-License-Identifier: Apache-2.0
#

import logging
import os
from kafka import KafkaProducer
from abm.jwt import decrypt_jwt
from datetime import datetime

logger = logging.getLogger(__name__)

KAFKA_SERVER = os.getenv("FOGPROTECT_KAFKA_SERVER") if os.getenv("FOGPROTECT_KAFKA_SERVER") else "172.31.35.158:9092"
KAFKA_DENY_TOPIC = os.getenv("KAFKA_DENY_TOPIC") if os.getenv("KAFKA_TOPIC") else "blocked-access"
KAFKA_ALLOW_TOPIC = os.getenv("KAFKA_ALLOW_TOPIC") if os.getenv("KAFKA_TOPIC") else "granted-access"

FIXED_SCHEMA_USER = 'email'
FIXED_SCHEMA_ROLE = 'realm_access.roles'
FIXED_SCHEMA_ORG = 'organization'

ACCESS_DENIED_CODE = 403
ERROR_CODE = 406
VALID_RETURN = 200

kafkaDisabled = False
kafkaAwaitingFirstConnect = True

# Set up Kafka connection

def connectKafka():
    global kafkaAwaitingFirstConnect
    global kafkaDisabled
    global producer
# Set up Kafka connection
    logging.info('Trying to connect initialize Kafka connection')
    if kafkaDisabled == False and kafkaAwaitingFirstConnect:
        try:
            producer = KafkaProducer(
                bootstrap_servers=[KAFKA_SERVER],
                request_timeout_ms=2000
            )  # , value_serializer=lambda x:json.dumps(x).encode('utf-8'))
        except Exception as e:
            logger.warning(f"Connection to Kafka failed.  Is the server on {KAFKA_SERVER} running?")
            logger.warning(f"{e}")
            kafkaDisabled = True
        kafkaAwaitingFirstConnect = False

def sendToKafka(jString, kafka_topic):
    global kafkaDisabled

    if kafkaAwaitingFirstConnect == True:
        connectKafka()
    if (kafkaDisabled):
        return
    jSONoutBytes = str.encode(jString)
    try:
        logging.info(f"Writing to Kafka queue: {kafka_topic}: {jString}")
        producer.send(kafka_topic, value=jSONoutBytes)  # to the SIEM
    except Exception as e:
        logger.warning(f"Write to Kafka failed.  Is the server on {KAFKA_SERVER} running?")
        logger.warning(f"{e}")
        kafkaDisabled = True

def logToKafka(request, action, policy, url):
    payloadEncrypted = request.headers.get('Authorization')
    if (payloadEncrypted != None):
        noJWT = False
        userKey = os.getenv("SCHEMA_USER") if os.getenv("SCHEMA_USER") else FIXED_SCHEMA_USER
        roleKey = os.getenv("SCHEMA_ROLE") if os.getenv("SCHEMA_ROLE") else FIXED_SCHEMA_ROLE
        try:
            user = str(decrypt_jwt(payloadEncrypted, userKey))
        except:
            user = 'No user defined'
        role = str(decrypt_jwt(payloadEncrypted, roleKey))
        organizationKey = os.getenv("SCHEMA_ORG") if os.getenv("SCHEMA_ORG") else FIXED_SCHEMA_ORG
        try:
            organization = str(decrypt_jwt(payloadEncrypted, organizationKey))
        except:
            logger.error("No organization in JWT! key = " + organizationKey)
            organization = "ERROR"
    if (noJWT):
        role = request.headers.get('role')  # testing only
        try:
            user = request.headers.get('user')
        except:
            user = 'No user defined'
    timeOut = datetime.timestamp(datetime.now())
    if (role == 'Missing value'):
        role = "['ERROR NO ROLE!']"
    # role *should* be a string representation of an array, and therefore should not be surrounded by "
    jString = "{\"user\": \"" + user + "\"," + \
              "\"role\": " + role + "," + \
              "\"org\": \"" + organization + "\"," + \
              "\"URL\": \"" + url + "\"," + \
              "\"Reason\": \"" + policy + "\"," + \
              "\"Timestamp\": \"" + str(timeOut) + "\"}"
    jStringFormatted = jString.replace("'", "\"")
    logging.info('logging to Kafka: ' + jString)
    if action == "BlockURL":
        sendToKafka(jStringFormatted, KAFKA_DENY_TOPIC)
        return ("Access denied!", ACCESS_DENIED_CODE)
    else:
        sendToKafka(jStringFormatted, KAFKA_ALLOW_TOPIC)