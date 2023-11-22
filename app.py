#-----------------------------------------------------------------------
# app.py
# Authors: Anika Maskara, Srija Patcha, Maya Rozenshteyn, Rifat Islam
#-----------------------------------------------------------------------

from flask import Flask, url_for, render_template, request, make_response, redirect
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
import requests
import json
import zipcounty
import re
from oauthlib.oauth2 import WebApplicationClient
from database import Database
from zipcounty import zipdict
import difftime
import math
from functools import cmp_to_key
from jinja2 import Environment, FileSystemLoader
import os

#-----------------------------------------------------------------------

app = Flask(__name__, template_folder = "templates")

def validateSite(site_id):
    reg = "........-....-....-....-............"
    return (re.match(reg, str(site_id)) != None)

# retrieve all sites from the VaccinateNJ database
def getAllSites():
    url = "https://c19vaccinelocatornj.info/api/v1/vaccine/locations/page"
    headers = {'Accept': 'application/json',
               'Content-Type': 'application/json'}
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
    if response['recordsTotal'] == 0:
        return []
    return response['data']

@app.route('/')
@app.route('/index', methods=["GET", "POST"])
def index():
    signed_in = request.cookies.get('signed_in')

    html = render_template('landing.html', signedIn=signed_in)
    response = make_response(html)
    return response

@app.route('/dashboard', methods=['GET'])
def dashboard():
    signed_in = request.cookies.get('signed_in')
    user_id = request.cookies.get('user_id')
    user_name = request.cookies.get('user_name')

    if signed_in is not None:
        database = Database()
        database.connect()

        # corner case where user might be signed in but not yet in the dashboard
        if database.get_user_info(user_id) is None:
            html = render_template('dashboard.html', signedIn = signed_in, inDatabase = False)
            response = make_response(html)
            return response

        sites = getAllSites()
        # filter for the sites the user has favorited
        sites = database.get_site_preferences(user_id, sites)
        database.disconnect()

        sites = list(filter(lambda i: i.get('status') != 404, sites))

        for site in sites:
            site["favorited"] = True

        addDateLocation(sites)

        html = render_template('dashboard.html', user_name = user_name, sites = sites, 
                        signedIn = signed_in, inDatabase = True)
    else:
        html = render_template('dashboard.html', signedIn = signed_in)

    return make_response(html)

@app.route('/profile')
def profile():
    signed_in = request.cookies.get('signed_in')
    user_id = request.cookies.get('user_id')

    database = Database()
    database.connect()

    # corner case where user might be signed in but not yet in the dashboard
    if signed_in is True and database.get_user_info(user_id) is None:
        return redirect(url_for("editprofile"))

    database.disconnect()

    html = render_template("profile.html", first_name=request.cookies.get('user_name'),
            last_name=request.cookies.get('user_last_name'), email=request.cookies.get('user_email'),
            notif=request.cookies.get('notif_option'), signedIn=signed_in)

    return make_response(html)

@app.route('/editprofile')
def editprofile():
    signed_in = request.cookies.get('signed_in')
    first_name = request.cookies.get('user_name')
    last_name = request.cookies.get('user_last_name')
    email = request.cookies.get('user_email')
    notif = request.cookies.get('notif_option')

    # indicator that the user is new
    first_time = request.args.get('first')

    html = render_template('editprofile.html', signedIn=signed_in,
        first_name=first_name, last_name=last_name, email=email,
        notif=notif, first=first_time)

    return make_response(html)

@app.route('/vaccinesearch', methods=['GET'])
def vaccinesearch():
    signed_in = request.cookies.get('signed_in')
    user_id = request.cookies.get('user_id')
    zipcode = request.args.get('zipcode')
    
    if zipcode is None:
        zipcode = ''
    else:
        zipcode = zipcode.strip()

    sites = getAllSites()

    error_in_zip = False
    orig_input = zipcode

    if (zipcode != '') and (zipcode not in zipdict):
        zipcode = ''
        error_in_zip = True

    if zipcode != '':
        radius = '10'
        sites = sortSites(sites, zipcode)
    else:
        radius = '40+'

    if signed_in is not None:
        database = Database()
        database.connect()
        sites = database.check_site_preferences(user_id, sites)
        database.disconnect()

    addDateLocation(sites)

    html = render_template('vaccinesearch.html', sites=sites, no_zip=zipcode == '', 
            initial_error=error_in_zip, signedIn=signed_in, my_zip=orig_input,
            availabilityFilter='--', eligibilityFilter='--', radius=radius)

    return make_response(html)

# send inner html for site box container and list of sites
# based on new zip code to front-end
@app.route('/filtersites', methods=['POST'])
def filtersites():
    signed_in = request.cookies.get('signed_in')
    user_id = request.cookies.get('user_id')

    availability = request.args.get('availability')
    eligibility = request.args.get('eligibility')
    zipcode = request.args.get('zipcode')

    if availability is None:
        availabiity = "--"
    if eligibility is None:
        eligibility = "--"

    if zipcode is None:
        zipcode = ''
    else:
        zipcode = zipcode.strip()

    sites = getAllSites()

    if zipcode != '':
        sites = sortSites(sites, zipcode)

    if signed_in is not None:
        database = Database()
        database.connect()
        sites = database.check_site_preferences(user_id, sites)
        database.disconnect()

    addDateLocation(sites)

    env = Environment(loader=FileSystemLoader('templates'))

    template_sites = env.get_template('site-box.html')
    sitebox_html = template_sites.render(signedIn=signed_in, sites=sites)

    to_send = {'siteboxes': sitebox_html, 'sites': sites, 'availabilityFilter': availability, 
        'eligibilityFilter': eligibility, 'zipcode': zipcode}

    return make_response(to_send)

# get the geolocation of the current zip code 
# using the Google Geocoding API
def getGeo(zipcode):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    API_KEY = os.environ['API_KEY']
    params = {'address': zipcode, 'key': API_KEY}
    r = requests.get(url, params = params)
    results = r.json()['results']
    location = results[0]['geometry']['location']
    return (location['lat'], location['lng'])

# implementing the Haversine formula to find distance between
# two coordinates in miles
def findDistance(lat1, lat2, lng1, lng2):
    R = 6371
    dLat = (lat2 - lat1) * (math.pi / 180)
    dLng = (lng2 - lng1) * (math.pi / 180)
    a = \
        math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(lat1 * (math.pi / 180)) * math.cos(lat2 * (math.pi / 180)) * \
        math.sin(dLng/2) * math.sin(dLng/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = R * c
    km_to_mile = 0.621371
    return d * km_to_mile

def cmpDistance(site1, site2):
    return site1['distance'] - site2['distance']

# sort sites based on distance from zip code
def sortSites(sites, zipcode):
    lat1, lng1 = getGeo(zipcode)
    for i in range(len(sites)):
        lat2 = sites[i]['geoCode']['latitude']
        lng2 = sites[i]['geoCode']['longitude']
        sites[i]['distance'] = findDistance(lat1, lat2, lng1, lng2)
    sites = sorted(sites, key=cmp_to_key(cmpDistance))
    return sites

# add time last updated and geolocation to each site
def addDateLocation(sites):
    for site in sites:
        site['lastUpdated'] = difftime.convertDate(site['updatedDate'])
        geo = {}
        geo['lat'] = site['geoCode']['latitude']
        geo['lng'] = site['geoCode']['longitude']
        site['location'] = geo

# check if zip code is a valid NJ zip code
@app.route('/checkzipdict', methods=['POST'])
def check_zipdict():
    zipcode = request.args.get('zipcode')
    if not zipcode in zipdict:
        response = make_response("notOK")
    else:
        response = make_response("OK")
    return response

# set cookies based on user login information
@app.route('/getuserinfo', methods=['POST'])
def get_post_javascript_data():
    user_info = json.loads(request.data, encoding='utf-8')
    database = Database()
    database.connect()
    db_info = database.get_user_info(user_info['id_token'])

    if db_info is None:
        response = make_response("new")
    else:
        response = make_response("old")

    database.disconnect()
    response.set_cookie('user_id', user_info['id_token'])
    response.set_cookie('user_email', user_info['email'])
    response.set_cookie('signed_in', 'True')

    if db_info is not None:
        response.set_cookie('user_name', db_info[1])
        response.set_cookie('user_last_name', db_info[2])
        response.set_cookie('notif_option', str(db_info[5]))
    else:
        response.set_cookie('user_name', user_info['first_name'])
        response.set_cookie('user_last_name', user_info['last_name'])
        response.set_cookie('notif_option', '3')

    return response

# add site to database as favorited
@app.route('/savesite/<site>', methods=['POST'])
def savesite(site):
    signed_in = request.cookies.get('signed_in')

    if signed_in:
        user_id = request.cookies.get('user_id')

        database = Database()
        database.connect()

        if database.get_user_info(user_id) is None:
            response = "NotInDatabase"
            return response
        if database.has_site_preference(user_id, site):
            database.delete_site_preference(user_id, site)
            response = "DeletedSite"
        else:
            database.insert_site_preference(user_id, site)
            response = "AddedSite"
        database.disconnect()
    
    else:
        response = "NotSignedIn"

    return response

# add list of sites to database as favorited
@app.route('/saveallsites', methods=['POST'])
def saveallsites():
    signed_in = request.cookies.get('signed_in')

    if signed_in:
        user_id = request.cookies.get('user_id')
        sites = json.loads(request.data, encoding='utf-8')
        database = Database()
        database.connect()

        if database.get_user_info(user_id) is None:
            response = "NotInDatabase"
            return response

        database.insert_site_preferences(user_id, sites)
        database.disconnect()
        response = "success"

    else:
        response = "NotSignedIn"

    return response

# remove list of sites as favorited from database
@app.route('/deleteallsites', methods=['POST'])
def deleteallsites():
    signed_in = request.cookies.get('signed_in')
    if signed_in:
        user_id = request.cookies.get('user_id')
        sites = json.loads(request.data, encoding='utf-8')

        database = Database()
        database.connect()

        if database.get_user_info(user_id) is None:
            response = "NotInDatabase"
            return response

        database.delete_site_preferences(user_id, sites)
        database.disconnect()
        response = "success"

    else:
        response = "NotSignedIn"

    return response

# add or update user information to the database
@app.route('/saveprofilechanges', methods=['GET'])
def saveprofilechanges():
    signed_in = request.cookies.get('signed_in')

    if not signed_in:
        response = make_response(render_template("profile.html", signedIn = signed_in))
        return response

    email = request.cookies.get('user_email')

    first_name = request.args.get('first_name')
    last_name = request.args.get('last_name')
    notifFav = request.args.get('notifFav') != None
    notifDaily = request.args.get('notifDaily') != None
    notifNone = request.args.get('notifNone') != None

    if notifFav and notifDaily:
        notif_on = True
        freq = 2
    elif notifFav:
        notif_on = True
        freq = 0
    elif notifDaily:
        notif_on = True
        freq = 1
    else:
        notif_on = False
        freq = 3

    database = Database()
    database.connect()
    courses = database.insert_user(request.cookies.get('user_id'), first_name, last_name, email, notif_on, freq)
    database.disconnect()
    response = make_response(render_template("profile.html", first_name=first_name, last_name=last_name, email=email, notif=str(freq)))
    response.set_cookie('user_name', first_name)
    response.set_cookie('user_last_name', last_name)
    response.set_cookie('notif_option', str(freq))

    return response

# delete user cookies, effectively signing them out
@app.route('/signout', methods=['POST'])
def signout():
    # if delete argument is string 'true', delete account before signing out
    delete = request.args.get('delete')

    if delete == 'true':
        deleteAccount()

    response = make_response('')
    response.delete_cookie('user_id')
    response.delete_cookie('user_name')
    response.delete_cookie('user_last_name')
    response.delete_cookie('user_email')
    response.delete_cookie('signed_in')
    return response

def deleteAccount():
    database = Database()
    database.connect()
    database.delete_user(request.cookies.get('user_id'))
    database.disconnect()

@app.errorhandler(404)
def page_not_found(e):
    signed_in = request.cookies.get('signed_in')
    response = make_response(render_template("404.html", signedIn=signed_in))
    return response, 404

# display page confirming that the account was deleted
@app.route('/accountdeleted')
def confirmDeletion():
    signed_in = request.cookies.get('signed_in')
    response = make_response(render_template("accountdeleted.html", signedIn=signed_in))
    return response