from kafka import KafkaProducer
from kafka.errors import KafkaError
from random import seed
from random import randint
from json import dumps
from datetime import datetime
import time

SLEEPTIME = 30  # seconds
NUM_WRITES = 30

TEST = False
if TEST:
    KAFKA_HOST = 'localhost:9092'
else:
    KAFKA_HOST = 'kafka.fybrik-system:9092'
#    KAFKA_HOST = '192.168.1.242:9092'
KAFKA_TOPIC = 'manufacturing-events'

FNAMES = ['Jim', 'John', 'Joan', 'Jack']
LNAMES = ['Smith', 'Jones', 'Parker', 'Henderson']

seed(1)
randFname = randint(0, len(FNAMES) -1 )
randLname = randint(0, len(LNAMES) - 1)


print("about to connect to " + KAFKA_HOST + ' writing to topic ' + KAFKA_TOPIC)
try:
    producer = KafkaProducer(bootstrap_servers=[KAFKA_HOST],
                             value_serializer=lambda x:
                             dumps(x).encode('utf-8'))
except Exception as e:
    print('Connecting to Kafka failed!')
    print(e)
for i in range(NUM_WRITES):
    outString = '''
    {
        "zone": {
            "secure": {
                "total_people": 1,
                "with_helmet": 0,
                "without_helmet": 1
            },
            "not_secure": {
                "total_people": 1,
                "with_helmet": 0,
                "without_helmet": 1
            },
            "full_container": {
                "total_people": 2,
                "with_helmet": 0,
                "without_helmet": 2
            }
        },
        ''' + '"timestamp" : "' + str(datetime.now()) + '", ' + \
                '\n\t"production_secure": false ' + \
        "\n}"

    try:
        future = producer.send(KAFKA_TOPIC, value=outString)
        producer.flush()
    except Exception as e:
        print("Error sending "+outString+" to Kafka")
        print(e)
    # Wait for send to complete
    try:
        record_metadata = future.get(timeout=10)
    except KafkaError:
        print('Error on completing of Kafka write')
        exit(0)
    # Wait before next loop iteration
    time.sleep(SLEEPTIME)
    print(outString + ' sent to Kafka topic ' + KAFKA_TOPIC + ' at ' + KAFKA_HOST)
exit(0)