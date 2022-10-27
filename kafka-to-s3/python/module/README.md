1. Running Kafka for testing:
   zookeeper-server-start /usr/local/etc/kafka/zookeeper.properties
   kafka-server-start /usr/local/etc/kafka/server.properties
2. Create a topic:
    kafka-topics --create --bootstrap-server localhost:9092 --topic sm
3. Add a record
    kafka-console-producer --broker-list localhost:9092 --topic sm
 > {"DOB": "01/02/1988", "FirstName": "John", "LastNAME": "Jones"}
4. Read a record:
   kafka-console-consumer --topic sm --from-beginning --bootstrap-server localhost:9092 
   