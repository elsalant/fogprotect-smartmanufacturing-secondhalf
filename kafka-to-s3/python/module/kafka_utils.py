import logging
import os
import json
from json import loads
import boto3
from kafka import KafkaProducer
from kafka import KafkaConsumer

TEST = False
DEFAULT_KAFKA_LOG_TOPIC = 'sm'
if TEST:
    DEFAULT_KAFKA_HOST = 'localhost:9092'
else:
    DEFAULT_KAFKA_HOST = 'kafka.fybrik-system:9092'

logger = logging.getLogger(__name__)
#kafkaHost = os.getenv("FOGPROTECT_kafkaHost") if os.getenv("FOGPROTECT_kafkaHost") else DEFAULT_KAFKA_HOST
#kafkaLogTopic = os.getenv("SM_kafkaLogTopic") if os.getenv("SM_kafkaLogTopic") \
#    else DEFAULT_KAFKA_LOG_TOPIC
kafkaDisabled = True
consumer = None

def createKafkaConsumer(kafkaMsgTopic, kafkaHost):
    try:
        consumer = KafkaConsumer(
            kafkaMsgTopic,
            bootstrap_servers=[kafkaHost],
            group_id='els',
            auto_offset_reset='earliest',  #latest
            enable_auto_commit=True,
            value_deserializer=lambda x: loads(x.decode('utf-8')))
    except:
        raise Exception("Kafka did not connect for host " + kafkaHost + " and  topic " + kafkaMsgTopic)

    logger.info(f"-- > Connection to kafka consumer at host " + kafkaHost + " and  topic " + kafkaMsgTopic + " succeeded!")
    return consumer

def connect_to_kafka_producer(kafkaHost):
    global producer, kafkaDisabled
    try:
        producer = KafkaProducer(
            bootstrap_servers=[kafkaHost]
        )  # , value_serializer=lambda x:json.dumps(x).encode('utf-8'))
    except Exception as e:
        logger.warning(f"\n--->WARNING: Connection to Kafka failed.  Is the server on " + kafkaHost + " running?")
        logger.warning(e)
        kafkaDisabled = True
        return None
    kafkaDisabled = False
    logger.info(f"Connection to Kafka succeeded! " + kafkaHost)
    return(producer)

def writeToKafka(jString, kafkaLogTopic):
    if kafkaDisabled:
        logger.info(f"Kafka topic: " + kafkaLogTopic + " log string: " + jString)
        logger.warning(f"But kafka is disabled...")
        return None
    jSONoutBytes = str.encode(jString)
    try:
        logger.info(f"Writing to Kafka queue " + kafkaLogTopic + ": " + jString)
        producer.send(kafkaLogTopic, value=jSONoutBytes)  # to the SIEM
    except Exception as e:
        logger.warning(f"Write to Kafka logging failed.  Is the server on " + kafkaLogTopic + " running?")
        logger.info(e)
    return None