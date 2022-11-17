package dataapi.authz

rule[{"name": "Block all reads for User if not at Level0", "action": "BlockResource"}]{
       lower(input.situationStatus) != lower("level0")
       lower(input.request.role) == lower("User")
       input.request.operation == "READ"
}

rule[{"name": "Block all reads to safe data for Admin if at level2", "action": "BlockResource"}]{
       lower(input.situationStatus) == lower("level2")
       lower(input.request.role) == lower("Admin")
       input.request.asset.name == ".s3-userdata"
       input.request.operation == "READ"
}

rule[{}] {
  1 == 1
}


