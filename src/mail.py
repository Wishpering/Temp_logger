import smtplib
from email.mime.multipart import MIMEMultipart

class Mail(object):
    def __init__(self, File, logger, email_configuration):
        self.temp_Log_File = File
        self.email_configuration = email_configuration
        self.Logger = logger

    def login(self):
        """Функция для логина на SMTP сервере"""

        # Устанавливаем соединение
        try:
            self.server = smtplib.SMTP_SSL(self.email_configuration.get('server_address'))
        except smtplib.SMTPException: 
            self.Logger.critical('Can\'not create SSL connection to SMTP server')
            return

        # Смотрим, нужно ли включать дебаг
        if self.email_configuration['Debug info'] is True:
            self.server.set_debuglevel(True)
        else:
            self.server.set_debuglevel(False)
       
        # Логинимся
        try:
            self.server.login(self.email_configuration.get('Login'),self.email_configuration.get('Passwd'))
        except smtplib.SMTPException:
            self.Logger.critical('Can\'not log in SMTP server')
            return

    def send_File(self, file_Name):
        """Функция для отправки файла"""

        # Получаем период начало-конец записи лога температуры
        first_Line, last_Line = self.temp_Log_File.get_Period()
        # Готовим файл к отправке
        attachable_file = self.temp_Log_File.prepare_For_Upload(file_Name)

        msg = MIMEMultipart()
        msg['Subject'] = f'Показания с датчика за период {first_Line} - {last_Line}' 
        msg['From'] = self.email_configuration.get('Login') 
        msg['To'] = self.email_configuration.get('email_to_send') 

        # Прикрепляем сам файл и отсылаем
        msg.attach(attachable_file)
        
        try:
            self.server.sendmail(self.email_configuration.get('Login'), self.email_configuration.get('email_to_send'), msg.as_string())
        except smtplib.SMTPException:
            self.Logger.critical('Can\'not send file via email')
            return