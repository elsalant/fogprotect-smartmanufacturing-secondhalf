kubectl -n fybrik-system create configmap smartmanufacturing-policy --from-file=$AIRBYTE_MODULE_DIR/fybrik/smartmanufacturing-policy.rego
kubectl -n fybrik-system label configmap smartmanufacturing-policy openpolicyagent.org/policy=rego
while [[ $(kubectl get cm smartmanufacturing-policy -n fybrik-system -o 'jsonpath={.metadata.annotations.openpolicyagent\.org/policy-status}') != '{"status":"ok"}' 
]]; do echo "waiting for policy to be applied" && sleep 5; done
