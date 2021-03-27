from abc import ABCMeta
from abc import abstractmethod

import requests
from requests import ConnectTimeout
from requests import ConnectionError

__author__ = 'antonior'
import sys
from core_utils.sysUtils import make_dir
import os
from time import gmtime, strftime
from datetime import datetime
import json
import logging


class Configuration:
    def __init__(self, conf):
        self.path_to_out = conf["sRNAtoolboxSODataPath"]
        self.path_to_makeenrichmentanalysis = os.path.join(conf["exec"], "sRNAfuncTerms.jar")
        self.path_to_makede = os.path.join(conf["exec"],  "sRNAde.jar")
        self.path_to_srnabech = os.path.join(conf["exec"], "sRNAbench.jar")
        self.path_to_srnablast = os.path.join(conf["exec"], "sRNAblast.jar")
        self.path_to_srnajbrowser = os.path.join(conf["exec"], "sRNAjBrowser.jar")
        self.path_to_srnajbrowserde = os.path.join(conf["exec"], "sRNAjBrowserDE.jar")
        self.path_to_mirnatarget = os.path.join(conf["exec"], "miRNAconsTargets.jar")
        self.path_to_srnagfree = os.path.join(conf["exec"], "miRNAgFree.jar")
        self.path_to_helpers = os.path.join(conf["exec"], "sRNAhelper.jar")
        self.taxon_file = conf["tax"]
        self.trna_file = conf["tRNA"]
        self.rnac_file = conf["RNAcentral"]
        self.media = conf["media"]
        self.mirnaconstargets_plants = os.path.join(conf["exec"], "miRNAconsTargets_plants.py")
        self.path_to_chmod = os.path.join(conf["exec"], "chmod.jar")
        self.path_to_mirg = os.path.join(conf["exec"], "miRgFree.jar")



class Pipeline:
    __metaclass__ = ABCMeta

    def __init__(self, pipeline_key, job_name, outdir, tool, parameters, mode='prod'):
        self.parameters = parameters
        self.tool = tool
        self.outdir = outdir
        make_dir(self.outdir)
        self.table_log = "progress_jobstatus"
        self.error_logger = open(os.path.join(self.outdir, "error_logFile.txt"), "w")
        # self.logger = file(os.path.join(self.outdir, "logFile.txt"), "w")

        # Pipeline key
        self.pipeline_key = pipeline_key

        # Open logDB connection
        self.job_name = job_name
        # self.api_server = ':8000'
        # self.api_server = 'https://arn.ugr.es/srnatoolbox/'
        self.api_server = 'http://arn.ugr.es:8012/srnatoolbox/'
        #172.17.0.4
        self.api_path = os.path.join(self.api_server, 'jobstatus', 'api')
        self.api_path_key = os.path.join(self.api_path, self.pipeline_key)
        self.api_path_add_status = os.path.join(self.api_path, self.pipeline_key, 'add_status')
        conf = json.load(open(os.path.join(os.path.dirname(__file__), 'configuration', mode, 'conf_core.json')))
        self.configuration = Configuration(conf)

    # def initialize_pipeline_status(self):
    #
    #     started_info = (strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: Analysis starts")
    #     payload = {
    #         "job_status": "Running",
    #         "command_line": " ".join(sys.argv),
    #         "parameters": self.parameters,
    #         "outdir": self.outdir
    #     }
    #     try:
    #         requests.patch(self.api_path_key, json=payload, timeout=10)
    #         self.actualize_pipeline_progress(new_step=started_info)
    #     except ConnectionError or ConnectTimeout:
    #         logging.error('Connection error')

    def initialize_pipeline_status(self):

        started_info = (strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " INFO: Analysis starts")
        payload = {
            "job_status": "Running",
            "command_line": " ".join(sys.argv),
            "parameters": self.parameters,
            "outdir": self.outdir
        }
        r=requests.patch(self.api_path_key, json=payload, timeout=10)
        self.actualize_pipeline_progress(new_step=started_info)
        print("init")


    def actualize_pipeline_progress(self, new_step):
        payload = {
            "status_progress": new_step
        }
        try:
            requests.put(self.api_path_add_status, json=payload)
            if "ERROR" in new_step:
                self.change_pipeline_status("Finished with Errors")
        except ConnectionError or ConnectTimeout:
            logging.error('Connection error')

    def change_pipeline_status(self, new_status):
        payload = {
            "job_status": new_status,
        }
        try:
            requests.patch(self.api_path_key, json=payload)
        except ConnectionError or ConnectTimeout:
            logging.error('Connection error')

    def set_finish_time(self):
        payload= {
            "finish_time": str(datetime.now())
        }
        try:
            requests.patch(self.api_path_key, json=payload)
        except ConnectionError or ConnectTimeout:
            logging.error('Connection error')

    def set_java_command_line(self, line):
        payload = {"java_commad_line": line}
        try:
            requests.patch(self.api_path_key, json=payload)
        except ConnectionError or ConnectTimeout:
            logging.error('Connection error')

    def raw_update(self, payload):
        try:
            requests.patch(self.api_path_key, json=payload)
        except ConnectionError or ConnectTimeout:
            logging.error('Connection error')

    @abstractmethod
    def run(self):
        pass


