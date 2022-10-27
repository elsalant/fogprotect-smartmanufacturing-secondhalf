kubectl -n fybrik-system create configmap kafka-s3-policy --from-file=../misc/policy.rego
kubectl -n fybrik-system label configmap kafka-s3-policy openpolicyagent.org/policy=rego
while [[ $(kubectl get cm kafka-s3-policy -n fybrik-system -o 'jsonpath={.metadata.annotations.openpolicyagent\.org/policy-status}') != '{"status":"ok"}' 
]]; do echo "waiting for policy to be applied" && sleep 5; done
