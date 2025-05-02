import json

import boto3
from datetime import datetime, timedelta


# --- Sorting Function ---
def sort_data_by_time(data):
    """
    Sorts data in-place based on the 'time' field.
    Assumes time strings are in 'YYYY-MM-DD HH:MM' format,
    which can be lexicographically sorted.
    """
    # Zip the lists together
    zipped_data = list(zip(data["time"], data["temperature"], data["humidity"]))
    # Sort by time (first element of each tuple)
    zipped_data.sort(key=lambda x: x[0])
    # Unzip back to individual lists
    if not zipped_data:
        return data
    data["time"], data["temperature"], data["humidity"] = map(list, zip(*zipped_data))
    return data

def lambda_handler(event, context):

    dynamodb = boto3.client("dynamodb")

    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M")

    one_week_ago = current_time - timedelta(days=1)
    formatted_query_time = one_week_ago.strftime("%Y-%m-%d %H:%M")

    stmt = f"SELECT * FROM WeatherData WHERE Datetime >= '{formatted_query_time}'"
    resp = dynamodb.execute_statement(Statement=stmt)

    forecasted_data = {
        "time": [],
        "temperature": [],
        "humidity": []
    }

    measured_data = {
        "time": [],
        "temperature": [],
        "humidity": []
    }

    inside_data = {
        "time": [],
        "temperature": [],
        "humidity": []
    }


    for item in resp["Items"]:
        if item["Type"]["S"] == "forecasted":
            forecasted_data["time"].append(item["Datetime"]["S"])
            forecasted_data["temperature"].append(float(item["Temperature"]["N"]))
            forecasted_data["humidity"].append(float(item["Humidity"]["N"]))
        else:
            measured_data["time"].append(item["Datetime"]["S"])
            measured_data["temperature"].append(float(item["Temperature"]["N"]))
            measured_data["humidity"].append(float(item["Humidity"]["N"]))

            inside_data["time"].append(item["Datetime"]["S"])
            inside_data["temperature"].append(float(item["Inside Temperature"]["N"]))
            inside_data["humidity"].append(float(item["Inside Humidity"]["N"]))

    # Sort both measured and forecasted data
    measured_data = sort_data_by_time(measured_data)
    forecasted_data = sort_data_by_time(forecasted_data)
    inside_data = sort_data_by_time(inside_data)

    closest_forecast_index = None
    closest_forecast_time = None
    # get closest forecast in the future, iterating from the back of the list
    for i in range(len(forecasted_data["time"]) - 1, -1, -1):
        if forecasted_data["time"][i] > (current_time - timedelta(hours=7)).strftime("%Y-%m-%d %H:%M"):
            closest_forecast_index = i
            closest_forecast_time = forecasted_data["time"][i]
        else:
            break        

    return {
        'statusCode': 200,
        "headers": {
            "Content-Type": "application/json"
        },
        'body': json.dumps({
            "measured": { # report the latest
                "humidity": measured_data["humidity"][-1],
                "temperature": measured_data["temperature"][-1],
                "time": measured_data["time"][-1]
            },
            "insideMeasured": { # report the latest
                "humidity": inside_data["humidity"][-1],
                "temperature": inside_data["temperature"][-1],
                "time": inside_data["time"][-1]
            },
            "forecasted": { # report the latest
                "humidity": forecasted_data["humidity"][closest_forecast_index],
                "temperature": forecasted_data["temperature"][closest_forecast_index],
                "time": forecasted_data["time"][closest_forecast_index]
            }
        })
    }
