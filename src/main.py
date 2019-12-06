#!/usr/bin/python3

from sensor import Sensor
from file import File
from mail import Mail
from spreadsheet import Spreadsheet
from logger import Logger

from datetime import datetime, timedelta
from json import load
from time import sleep
from os.path import dirname, abspath
from socket import create_connection

# Функция, для проверки наличия интернет-соединения
def is_Connected(site_For_Check):
    try:
        create_connection((str(site_For_Check), 80))
        return True
    except OSError:
        return False

# Path
Path = str(dirname(abspath(__file__))).rsplit('/', 1)[0] + '/'
path_To_Temperature_Log = 'data/temperature_log.txt'

# Создаем экземпляр класса Logger
Logger = Logger(Path, 'log.log')

# Инициализируем переменные
last_Time_Send, last_Arch_Time = datetime.now(), datetime.now()

# Флаговые переменные, указывающие на состояние коннекта к mail/spreadsheet
is_Connected_To_Mail = False
is_Connected_To_Spreadsheet = False

# Первая ли ты, попытка законнектится?
first_Try_To_Connect = True

# Считываем конфигурационный файл
try:
    with open(f'{Path}configs/config.json', 'r') as config_File:
        cfg = load(config_File)
except FileNotFoundError:
    print('Не найден конфигурационный файл, положите его в папку configs и перезапустите программу')
    Logger.write_To_Log('Не найден конфигурационный файл, положите его в папку configs и перезапустите программу')
    exit()

# Создаем экземляры классов
log_File = File(Path, path_To_Temperature_Log, Logger)
sensor = Sensor(Logger, cfg.get('DHT'))
mail = Mail(log_File, Logger, cfg.get('email'))
spr_sheet = Spreadsheet(Logger, Path, path_To_Temperature_Log, cfg.get('Spreadsheet'))

# Если есть инет, пробуем законнектится
if is_Connected(cfg['Main']['Site_for_check']) == True:
    # Инициализруем почту, если включена отправка почты
    if cfg['email']['Mail_status'].lower() == 'on':
        mail.login()
        is_Connected_To_Mail = True

    # Инициализруем гугл докс, если они включены в конфиге
    if cfg['Spreadsheet']['Status'].lower() == 'on':
        # Логинимся и открываем таблицу
        spr_sheet.login()
        spr_sheet.open_Spreadsheet()
        
        # Если нужно, отчищаем гугл таблицу при старте
        if cfg['Spreadsheet']['Clear spreadsheet on start'].lower() == 'on':
            spr_sheet.clear_Spreadsheet()

        # Создаем описание колонок
        spr_sheet.create_Cols_Description()

        # Устанавливаем флаг коннекта к Spreadsheet API
        is_Connected_To_Spreadsheet = True

    # Записываем время коннекта к серверам
    last_Auth_Refresh_Time = datetime.now()
    
    first_Try_To_Connect = False

# Loop
while True:
    try:
        # Снимаем показания и записываем в файл
        temperature, humidity = sensor.read_Data()
        
        print(f'{datetime.now()} Температура = {temperature}' + '\u2103 ' + f'Влажность = {humidity} %')
        log_File.write_Data(temperature, humidity)

        # Если включена отправка на почту / в таблицу
        if is_Connected(cfg['Main']['Site_for_check']) == False and (cfg['email']['Mail_status'].lower() == 'on' or cfg['Spreadsheet']['Status'].lower() == 'on'):
            # Ставим переменные в ложь для того, чтобы перелогиниться после того как появится интернет
            is_Connected_To_Mail, is_Connected_To_Spreadsheet = False, False

            print('Connection lost, cannot sell mail/upload data to spreadsheet, retry on next cycle')
            Logger.write_To_Log('Connection lost, cannot sell mail/upload data to spreadsheet, retry on next cycle') 
        
        # Если не смогли залогиниться на старте или нужно перелогиниться после пропажи интернета
        if is_Connected(cfg['Main']['Site_for_check']) is True:
            if cfg['email']['Mail_status'].lower() == 'on' and is_Connected_To_Mail is False:
                mail.login()

                is_Connected_To_Mail, last_Auth_Refresh_Time = True, datetime.now()
                
            if cfg['Spreadsheet']['Status'].lower() == 'on' and is_Connected_To_Spreadsheet is False:
                spr_sheet.login()
                spr_sheet.open_Spreadsheet()

                # Если это первая попытка логина при неудачном логине на старте
                if cfg['Spreadsheet']['Clear spreadsheet on start'].lower() == 'on' and first_Try_To_Connect is True:
                    spr_sheet.clear_Spreadsheet()
                    
                    # Создаем описание колонок
                    spr_sheet.create_Cols_Description()
                
                is_Connected_To_Spreadsheet, first_Try_To_Connect = True, False

                last_Auth_Refresh_Time = datetime.now()

        # Перелогиниваемся каждый час, иначе будем получать connection timed out
        if is_Connected(cfg['Main']['Site_for_check']) == True and datetime.now() >= last_Auth_Refresh_Time + timedelta(hours = 1):
            
            if cfg['email']['Mail_status'].lower() == 'on':
                mail.login()
                last_Auth_Refresh_Time = datetime.now()

            if cfg['Spreadsheet']['Status'].lower() == 'on':
                spr_sheet.refresh_Token()
                last_Auth_Refresh_Time = datetime.now()
        
        # Заливаем в таблицу построчно
        if cfg['Spreadsheet']['Status'].lower() == 'on' and cfg['Spreadsheet']['Send_by_str'].lower() == 'on':
            spr_sheet.send_Str_To_Spreadsheet(temperature, humidity)
            print('Str sended to Spreadsheets')

        # Проверяем соединение с интернетом и пришло ли время для отправки
        if is_Connected(cfg['Main']['Site_for_check']) == True:
            if datetime.now() >= last_Time_Send + timedelta(hours = int((cfg['Main']['Period_before_send'].split(','))[0]), minutes = int((cfg['Main']['Period_before_send'].split(','))[1])):

                # Отправляем на почту при необходимости                                     
                if cfg['email']['Mail_status'].lower() == 'on':
                    mail.send_File('Температура')
                    print('Send on', last_Time_Send)

                # Заливаем в таблицу файл, если построчная отправка выключена                                                         
                if cfg['Spreadsheet']['Status'].lower() == 'on' and cfg['Spreadsheet']['Send_by_str'].lower() == 'off':
                    spr_sheet.send_To_Spreadsheet()
                    print('File sended to Spreadsheets')

                # Если выбрано удаление, то просто отчищаем файл после каждой отправки
                if cfg['Main']['Delete after sending'].lower() == 'on' and (cfg['Spreadsheet']['Status'].lower() == 'on' or cfg['email']['Mail_status'].lower() == 'on'):
                    log_File.clear_File()

                # Записываем время отправки                                                        
                last_Time_Send = datetime.now()

            else:
                print('Dont need send anything')

        # Если включена архивация, то сжимаем файл по прошествию n-ого количества времени
        if cfg['Main']['Archive'].lower() == 'on' and datetime.now() >= last_Arch_Time + timedelta(hours = int((cfg['Main']['Period_before_arch'].split(','))[0]), minutes = int((cfg['Main']['Period_before_arch'].split(','))[1])):
            # Записываем время архивации
            last_Arch_Time = datetime.now()

            # Архивируем с помощью brotli и отчищаем сам файл после
            log_File.zip_File('data/')            
            log_File.clear_File()

            print('Ziped on', last_Arch_Time)
            
        # Ждем сколько-то и начинаем заново
        sleep(int(cfg['DHT']['Period']))

    # Дабы не ловить кучу errorов при выходе
    except KeyboardInterrupt:
        exit()
