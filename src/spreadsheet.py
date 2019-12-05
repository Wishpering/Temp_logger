#!/usr/bin/python3

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
    
class Spreadsheet(object):
    def __init__(self, log, Path, path_To_File, cfg):
        self.static_Val = 2
        self.Path = Path
        self.path_To_File = path_To_File
        self.cfg = cfg
        self.Logger = log

    def login(self):
        # Адреса для API
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
    
        # Вытаскиваем из JSON все что нужно
        self.credentials = ServiceAccountCredentials.from_json_keyfile_name(self.Path + "auth/auth.json", scope)
    
        # Пытаемся авторизоваться
        try:
            self.client = gspread.authorize(self.credentials)
        except gspread.exceptions.APIError:
            print("Cannot login into spreadsheets")
            self.Logger.write_To_Log("Cannot login into spreadsheets")
            return

    # Функция для открытия таблицы
    def open_Spreadsheet(self):
        # Пытаемся открыть уже существующую с указанным именем
        try:
            self.wrk_sheet = self.client.open(self.cfg["Spreadsheet_name"])
            self.sheet = self.wrk_sheet.get_worksheet(0)
        
        # Если таковой таблицы нет, то создаем новую с указанным именем
        except gspread.exceptions.SpreadsheetNotFound:
            print("Spreadsheet not found, creating new....")
            
            wrk_sheet = self.client.create(self.cfg["Spreadsheet_name"])
            # Отправялем ссылку на созданную таблицу 
            wrk_sheet.share(str(self.cfg["email_To_Share"]), perm_type = 'user', role = 'writer')
            
            self.wrk_sheet = self.client.open(self.cfg["Spreadsheet_name"])
            self.sheet = self.wrk_sheet.get_worksheet(0)

    def refresh_Token(self):
        # Авторизовываемся и открываем таблицу (иначе будем получать 401 по таймауту)                                                                                                                                                                                           
        try:
            self.client = gspread.authorize(self.credentials)
            self.wrk_sheet = self.client.open(self.cfg["Spreadsheet_name"])
            self.sheet = self.wrk_sheet.get_worksheet(0)
        except gspread.exceptions:
            print("Cannot refresh auth")
            self.Logger.write_To_Log("Cannot refresh auth")
            return

    # Функция для отчистки таблицы
    def clear_Spreadsheet(self):
        if self.cfg["No beauty"] == "on":
            self.sheet.resize(rows = 1, cols = 1)
        else:
            self.sheet.resize(rows = 1, cols = 4)

    # Функция для создания описания колонок
    def create_Cols_Description(self):
        if self.cfg["No beauty"] != "on":
            self.sheet.update_acell('A' + str(1), "Дата")
            self.sheet.update_acell('B' + str(1), "Время")
            self.sheet.update_acell('C' + str(1), "Температура")
            self.sheet.update_acell('D' + str(1), "Влажность")

    # Функция для подсчета уже существующих строк
    def __line_Counting(self):
        # На старте считаем количество строчек и присваиваем полученное значение переменной i  
        if self.static_Val == 2:
            max_rows = len(self.sheet.get_all_values())
            # Если есть только 1 колонка с подписями, то записываем со второй
            if max_rows == 1:
                self.static_Val = 2
            else:
                self.static_Val= max_rows + 1
    
    # # Функция для отправки строки в таблицу
    def send_Str_To_Spreadsheet(self, temp, hum):
        try:
            self.sheet = self.wrk_sheet.get_worksheet(0)
        except gspread.exceptions.APIError:
            print("Cannot send str to spreadsheet")
            self.Logger.write_To_Log("Cannot send str to spreadsheet")
            return

        # Разбиваем datetime на дату и время
        data = str(datetime.now()).rstrip().split(" ")

        # Подсчитываем строки, для того, чтобы узнать с какой строки нужно записывать
        Spreadsheet.__line_Counting(self)

        # По мере необходимости добавляем строки
        self.sheet.resize(rows = self.static_Val)

        if self.cfg["No beauty"] == "on":
            # Записываем данные в соответствующие ячейки
            self.sheet.update_acell('A' + str(self.static_Val), data[0] + ' ' + data[1].split('.')[0] + ' Температура - ' + temp + '℃ Влажность - ' + hum + '%')
        else:
            self.sheet.update_acell('A' + str(self.static_Val), data[0])
            self.sheet.update_acell('B' + str(self.static_Val), data[1].split('.')[0])
            self.sheet.update_acell('C' + str(self.static_Val), temp)
            self.sheet.update_acell('D' + str(self.static_Val), hum)

        # Увеличиваем счетчик строк на 1
        self.static_Val += 1         

    # Функция для отправки файла в таблицу
    def send_To_Spreadsheet(self):
        objects_For_Rm = ['Температура', '=', 'Влажность', '=', '%', '℃']

        # Считаем количество строк в файле
        count_Of_Lines = len(open(self.Path + self.path_To_File, "r").readlines())
        
        # Если в файле больше 20 строк, то отсылаем только последние 20 (связано с ограничением Google API на 100 requests в 100 секунд)
        try:
            with open(self.Path + self.path_To_File, "r") as temperature_Data:
                # С красотой - только 20 строк за раз
                if self.cfg["No beauty"] != "on" and count_Of_Lines > 20:
                    lines = temperature_Data.readlines()[count_Of_Lines - 20:]

                # Без красоты - 45 строк за раз
                if self.cfg["No beauty"] == "on" and count_Of_Lines > 45:
                    lines = temperature_Data.readlines()[count_Of_Lines - 45:]  

                else:
                    lines = temperature_Data.readlines()
        
        except FileNotFoundError:
            print("Cannot open file to send it to spreadsheet")
            self.Logger("Cannot open file to send it to spreadsheet")

        if self.cfg["No beauty"] == "on":
            for line in lines:              
                # Подсчитываем строкив таблице, для того, чтобы узнать с какой строки нужно записывать
                Spreadsheet.__line_Counting(self)
            
                # По мере необходимости добавляем строки
                self.sheet.resize(rows = self.static_Val)

                self.sheet.update_acell('A' + str(self.static_Val), str(line))

                self.static_Val += 1
        
        else:   
            for line in lines:
                line = line.rstrip().split(" ")
        
                # Убираем ересь
                for obj in objects_For_Rm:
                    if obj in line:
                        line.remove(obj)
                
                # Подсчитываем строкив таблице, для того, чтобы узнать с какой строки нужно записывать
                Spreadsheet.__line_Counting(self)
            
                # По мере необходимости добавляем строки
                self.sheet.resize(rows = self.static_Val)
                    
                # Добавляем сами значения в 4 столбца
                self.sheet.update_acell('A' + str(self.static_Val), line[0])
                self.sheet.update_acell('B' + str(self.static_Val), line[1])
                self.sheet.update_acell('C' + str(self.static_Val), line[2])
                self.sheet.update_acell('D' + str(self.static_Val), line[3])

                self.static_Val += 1

            
