
import boto3

AWS_ACCESS_KEY= "cae190fe77674a6a9fa92863d6d4e814"
AWS_SECRET_KEY="88e2f522b47c4224859a21fc5595dacdcf0629b7bebbf0d9"
S3_BUCKET_NAME="smartmanufacturing-safe-bucket"
ENDPT_URL='http://s3.eu.cloud-object-storage.appdomain.cloud'

s3 = boto3.resource('s3', aws_access_key_id=AWS_ACCESS_KEY,aws_secret_access_key=AWS_SECRET_KEY, endpoint_url=ENDPT_URL)
bucket=s3.Bucket(S3_BUCKET_NAME)
bucket.objects.delete()