import json
import boto3
from decimal import Decimal
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

client = boto3.client('dynamodb')
dynamodb = boto3.resource("dynamodb")
tableName = 'WeatherData'
table = dynamodb.Table(tableName)

# Replace sender@example.com with your "From" address.
# This address must be verified with Amazon SES.
SENDER = "Notification Service <notif@mail.pascalreich.com>"

# Replace recipient@example.com with a "To" address. If your account 
# is still in the sandbox, this address must be verified.
RECIPIENTS = ["preich5404@sdsu.edu", "jeppinette3211@sdsu.edu"]

# If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
AWS_REGION = "us-west-2"

# The character encoding for the email.
CHARSET = "UTF-8"


def lambda_handler(event, context):

    try:
        data = event #json.loads(event['body'])
        data['temperature'] # check if data exists
        data['humidity']
        data['insideTemp']
        data['insideHumidity']
    except:
        return {
            'statusCode': 400,
            'body': json.dumps('Invalid Request!')
        }
    
    current_time = datetime.now() - timedelta(hours=7)
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M")

    table.put_item(
                Item={
                    'Datetime': formatted_time,
                    'Temperature': Decimal(data['temperature']),
                    'FeelsLike': Decimal(data['temperature']),
                    'Humidity': Decimal(data['humidity']),
                    'Inside Temperature': Decimal(data['insideTemp']),
                    'Inside Humidity': Decimal(data['insideHumidity']),
                    'Type': 'measured'
                }
            )

    # Create a new SES resource and specify a region.
    SESclient = boto3.client('ses',region_name=AWS_REGION)

    if float(data['temperature']) > 85:
        
        # The subject line for the email.
        SUBJECT = "High Temperature Alert"

        # The email body for recipients with non-HTML email clients.
        BODY_TEXT = (f"The temperature has been measured at {data['temperature']} degrees fahrenheit. "
                     "Take appropriate action. \r\n\n\n"
                     "This email was sent with Amazon SES using the "
                     "AWS SDK for Python (Boto)."
                    )
                    
                

        # Try to send the email.
        try:
            #Provide the contents of the email.
            response = SESclient.send_email(
                Destination={
                    'ToAddresses': RECIPIENTS
                },
                Message={
                    'Body': {
                        'Text': {
                            'Charset': CHARSET,
                            'Data': BODY_TEXT,
                        },
                    },
                    'Subject': {
                        'Charset': CHARSET,
                        'Data': SUBJECT,
                    },
                },
                Source=SENDER,
                # If you are not using a configuration set, comment or delete the
                # following line
                # ConfigurationSetName=CONFIGURATION_SET,
            )
        # Display an error if something goes wrong.	
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            print("Email sent! Message ID:"),
            print(response['MessageId'])

    elif float(data['temperature']) - float(data['insideTemp']) > 20:

        # The subject line for the email.
        SUBJECT = "Temperature Differential Alert"

        # The email body for recipients with non-HTML email clients.
        BODY_TEXT = (f"The temperature has been measured at {data['temperature']} degrees fahrenheit outside, but only at {data['insideTemp']} degrees inside. "
                     "Take appropriate action. \r\n\n\n"
                     "This email was sent with Amazon SES using the "
                     "AWS SDK for Python (Boto)."
                    )


        # Try to send the email.
        try:
            #Provide the contents of the email.
            response = SESclient.send_email(
                Destination={
                    'ToAddresses': RECIPIENTS
                },
                Message={
                    'Body': {
                        'Text': {
                            'Charset': CHARSET,
                            'Data': BODY_TEXT,
                        },
                    },
                    'Subject': {
                        'Charset': CHARSET,
                        'Data': SUBJECT,
                    },
                },
                Source=SENDER,
                # If you are not using a configuration set, comment or delete the
                # following line
                # ConfigurationSetName=CONFIGURATION_SET,
            )
        # Display an error if something goes wrong.
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            print("Email sent! Message ID:"),
            print(response['MessageId'])


    return {
        'statusCode': 200,
        'body': json.dumps('Successfully Uploaded!')
    }
