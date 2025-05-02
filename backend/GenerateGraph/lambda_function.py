import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import boto3
from datetime import datetime, timedelta

#table_name = "WeatherData"

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
    #table = dynamodb.Table(table_name)

    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M")

    one_week_ago = current_time - timedelta(weeks=1)
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

    measured_inside_data = {
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

            if "Inside Temperature" not in item:
                continue
            
            measured_inside_data["time"].append(item["Datetime"]["S"])
            measured_inside_data["temperature"].append(float(item["Inside Temperature"]["N"]))
            measured_inside_data["humidity"].append(float(item["Inside Humidity"]["N"]))

    # Sort both measured and forecasted data
    measured_data = sort_data_by_time(measured_data)
    forecasted_data = sort_data_by_time(forecasted_data)
    measured_inside_data = sort_data_by_time(measured_inside_data)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # measured (outside) data
    fig.add_trace(go.Scatter(x=measured_data["time"], y=measured_data["temperature"],
                    mode='lines+markers',
                    name='Actual Temperature'),
                    secondary_y=False)
    fig.add_trace(go.Scatter(x=measured_data["time"], y=measured_data["humidity"],
                    mode='lines+markers',
                    name='Actual Humidity',
                    visible='legendonly'),
                    secondary_y=True)

    # forecasted data
    fig.add_trace(go.Scatter(x=forecasted_data["time"], y=forecasted_data["temperature"],
                    mode='lines+markers',
                    name='Forecasted Temperature'),
                    secondary_y=False)
    fig.add_trace(go.Scatter(x=forecasted_data["time"], y=forecasted_data["humidity"],
                    mode='lines+markers',
                    name='Forecasted Humidity',
                    visible='legendonly'),
                    secondary_y=True)
    
    # measured inside data
    fig.add_trace(go.Scatter(x=measured_inside_data["time"], y=measured_inside_data["temperature"],
                    mode='lines+markers',
                    name='Inside Temperature'),
                    secondary_y=False)

    fig.add_trace(go.Scatter(x=measured_inside_data["time"], y=measured_inside_data["humidity"],
                    mode='lines+markers',
                    name='Inside Humidity',
                    visible='legendonly'),
                    secondary_y=True)

    return {
        'statusCode': 200,
        "headers": {
            "Content-Type": "text/html" # or another type such as "application/json"
        },
        'body': fig.to_html(full_html=False, include_plotlyjs='cdn')
    }
