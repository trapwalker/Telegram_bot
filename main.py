
import secret
import telebot
import paramiko  # импорт библиотеки для работы с ssh
import os
import sqlite3
import socket
import time  # импорт библ для задержки команды
import requests

bot = telebot.TeleBot(token=secret.TOKEN)


class ComplexDriver:
    def __init__(self):
        self.db = sqlite3.connect(secret.DB_NAME)

    def close(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        self.close()

    def start_sqlite(self):
        cursor = self.db.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS VzorBel
        (
           id_number_complecs TEXT, 
           ip_912 TEXT,
           ip_microPC TEXT,
           ip_cam TEXT,
           ip_750 TEXT
           )
           ;""")


    def len_complecsov(self):
        cursor = self.db.cursor()
        cursor.execute("SELECT COUNT(*) FROM VzorBel ")
        hostname = cursor.fetchall()
        return hostname[0][0]

    def delete_complecs(self, id_number_complecs):
        cursor = self.db.cursor()
        cursor.execute(f"""
            DELETE from VzorBel WHERE id_number_complecs = {id_number_complecs}
        """)
        return "Удалено"

    def append_new(self, id_number_complecs, ip_912, ip_microPC, ip_cam, ip_750):
        cursor = self.db.cursor()
        print(id_number_complecs, ip_912, ip_microPC, ip_cam, ip_750)
        cursor.execute(f"""
            INSERT INTO VzorBel 
            VALUES ('{id_number_complecs}','{ip_912}','{ip_microPC}','{ip_cam}','{ip_750}')
        """)
        self.db.commit()
        return "Добавленно"

    def one_complecs(self, id_number_complecs):
        cursor = self.db.cursor()
        cursor.execute(f"SELECT * FROM VzorBel WHERE id_number_complecs = {id_number_complecs}")
        hostname = cursor.fetchone()

        is_down_oborud = []

        for i in hostname[1:5]:
            response = os.system("ping -c 3 " + i)

            if response != 0:
                is_down_oborud.append(i)

        return f'Нет доступа к {is_down_oborud}'

    def all_complecs(self):
        cursor = self.db.cursor()
        cursor.execute(f"SELECT * FROM VzorBel ")
        hostname = cursor.fetchall()

        is_down_complecs = []

        for i in hostname:
            for j in i[1:5]:
                response = os.system("ping -c 3 " + j)

                if response != 0:
                    is_down_complecs.append(i[0])
                    break

        return f"Не работают {is_down_complecs}"

    def ip_complecs(self, id_number_complecs):
        cursor = self.db.cursor()
        cursor.execute(f"SELECT * FROM VzorBel WHERE id_number_complecs = {id_number_complecs}")
        hostname = cursor.fetchall()
        print(hostname)
        return str(hostname[0])

    def queue_complecs(self, id_number_complecs):
        cursor = self.db.cursor()
        cursor.execute(f"SELECT ip_microPC FROM VzorBel WHERE id_number_complecs = {id_number_complecs}")
        ip_microPC = cursor.fetchall()
        print(ip_microPC[0][0])
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # Политика paramiko.AutoAddPolicy() автоматически добавляет новое имя хоста и ключ в локальный объект HostKeys
        try:
            ssh.connect(f"{ip_microPC[0][0]}", username=secret.COMPLEX_USER, password=secret.COMPLEX_PASSWORD, timeout=7)
        except socket.timeout:
            return "комплекс не доступен"
        else:
            print("connected")
            stdin, stdout, stderr = ssh.exec_command(secret.COMMAND_FOR_QUEUE)
            time.sleep(5)  # дает время на выполнение строчки выше
            ssh.close()
            return stdout.read()

    def send_photo_complecs(self,id_number_complecs):
        cursor = self.db.cursor()
        cursor.execute(f"SELECT ip_cam FROM VzorBel WHERE id_number_complecs = {id_number_complecs} ")
        ip_cam = cursor.fetchall()
        print(ip_cam[0][0])
        try:
            response = requests.get(f"http://{secret.LOGING_CAM}:{secret.POSsWORD_CAM}@{ip_cam[0][0]}/ISAPI/Streaming/channels/101/picture?videoResolutionWidth=1920&videoResolutionHeight=1024",timeout=5)
        except requests.exceptions.ConnectTimeout:
            return print("Превышено время ожидания")
        print(response)
        with open('/home/evgeny/screen.png', 'rb+') as photo:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    photo.write(chunk)
            photo_send = open('/home/evgeny/screen.png', 'rb')
            return photo_send


@bot.message_handler(commands=['start'])
def start_bd_table(message):
    with ComplexDriver() as driver:
        bot.send_message(message.from_user.id, driver.start_sqlite())


@bot.message_handler(content_types=['text', 'photo'])
def get_text_messages(message):
    cmd, *args = message.text.split()
    cmd = cmd.lower()
    with ComplexDriver() as driver:

        if cmd == 'ping':
            if len(*args) == 4:
                bot.send_message(message.from_user.id, driver.one_complecs(*args))
            else:
                bot.send_message(message.from_user.id, "Номера комплекса должна состоять из четырех цыфр ")

        elif cmd == "photo":
            if len(*args) == 4:
                try:
                    bot.send_photo(message.from_user.id, driver.send_photo_complecs(*args))
                    time.sleep(10)
                except BaseException:
                    bot.send_message(message.from_user.id, "Нет доступа к камере или такого комплекса не существует")
            else:
                    bot.send_message(message.from_user.id, "Номера комплекса должна состоять из четырех цыфр ")

        elif cmd == 'all':
            bot.send_message(message.from_user.id, driver.all_complecs())

        elif cmd == 'new':
            if len(args) == 5:
                driver.append_new(*args)
                bot.send_message(message.from_user.id, "Добавленно")
            else:
                bot.send_message(message.from_user.id, "мало данных")

        elif cmd == "delete":
            if len(*args) == 4:
                driver.delete_complecs(args[0])
                bot.send_message(message.from_user.id, "Удалено")
            else:
                bot.send_message(message.from_user.id, "Номера комплекса должна состоять из четырех цыфр ")

        elif cmd == "len":
            bot.send_message(message.from_user.id, str(driver.len_complecsov()))

        elif cmd == "ip":
            if len(*args) == 4:
                bot.send_message(message.from_user.id, driver.ip_complecs(args[0]))
            else:
                bot.send_message(message.from_user.id, "Номера комплекса должна состоять из четырех цыфр ")

        elif cmd == "help":
            bot.send_message(
                message.from_user.id,
                (
                    "Delete (номер комплекса) - удаление комплекса из БД\n"
                    "Ping (номер комплекса) - узнать доступность оборудования\n" 
                    "Len - узнать количество комплексов в БД\n" 
                    "All - узнать какие из комплексов не доступны\n" 
                    "New (id_complecs   ip_912   ip_microPC   ip_cam   ip_750 ) - ввод через пробел. "
                    "Добавление нового комплекса\n"
                    "Ip (номер комплекса) - Узнать все Ip комплекса\n"
                    "queue (номер комплекса) - Узнать очередь фактов на комплекса\n"
                    "photo (номер комплекса) - Получть фото с комплекса"

                )
            )

        elif cmd == "queue":
            if len(*args) == 4:
                bot.send_message(message.from_user.id, driver.queue_complecs(*args))
            else:
                bot.send_message(message.from_user.id, "Номера комплекса должна состоять из четырех цыфр ")

        else:
            bot.send_message(message.from_user.id, "Команда отсутствует")



if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
