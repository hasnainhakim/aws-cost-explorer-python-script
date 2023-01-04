#!/usr/bin/env python3

import io
import boto3
import csv
import os
import smtplib
import datetime
from datetime import timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def lambda_handler(event, context):

    # Create the Cost Explorer client
    ce = boto3.client('ce')
    
    # Set the desired AWS services to include in the report
    services = ['AWSLambda', 'AmazonEC2']

    # Set the desired date range for the Cost Explorer data
    #start_date = '2022-01-01'
    #end_date = '2022-01-31'
    month = datetime.datetime.now().replace(day=1) - timedelta(days=1)

    # Set the desired granularity for the Cost Explorer data
    granularity = 'DAILY'

    # Set the desired metric for the Cost Explorer data
    metric = 'UnblendedCost'

    # Set the desired grouping for the Cost Explorer data
    group_by = [{'Type': 'DIMENSION', 'Key': 'SERVICE'}]

    # Set the desired filter for the Cost Explorer data
    filter = {
        'Not': {
            'Dimensions': {
                'Key': 'SERVICE',
                'Values': ['Savings Plan Negation']
            }
        }
    }

    # Retrieve the Cost Explorer data
    result  = ce.get_cost_and_usage(
        TimePeriod={
            'Start': month.strftime('%Y-%m-%d'),
            'End': (month + timedelta(days=30)).strftime('%Y-%m-%d')
        },
        Granularity=granularity,
        Metrics=['UnblendedCost'],
        GroupBy=group_by,
        Filter=filter
    )

    # Create a CSV file in memory
    csv_file = io.StringIO()
    csv_writer = csv.writer(csv_file)
    
    # Write the header row
    csv_writer.writerow(['Service', 'Cost'])
    
    # Iterate over the groups and add the cost for the desired services to the CSV
    for group in result['ResultsByTime'][0]['Groups']:
        service = group['Keys'][0]
        if service in services:
            cost = group['Metrics']['UnblendedCost']['Amount']
            csv_writer.writerow([service, cost])
            
    # Rewind the file pointer to the beginning of the file
    csv_file.seek(0)
    
    # Connect to the SES service
    client = boto3.client('ses')
    

    # Set the email content
    to_address = "a@abc.com"
    subject = "AWS Cost Explorer Data"
    body = "Here is the aws billing data from last month."
    charset = "UTF-8"

    msg = MIMEMultipart()
    msg['From'] = to_address
    msg['To'] = to_address
    msg['Subject'] = subject
    msg.attach(MIMEText(body))

    #with open('cost_explorer_data.csv', 'rb') as f:
    part = MIMEApplication(csv_file.read(), _subtype='csv')
        #part = MIMEApplication(f.read(), Name='cost_explorer_data.csv')
    part.add_header('Content-Disposition', 'attachment', filename=f'aws-cost-report-{month.strftime("%Y-%m")}.csv')
    msg.attach(part)
    
        # Send the email
    response = client.send_raw_email(
        RawMessage={
            'Data': msg.as_bytes(),
        },
        Source=to_address
    )
    
    # Print the response
    print(response)
