from flask import Flask, request, session, render_template, jsonify, redirect, url_for
from flask_paginate import Pagination, get_page_parameter
import csv
import os
from enum import Enum
from flask import make_response

app = Flask(__name__)
app.secret_key = 'This is my Secret Key'

@app.route('/')
def index2():
    return render_template('index2.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/Reports')
def Reports():
    return render_template('Reports.html') 

@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/success', methods=['POST'])
def success():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        uploaded_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), uploaded_file.filename)
        uploaded_file.save(uploaded_file_path)
        csv_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Feeding Dashboard data.csv")

        with open(uploaded_file_path, 'r') as uploaded_csv_file:
            reader = csv.reader(uploaded_csv_file)
            rows = list(reader)

        if len(rows) <= 1:
            return "Uploaded CSV file is empty or contains only header"

        with open(csv_file_path, 'a', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(rows)

        return redirect(url_for('viewpatient'))

@app.route('/viewpatient', methods=['GET', 'POST'])
def viewpatient():
    referral_filter = request.form.get('referralFilter')
    search_query = request.form.get('searchQuery')
    datarows = []
    absolute_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(absolute_path, "Feeding Dashboard data.csv"), 'r') as csv_file:
        reader = csv.reader(csv_file)
        next(reader)  # Skip header
        for line in reader:
            if len(line) >= 18:  # Check if data has at least 18 elements
                data = [item.strip() if item.strip() != "" else "None" for item in line]
                ref = data[17]
                if ref == "0":
                    data[17] = "Not Referred"
                else:  
                    data[17] = "Need refferal"
                datarows.append(data)        
            
    if request.method == 'POST':
        if search_query:
            datarows = [row for row in datarows if search_query == row[0]]
        elif referral_filter:
            datarows = [row for row in datarows if referral_filter == 'All' or referral_filter == row[17]]
            
    per_page=10
    page = request.args.get('page', 1, type=int)
    pagination = Pagination(page=page, total=len(datarows), per_page=per_page)
    first_page = (page - 1) * per_page 
    last_page = first_page + per_page
    paginated_data = datarows[first_page:last_page]  # start from first page and should end with the last page

    return render_template('patient.html', datarows=paginated_data, pagination=pagination,referral_filter=referral_filter)


@app.route('/patientdetails', methods=['POST'])
def patientdetails():
    encounter_id = request.form.get('encounterId')  
    patient_data = None

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Feeding Dashboard data.csv"), 'r') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            if row['encounterId'] == encounter_id:
                patient_data = row
                break

    if patient_data:
        return render_template('patient_details.html', patient_data=patient_data)
    else:
        return "Patient details not found"

class ReferralStatus(Enum):
    NOT_REFERRED = '0'
    REFERRED = '1'

class PatientReferral:
    def __init__(self, encounterId, end_tidal_co2, feed_vol, feed_vol_adm, fio2, fio2_ratio, insp_time,
                 oxygen_flow_rate, peep, pip, resp_rate, sip, tidal_vol, tidal_vol_actual, tidal_vol_kg,
                 tidal_vol_spon, bmi, referral):
        self.encounterId = encounterId
        self.end_tidal_co2 = end_tidal_co2
        self.feed_vol = feed_vol
        self.feed_vol_adm = feed_vol_adm
        self.fio2 = fio2
        self.fio2_ratio = fio2_ratio
        self.insp_time = insp_time
        self.oxygen_flow_rate = oxygen_flow_rate
        self.peep = peep
        self.pip = pip
        self.resp_rate = resp_rate
        self.sip = sip
        self.tidal_vol = tidal_vol
        self.tidal_vol_actual = tidal_vol_actual
        self.tidal_vol_kg = tidal_vol_kg
        self.tidal_vol_spon = tidal_vol_spon
        self.bmi = bmi

        # Set referral status to a default value if the extracted value is not recognized
        try:
            self.referral = ReferralStatus(referral).name
        except ValueError:
            self.referral = ReferralStatus.NOT_REFERRED.name  # Set default value


def load_data_from_csv(file_path):
    data = []
    with open(file_path, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            # Convert all values to strings
            row = {key: str(value) for key, value in row.items()}
            data.append(PatientReferral(
                encounterId=row['encounterId'],
                end_tidal_co2=row['end_tidal_co2'],
                feed_vol=row['feed_vol'],
                feed_vol_adm=row['feed_vol_adm'],
                fio2=row['fio2'],
                fio2_ratio=row['fio2_ratio'],
                insp_time=row['insp_time'],
                oxygen_flow_rate=row['oxygen_flow_rate'],
                peep=row['peep'],
                pip=row['pip'],
                resp_rate=row['resp_rate'],
                sip=row['sip'],
                tidal_vol=row['tidal_vol'],
                tidal_vol_actual=row['tidal_vol_actual'],
                tidal_vol_kg=row['tidal_vol_kg'],
                tidal_vol_spon=row['tidal_vol_spon'],
                bmi=row['bmi'],
                referral=row['referral']
            ))
    return data

data = load_data_from_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Feeding Dashboard data.csv'))

@app.route('/api/patients', methods=['GET'])
def get_patient_referrals():
    json_data = [{'encounterId': patient.encounterId,
                  'end_tidal_co2': patient.end_tidal_co2,
                  'feed_vol': patient.feed_vol,
                  'feed_vol_adm': patient.feed_vol_adm,
                  'fio2': patient.fio2,
                  'fio2_ratio': patient.fio2_ratio,
                  'insp_time': patient.insp_time,
                  'oxygen_flow_rate': patient.oxygen_flow_rate,
                  'peep': patient.peep,
                  'pip': patient.pip,
                  'resp_rate': patient.resp_rate,
                  'sip': patient.sip,
                  'tidal_vol': patient.tidal_vol,
                  'tidal_vol_actual': patient.tidal_vol_actual,
                  'tidal_vol_kg': patient.tidal_vol_kg,
                  'tidal_vol_spon': patient.tidal_vol_spon,
                  'bmi': patient.bmi,
                  'referral': patient.referral}  for patient in data]

    response = make_response(jsonify({'patients': json_data}))
    response.headers['Access-Control-Allow-Origin'] = '*' 
    return response

if __name__ == '__main__':
    app.run(debug=True)
