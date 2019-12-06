#!/usr/bin/python3
                                                                                                                                                                                                
import Adafruit_DHT as DHT
from logger import Logger
from datetime import datetime
from time import time

class Sensor(object):
    def __init__(self, Logger, config):
        self.config = config
        self.Logger = Logger
    
        fail_Count = 0

        for count in range(3):
            # Пробуем опросить датчик                                                                                                                                                                                
            humidity, temperature = DHT.read(int(config['Sensor_Type']), config['GPIO_Pin'])
            
            # Если удалось опросить дачтик, то выходим
            if temperature is not None and humidity is not None:
                break
            # В другом случае увеличиваем счетчик фейлов на единичку
            else:
                fail_Count += 1

            # Если не удалось опросить датчик три раза
            if fail_Count == 3:    
                print('Cannot read data from sensor, check if pin and sesnor type is correct')
                self.Logger.write_To_Log('Cannot read data from sensor, check if pin and sensor type is correct')
                exit()

    def read_Data(self):                                                                                                                   
        # Объявляем переменные
        humidity = None
        temperature = None
        time_Start = time()

        # Опрашиваем датчик, пока не получим нормальные показания
        while humidity is None and temperature is None or (humidity >= 100 or (temperature >= 125 or temperature <= -40)):
            
            humidity, temperature = DHT.read(int(self.config['Sensor_Type']), self.config['GPIO_Pin'])
            
            # На всякий случай выход по таймауту
            if time() - time_Start > 3:
                break

        # Округляем
        temperature = f'{round(temperature, int(self.config["Round"]))}'
        humidity = f'{round(humidity, 0)}'.split('.')[0]

        return temperature, humidity

if __name__ == '__main__':
    # for standalone use
    from os.path import abspath, dirname 
    from json import load

    Path = str(dirname(abspath(__file__))).rsplit('/', 1)[0]

    standalone_Logger = Logger(Path, 'only_sensor.log')

    # Считываем конфигурационный файл
    try:
        with open(f'{Path}/configs/config.json', 'r') as config_File:
            config = load(config_File)
    except FileNotFoundError:
        print('Не найден конфигурационный файл, положите его в папку configs и перезапустите программу')
        standalone_Logger.write_To_Log('Не найден конфигурационный файл, положите его в папку configs и перезапустите программу')
        exit()

    sensor = Sensor(standalone_Logger, config['DHT'])

    temperature, humidity = sensor.read_Data()
    print(f'Температура = {temperature}' + '\u2103 ' + f'Влажность = {humidity} %')
    
