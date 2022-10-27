1. Get the specs for the config file for the desired connector:
   e.g. docker run --rm -i airbyte/destination-s3 spec
2. Create the config file, and then check e.g.:
   docker run -v /Users/eliot/temp:/local --rm -i airbyte/destination-s3 check --config /local/s3_write_config.yaml
