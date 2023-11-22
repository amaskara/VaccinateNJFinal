#-----------------------------------------------------------------------

# notifyusers.py

#-----------------------------------------------------------------------

import os
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests, json
from database import Database
from datetime import datetime, time, timedelta, timezone
import pytz

#-----------------------------------------------------------------------

# Sends email containing updated vaccination site information to
# specified receiver.
def send_email(receiver_name, receiver_email, sites, is_daily_summary):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = "vaccinatenjnotify@gmail.com"
    receiver_email = receiver_email
    password = os.environ['EMAIL_PASSWORD']

    message = MIMEMultipart("alternative")
    if is_daily_summary:
        message["Subject"] = "VaccinateNJ Daily Summary"
    else:
        message["Subject"] = "Vaccine Availability Updated"
    message["From"] = sender_email
    message["To"] = receiver_email

    # Create the plain-text and HTML version of your message
    if is_daily_summary:
        text = "<p>" + "Hi, " + receiver_name + "!</p><p>Here's your daily summary for your saved vaccination sites:</p>"
    else:
        text = "<p>" + "Hi, " + receiver_name + "!</p><p>" + str(len(sites))
        if len(sites) == 1:
            text += " of your saved vaccination locations now has vaccines availabile as of "
            text += datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(pytz.timezone("America/New_York")).strftime("%m/%d/%Y @ %I:%M %p")
            text += " EDT! See more info below: </p>"
        else:
            text += " of your saved vaccination locations now have vaccines availabile as of "
            text += datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(pytz.timezone("America/New_York")).strftime("%m/%d/%Y @ %I:%M %p")
            text += " EDT! See more info below: </p>"
    for site in sites:
        date_time = site['updatedDate'].replace(tzinfo=timezone.utc).astimezone(pytz.timezone("America/New_York")).strftime("%m/%d/%Y @ %I:%M %p")

        text += "<p><strong>Site: </strong>" + site['name']
        text += "</p><p><strong>Website: </strong><a href='" + site['url'] + "'>" + site['url']+ "</a>"
        if site['availabilityStatus'] == "Available":
            text += "</p><p><strong>Availability: </strong><span style='color:green;'>" + site['availabilityStatus'] + "</span>"
        elif site['availabilityStatus'] == "Wait List":
            text += "</p><p><strong>Availability: </strong><span style='color:orange;'>" + site['availabilityStatus'] + "</span>"
        else:
            text += "</p><p><strong>Availability: </strong><span style='color:red;'>" + site['availabilityStatus'] + "</span>"
        text += "</p><p>Updated On "  + date_time + " EDT</p>"
        text += "-------------------------------------------"
    text += '''<p>You're recieving this email because you subscribed to
    email notifications on <a href='https://vaccinatenj.herokuapp.com/editprofile'>
    vaccinatenj.herokuapp.com</a>. Please update your notification
    preferences on our site to unsubscribe.</p>''' # TO DO: ADD EMAIL OPT OUT
    html = """\
    <html>
    <body>
    """ + text + """\
    </body>
    </html>
    """

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)

    # Send email with SMTP_SSL server
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

    print("Sent email to: " + receiver_email)

#-----------------------------------------------------------------------

# Queries VaccinateNJ API to get current site info.
def query_vaxNJ():
    url = "https://c19vaccinelocatornj.info/api/v1/vaccine/locations/page"
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    payload = {
        "draw": 1,
        "columns": [],
        "order": [],
        "start": 0,
        "length": 1000,
        "search": {
            "value": "",
            "regex": False
        }
    }
    response = requests.request("POST", url, data=json.dumps(payload), headers=headers).json()
    site_info = response["data"]
    # print(site_info[0:5])
    return site_info

#-----------------------------------------------------------------------

# Evaluates sites in VaccinateNJ database to determine which ones have
# been updated in the last 11 minutes. Appends relevant information about these
# sites to a list and return that list.
def get_updated_sites():
    now = datetime.utcnow() # datetime object containing current date and time (utc)

    site_info = query_vaxNJ()

    current_site_status = {}
    for site in site_info:
       if site['availabilityChangedDate'] is not None:
            date = site['availabilityChangedDate'].split("T")
            date_split = date[0].split("-")
            time_split = date[1].split(":")
            time_split[2] = time_split[2].split("Z")[0]
            updated_date = datetime(int(date_split[0]),int(date_split[1]),int(date_split[2]), int(time_split[0]), int(time_split[1]), int(time_split[2]))

            eleven_min_ago = now + timedelta(minutes = -11)

            if eleven_min_ago < updated_date:
                current_site_status[site['id']] = {"name": site['name'], "url": site['url'], "availabilityStatus": site['availabilityStatus'], "updatedDate": updated_date, "updated": "True"}
            else:
                current_site_status[site['id']] =  {"name": site['name'], "url": site['url'], "availabilityStatus": site['availabilityStatus'], "updatedDate": updated_date, "updated": "False"}

    return site_info, current_site_status, now

#-----------------------------------------------------------------------

# Notifies all users (via email) who have sites saved in the
# site_prefences database tabel that have been recently updated.
# 0 = immediately, 1 = daily summary, 2 = both, 3 = no notifications
def send_all_notif():
    site_info, current_site_status, now = get_updated_sites()
    database = Database()
    database.connect()
    users = database.get_all_users()
    for user in users:
        if user[4] is True:
            if user[5] is 0 or user[5] is 2:
                site_preferences = database.get_site_preferences(user[0], site_info)
                receiver_email = user[3]
                receiver_name = user[1]
                updated_sites = []
                for site in site_preferences:
                    if "code" not in site:
                        if current_site_status[site['id']]["updated"] is not "False" and current_site_status[site['id']]['availabilityStatus'] == "Available":
                            if current_site_status[site['id']]['url'] is None:
                                current_site_status[site['id']]['url'] = "No Website Available"
                            updated_sites.append(current_site_status[site['id']])
                if (len(updated_sites) is not 0):
                    send_email(receiver_name, receiver_email, updated_sites, False)
            if (user[5] is 1 or user[5] is 2) and time(12) <= now.time() <= time(12, 11):
                site_preferences = database.get_site_preferences(user[0], site_info)
                receiver_email = user[3]
                receiver_name = user[1]
                updated_sites = []
                for site in site_preferences:
                    if "code" not in site and current_site_status[site['id']]['name'] is not None:
                        if current_site_status[site['id']]['url'] is None:
                                current_site_status[site['id']]['url'] = "No Website Available"
                        # if current_site_status[site['id']]['availabilityStatus'] is None:
                        #         current_site_status[site['id']]['availabilityStatus'] = "No Availability Info Available"
                        updated_sites.append(current_site_status[site['id']]) # TO DO: SORT BY AVAILABILITY STATUS
                if (len(updated_sites) is not 0):
                    send_email(receiver_name, receiver_email, updated_sites, True)
    database.disconnect()

#-----------------------------------------------------------------------

# Initiates email notification process
if __name__ == '__main__':
    send_all_notif()
