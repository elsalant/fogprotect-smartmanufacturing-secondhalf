import boto3
import uuid
import tempfile
#import pyarrow as pa
#import pyarrow.parquet as pq
import pandas as pd
import json
import logging

BUCKET_PREFIX = '-fogprotect-'
PARQUET_SUFFIX = '.parquet'
CSV_SUFFIX = '.csv'
SEED = 'sm' # for file name

PARQUET=True

class S3utils:

    def __init__(self, s3_access_key,s3_secret_key, s3_URL):
        self.logger = logging.getLogger(__name__)
        self.connection = boto3.resource(
            's3',
            aws_access_key_id=s3_access_key,
            aws_secret_access_key=s3_secret_key,
            endpoint_url=s3_URL,
        )
        self.logger.info('Connection object set up with aws_access_key = ' + s3_access_key +
                         ' s3_secret_key = ' + s3_secret_key + ' endpoint_url = ' + s3_URL)

    def contentToFile(self, content):
        random_file_name = ''.join([str(uuid.uuid4().hex[:6]), SEED])
        if PARQUET:
            suffix = PARQUET_SUFFIX
        else:
            suffix = CSV_SUFFIX
        try:
            tempFile = tempfile.NamedTemporaryFile(prefix=random_file_name, suffix=suffix, mode='w+t')
            #dump the whole input into a string, and then put into a dataframe with a single entry

            content1 = json.dumps([content])
            df = pd.read_json(content1)
            if PARQUET:
                df.columns = df.columns.astype(str)
                df.to_parquet(tempFile.name)
                print(df)
            else:
                df.to_csv(tempFile.name)
  #              tempFile.write(content)
  #              tempFile.seek(0)
        except Exception as e:
            tempFile.close()
            print("exception writing to tmpfile")
            print('content1 = ' + content1)
            print(e)
            return('ERROR')
        logging.info('information written to tmpfile' + str(tempFile.name))
        return tempFile

    def write_to_S3(self, bucketName, data):
        matchingBucket = self.get_resource_buckets(bucketName)
        if len(matchingBucket) > 1:
            raise AssertionError('Too many matching buckets found! ' + len(matchingBucket) + ' ' + str(matchingBucket))
        elif len(matchingBucket) == 1:
            bucketName = matchingBucket[0]
            self.logger.info(f'matching bucket found: ' + bucketName)
        else:
            self.logger.info(f"new bucket being created:" + bucketName)
            bucketName, response = self.create_bucket(bucketName, self.connection)
        # Generate a random prefix to the resource type
        fName = ''.join([str(uuid.uuid4().hex[:6]), SEED])
        tempFile = self.contentToFile(data)
        if tempFile == 'ERROR':
            self.logger.info('No file being written out - bad input')
            return None
        self.write_to_bucket(bucketName, tempFile, fName)
        logStr = 'information written to bucket ' + bucketName + ' as ' + fName
        self.logger.info(logStr)
        return None

    def write_to_bucket(self, bucketName, tempFile, fnameSeed):
        try:
            if PARQUET:
                objectName = fnameSeed+PARQUET_SUFFIX
            else:
                objectName=fnameSeed+CSV_SUFFIX
            bucketObject = self.connection.Object(bucket_name=bucketName, key=objectName)
            self.logger.info(f"about to write to S3: bucketName = " + bucketName + " fnameSeed = " + objectName)
            bucketObject.upload_file(tempFile.name)
        finally:
            tempFile.close()
        return None

    def create_bucket(self, bucket_name, s3_connection):
        session = boto3.session.Session()
        current_region = session.region_name
        if current_region == None:
            current_region = ''
            self.logger.info('Creating bucket with bucket_name = ' + bucket_name +
                             'current_region = ' + current_region)
        bucket_response = s3_connection.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={
            'LocationConstraint': current_region})
        return bucket_name, bucket_response

    def get_resource_buckets(self, searchPrefix):
        # Get a bucket with a name that contains the passed prefix
        try:
            bucketCollection = self.connection.buckets.all()
        except:
            self.logger.WARN('connection.buckets.all() fails!')
        bucketList = []
        try:
            for bucket in bucketCollection:
                bucketList.append(str(bucket.name))
        except:
            self.logger.error('bucketCollection fails!')
        matchingBuckets = [s for s in bucketList if searchPrefix == s]
        if (matchingBuckets):
            self.logger.info("matchingBuckets = " + str(matchingBuckets))
        return matchingBuckets