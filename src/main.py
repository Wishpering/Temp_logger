#!/usr/bin/python3

from datetime import datetime, timedelta
from json import load
from time import sleep
from os.path import dirname, abspath
from socket import create_connection

from sensor import Sensor
from file import File
from mail import Mail
from spreadsheet import Spreadsheet
from logger import Logger

# Функция, для проверки наличия интернет-соединения
def is_Connected(site_For_Check):
    try:
        create_connection((str(site_For_Check), 80))
        return True
    except OSError:
        return False

# Path
Path = f'{dirname(abspath(__file__))}'.rsplit('/', 1)[0]
path_To_Temperature_Log = '/data/temperature_log.txt'

# Создаем экземпляр класса Logger
logger = Logger.get()

# Инициализируем переменные
last_Time_Send, last_Arch_Time = datetime.now(), datetime.now()
# Переменные, указывающие на состояние коннекта к mail/spreadsheet
is_Connected_To_Mail = False
is_Connected_To_Spreadsheet = False
# Первая ли ты, попытка законнектится?
first_Try_To_Connect = True

# Считываем конфигурационный файл
try:
    with open(f'{Path}/configs/config.json', 'r') as config_File:
        cfg = load(config_File)
except FileNotFoundError:
    logger.critical('Не найден конфигурационный файл, положите его в папку configs и перезапустите программу')
    exit(1)

sleep_Period = cfg['DHT']['Period']
site_For_Check = cfg['Main']['Site_for_check'].lower()
mail_Status = cfg['email']['Mail_status']
spreadsheet_Status = cfg['Spreadsheet']['Status']
clear_spreadsheet_on_start = cfg['Spreadsheet']['Clear spreadsheet on start']
send_by_str = cfg['Spreadsheet']['Send_by_str']
period_before_send = cfg['Main']['Period_before_send'].split(',')
period_before_archive = cfg['Main']['Period_before_arch'].split(',')

# Создаем экземляры классов
temp_logfile = File(
    Path, 
    path_To_Temperature_Log, 
    logger
)
sensor = Sensor(
    logger, 
    cfg.get('DHT')
)
mail = Mail(
    temp_logfile, logger, 
    cfg.get('email')
)
spr_sheet = Spreadsheet(
    logger, Path, 
    path_To_Temperature_Log, 
    cfg.get('Spreadsheet')
)

# Если есть инет, пробуем законнектится
if is_Connected(site_For_Check) == True:
    # Инициализруем почту, если включена отправка почты
    if mail_Status is True:
        mail.login()
        is_Connected_To_Mail = True

    # Инициализруем гугл докс, если они включены в конфиге
    if spreadsheet_Status is True:
        # Логинимся и открываем таблицу
        spr_sheet.login()
        spr_sheet.open()
        
        # Если нужно, отчищаем гугл таблицу при старте
        if clear_spreadsheet_on_start is True:
            spr_sheet.clear()

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
        temperature, humidity = sensor.read()
        
        logger.info(f'{datetime.now()} Температура = {temperature}' + '\u2103 ' + f'Влажность = {humidity} %')
        temp_logfile.write_Data(temperature, humidity)

        # Если включена отправка на почту / в таблицу
        if is_Connected(site_For_Check) == False \
            and (
                mail_Status is True or spreadsheet_Status is True
            ):
                # Ставим переменные в ложь для того, чтобы перелогиниться после того как появится интернет
                is_Connected_To_Mail, is_Connected_To_Spreadsheet = False, False

                logger.critical('Connection lost, cannot sell mail/upload data to spreadsheet, retry on next cycle') 
        
        # Если не смогли залогиниться на старте или нужно перелогиниться после пропажи интернета
        if is_Connected(site_For_Check) is True:
            if mail_Status is True and is_Connected_To_Mail is False:
                mail.login()

                is_Connected_To_Mail, last_Auth_Refresh_Time = True, datetime.now()
                
            if spreadsheet_Status is True and is_Connected_To_Spreadsheet is False:
                spr_sheet.login()
                spr_sheet.open()

                # Если это первая попытка логина при неудачном логине на старте
                if clear_spreadsheet_on_start is True and first_Try_To_Connect is True:
                    spr_sheet.clear()
                    spr_sheet.create_Cols_Description()
                
                is_Connected_To_Spreadsheet, first_Try_To_Connect = True, False

                last_Auth_Refresh_Time = datetime.now()

        # Перелогиниваемся каждые полчаса, иначе будем получать connection timed out
        if is_Connected(site_For_Check) == True and datetime.now() >= last_Auth_Refresh_Time + timedelta(minutes = 30):     
            if mail_Status is True:
                mail.login()
                last_Auth_Refresh_Time = datetime.now()

            if spreadsheet_Status is True:
                spr_sheet.refresh_auth()
                last_Auth_Refresh_Time = datetime.now()
        
        # Заливаем в таблицу построчно
        if spreadsheet_Status is True and send_by_str is True:
            spr_sheet.send_str(temperature, humidity)
            logger.info('Str sended to Spreadsheets')

        # Проверяем соединение с интернетом и пришло ли время для отправки
        if is_Connected(site_For_Check) == True:
            if datetime.now() >= last_Time_Send \
                + timedelta(
                        hours = int(
                            period_before_send[0])
                        , 
                        minutes = int(
                            period_before_send[1]
                        )
                ):

                # Отправляем на почту при необходимости                                     
                if mail_Status is True:
                    mail.send_File('Температура')
                    logger.info(f'Sended to the e-mail')

                # Заливаем в таблицу файл, если построчная отправка выключена                                                         
                if spreadsheet_Status is True \
                    and send_by_str is False:
                        spr_sheet.send_file()
                        logger.info('File sended to Spreadsheets')

                # Если включена архивация, то сжимаем файл по прошествию n-ого количества времени
                if cfg['Main']['Archive'] is True and datetime.now() >= last_Arch_Time \
                    + timedelta(
                        hours = int(period_before_archive[0])
                        , 
                        minutes = int(period_before_archive[1])
                    ):
                        # Записываем время архивации
                    last_Arch_Time = datetime.now()

                    # Архивируем с помощью brotli и отчищаем сам файл после
                    temp_logfile.zip_File()            
                    temp_logfile.clear_File()

                    logger.info('Data compressed')

                # Если выбрано удаление, то просто отчищаем файл после каждой отправки
                if cfg['Main']['Delete after sending'] is True \
                    and (spreadsheet_Status is True or mail_Status is True):
                        temp_logfile.clear_File()

                # Записываем время отправки                                                        
                last_Time_Send = datetime.now()

            else:
                logger.info('Dont need send anything')
            
        # Ждем сколько-то и начинаем заново
        sleep(sleep_Period)

    # Дабы не ловить кучу errorов при выходе
    except KeyboardInterrupt:
        exit()
