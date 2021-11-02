#!/usr/bin/python
#
# filename: bwaf_associate_cert.py
# author: bwolmarans@barracuda.com
# note: you may wish to back up your systems before using this script.
#       this is a utility script, please verify it works on test systems before using on production systems
#
# dependencies: python3 and several libraries that you can install with pip as shown below.
#
# usage: python3 bwaf_associate_certificate.py <certificate csv file name>
# 
# you will be prompted to enter username and password for the bwaf.
# the same username and password must exist on all bwafs.
#
# where certificate csv file format is each row has three columns: bwaf url, service name, and certificate to apply.  
# There is a header row: bwaf_url,service_name,new_cert
# for example here is a csv file with three services and the certificates to apply to them:
#
# bwaf_url,service_name,new_cert
# https://waf.cudathon.com:8443,juiceshop,aaaaa
# https://waf.cudathon.com:8443,ssl1,ffffff
# https://waf.cudathon.com:8443,ssl2,qqqq
#
import sys
import requests
import json
import base64
import csv
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from getpass import getpass
from datetime import datetime
import os

# Working curl example: 
# curl -K token.txt -X PUT -k https://waf.cudathon.com:8443/restapi/v3.2/services/juiceshop/ssl-security -H Content-Type:application/json -d '{"certificate":"qqqq"}'
# {"id":"juiceshop","token":"eyJ1c2VyIjoiYWRtaW4iLCJldCI6IjE2MzU3NTgxMDYiLCJwYXNzd29yZCI6IjU2YWRiNWM3MTMw\nNjcxYTgzZDE4M2U2NmE2YjQ5NGM4In0=\n","msg":"Configuration updated"}
#
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

waf_login_username = getpass("BWAF Login Username:")
waf_login_password = getpass("BWAF Login Password:")
waf_urls = []
service_names = []
new_certs = []
csv_filename = str(sys.argv[1])
with open(csv_filename, newline='') as csvfile:
    rows = csv.reader(csvfile, delimiter=',')
    next(rows)
    for row in rows:
        #print(row)
        waf_urls.append(row[0].strip())
        service_names.append(row[1].strip())
        new_certs.append(row[2].strip())
        
rr = 1
new_lines = []
for waf_url, service_name, new_cert in zip(waf_urls, service_names, new_certs):
    waf_rest_url=waf_url + "/restapi/v3.2/"
    hhh = { 'Content-Type': 'application/json'}
    post_data = json.dumps({ 'username': waf_login_username, 'password': waf_login_password })
    r = requests.post(waf_rest_url + 'login', headers=hhh, data=post_data, verify=False )
    token = json.loads(r.text)['token']
    token = token.encode('ascii')
    b64token = base64.b64encode(token)
    b64token = b64token.decode('ascii')
    hhh={"Content-Type": "application/json", "Authorization": "Basic " + b64token}
    r = requests.get(waf_rest_url + "services/" + service_name + "/ssl-security", headers=hhh, verify=False)
    j = r.json()
    existing_cert = j['data'][service_name]['SSL Security']['certificate']
    print("Processing row " + str(rr) + " from file " + csv_filename + " bwaf: " + waf_url + " service: " + service_name + " existing cert: " + existing_cert + " new cert: " + new_cert)
    if existing_cert != new_cert:
        print("    changing certificate from " + existing_cert + " to: " + new_cert)
        r = requests.put(waf_rest_url + "services/" + service_name + "/ssl-security", headers=hhh, data='{"certificate":"' + new_cert + '"}', verify=False)
        t = r.text
        print("    " + json.loads(t)['msg'])
        r = requests.get(waf_rest_url + "services/" + service_name + "/ssl-security", headers=hhh, verify=False)
        j = r.json()
        new_existing_cert = j['data'][service_name]['SSL Security']['certificate']
        print("    new current certificate: " + new_existing_cert )

    new_lines.append(waf_url + ',' + service_name + ',' + existing_cert + ',' + new_existing_cert)
    rr += 1

new_csv_file = 'bwaf_ssl_cert_service_association_' + csv_filename + "_" + str(datetime.now().strftime('%Y_%m_%d_%H_%M_%S')) + '.csv'
csv_file_full = new_csv_file
print("writing out changes to file " + csv_file_full)
f = open(csv_file_full, "w")
f.write("bwaf_url,service_name,old_cert,new_cert\n")
for new_line in new_lines:
    f.write(new_line + "\n")
f.close
