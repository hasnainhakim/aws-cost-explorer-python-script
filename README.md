# Overview

A simple Python 3 script to run via AWS Lambda to report last month's billing

# Getting the Data

Getting the data is pretty straigtforward. Create a Cost Explorer client:
```
client = boto3.client('ce')
```

Query for the cost data for the time period defined by `start` and `end`:
```
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
```




After reformatting the data, we email it using AWS SES (see [Amazon SES Quick Start](https://docs.aws.amazon.com/ses/latest/DeveloperGuide/quick-start.html) for instructions on enabling SES and creating an authorized email endpoint). Because we're including a file attachment, we need to create an email using `MIMEMultipart()`.


# AWS

Log into the AWS Console to create the Lambda function, give it the correct access permissions, and configure its run schedule.

## Create the Lambda function

* Lambda > Functions > Create function
* Name: monthlyBillingEmail
* Runtime: Python 3.6
* Role: Create a custom role

* IAM Role: Create a new IAM Role
* Role Name: lambda_send_billing_email

Create Function

## Creating IAM permissions

Create a Policy that allows access to the Cost Explorer API:

* IAM > Policies > Create policy
* Service: Cost Explorer Service
* Actions: All
* Name: allowCostExplorerRead

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": "ce:*",
            "Resource": "*"
        }
    ]
}
```

Create another Policy that allows sending email over SES:

* IAM > Policies > Create new 
* Service: SES
* Write: SendEmail, SendRawEmail
* Name: allowSESSendEmail

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "ses:SendEmail",
                "ses:SendRawEmail"
            ],
            "Resource": "*"
        }
    ]
}
```

Bundle these Policies into a Role:

* IAM > Roles > Search "lambda_send_billing_email"
* Attach policy:
 - [x] allowCostExplorerRead
 - [x] allowSESSendEmail


## Actually create the Lambda function

Lambda > Functions > monthlyBillingEmail

We don't have any external libraries other than boto, so we can just edit inline

Paste the contents of `generate_report.py` into the `lambda_function` tab 
(except the shebang line although maybe that doesn't matter?)

Create a test, using Hello World as a template
(we're not actually using the contents so NBD)

Run the test; it should report success and the billing output!

## Add Triggers

In order to schedule the function to run automatically each month, we create a Trigger in CloudWatch. We will schedule it to run at midnight on the third of each month just in cause there is some latency is AWS aggregating the billing data (note that that is pure speculative paranoia on my part).

* CloudWatch Events
* Configure triggers
* Create a new rule
  * Rule name: lambda_monthly_billing
  * Rule description: Running on the 3rd of the month
  * Rule type: Schedule expression
  * Schedule expression: `cron(0 0 3 * ? *)`  <- Syntax on this is a little wonky... need to have `?` for Day-of-month or Day-of-week