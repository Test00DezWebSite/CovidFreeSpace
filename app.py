from flask import Flask
from flask import render_template, request, redirect, url_for
from countryinfo import CountryInfo
from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from cfg import TWILLIO_SID, TWILLIO_TOKEN, TWILLIO_PHONE_NUMBER, SENDGRID_API_KEY


import json
import textwrap
import country_converter as coco
import pymongo
import datetime
import re
import csv
import math

app = Flask(__name__)

client = Client(TWILLIO_SID, TWILLIO_TOKEN)
sg = SendGridAPIClient(SENDGRID_API_KEY)
myclient = pymongo.MongoClient(
    "mongodb+srv://EpicN:wGLI0ccfbrU9ngfv@cluster0-8iybi.gcp.mongodb.net/test?retryWrites=true&w=majority")

mdb = myclient['covidfree']


# Define a function for
# for validating an Email


def check_email(email):

    regex = "^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$"

    if(re.search(regex, email)):
        return True
    else:
        return False


@app.route('/video-demo')
def video_demo():
    return redirect("https://www.loom.com/share/c5c73c2237284136902ecd43bb57063f")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/letter', methods=['POST'])
def letter():

    ref_url = request.referrer.replace('&address=invalid', '')
    ref_url = ref_url.replace('&address=valid', '')

    if "@" not in request.form['address']:

        if len(request.form['address'].strip()) != 10:
            return redirect(ref_url + "&address=invalid")

        address = "+1" + re.sub('[^0-9]', '', request.form['address']).strip()

        if request.form['letter_type'] == 0:
            text = """
        {0}, Somebody Wants You to be a #CovidChampion at {1}

        Somebody that cares about you wants you to stay safe from COVID-19. This novel virus has been a growing concern to everybody worldwide, and it has made our world less fun to live in :(

        #CovidFreeSpace again by practicing social distancing and #WorkFromHome if possible.
        Let's help make the world a

        You can learn more about the spread of COVID-19 in your area by clicking the link below. We at CovidFreeSpace have worked hard to analyze the numbers using data science magic, so that you don't need to do all of that by yourself!
            """.format(request.form['name'], request.form['location'])
        else:
            text = """
        {0}, Somebody Wants You to be a #CovidChampion at {1}

        #CovidChampion movement by allowing your workers to #WorkFromHome and practice social distancing..
        One of your customer or employer wants you to join the

        #CovidFreeSpace again by practicing social distancing and working from home if possible.
        Let's help make the world a

        You can learn more about the spread of COVID-19 in your area by clicking the link below. We at CovidFreeSpace have rigorously analyzed the numbers using data science methodologies, so that your business can make the best decision for the company and the community.
            """.format(request.form['name'], request.form['location'])

        client.messages.create(
            to=address,
            from_=TWILLIO_PHONE_NUMBER,
            body=textwrap.dedent("""

        {0}
        Link: {1}


            """.format(text, ref_url)))
    else:

        if not check_email(request.form['address']):
            return redirect(ref_url + "&address=invalid")

        if request.form['letter_type'] == "0":
            template_id = "d-8d2d90d873464e4dbe4072e159424a67"
        else:
            template_id = "d-f978a9411dfc4a09888aa3a5ff7babfe"

        data = {
            "template_id": template_id,
            "from": {
                "email": 'champion@covidfree.space',
                "name": 'Scott at CovidFreeSpace'
            },

            "personalizations": [
                {

                    "dynamic_template_data": {
                        "name": request.form['name'],
                        "location": request.form['location'],
                        "link": ref_url,
                    },
                    "to": [
                        {
                            "email": request.form['address'].strip(),
                        }
                    ]
                }
            ],

        }

        try:
            response = sg.client.mail.send.post(request_body=data)
        except Exception as e:
            return redirect(ref_url + "&address=invalid")
    return redirect(ref_url + "&address=valid")


@app.route('/info', methods=['GET'])
def info():
    if (request.args['location'] == ''):
        return redirect(url_for('index'))

    current_data_col = mdb['complete_df_safety_measures']
    hospital_data_col = mdb['Definitive_Healthcare__USA_Hospital_Beds']
    predicted_data_col = mdb['prediction']

    addressValid = ""

    if 'address' in request.args:
        if request.args['address'] == "valid":
            addressValid = "true"
        else:
            addressValid = "false"

    country = coco.convert(names=[request.args['location'].split(
        ',')[-1].strip()], to="name_short")
    iso2_country = coco.convert(names=[request.args['location'].split(
        ',')[-1].strip()], to="ISO2")
    city = request.args['location'].split(',')[0].strip()
    region = request.args['location'].split(',')[1].strip()
    try:
        current_confirmed_case = current_data_col.find_one(
            {"Region": region, "Date": "2020-03-27"})["Confirmed"]
    except:
        current_confirmed_case = current_data_col.find_one(
            {"CountryCode": iso2_country, "Date": "2020-03-27"})["Confirmed"]

    beds_available_city_data = hospital_data_col.find_one({"City": city})
    beds_available_state_data = hospital_data_col.find({"StateCode": region})

    state_bed_sum = 0
    state_util_ave = 0
    state_counter = 0

    beds_available_city = 0
    beds_available_state = 0
    beds_util_state = 0

    if iso2_country == "US":
        for x in beds_available_state_data:
            state_bed_sum += x["NumStaffedBeds"]
            state_util_ave = ((state_counter*state_util_ave) +
                              x["AveBedUtilizationRate"]) / (state_counter + 1)
            state_counter += 1

        beds_available_city = math.floor(beds_available_city_data["NumStaffedBeds"] * (
            1-beds_available_city_data["AveBedUtilizationRate"]) if beds_available_city_data else 0)
        beds_available_state = math.floor(state_bed_sum * (1-state_util_ave))

        if current_confirmed_case > beds_available_state:
            beds_util_state = math.floor(
                (current_confirmed_case + (state_bed_sum * state_util_ave)) / state_bed_sum * 100)
            beds_available_city = 0
            beds_available_state = 0
        else:
            beds_util_state = math.floor(
                (current_confirmed_case + (state_bed_sum * state_util_ave)) / state_bed_sum * 100)
            beds_available_state = beds_available_state - current_confirmed_case

    display_location = city + ", " + country

    if iso2_country == "US":
        predicted_case_data = int(predicted_data_col.find_one(
            {"date": {"$regex": '2020-04-24'}, "area": {"$regex": "CA$"}})["Confirmed"]) + current_confirmed_case
    else:
        predicted_case_data = int(predicted_data_col.find_one(
            {"date": {"$regex": '2020-04-24'}, "area": {"$regex": "{}".format(iso2_country)}})["Confirmed"]) + current_confirmed_case

    percentageData = round(
        current_confirmed_case / predicted_case_data * 100)

    return render_template('info.html', iso2_country=iso2_country, display_location=display_location, iso2Country=iso2_country, currentCase=current_confirmed_case, predictedCase=predicted_case_data, percentageData=percentageData, bedsAvailableCity=beds_available_city, bedsAvailableState=beds_available_state, bedsUtilState=beds_util_state, addressValid=addressValid)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
