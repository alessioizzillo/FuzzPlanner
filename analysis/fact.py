import sys
import requests
import json
from tqdm import tqdm
from time import sleep

FACT_URL="http://192.168.30.177:5000"

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 fact.py <firmware_name> <executable_json_file> <fact_uid>")
        exit(1)

    firmware_name = sys.argv[1]
    executable_json_file = sys.argv[2]
    fact_uid = sys.argv[3]

    r = requests.get("%s/rest/firmware/%s"%(FACT_URL, fact_uid))
    firmware_json = r.json()

    with open(executable_json_file) as file:
        executable_files = json.load(file)
    executable_files = {item['id']: {key: item[key] for key in item if key != 'id'} for item in executable_files}

    for exec_id in executable_files:
        executable_files[exec_id]["cves"] = []
        executable_files[exec_id]["cwes"] = []

    included_files_uid_list = firmware_json["firmware"]["meta_data"]["included_files"]

    for obj_uid in tqdm(list(included_files_uid_list)):
        r = requests.get("%s/rest/file_object/%s"%(FACT_URL, obj_uid))
        obj_json = r.json()
        if "file_object" in obj_json:
            exec_id = obj_json["file_object"]["meta_data"]["hid"]

            if exec_id in executable_files:
                if "full" in obj_json["file_object"]["analysis"]["cwe_checker"]:
                    cwe_keys = obj_json["file_object"]["analysis"]["cwe_checker"]["full"].keys()
                    cwe_list = []
                    for key in cwe_keys:
                        d = obj_json["file_object"]["analysis"]["cwe_checker"]["full"][key]
                        cwe = {"id" : key, "plugin_version" : d["plugin_version"], "warnings" : d["warnings"]}
                        cwe_list.append(cwe)

                    executable_files[exec_id]["cwes"] = cwe_list

                if "cve_results" in obj_json["file_object"]["analysis"]["cve_lookup"]:
                    cve_keys = list(obj_json["file_object"]["analysis"]["cve_lookup"]["cve_results"].keys())
                    cve_list = []
                    if cve_keys:
                        cve_key_list = list(obj_json["file_object"]["analysis"]["cve_lookup"]["cve_results"][cve_keys[0]].keys())
                
                        for cve in cve_key_list:
                            while True:
                                r = requests.get("https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=%s"%(cve))
                                try:
                                    cve_json = r.json()
                                except:
                                    sleep(5)
                                else:
                                    break

                            print(cve)
                            cve_result = cve_json["vulnerabilities"][0]["cve"]
                            cve_list.append(cve_result)
                    
                    executable_files[exec_id]["cves"] = cve_list


    
    executable_files_list = []
    for ex in executable_files:
        executable_files_list.append({"id" : ex, "type" : executable_files[ex]["type"], "interpreter" : executable_files[ex]["interpreter"], "is_proprietary" : executable_files[ex]["is_proprietary"], "symlink_target" : executable_files[ex]["symlink_target"], "cves" : executable_files[ex]["cves"], "cwes" : executable_files[ex]["cwes"]})

    with open(executable_json_file, "w") as f:
        f.write(json.dumps(executable_files_list, indent=4))