### This is an example of Fybrik read module that uses REST protocol to connect to a FHIR server to obtain medical records.  Policies redact the information returned by the FHIR server or can even restrict access to a given resource type.
# User authentication is enabled, as well as (optional) logging to Kafka

Do once:  make sure helm v3.7+ is installed
> helm version
> 
Setting up a kind cluster - if required:
> kind create cluster --name fogprotect-sm

1. Install fybrik from the instructions in: https://fybrik.io/v0.7/get-started/quickstart/
1. Start the Kafka server without persisting data:  
   - helm install kafka bitnami/kafka -n fybrik-system --set persistence.enabled=false  --set zookeeperConnectionTimeoutMs=60000
1. Create a namespace for the kafka-s3 demo:  
kubectl create namespace kafka-s3
1. Pull the files:
git pull https://github.com/elsalant/fogprotect-kafka-to-s3.git
1. Install the policy:  
\<ROOT>/scripts/applyPolicy.sh
1. Edit \<ROOT>/yaml/s3-credentials.yaml to input the correct S3 tokens
1. Apply the S3 secrets and permissions  
\<ROOT>/scripts/deployS3secrets.sh 
1. kubectl edit cm cluster-metadata -n fybrik-system
and change theshire to UK
1. kubectl apply -f https://raw.githubusercontent.com/datashim-io/datashim/master/release-tools/manifests/dlf.yaml
1. kubectl apply -f \<ROOT>/yaml/kafka_asset.yaml  
    kubectl apply -f \<ROOT>/yaml/s3_asset.yaml
1. Edit s3-account.yaml and configure the endpoint for your s3 store, then apply:
kubectl apply -f s3-account.yaml
1. Apply the module
kubectl apply -f \<ROOT>/yaml/kafkaToS3module.yaml  
1. Apply the application - note that the name (or JWT) for the requester is in the label.requestedBy field!  
kubectl apply -f \<ROOT>/yaml/kafakToS3application.yaml

### Test
- a) Send events to the Kafka queue  
kubectl apply -f kafka_producer.yaml 
- b) Change the situation status:
kubectl edit cm situationstatus -n fybrik-blueprints
and toggle the "situation-status" value.

#### Hints
To test redaction: pick a field in the resource (e.g. "id") and set the tag in the asset.yaml file to "PII".
Note that to redact a given field in a given resource, e.g. "id" in "Patient" sources, in the asset.yaml file, specify the componentsMetadata value as "Patient.id".

If either the asset or policy is changed, then the Fybrik application needs to be restarted:
kubectl delete -f <name of FybrikApplication file>  
kubectl apply -f <name of FybrikApplication file>
 
#### DEVELOPMENT

1. To build Docker image:  
cd /Users/eliot/projects/HEIR/code/kafka-to-s3  
make docker-build  

Push the image to Docker package repo  
make docker-push

1a. To build kafka-producer image:
 make docker-build-producer
 make docker-push-producer

2. Push the Helm chart to the repo
export HELM_EXPERIMENTAL_OCI=1  
helm registry login -u elsalant -p \<PASSWORD> ghcr.io

Package the chart: (cd charts)  
helm package kafka-to-s3 -d /tmp  
helm push /tmp/kafka-to-s3-chart-0.0.1.tgz oci://ghcr.io/elsalant

##### Development hints
1. files/conf.yaml controls the format of the policy evaluation.  This will be written into a file mounted inside the pod running in the fybrik-blueprints namespace.
2. templates/deployment.yaml defines the mount point (e.g. /etc/conf/conf.yaml) for this file.
3. Redaction values defined in values.yaml will be ignored.  This information will be supplied by the manager and connectors.
4. The FHIR server can be queried directly by:
 - kubectl port-forward svc/ibmfhir 9443:9443 -n fybrik-system  
 - curl -k -u 'fhiruser:change-password' 'https://127.0.0.1:9443/fhir-server/api/v4/Patient'
