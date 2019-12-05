#!/usr/bin/python3

from fastapi import FastAPI
from uvicorn import run
from os.path import abspath, dirname 
from json import load
import socket 
from socket import gethostname, gethostbyname

from logger import Logger
from sensor import Sensor

Path = str((str(dirname(abspath(__file__)))).rsplit("/", 1)[0])

standalone_Logger = Logger(Path, 'sensor.log')

with open(f'{Path}/configs/config.json', 'r') as config_File:
    config = load(config_File)

app = FastAPI()
sensor = Sensor(standalone_Logger, config['DHT'])

@app.get("/")
def read_root():
    temp, hum = sensor.read_Data()

    return f'Температура - {temp} ' + '\u2103 ' + f' Влажность - {hum} %'

if __name__ == '__main__':
    run("simple_webserver:app", host = gethostbyname(gethostname()) , port = 1435, log_level = "info", reload = True)
