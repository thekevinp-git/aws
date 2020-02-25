import os
import boto3
import pprint
import json
import subprocess
from validate_email import validate_email
from datetime import datetime, timedelta

instance_name = ""
owner_value = ""
team_value = ""
instance_id = ""
key_data = ""
value_data = ""
acct_id = ""
email_status = ""
writeHeader = True
# Initializing map for email addresses and status
map_email_status = {}

# setup output file
if not os.path.exists('/tmp/ec2_instance'):

   path = "/tmp/ec2_instance"
   os.mkdir( path, 0755 );

curr_date = datetime.today().strftime('%Y-%m-%d_%H%M%S')
date_ = datetime.today() + timedelta(days=14)
curr_date_plus14 = date_.strftime('%Y/%m/%d')
logfile = "invalid_EC2_instance_emails_" + curr_date + ".csv"
target = open('/tmp/ec2_instance/' + logfile, 'w')

### print header
def printHeader():
   global writeHeader
   target.truncate()
   target.write("Account ID,Instance ID,Tag Key,Tag Key Value,Instance Name\n")
   writeHeader = False

### verify that the email is valid. Save the results in a map to alleviate 
### extraneous and expensive calls to validate_email.
def verify_email(acctId, instanceId, key, value, insName, c7n_email):
    #check map if email exist in map, if not save email in map
    if value not in map_email_status.keys():
       email_status = validate_email(value, verify=True)
       map_email_add(value, email_status)
    if (map_email_status.get(value) != True):
       send_notification(acctId, instanceId, key, value, insName, c7n_email)
    else:
       update_tag(acctId, instanceId, key, value, insName, c7n_email)


### send notification
def send_notification(acct_id, instance_id, key_data, value_data, ins_Name, c7n_email):
    #check map if email exist in map, if not save email in map
    #print "Account ID,Instance ID,Tag Key,Tag Key Value,Instance Name"
    #print acct_id + "," + instance_id + "," + key_data + ","  + value_data + "," + ins_Name

    global writeHeader 
    if (len(c7n_email) < 1): 
       if (writeHeader == True):
         printHeader()
       target.write("%s,%s,%s,%s,%s \n" % (acct_id, instance_id, key_data, value_data, ins_Name))
    update_tag(acct_id, instance_id, key_data, value_data, ins_Name, c7n_email)



### add email and status to map, where the email is the key 
### and the email status is the value. 
def map_email_add(key, e_status):
    #if email does not exist in map, then add email and status
    if key not in map_email_status.keys():
       map_email_status[key] = e_status

### add "c7n_email_validation" tag if email is invalid and tag does not exist
### remove tag if team and owner email addresses are valid
def update_tag(acct_id, instance_id, key_data, value_data, ins_Name, c7n_email):
    #  If Tag, c7n_email_validation, is not present then cerate tag with "stop@" appended with current 
    #  date plus 14 days
    if (len(c7n_email) < 1):         
     response1 = client.create_tags(
       DryRun=False,
       Resources=[
           str(instance_id),
       ],
       Tags=[
           {
               'Key': 'c7n_email_validation',
               'Value': 'stop@' + str(curr_date_plus14)
           },
       ]
     )


    # Remove Tag, c7n_email_validation, if it exists and email addresses are valid for Owner and Team 
    if (map_email_status.get(owner_value) == True and map_email_status.get(team_value) == True and len(c7n_email) > 0): 
     response2 = client.delete_tags(
       DryRun=False,
       Resources=[
           str(instance_id),
       ],
       Tags=[
           {
               'Key': 'c7n_email_validation'
           },
       ]
     )



# get all EC2 objects via boto3
client = boto3.client('ec2')
instances = client.describe_instances()

# For debugging purposes, print the EC2 objects returned
#pprint.pprint(instances)
#pprint.pprint("==================================================")

# read the dictionary and parse the needed fields
for r in instances['Reservations']:
  acct_id = ""
  instance_id = ""
  key_data = ""
  value_data = ""
  instance_name = ""
  owner_value = ""
  team_value = ""
  c7n_email_value = ""

  acct_id = r['OwnerId']
  for i in r['Instances']:
    instance_id = i['InstanceId']
    if not "Tags" in i.keys():
      continue  # if record has no Tags don't attempt to process
    for b in i['Tags']:
      key_data = b['Key'].strip().encode('utf-8')
      # Save EC2 tag values for Name, Owner and Team
      value_data = b['Value'].strip().encode('utf-8')
      if (key_data == "Name"):
          instance_name = value_data
      if (key_data == "Owner"):
          owner_value = value_data
      if (key_data == "Team"):
          team_value = value_data

      if (key_data == "c7n_email_validation"):
          c7n_email_value = value_data


    if (len(owner_value) > 0 and (len(instance_name)) > 0):
          check_mail = validate_email(owner_value)
          if (check_mail == False):
             # invalid email so generate notification
             send_notification(acct_id, instance_id, "Owner", owner_value, instance_name, c7n_email_value)
          elif (check_mail == True):
             # valid email
             # save in map where email is the key
             verify_email(acct_id, instance_id, "Owner", owner_value, instance_name, c7n_email_value)
          else:
             print "unknown response where check_mail = ", check_mail

    if (len(team_value) > 0 and (len(instance_name)) > 0):
          check_mail = validate_email(team_value)
          if (check_mail == False):
             # invalid email so generate notification
             send_notification(acct_id, instance_id, "Team", team_value, instance_name, c7n_email_value)
          elif (check_mail == True):
             # valid email
             # save in map where email is the key
             verify_email(acct_id, instance_id, "Team", team_value, instance_name, c7n_email_value)
          else:
             print "unknown response where check_mail = ", check_mail

#close the output csv file
if os.path.exists('/tmp/ec2_instance/' + logfile):
   target.close()

if os.path.getsize('/tmp/ec2_instance/' + logfile) == 0:
   os.remove('/tmp/ec2_instance/' + logfile)
else:
   # Print output file to screen and send the file via email
   print("output file: /tmp/ec2_instance/" + logfile)
   logfile1 = "/tmp/ec2_instance/" + logfile
   cmd = 'mailx -r "KP <kpatrick@shutterstock.com>" -s "EC2 Invalid Tags Report - %s""" "kpatrick@shutterstock.com" < %s' % (logfile, logfile1)
   subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True).communicate()[0]
