1. To populate minio, go to ~/fogprotect-kafka-to-s3 and follow the directions
in the README (start the minioserver, kubectl apply -f kafka_producer.yaml)
2. Apply the yaml files:
 In the sample directly, apply:
  s3_read_secret.yaml
  s3_minio_read_asset.yaml
3. Apply the read policies:
/home/salant/airbyte-module/sample/curlUpdateOPApolicy.sh
4. Note that the write policies are inside the module 
Will always write to the quarantined bucket if the situationstatus is anything other than "safe"
(See /home/salant/fogprotect-kafka-to-s3/python/kafkaToS3.py)
5. Start the module from the toplevel, airbyte-module directory by:
kubectl apply -f module.yaml
from fybrik directory:
kubectl apply -f application.yaml
6. To read the data:
 Make sure the minio server is running in a docker container:
docker ps | grep minio
If not:
~/fogprotect-kafka-to-s3/scripts/runMinioContainer.sh
7. To populate Kafka with events (topic: manufacturing-events):
 In /home/salant/fogprotect-kafka-to-s3/yaml:
kubectl apply -f kafka_producer.yaml

Note that this will create in the default namespace a pod (kafka-producer-job-XXX) which completes and will need to be removed.
Sample data generated:
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
        "timestamp" : "2022-10-26 13:17:49.628759", 
        "production_secure": false 
} 

6. To read data from the Parquet files in minio:
a) Files located in /tmp/minio/data 
 .sample/runPortForward.sh
 ~/airbyte-module/sample$ ./runCurlJWT_k8s.sh
7. Policy for read is defined in:
/home/salant/airbyte-module/fybrik/smartmanufacturing-policy.rego
To apply the policies:
/home/salant/airbyte-module/sample/curlUpdateOPApolicy.sh
8. To set the situationstatus variable:
kubectl apply -f /home/salant/airbyte-module/fybrik/levelX-situation.yaml   (where X = [0,1,2])

