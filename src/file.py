#!/usr/bin/python3

from datetime import datetime, timedelta
from os.path import isfile
from brotli import compress
from email import encoders
from email.mime.base import MIMEBase

class File(object):
    def __init__(self, Path, path_To_File, Logger):
        self.Path = Path
        self.path_To_File = path_To_File
        self.Logger = Logger
        
    def write_Data(self, temperature, humidity):
        with open(self.Path + self.path_To_File, "a+") as data:
            data.write((str(datetime.now()).split('.'))[0] + " Температура = " + temperature + " ℃ " + " Влажность = " + humidity + " %" + "\n")

    # Узнаем, за какой период файл
    def get_Period(self):
        try:
            with open(self.Path + self.path_To_File, "r") as file_For_Load:
        
                # Считываем первую и последнюю строку файла для того, чтобы узнать, в каких пределах находятся значения
                first_Line = file_For_Load.readline().split(" ")
                first_Line = first_Line[0] + " " + first_Line[1]
                    
                try:
                    last_Line = file_For_Load.readlines()[-1].split(" ")
                    last_Line = last_Line[0] + " " + last_Line[1]
                
                # Если в доке только одна строка
                except IndexError:
                    return first_Line, first_Line
                    
                return first_Line, last_Line

        except FileNotFoundError:
            print("Cannot open file to get period of data")
            self.Logger.write_To_Log("Cannot open file to get period of data")

    # Подготовка файла к отправке
    def prepare_For_Upload(self, file_Name):
        try:
            with open(self.Path + self.path_To_File, "rb") as file_For_Load:
                # Добавляем заголовки (используем общий тип)
                maintype, subtype = 'application/octet-stream'.split('/', 1)
                file = MIMEBase(maintype,subtype)
                file.set_payload(file_For_Load.read())

                # Кодируем файл с помощью Base64
                encoders.encode_base64(file)

                # Прикрепляем заголовки
                file.add_header('Content-Disposition', 'attachment', filename = file_Name)
                return file
            
        except FileNotFoundError:
            print("Cannot open file to prepare it for upload")
            self.Logger.write_To_Log("Cannot open file to prepare it for upload")  

    # Сжатие файла
    def zip_File(self, path_For_Zip):
        # Записываем дату сжатия                                                                                                                                                                              
        zip_Data = str(datetime.now()).split(" ")

        # Архивируем файл с помощью bzip2 сжатия                                                                                                                                                              
        with open(self.Path + self.path_To_File, "rb") as temperature_Log:
            with open(self.Path + path_For_Zip + zip_Data[0] + "__" + (str(zip_Data[1]).split("."))[0] + ".br", "wb") as arch:
                arch.write(compress(temperature_Log.read()))

    # Отчистка файла
    def clear_File(self):
        # Если файла не существует, то просто выходим 
        if not isfile(self.Path + self.path_To_File):
            print("Cannot clear file, file not found")
            self.Logger.write_To_Log("Cannot clear file, file not found")
            return
        
        file = open(self.Path + self.path_To_File, "w").close()
