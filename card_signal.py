#!/usr/bin/python

import requests
import sys
import time
import csv
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import Encoders

#Import the CRED module from a separate directory
sys.path.insert(0,'../CRED')
import cred

#custom variables for the program imported from the cred.py file located in the same directory
organization = cred.organization
key = cred.key
email_server = cred.email_server
me = cred.card_signal_sender
you = cred.card_signal_receiver

#Main URL for the Meraki Platform
dashboard = "https://dashboard.meraki.com"
#api token and other data that needs to be uploaded in the header
headers = {'X-Cisco-Meraki-API-Key': (key), 'Content-Type': 'application/json'}

#pull back all of the networks for the organization
get_network_url = dashboard + '/api/v0/organizations/%s/networks' % organization

#request the network data
get_network_response = requests.get(get_network_url, headers=headers)

#puts the data into json format
get_network_json = get_network_response.json()

with open('card_status.csv', "w", 0) as csv_file:
    fieldnames = ['Store', 'Provider', 'Status', 'Signal']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    for network in get_network_json:
        time.sleep(1)
        network_id=(network["id"])
        get_device_url = dashboard + '/api/v0/networks/%s/devices' % network_id
        get_device_response = requests.get(get_device_url, headers=headers)
        get_device_json = get_device_response.json()
        for device in get_device_json:
            device_id=(device["serial"])
            uplink_network_url = dashboard + '/api/v0/networks/%s/devices/%s/uplink' % (network_id, device_id)
            uplink_response = requests.get(uplink_network_url, headers=headers)
            get_uplink_json = uplink_response.json()
            for uplink in get_uplink_json:
                try:
                    if uplink["interface"] == "Cellular":
                        #print (network["name"] + " - " + uplink["provider"] + " - " + uplink["status"] + " - " + uplink["signal"])
                        writer.writerow({'Store': network['name'], 'Provider': uplink['provider'], 'Status': uplink['status'], 'Signal': uplink['signal']})
                except TypeError:
                    continue
# Send email to individuals with just the info requested on the devices.

# me == the sender's email address
# you == the recipient's email address
msg = MIMEMultipart()
msg['Subject'] = 'Card Signal Strength'
msg['From'] = me
msg['To'] = you

part = MIMEBase('application', "octet-stream")
part.set_payload(open("card_status.csv", "rb").read())
Encoders.encode_base64(part)

part.add_header('Content-Disposition', 'attachment; filename="card_status.csv"')

msg.attach(part)

# Send the message via our own SMTP server, but don't include the
# envelope header.
s = smtplib.SMTP(email_server)
s.sendmail(me, you, msg.as_string())
s.quit()
    
   