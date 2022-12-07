import pandas as pd
from minio import Minio
def main():
    minioClient = Minio('192.168.1.248:9000',
                     access_key='minioadmin',
                     secret_key='minioadmin',
                     secure=False)
    objects = minioClient.list_objects('smartmanufacturing-unsafe-bucket', recursive=True)
    try:
        for obj in objects:
            print(obj.object_name)
        fname = input('Input file to be read: ')
        minioClient.fget_object(obj.bucket_name,  fname, 'newfile.parquet')
        df = pd.read_parquet('newfile.parquet', engine='pyarrow')
        print(df.to_string())
    except:
        print('No objects found in smartmanufacturing-unsafe-bucket')
if __name__ == "__main__":
    main()