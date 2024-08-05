import boto3
import os

def compare_faces(source_image, target_image, similarity_threshold):
    rekognition = boto3.client('rekognition')

    response = rekognition.compare_faces(
        SourceImage={
            'S3Object': {
                'Bucket': os.environ['BUCKET_NAME'],
                'Name': source_image
            }
        },
        TargetImage={
            'S3Object': {
                'Bucket': os.environ['BUCKET_NAME'],
                'Name': target_image
            }
        },
        SimilarityThreshold=similarity_threshold
    )

    return response

def process_images():
    s3_client = boto3.client('s3')
    sns_client = boto3.client('sns')

    bucket = os.environ['BUCKET_NAME']
    sns_topic_arn = os.environ['SNS_TOPIC_ARN']

    try:
        response = s3_client.list_objects_v2(Bucket=bucket)

        if 'Contents' in response:
            keys = [obj['Key'] for obj in response['Contents']]

            similarity_threshold = 20  # Adjust the threshold value as needed

            for i in range(len(keys)):
                for j in range(i+1, len(keys)):
                    source_image = keys[i]
                    target_image = keys[j]

                    print(f"Comparison result between {source_image} and {target_image}:")
                    response = compare_faces(source_image, target_image, similarity_threshold)

                    if response['FaceMatches']:
                        for match in response['FaceMatches']:
                            similarity = match['Similarity']
                            confidence = match['Face']['Confidence']
                            message = f"Similarity: {similarity}%, Confidence: {confidence}% of Source Image {source_image}"
                            print(message)
                            sns_client.publish(
                                TopicArn=sns_topic_arn,
                                Message=message
                            )
                    else:
                        print("No face match found.")
        else:
            print("The S3 bucket is empty.")

    except Exception as e:
        print(f"Error: {str(e)}")

def lambda_handler(event, context):
    process_images()