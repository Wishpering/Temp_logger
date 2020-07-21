import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
    
class Spreadsheet(object):
    def __init__(self, log, Path, path_To_File, cfg):
        self.row_Count = 2
        self.Path = Path
        self.path_To_File = path_To_File
        self.Logger = log

        self.spreadsheet_name = cfg['Spreadsheet_name']
        self.email_to_send = cfg['email_To_Share']
        self.no_beauty = cfg['No beauty']

    def login(self):
        """Функция для логина в Google API"""

        # Адреса для API
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
    
        # Вытаскиваем из JSON все что нужно
        self.credentials = ServiceAccountCredentials.from_json_keyfile_name(f'{self.Path}/auth/auth.json', scope)
    
        # Пытаемся авторизоваться
        try:
            self.client = gspread.authorize(self.credentials)
        except gspread.exceptions.APIError:
            self.Logger.critical('Can\'not login into spreadsheets')
            return

    def open(self):
        """Функция для открытия таблицы"""

        # Пытаемся открыть уже существующую с указанным именем
        try:
            self.wrk_sheet = self.client.open(self.spreadsheet_name)
            self.sheet = self.wrk_sheet.get_worksheet(0)
        
        # Если таковой таблицы нет, то создаем новую с указанным именем
        except gspread.exceptions.SpreadsheetNotFound:
            self.Logger.info('Spreadsheet not found, creating new....')
            
            wrk_sheet = self.client.create(self.spreadsheet_name)
            # Отправялем ссылку на созданную таблицу 
            wrk_sheet.share(self.email_to_send, perm_type='user', role='writer')
            
            self.wrk_sheet = self.client.open(self.spreadsheet_name)
            self.sheet = self.wrk_sheet.get_worksheet(0)

    def refresh_auth(self):
        """Функция для открытия таблицы"""

        # Авторизовываемся и открываем таблицу (иначе будем получать 401 по таймауту)                                                                                                                                                                                           
        try:
            self.client = gspread.authorize(self.credentials)
            self.wrk_sheet = self.client.open(self.spreadsheet_name)
            self.sheet = self.wrk_sheet.get_worksheet(0)
        except gspread.exceptions:
            self.Logger.critical('Can\'not refresh auth')
            return

    def clear(self):
        """Функция для отчистки таблицы"""

        if self.no_beauty is True:
            self.sheet.resize(rows = 1, cols = 1)
        else:
            self.sheet.resize(rows = 1, cols = 4)

    def create_Cols_Description(self):
        """Функция для создания описания колонок"""

        if self.no_beauty is not True:
            self.sheet.update_acell(f'A{1}', 'Дата')
            self.sheet.update_acell(f'B{1}', 'Время')
            self.sheet.update_acell(f'C{1}', 'Температура')
            self.sheet.update_acell(f'D{1}', 'Влажность')

    def __line_Counting(self):
        """Функция для подсчета уже существующих строк в таблице"""

        # На старте считаем количество строчек и присваиваем полученное значение переменной i  
        if self.row_Count == 2:
            max_rows = len(self.sheet.get_all_values())
            
            # Если есть только 1 колонка с подписями, то записываем со второй
            if max_rows == 1:
                self.row_Count = 2
            else:
                self.row_Count= max_rows + 1
    
    def send_str(self, temp, hum):
        """Функция для отправки строки в таблицу"""

        try:
            self.sheet = self.wrk_sheet.get_worksheet(0)
        except gspread.exceptions.APIError:
            self.Logger.critical('Can\'not send str to spreadsheet')
            return

        data = datetime.now()

        # Подсчитываем строки, для того, чтобы узнать с какой строки нужно записывать
        Spreadsheet.__line_Counting(self)

        # По мере необходимости добавляем строки
        self.sheet.resize(rows = self.row_Count)

        if self.no_beauty is True:
            # Записываем данные в соответствующие ячейки
            self.sheet.update_acell(
                f'A{self.row_Count}', 
                f'{data.date()} {data.time()} Температура - {temp}' + '\u2103 ' + f'Влажность - {hum} %'
            )
        else:
            self.sheet.update_acell(f'A{self.row_Count}', data[0])
            self.sheet.update_acell(f'B{self.row_Count}', data[1].split('.')[0])
            self.sheet.update_acell(f'C{self.row_Count}', temp)
            self.sheet.update_acell(f'D{self.row_Count}', hum)

        # Увеличиваем счетчик строк на 1
        self.row_Count += 1         

    def send_file(self):
        """Функция для отправки файла в таблицу"""

        objects_For_Rm = ['Температура', '=', 'Влажность', '=', '%', '℃']

        # Считаем количество строк в файле
        count_Of_Lines = len(
            open(f'{self.Path}{self.path_To_File}', 'r').readlines()
        )
        
        # Если в файле больше 20 строк, то отсылаем только последние 20 (связано с ограничением Google API на 100 requests в 100 секунд)
        try:
            with open(f'{self.Path}{self.path_To_File}', 'r') as temperature_Data:
                # С красотой - только 20 строк за раз
                if self.no_beauty is not True and count_Of_Lines > 20:
                    lines = temperature_Data.readlines()[count_Of_Lines - 20:]

                # Без красоты - 45 строк за раз
                if self.no_beauty is True and count_Of_Lines > 45:
                    lines = temperature_Data.readlines()[count_Of_Lines - 45:]  

                else:
                    lines = temperature_Data.readlines()
        
        except FileNotFoundError:
            self.Logger.critical('Can\'not open file to send it to spreadsheet')

        if self.no_beauty is True:
            for line in lines:              
                # Подсчитываем строкив таблице, для того, чтобы узнать с какой строки нужно записывать
                Spreadsheet.__line_Counting(self)
            
                # По мере необходимости добавляем строки
                self.sheet.resize(rows = self.row_Count)
                self.sheet.update_acell(f'A{self.row_Count}', f'{line}')
                self.row_Count += 1
        
        else:   
            for line in lines:
                line = line.rstrip().split(' ')
        
                # Убираем ересь
                for obj in objects_For_Rm:
                    if obj in line:
                        line.remove(obj)
                
                # Подсчитываем строкив таблице, для того, чтобы узнать с какой строки нужно записывать
                Spreadsheet.__line_Counting(self)
            
                # По мере необходимости добавляем строки
                self.sheet.resize(rows = self.row_Count)
                    
                # Добавляем сами значения в 4 столбца
                self.sheet.update_acell(f'A{self.row_Count}', line[0])
                self.sheet.update_acell(f'B{self.row_Count}', line[1])
                self.sheet.update_acell(f'C{self.row_Count}', line[2])
                self.sheet.update_acell(f'D{self.row_Count}', line[3])

                self.row_Count += 1