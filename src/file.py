from datetime import datetime
from brotli import compress
from email import encoders
from email.mime.base import MIMEBase

class File(object):
    def __init__(self, Path, path_To_File, Logger):
        self.Path = Path
        self.path_To_File = path_To_File
        self.Logger = Logger
        
    def write_Data(self, temperature, humidity):
        """Функция для записи данных в файл"""

        with open(f'{self.Path}{self.path_To_File}', 'a+') as data:
            data.write(
                f'{datetime.now()} Температура = {temperature}' + '\u2103 ' + f'Влажность = {humidity} % \n'
            )

    def get_Period(self):
        """Функция для получения информации, за какой период файл содержит данные"""

        try:
            with open(f'{self.Path}{self.path_To_File}', 'r') as file_For_Load:
                # Считываем первую и последнюю строку файла для того, чтобы узнать, в каких пределах находятся значения
                first_Line = file_For_Load.readline().rsplit(' ', 7)[0].split('.')[0]
                    
                try:
                    last_Line = file_For_Load.readlines()[-1].rsplit(' ', 7)[0].split('.')[0]
                    
                # Если в доке только одна строка
                except IndexError:
                    return first_Line, first_Line
                    
                return first_Line, last_Line

        except FileNotFoundError:
            self.Logger.critical('Cannot open file to get period of data')

    def prepare_For_Upload(self, file_Name):
        """Функция для подготовки файла к отправке по почте"""

        try:
            with open(f'{self.Path}{self.path_To_File}', 'rb') as file_For_Load:
                # Добавляем заголовки (используем общий тип)
                maintype, subtype = 'application/octet-stream'.split('/', 1)
                file = MIMEBase(maintype, subtype)
                file.set_payload(file_For_Load.read())

                # Кодируем файл с помощью Base64
                encoders.encode_base64(file)

                # Прикрепляем заголовки
                file.add_header('Content-Disposition', 'attachment', filename = file_Name)
                return file
            
        except FileNotFoundError:
            self.Logger.critical('Cannot open file to prepare it for upload')  

    def zip_File(self):
        """Функция для архивации файла"""

        # Записываем дату сжатия                                                                                                                                                                              
        zip_Data = f'{datetime.now()}'.split(' ')

        # Архивируем файл с помощью brotli сжатия                                                                                                                                                              
        with open(f'{self.Path}{self.path_To_File}', 'rb') as temperature_Log:
            with open(f'{self.Path}/data/{zip_Data[0]}__{zip_Data[1].split(".")[0]}.br', 'wb') as arch:
                arch.write(compress(temperature_Log.read()))

    def clear_File(self):
        """Функция для отчистки файла"""

        try:
            open(f'{self.Path}{self.path_To_File}', 'w').close()
        # Если файла не существует, то просто выходим 
        except FileNotFoundError:
            self.Logger.critical('Cannot clear file, file not found')
