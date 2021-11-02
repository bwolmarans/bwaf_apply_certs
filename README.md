cat certs2.csv
bwaf_url,service_name,new_certificate,sni_certificate_list,sni_domain_list
https://waf.cudathon.com:8443,ssl1,sni2,sni3,sni3.wolmarans.com
https://waf.cudathon.com:8443,juiceshop,ffffff,sni1 sni2 sni3,sni1.1.com sni2.2.com sni3.3.com
https://waf.cudathon.com:8443,ssl2,sni1,,
(bwaf) ubuntu@brett-jumpbox:~/bwaf_apply_cert$ python3 bwaf_associate_certificate.py certs2.csv
BWAF Login Username:
BWAF Login Password:
row 1 of certs2.csv bwaf: https://waf.cudathon.com:8443 service: ssl1 existing cert: sni2 new cert: sni2 enable sni: Yes
row 2 of certs2.csv bwaf: https://waf.cudathon.com:8443 service: juiceshop existing cert: sni1 new cert: ffffff enable sni: Yes
    changing cert from sni1 to: ffffff sni: Yes sni certs: "sni1","sni2","sni3" sni domains: "sni1.1.com","sni2.2.com","sni3.3.com"
    Configuration updated
    new current certificate: ffffff
row 3 of certs2.csv bwaf: https://waf.cudathon.com:8443 service: ssl2 existing cert: ffffff new cert: sni1 enable sni: No
    changing cert from ffffff to: sni1 sni: No sni certs:  sni domains:
    Configuration updated
    new current certificate: sni1

writing out system state including deltas (if any) to file bwaf_changes_certs2.csv_2021_11_02_20_08_00.csv
(bwaf) ubuntu@brett-jumpbox:~/bwaf_apply_cert$ cat bwaf_changes_certs2.csv_2021_11_02_20_08_00.csv
bwaf_url,service_name,old_cert,new_cert,enable_sni,sni_cert_str,sni_domain_str
https://waf.cudathon.com:8443,ssl1,sni2,sni2,Yes,"sni3","sni3.wolmarans.com"
https://waf.cudathon.com:8443,juiceshop,sni1,ffffff,Yes,"sni1","sni2","sni3","sni1.1.com","sni2.2.com","sni3.3.com"
https://waf.cudathon.com:8443,ssl2,ffffff,sni1,No,, 
