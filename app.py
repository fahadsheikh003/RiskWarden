from flask import Flask, jsonify
from config import LOCAL_DIR, DOCKER_DIR, CONTAINER_NAME
from controller import Controller
import threading
from time import sleep
import os
import subprocess
import time
from typing import List
from flask import jsonify

app = Flask(__name__)
cont = Controller()
logs = []

def read_alerts_from_file():
    global logs
    while True:
        with subprocess.Popen(['tail', '-f', LOCAL_DIR], stdout=subprocess.PIPE, bufsize=1, universal_newlines=True) as proc:
            for line in proc.stdout:
                line = line.rstrip('\n')
                parsed_output = cont.parse_get_request(line)
                if not parsed_output:
                    parsed_output = cont.parse_post_request(line)

                if parsed_output:
                    logs.append(parsed_output)
                    alert = cont.check_alert(parsed_output)
                    if alert:
                        logs.append(alert)
                        # send_alert(alert) # send the alert to an external system or log it.
        time.sleep(1)

@app.route('/')
def index():
    return "RiskWarden is running"

@app.route('/logs')
def read_logs():
    with open(LOCAL_DIR, 'r') as f:
        raw_logs = f.readlines()
        logs = []
        for line in raw_logs:
            parsed_output = cont.parse_get_request(line)
            if parsed_output:
                logs.append(parsed_output)
            else:
                parsed_output = cont.parse_post_request(line)
                if parsed_output:
                    logs.append(parsed_output)
        return jsonify(logs)

@app.route('/sqli')
def read_alerts():
    logs = []
    with open(LOCAL_DIR, 'r') as f:
        raw_logs = f.readlines()
        for line in raw_logs:
            parsed_output = cont.parse_get_request(line)
            if parsed_output:
                logs.append(parsed_output)
            else:
                parsed_output = cont.parse_post_request(line)
                if parsed_output:
                    logs.append(parsed_output)
    alerts = cont.check_alerts(logs)
    return jsonify(alerts)

@app.route('/alerts')
def read_alerts_from_file() -> List[dict]:
    global logs
    while True:
        with subprocess.Popen(['tail', '-f', LOCAL_DIR], stdout=subprocess.PIPE, bufsize=1, universal_newlines=True) as proc:
            for line in proc.stdout:
                line = line.rstrip('\n')
                parsed_output = cont.parse_get_request(line)
                if not parsed_output:
                    parsed_output = cont.parse_post_request(line)
                    
                if parsed_output:
                    logs.append(parsed_output)
                    alert = cont.check_alert(parsed_output)
                    if alert:
                        logs.insert(0, alert)
                        # send_alert(alert) # send the alert to an external system or log it.
                sleep(1)
                return jsonify(logs)
            proc.stdout.close()


if __name__ == '__main__':
    #use forked process to run docker container
    docker_process = threading.Thread(target=cont.run_docker_container, args=(CONTAINER_NAME, LOCAL_DIR, DOCKER_DIR))
    docker_process.start()

    flask_process = threading.Thread(target=app.run)
    flask_process.start()
    
    docker_process.join()
    flask_process.join()
