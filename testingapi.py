
import os
from sys import argv, stderr, exit
from typing import Tuple, List
import requests, json


def main(argv):
            
    row = "acd92d86-3b43-4dc1-94d2-ded3f5c9bd8b"
           
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    payload = {
                "draw":1,
                "columns":[],
                "order":[],
                "start":0,
                "length":2,
                "search":{
                    "value":"",
                    "regex":False
                }
    }
    url = "https://c19vaccinelocatornj.info/api/v1/vaccine/locations/" + row
    response = requests.request("GET", url, data = json.dumps(payload), headers=headers).json()
    print(response)

    # url = "https://c19vaccinelocatornj.info/api/v1/vaccine/locations/page"
    # headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    # payload = {
    #    "draw":1,
    #    "columns":[],
    #    "order":[],
    #    "start":0,
    #    "length":1,
    #    "search":{
    #       "value":"Atlantic",
    #       "regex":False
    #    }
    # }
    # response = requests.request("POST", url, data = json.dumps(payload), headers=headers).json()
    # print(response)
    

  


if __name__ == '__main__':
    main(argv)