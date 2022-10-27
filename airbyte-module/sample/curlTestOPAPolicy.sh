curl localhost:8181/v1/data/dataapi/authz -d '{"input": {"situationStatus": "unsafe-high","request": {"operation": "READ","role": "['Admin']", 
"asset": {"namespace": "fybrik-system","name": ".myendpt"}}}}'

