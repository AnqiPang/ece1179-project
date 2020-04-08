import boto3

# generate a presigned URL to share an S3 object
def s3_create_presigned_url(bucket, key, expiration_sec=43200):
    s3_client = boto3.client('s3')
    response = s3_client.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': key}, ExpiresIn=expiration_sec)
    return response
