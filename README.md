# Validate email addresses defined in EC2 tags
Email validator for tag values associated with a given EC2 instance

The python script, get_tags.py, will ultimately be used by an AWS policy that will stop/terminate EC2 instances that are inactive.
When an EC2 instance is spun up the EC2 tags need to be defined according to the Shutterstock AWS Tagging Policy. Heres a link to the policy:
https://docs.google.com/document/d/11WZ6mCjSxXoqMiOJ9pfFA0rlDuwYkzpJqHIMw2-l3bA/edit#heading=h.3bp1mns634al

The Tag definitions are key/value pairs. The script will validate that keys, "Owner" and "Team" have a valid shutterstock email address.
The script uses the boto3 to retrieve all EC2 instances for a given AWS account. Boto is the Amazon Web Service (AWS) SDK for Python
that enables python developers to creates, configure and manage AWS services. The script also uses a python module called validate_email which
has 3 levels of email validation, including asking a valid SMTP server if the email address is valid (without sending an email).

The script makes a boto3 call to retrieve the EC2 instances for an AWS account. The call returns a python dictionary where the Tag
data is parsed. The key value is evaluated against the following criteria:
```
  1. a well formed email address
  2. a valid Shutterstock email
```

## How to get up and running
```
Complete the setup defined in the c7n-tools README
Clone the cloud-governance/c7n-tools to your vagrant VM
- ./awscli sts get-caller-identity   # settup access to awscli
Install the required library for get_tags.py
- cd c7n-tools/scripts/
- virtualenv email-validator
- source email-validator/bin/activate
- pip install boto3 validate_email pyDNS  ### this only need to be done once
- cd email-validator
Run the python script: python get_tags.py
- python get_tags.py
The ouput file is written to:
   /tmp/ec2_instance/invalid_EC2_instance_emails_yyyy-mm-dd_hhmmss.csv
```
