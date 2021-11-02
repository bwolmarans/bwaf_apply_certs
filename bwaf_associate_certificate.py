#!/usr/bin/python
#
# filename: bwaf_associate_cert.py
# usage: python3 bwaf_associate_certificate.py <certificate csv file name>
#
# purpose: this script reads in a csv file, and then according to that csv file, it applies ssl certs to services as needed.
#          the certs must already exist on the waf.
#          the script then goes back and polls the waf to make sure the changes were applied.
#          this script writes out a timestampped fiel of changes it has made.
#
# author: bwolmarans@barracuda.com 11/1/2021
#
# important note: this is a utility script, please verify it works on test systems before using on production systems. 
#                 backing up your wafs before any major changes is always recommended.
#
# dependencies: python3 and several libraries that you can install with pip as shown below.
#
# 
# you will be prompted to enter username and password for the bwaf.
# the same username and password must exist on all bwafs.
#
# where certificate csv file format is:
# There is a header row: bwaf_url,service_name,new_cert
# for example here is a csv file with three services and the certificates to apply to them:
#
# bwaf_url,service_name,new_certificate,sni_certificate_list,sni_domain_list
# https://waf.cudathon.com:8443,ssl1,sni1,,
# https://waf.cudathon.com:8443,ssl2,sni2,sni3,sni3.wolmarans.com
# https://waf.cudathon.com:8443,juiceshop,qqqq,sni1 sni2 sni3,sni1.1.com sni2.2.com sni3.3.com
#
import sys
import requests
import json
import base64
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
sni_certs = []
sni_domains = []
csv_filename = str(sys.argv[1])
f = open(csv_filename,"r")
content = f.read()
rows=content.splitlines()
#rows=rows.split(",")
f.close
for row2 in rows[1:]:
    row = row2.split(",")
    waf_urls.append(row[0].strip())
    service_names.append(row[1].strip())
    new_certs.append(row[2].strip())
    sni_certs.append(row[3].strip())
    sni_domains.append(row[4].strip())
#curl -K token.txt -X PUT -k https://waf.cudathon.com:8443/restapi/v3.2/services/ssl1/ssl-security -H Content-Type:application/json -d '{"certificate":"sni1","sni-certificate":["sni2","sni3"],"domain":["sni2.wolmarans.com","sni3.wolmarans.com"]}'
#{"msg":"Configuration updated","token":"eyJldCI6IjE2MzU5MDQ4OTUiLCJwYXNzd29yZCI6IjI1Mzk5Y2E5ZmRlMWI2OTFmOTZkZWU0ODM1\nOGVmZmVjIiwidXNlciI6ImFkbWluIn0=\n","id":"ssl1"}
rr = 1
new_lines = []
for waf_url, service_name, new_cert, sni_cert, sni_domain in zip(waf_urls, service_names, new_certs, sni_certs, sni_domains):
    sni_cert = sni_cert.split()
    sni_domain = sni_domain.split()

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
    existing_sni = j['data'][service_name]['SSL Security']['enable-sni']
    new_existing_cert = existing_cert
    enable_sni = "No"
    #print("sni_cert: " + ' '.join(sni_cert) + " with length: " + str(len(sni_cert)))
    sni_domain_quoted = []
    sni_cert_quoted = []
    for sni in sni_cert:
        sni_cert_quoted.append('"' + sni + '"')
    for dom in sni_domain:
        sni_domain_quoted.append('"' + dom + '"')
    if (len(sni_cert)) > 0:
        enable_sni = "Yes"
    print("row " + str(rr) + " of " + csv_filename + " bwaf: " + waf_url + " service: " + service_name + " existing cert: " + existing_cert + " new cert: " + new_cert + " enable sni: " + enable_sni, end='')

    sni_cert_str  = ','.join([str(item) for item in sni_cert_quoted])
    sni_domain_str = ','.join([str(item) for item in sni_domain_quoted])
    #sni_cert_str = '[' + sni_cert_str + ']'
    #sni_domain_str = '[' + sni_domain_str + ']'
    if existing_cert != new_cert or existing_sni != enable_sni:
        print(" --> making changes:")    
        #"sni-certificate":["sni2","sni3"],"domain":["sni1.wolmarans.com","sni2.wolmarans.com","sni3.wolmarans.com"]}'
        #print("    changing cert from " + existing_cert + " to: " + new_cert + " sni: " + enable_sni + " sni certs: " + sni_cert_str + " sni domains: " + sni_domain_str )
        print("    " + service_name + ' {"enable-sni":"' + enable_sni + '","certificate":"' + new_cert + '","sni-certificate":[' + sni_cert_str + '],"domain":[' + sni_domain_str + ']}')
        r = requests.put(waf_rest_url + "services/" + service_name + "/ssl-security", headers=hhh, data='{"enable-sni":"' + enable_sni + '","certificate":"' + new_cert + '","sni-certificate":[' + sni_cert_str + '],"domain":[' + sni_domain_str + ']}', verify=False)
        t = r.text
        try:
            print("    " + json.loads(t)["msg"])
        except:
            print("     --> ERROR IN REST API CALL: " + t)
        r = requests.get(waf_rest_url + "services/" + service_name + "/ssl-security", headers=hhh, verify=False)
        j = r.json()
        new_existing_cert = j['data'][service_name]['SSL Security']['certificate']
        print("    new current certificate: " + new_existing_cert )
    else:
        print(" <--- no changes required")

    new_lines.append(waf_url + ',' + service_name + ',' + existing_cert + ',' + new_existing_cert + ',' + enable_sni + ',' + sni_cert_str + ',' + sni_domain_str)
    rr += 1


new_csv_file = 'bwaf_ssl_cert_service_association_' + csv_filename + "_" + str(datetime.now().strftime('%Y_%m_%d_%H_%M_%S')) + '.csv'
csv_file_full = new_csv_file
print("writing out changes to file " + csv_file_full)
f = open(csv_file_full, "w")
f.write("bwaf_url,service_name,old_cert,new_cert,enable_sni,sni_cert_str,sni_domain_str\n")
for new_line in new_lines:
    f.write(new_line + "\n")
f.close
