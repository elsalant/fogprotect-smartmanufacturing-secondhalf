docker run \
  -p 9000:9000 \
  -p 9001:9001 \
  --name minio1 \
  --rm \
   -e "MINIO_ROOT_USER=minioadmin" \
   -e "MINIO_ROOT_PASSWORD=minioadmin" \
   -v /tmp/minio/data:/data \
   -d \
   quay.io/minio/minio server /data --console-address ":9001"
