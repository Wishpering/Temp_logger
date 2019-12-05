#!/usr/bin/python3

import smtplib
from email.mime.multipart import MIMEMultipart

class Mail(object):
    def __init__(self, File, logs, email_configuration):
        self.log_File = File
        self.email_configuration = email_configuration
        self.Logger = logs

    def login(self):
        # Устанавливаем соединение
        try:
            self.server = smtplib.SMTP_SSL(self.email_configuration.get("server_address"))
        except:
            print("Cannot create SSL connection to SMTP server")
            self.Logger.write_To_Log("Cannot create SSL connection to SMTP server")
            return

        # Смотрим, нужно ли включать дебаг
        if self.email_configuration["Debug info"].lower() == "on":
            self.server.set_debuglevel(True)
        if self.email_configuration["Debug info"].lower() == "off":
            self.server.set_debuglevel(False)
       
        # Логинимся
        try:
            self.server.login(self.email_configuration.get("Login"),self.email_configuration.get("Passwd"))
        except:
            print("Cannot log in SMTP server")
            self.Logger.write_To_Log("Cannot log in SMTP server")
            return

    # Функция для отправки файла
    def send_File(self, file_Name):
        # Получаем период начало-конец записи лога температуры
        first_Line, last_Line = self.log_File.get_Period()
        # Готовим файл к отправке
        attachable_file = self.log_File.prepare_For_Upload(file_Name)

        msg = MIMEMultipart()
        msg['Subject'] = 'Показания с датчика за период ' + first_Line + " - " + last_Line 
        msg['From'] = self.email_configuration.get("Login") 
        msg['To'] = self.email_configuration.get("email_to_send") 

        # Прикрепляем сам файл и отсылаем
        msg.attach(attachable_file)
        
        try:
            self.server.sendmail(self.email_configuration.get("Login"), self.email_configuration.get("email_to_send"), msg.as_string())
        except:
            print("Cannot send file via email")
            self.Logger.write_To_Log("Cannot send file via email")
            return