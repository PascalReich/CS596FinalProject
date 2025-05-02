import json
import boto3
from decimal import Decimal

client = boto3.client('dynamodb')
dynamodb = boto3.resource("dynamodb")
tableName = 'WeatherData'
table = dynamodb.Table(tableName)
apikey = "13acbb2f96a949e397a22822252503"

url = "http://api.weatherapi.com/v1/forecast.json?key=13acbb2f96a949e397a22822252503&q=92115"

import urllib.request


def lambda_handler(event, context):
    # TODO implement

    res = urllib.request.urlopen(urllib.request.Request(
        url=url,
        headers={'Accept': 'application/json'},
        method='GET'),
    timeout=5)

    response = json.loads(res.read())

    # print("Got Response")


    for day in response['forecast']['forecastday']:
        for hour in day['hour']:
            table.put_item(
                Item={
                    'City': response['location']['name'],
                    'Datetime': hour['time'],
                    'Temperature': Decimal(str(hour['temp_f'])),
                    'FeelsLike': Decimal(str(hour['feelslike_f'])),
                    'Humidity': Decimal(str(hour['humidity'])),
                    'Weather': hour['condition']['text'],
                    'Type': 'forecasted'
                }
            )
            #print(f"Saved {hour['time']}")


    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
