#!/usr/bin/python3
                                                                                                                                                                                                
import Adafruit_DHT as DHT
from logger import Logger
from time import time

class Sensor(object):
    def __init__(self, Logger, config):
        self.Logger = Logger

        self.sensor = config['Sensor_Type']
        self.pin = config['GPIO_Pin']
        self.round = config['Round']
    
        for count in range(3):
            # Пробуем опросить датчик                                                                                                                                                                                
            humidity, temperature = DHT.read(self.sensor, self.pin)
            
            # Если удалось опросить дачтик, то выходим
            if temperature is not None and humidity is not None:
                break

            # Если не удалось опросить датчик три раза
            if count == 2:    
                self.Logger.critical('Cannot read data from sensor, check if pin and sensor type is correct')
                exit()

    def read(self):        
        """Функция для получения данных с датчика"""

        # Объявляем переменные
        humidity = None
        temperature = None
        time_Start = time()

        # Опрашиваем датчик, пока не получим нормальные показания
        while humidity is None and temperature is None or (humidity >= 100 or (temperature >= 125 or temperature <= -40)):
            humidity, temperature = DHT.read(self.sensor, self.pin)
            
            # На всякий случай выход по таймауту
            if time() - time_Start > 3:
                break

        # Округляем
        temperature = str(round(temperature, self.round))
        humidity = str(round(humidity, 0)).split('.')[0]

        return temperature, humidity

if __name__ == '__main__':
    # for standalone use
    from os.path import abspath, dirname 
    from json import load

    Path = str(dirname(abspath(__file__))).rsplit('/', 1)[0]
    logger = Logger.get()

    # Считываем конфигурационный файл
    try:
        with open(f'{Path}/configs/config.json', 'r') as config_File:
            config = load(config_File)
    except FileNotFoundError:
        logger.write_To_Log('Не найден конфигурационный файл, положите его в папку configs и перезапустите программу')
        exit(1)

    sensor = Sensor(logger, config['DHT'])

    temperature, humidity = sensor.read()
    print(f'Температура = {temperature}' + '\u2103 ' + f'Влажность = {humidity} %')
    
