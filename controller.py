import re
import urllib.parse
import json
import subprocess
from model import SQLIModel
from keras.models import load_model
from typing import List

class Controller:
    
    def __init__(self):
        self.Obj = SQLIModel()
        self.model = load_model('sqli_model.h5')
    
    def parse_get_request(self, line):
        match = re.search(r'^(\S+) \S+ \S+ \[(.*?)\] "(.*?) (\S+) \S+" \d+ \d+ "(.*?)" "(.*?)"$', line)
        if match:
            request_method = match.group(3)
            if request_method == 'GET':
                ip_address = match.group(1)
                timestamp = match.group(2)
                request_url = match.group(4)
                payload = match.group(6)
                # check if request_url contains parameters
                if '?' in request_url:
                    payload = request_url.split('&')
                    for i in range(len(payload)):
                        payload[i] = urllib.parse.unquote(payload[i])
                        #split on first '='
                        if '=' in payload[i]:
                            payload[i] = payload[i].split('=', 1)[1]
                    parsed_output = {'ip_address': ip_address, 'timestamp': timestamp, 'request_method': request_method, 'request_url': request_url, 'payload': payload}
                else:
                    parsed_output = {'ip_address': ip_address, 'timestamp': timestamp, 'request_method': request_method, 'request_url': request_url, 'payload': None}
                
                return parsed_output


    def parse_post_request(self, line):
        match = re.search(r'^(\S+) \S+ \S+ \[(.*?)\] "(.*?) (\S+) \S+" \d+ \d+ "(.*?)" "(.*?)"$', line)
        if match:
            request_method = match.group(3)
            if request_method == 'POST':
                ip_address = match.group(1)
                timestamp = match.group(2)
                request_url = match.group(4)
                if line.strip().endswith('}'):
                    payload = json.loads(line[line.find('{'):])
                else:
                    payload = None
                parsed_output = {'ip_address': ip_address, 'timestamp': timestamp, 'request_method': request_method, 'request_url': request_url, 'payload': payload}
                return parsed_output
    
    def check_alert(self, log):
        sentences = log.get('payload')
        if sentences and sentences != 'null' and self.Obj.is_sqli(sentences[0], self.model, 'sqli_model.h5', 'tokenizer.pickle'):
            return log
        
            
    def run_docker_container(self, container_name, local_dir, docker_dir):
        self.logs_maintenance(local_dir)
        command = f"docker run --rm -it -p 80:80 -v {local_dir}:{docker_dir} {container_name}"
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()
        stdout, stderr = process.communicate()
        if stderr:
            print(f"Error running Docker container: {stderr.decode('utf-8')}")
            return False
        else:
            print(f"Docker container {container_name} is running and {local_dir} is mounted to {docker_dir}")
            return True
        
    
    def logs_maintenance(self, local_dir):
        #check if file exists
        try:
            with open(local_dir, 'r') as f:
                pass
        except FileNotFoundError:
            print(f"File {local_dir} does not exist. Creating file...")
            with open(local_dir, 'w') as f:
                pass
