#!/usr/bin/env python3
import getpass  ## import getpass is required if prompting for XIQ crednetials
import json
import requests
from colored import fg
import os
import smtplib
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders

########################################################################################################################
## written by:       Mike Rieben
## e-mail:           mrieben@extremenetworks.com
## date:             May 16, 2025
## version:          1
## tested versions:  Python 3.13.2, XIQ 25r2 (May 2025)
########################################################################################################################
## Change Log:
## v1:  Initial release
# ########################################################################################################################
## This script ...  See README.md file for full description 
########################################################################################################################
## ACTION ITEMS / PREREQUISITES
## Please read the README.md file in the package to ensure you've completed the required and optional settings below
## Also as a reminder, do not forget to install required modules:  pip install -r requirements.txt
########################################################################################################################
## - ## two pound chars represents a note about that code or a title
## - # one pound char represents a note regarding the following line and may provide info about what it is or used for
########################################################################################################################


#region - Begin user settings section

## AUTHENTICATION Options:  Uncomment the section you wish to use whie other sections remain commented out
## 1) Static Username and password, must have empty token variable (Uncomment 3 total lines below). Enter values for username and password after uncommenting.
# XIQ_Token = ""
# XIQ_username = "name@contoso.com"  # Enter your ExtremeCloudIQ Username "xxxx"
# XIQ_password = "<password>"  # Enter your ExtremeCLoudIQ password "xxxx"

## 2) Prompt user to enter credentials, must have empty token variable (Uncomment 4 total lines below), simply uncomment - no entries required
# XIQ_Token = ""
# print ("Enter your XIQ login credentials ")
# XIQ_username = input("Email: ")
# XIQ_password = getpass.getpass("Password: ")

## 3) TOKEN generation from api.extremecloudiq.com (Swagger). Must have empty username and password variables (Uncomment 3 total lines below).  Enter XIQ Toekn within "" only.
XIQ_Token = "XXXXXX"
XIQ_username = ""
XIQ_password = ""
##Authentication Options END

# ##SMTP Settings - Check your SPAM/Junk folder ---------------------------------------------------------------------------------------------------
emailFeature = 'DISABLE' # Default: 'DISABLE' to disable email feature.  'ENABLE' to enable feature.
##example username = "apikey"
username = ""
##example password = "SG.BlAl0tUjQT"
password = ""
##example sender_email = 'mike@contoso.com'
sender_email = ''
##example of multiple email addresses in a list: tolist = ['mike@contoso.com','alerts@contoso.com'] 
##example of single email address:  tolist = ['mike@contoso.com'] 
tolist = ['']
##change email subject line as you see if
email_subject = 'Device Audit Mismatch Alert'
##smtp_server = '' #If you are not using email feature then leave this variable empty '' and the script will skip sending emails
##example smtp_server = 'smtp.sendgrid.net'
smtp_server = ''
smtp_port = 587  #<-- change port as required by your SMTP server
##end SMTP Settings------------------------------------------------------------------------------------------------------------------------------------
#endregion

#region #************************* No user edits below this line required ************************************************************************************
##Global Variables-------------------------------------------------------------------------------------------------------------------------------------
URL = "https://api.extremecloudiq.com"  ##XIQ's API portal
headers = {"Accept": "application/json", "Content-Type": "application/json"}
PATH = os.path.dirname(os.path.abspath(__file__))  #Stores the current Python script directory to write the CSV file to
filename = 'device-list.csv' #<- file name that will be created in the current directory of the Python file
colorWhite = fg(255) ##DEFAULT Color: color pallete here: https://dslackw.gitlab.io/colored/tables/colors/
colorRed = fg(1) ##RED
colorGreen = fg(2) ##GREEN
colorPurple = fg(54) ##PURPLE
colorCyan = fg(6) ##CYAN
colorOrange = fg(94) ##ORANGE
colorGrey = fg(8)  ##GREY
ccgMembersIDs = []  #Stores a list of device IDs that are a member of the CCG (ccgName)
ccgSimMemberID = []  #Stores the SIM device ID so it can be ommitted from being removed from the CCG (ccgName)
#endregion #end Global Variables---------------------------------------------------------------------------------------------------------------------------------

##Use provided credentials to acquire the access token if none was provided-------------------------
def GetaccessToken(XIQ_username, XIQ_password):
    url = URL + "/login"
    payload = json.dumps({"username": XIQ_username, "password": XIQ_password})
    response = requests.post(url, headers=headers, data=payload)
    if response is None:
        log_msg = "ERROR: Not able to login into ExtremeCloudIQ - no response!"
        raise TypeError(log_msg)
    if response.status_code != 200:
        log_msg = f"Error getting access token - HTTP Status Code: {str(response.status_code)}"
        try:
            data = response.json()
            if "error_message" in data:
                log_msg += f"\n\t{data['error_message']}"
        except:
            log_msg += ""
        raise TypeError(log_msg)
    data = response.json()
    if "access_token" in data:
        headers["Authorization"] = "Bearer " + data["access_token"]
        return 0
    else:
        log_msg = "Unknown Error: Unable to gain access token"
        raise TypeError(log_msg)
##end Use provided credentials to acquire the access token if none was provided-------------------------

##Get Device Hostnames if Real / Connected / Audit Mismatch is True----------------------------------------------------------
def GetDeviceOnlineList():
    page = 1
    pageCount = 1
    pageSize = 100
    foundDevices = []
    while page <= pageCount:
        # url = URL + "/devices?page=" + str(page) + "&limit=" + str(pageSize) + "&connected=true&adminStates=MANAGED&views=FULL&deviceTypes=REAL&configMismatch=true"
        url = URL + "/devices?page=" + str(page) + "&limit=" + str(pageSize) + "&connected=true&adminStates=MANAGED&views=&fields=ID&fields=DEVICE_FUNCTION&fields=PRODUCT_TYPE&fields=HOSTNAME&fields=IP_ADDRESS&fields=SOFTWARE_VERSION&fields=CONNECTED&fields=LAST_CONNECT_TIME&fields=NETWORK_POLICY_NAME&fields=LOCATIONS&fields=CONFIG_MISMATCH&deviceTypes=REAL&async=false&configMismatch=true"
        try:
            rawList = requests.get(url, headers=headers, verify = True)
        except ValueError as e:
            print('script is exiting...')
            raise SystemExit
        except Exception as e:
            print('script is exiting...')
            raise SystemExit
        if rawList.status_code != 200:
            print('Error exiting script...')
            print(rawList.text)
            raise SystemExit
        jsonDump = rawList.json()
        for device in jsonDump['data']:
            newData = {}
            newData['HOSTNAME'] = device['hostname']
            if device['device_function']: 
                newData['TYPE'] = device['device_function']
            else:
                newData['TYPE'] = 'Unknown'
            newData['STATUS'] = 'Online' # the URL filters for online devices
            newData['AUDIT FLAG'] = 'Mismatch' # the URL filters for devices with audit mismatch
            if device['locations']:
                newData['BUILDING'] = device['locations'][-2]['name']
                newData['FLOOR'] = device['locations'][-1]['name']
            else:
                newData['BUILDING'] = 'No Location'
                newData['FLOOR'] = 'No Floor'
            if device['software_version']: 
                newData['SOFTWARE'] = device['software_version']
            else:
                newData['SOFTWARE'] = 'Unknown'
            if device['ip_address']: 
                newData['IP'] = device['ip_address']
            else:
                newData['IP'] = 'Unknown'
            if device['network_policy_name']:
                newData['POLICY'] = device['network_policy_name']
            else:
                newData['POLICY'] = 'Unknown'
            if device['product_type']: 
                newData['MODEL'] = device['product_type']
            else:
                newData['MODEL'] = 'Unknown'
            newData['LAST SEEN'] = 'Now'
            foundDevices.append(newData)
        pageCount = jsonDump['total_pages']
        print(f"\n{colorGreen}Completed page {page} of {jsonDump['total_pages']} collecting Online devices")
        page = jsonDump['page'] + 1
    # else:
    #     print(f"\n{colorGreen}No online devices found with an audit mismatch")
    return foundDevices
##end Get Device Hostnames if Real / Connected / Audit Mismatch is True----------------------------------------------------------

##Get Device Hostnames if Real / Disconnected / Audit Mismatch is True------------------------------------------------------------------------------------
def GetDeviceOfflineList():
    page = 1
    pageCount = 1
    pageSize = 100
    foundDevices = []
    while page <= pageCount:
        # url = URL + "/devices?page=" + str(page) + "&limit=" + str(pageSize) + "&connected=false&adminStates=MANAGED&views=FULL&deviceTypes=REAL"
        url = URL + "/devices?page=" + str(page) + "&limit=" + str(pageSize) + "&connected=false&adminStates=MANAGED&views=&fields=ID&fields=DEVICE_FUNCTION&fields=PRODUCT_TYPE&fields=HOSTNAME&fields=IP_ADDRESS&fields=SOFTWARE_VERSION&fields=CONNECTED&fields=LAST_CONNECT_TIME&fields=NETWORK_POLICY_NAME&fields=LOCATIONS&fields=CONFIG_MISMATCH&deviceTypes=REAL&async=false&configMismatch=true"
        try:
            rawList = requests.get(url, headers=headers, verify = True)
        except ValueError as e:
            print('script is exiting...')
            raise SystemExit
        except Exception as e:
            print('script is exiting...')
            raise SystemExit 
        if rawList.status_code != 200:
            print('Error exiting script...')
            print(rawList.text)
            raise SystemExit
        jsonDump = rawList.json()
        for device in jsonDump['data']:
            newData = {}
            newData['HOSTNAME'] = device['hostname']
            if 'device_function' in device and device['device_function']:
                newData['TYPE'] = device['device_function']
            else:
                newData['TYPE'] = 'Unknown'
            newData['STATUS'] = 'Offline' # the URL filters for disconnected devices
            newData['AUDIT FLAG'] = 'Mismatch' # the URL filters for devices with audit mismatch
            if device['locations']:
                newData['BUILDING'] = device['locations'][-2]['name']
                newData['FLOOR'] = device['locations'][-1]['name']
            else:
                newData['BUILDING'] = 'No Location'
                newData['FLOOR'] = 'No Floor'
            if device['software_version']: 
                newData['SOFTWARE'] = device['software_version']
            else:
                newData['SOFTWARE'] = 'Unknown'
            if 'ip_address' in device and device['ip_address']:
                newData['IP'] = device['ip_address']
            else:
                newData['IP'] = 'Unknown'
            if device['network_policy_name']: 
                newData['POLICY'] = device['network_policy_name']
            else:
                newData['POLICY'] = 'Unknown'
            if device['product_type']: 
                newData['MODEL'] = device['product_type']
            else:
                newData['MODEL'] = 'Unknown'
            if 'last_connect_time' in device and device['last_connect_time']:
                newData['LAST SEEN'] = device['last_connect_time']
            else:
                newData['LAST SEEN'] = 'Check if device has ever connected to XIQ'
            foundDevices.append(newData)
        pageCount = jsonDump['total_pages']
        print(f"\n{colorGrey}Completed page {page} of {jsonDump['total_pages']} collecting Offline devices")
        page = jsonDump['page'] + 1
    return foundDevices
##end Get Device Hostnames if Real / Disconnected / Audit Mismatch is True--------------------------------------------------------------------------------

##Send email
def SendMail(fromaddr, toaddr, email_body, email_subject, smtpsrv, smtpport, reportName):
        # Build the email
        toHeader = ", ".join(toaddr)
        msg = MIMEMultipart()
        msg['Subject'] = email_subject
        msg['From'] = fromaddr
        msg['To'] = toHeader
        msg.attach(MIMEText(email_body))
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(f"{PATH}/{filename}", "rb").read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{reportName}"')
        msg.attach(part)
        try:
            server = smtplib.SMTP(smtpsrv, smtpport)
            server.starttls()
            server.login(username,password)
            server.send_message(msg)
            server.quit()
            #debug_print "email sent: %s" % fromaddr
        except Exception as e:
                logmsg = "Something went wrong when sending the email to {}".format(fromaddr)
                raise TypeError(f"{logmsg}\n   {e}")
##end SMTP Relay for email alerts section ---------------------------------------------------------

##This is the start of the program
def main():
    ##Test if a token is provided.  If not, use credentials.
    if not XIQ_Token:
        try:
            login = GetaccessToken(XIQ_username, XIQ_password)
        except TypeError as e:
            print(e)
            raise SystemExit
        except:
            log_msg = "Unknown Error: Failed to generate token"
            print(log_msg)
            raise SystemExit
    else:
        headers["Authorization"] = "Bearer " + XIQ_Token
    deviceOnlineList = GetDeviceOnlineList()
    deviceOfflineList = GetDeviceOfflineList()
    print(f'\n{colorWhite}---------- REPORT ----------')
    msg1 = ('\nTotal Number Devices Found: Real / Connected / Audit Mismatch Is True = ' + str(len(deviceOnlineList)))
    if len(deviceOnlineList) > 0:
        msg2 = ('Devices: ' + ', '.join(str(e['HOSTNAME']) for e in (deviceOnlineList)))
    else:
        msg2 = ('No devices found that meet the criteria above.')
    print(f'{colorGreen}' + msg1 + '\n' + msg2)
    msg3 = (f'\nTotal Number Devices Found: Real / Disconnected = ' + str(len(deviceOfflineList)))
    if len(deviceOfflineList) > 0:
        msg4 = ('Devices: ' + ', '.join(str(e['HOSTNAME']) for e in (deviceOfflineList)))
    else:
        msg4 = ('No devices found that meet the criteria above.')
    print(f'{colorGrey}' + msg3 + '\n' + msg4)
    email_msg = msg1 + '\n' + msg2 + '\n' + msg3 + '\n' + msg4 + '\n'
    print(f'\n{colorPurple}Populating CSV file with found devices: "' + filename + '" <-- Check script directory for file.\n')
    allDevices = deviceOnlineList + deviceOfflineList
    dfAllDevices = pd.DataFrame(allDevices)
    if len(allDevices) != 0:
        dfAllDevices.sort_values(by=['HOSTNAME'], inplace=True, ascending=True)  #sort rows by Hostname
    dfAllDevices.to_csv(filename, index=False)
    if smtp_server != '' and emailFeature == 'ENABLE':
        if len(deviceOnlineList) != 0:
            try:
                SendMail(sender_email, tolist, email_msg, email_subject, smtp_server, smtp_port, filename)
            except TypeError as e:
                print(e)
            print(f'{colorWhite}Email includes CSV and sent to: ' + ','.join(str(e) for e in (tolist)) + '\n')
        else:
            print(f'{colorWhite}No email was sent due to all online devices having current configurations. Check CSV for offline devices. \n')
    elif emailFeature != 'ENABLE':
        print(f'{colorWhite}***Email feature is disabled, skipping email.*** \n')
    elif smtp_server == '':
        print(f'{colorWhite}No SMTP server defined, skipping email. \n')
    else:
        print(f'{colorRed}Unknown issue... Verify all User Settings Section variables: smtp_server, emailFeature, etc.')
        
##Python will see this and run whatever function is provided: xxxxxx(), should be the last items in this file
if __name__ == '__main__':
    main() ##Go to main function

##***end script***


