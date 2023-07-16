import os
import boto3
import email
import imaplib

region = os.environ['Region']

def get_message_from_s3(message_id):
    incoming_email_bucket = os.environ['MailS3Bucket']
    incoming_email_prefix = os.environ['MailS3Prefix']
    if incoming_email_prefix:
        object_path = (incoming_email_prefix + "/" + message_id)
    else:
        object_path = message_id

    object_http_path = (f"http://s3.console.aws.amazon.com/s3/object/{incoming_email_bucket}/{object_path}?region={region}")

    # Create a new S3 client.
    client_s3 = boto3.client("s3")

    # Get the email object from the S3 bucket.
    object_s3 = client_s3.get_object(Bucket=incoming_email_bucket,
        Key=object_path)
    
    # Read the content of the message.
    file = object_s3['Body'].read()

    file_dict = {
        "file": file,
        "path": object_http_path
    }

    return file_dict


def upload_email(file_dict):
    email_address = os.environ['GmailAddress']
    password = os.environ['GmailPassword']

    gmail = imaplib.IMAP4_SSL("imap.gmail.com")
    gmail.login(email_address, password)

    mailobject = email.message_from_bytes(file_dict['file'])

    date = email.utils.parsedate_to_datetime(mailobject.get("Date"))
    mail_time = imaplib.Time2Internaldate(date)
    gmail.append("INBOX", "", mail_time, file_dict['file'])


def lambda_handler(event, context):
    # Get the unique ID of the message. This corresponds to the name of the file
    # in S3.
    message_id = event['Records'][0]['ses']['mail']['messageId']
    print(f"Received message ID {message_id}")

    file_dict = get_message_from_s3(message_id)
    upload_email(file_dict)