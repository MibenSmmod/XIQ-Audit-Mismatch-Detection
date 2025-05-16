# XIQ Audit Mismatch Detection
## Purpose
This script was a spinoff of the XIQ Audit Mismatch Alert.

ExtremeCloud IQ (XIQ) does not have a way to alert the admins if a configuration was changed thus causing an audit mismatch.  In a multi-team environment this can be problematic.  If someone is working on a new SSID and another admin pushes an update then you might be pushing an incomplete configuration by accident.  The intent here is to alert your entire team if the script detects a device in an audit mismatch state.

This script will search for all Online Devices, Real, with an Audit Mismatch and write to a CSV file in the current directory. Next it will append all Offline Devices in a mismatch state.  An email will be sent to a list of addresses you specify with an attached CSV file (optional feature).  This skips all Sim, Plan, and non-managed devices including any that are in a "New" state which haven't checked into XIQ yet.

## Actions & Requirements
You must update the user controllable variables within the XIQ-Audit-Mismatch-Alerts.py which are outlined below.  Install the required modules and generate an API Token to run script without user prompts.  If you need assistance setting up your computing environment, see this guide to aid in your setup: https://github.com/ExtremeNetworksSA/API_Getting_Started (currently the guide does not provide how to run scripts on a schedule at this time)

### Install Modules
There are additional modules that need to be installed in order for this script to function.  They're listed in the *requirements.txt* file and can be installed with the command `pip install -r requirements.txt` if using `PIP`.  Store the *requirements.txt* file in the same directory as the Python script file.

## Locate in the script "Begin user settings section" (around  line 35)
  - Authentication Options - [Token](#api-token) (Best Option), Static entry for User/Pass, or Prompt for credentials
  - [SMTP Settings](#smtp-relay-optional-feature) - Default: emailFeature = "DISABLE" , Complete the additional fields for SMTP relay server

### API Token
There are multiple authentication methods built-in, but the default setup will use Tokens so the code simply executes without user prompts.   Other options:  You can use hard code credentials to generate a token (not as secure).  Prompt the user to enter credentials every time you run this and will send credentials to XIQ over HTTPS to generate a token.

In order to have this script run without user prompts, you must generate a token using our api.extremecloudiq.com.
Follow this article to generate an API key with the minimum requirements below:  https://extreme-networks.my.site.com/ExtrArticleDetail?an=000102173
These permissions allow you to access the account APIs, device APIs in read-only, and allows you to logout.
Brief instructions of the process:
  1) Navigate to api.extremecloudiq.com
  2) Use the Authentication: /login API (Press: Try it out) to authenticate using a local administrator account in XIQ
  
    {
    "username": "username@company.com",
    "password": "ChangeMe"
    }
  3) Press Execute button
  4) Scroll down and copy clip the contents of the access_token; do not copy the "" characters

    {
    "access_token": "---CopyAllTheseCharacters---",
    "token_type": "Bearer",
    "expires_in": 86400    <--- Expires in 24 hours>
    }
  5) Scroll to the top and press the Authorize button
  6) Paste contents in the Value field then press the Authorize button.  You can now execute any API's listed on the page.  ***WARNING*** You have the power to run all POST/GET/PUT/DELETE/UPDATE APIs and affect your live production VIQ environment.
  7) Scroll down to Authorization section > /auth/apitoken API (Press: Try it out)
  8) You need to convert a desired Token expiration date and time to EPOCH time:  Online time EPOCH converter:  https://www.epochconverter.com/
     EPOCH time 1717200000 corresponds to June 1, 2024, 00:00:00 UTC
  9) Update the expire_time as you see fit from #8 above.  Update the permissions as shown for minimal privileges to run the script.  The permissions allow the script to push updates to CCGs and devices.

    "description": "Token for API Script",   <--- Update the description
    "expire_time": 1717200000,    <--- Expires based on your expiration date converted to EPOCH time
    "permissions": [
    "auth:r","device:r","logout","ccg","deployment"    <--- Token permissions
    ]

  10) Press Execute button
  11) Scroll down and copy clip the contents of the access_token

    "access_token": "---ThisIsYourScriptToken---",
    ^^^ Use this Token in your script ^^^
    
    Locate in your Python script and paste your token:
    XIQ_Token = "---ThisIsYourScriptToken---"

### SMTP Relay (Optional Feature)
This script uses an SMTP relay to email alerts.  Tested with a local SMTP relay server.  A free 100 messages per day cloud service called Sendgrid was used for the example but does not function without you creating an account and updating your API key, To address, From address variables.
https://app.sendgrid.com/ (not affiliated)
- Default:  emailFeature = "DISABLE" or ""
- To enable change:  emailFeature = "ENABLE" then complete the remaining variable for your SMTP server

## Screen Output & CSV Report
1) You will receive a report onscreen of what the script identified and updated (if READ-Only was disabled)
2) Script will create a "device-list.csv" in the same directory as the PY script file. User will require write access to the directory.
3) If you setup the email feature, the CSV will be included as an attachment.

>**Note:  The CSV file is overritten each time the script is ran.**

Example CSV Output:

| HOSTNAME | TYPE | STATUS | AUDIT FLAG | BUILDING | FLOOR |
| -------- |:----:| ------:| ----------:| --------:| -----:|
| AP1 | AP | Online | Mismatch | Bldg | Floor |
| AP2 | AP | Online | Mismatch | Bldg | Floor |
| AP4 | AP | Offline | Mismatch | Bldg | Floor |

| SOFTWARE | IP | POLICY | MODEL | LAST SEEN |
| --------:| --:| ------:| -----:| ---------:|
| 10.6.5.0 | 10.48.1.178 | Test | AP_3000 | Now |
| 10.6.7.0 | 10.48.1.108 | Test | AP_5010 | Now |
| 10.6.6.0 | 10.48.1.172 | Test | AP_302W | 2024-06-11T19:42:16.000+0000 |

Notes: 
- AP3 was Online wth No Mismatch and therefore skipped.
