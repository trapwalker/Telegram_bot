
import secret

import telebot
import paramiko  # импорт библиотеки для работы с ssh

import os
import sqlite3
import socket
import time  # импорт библ для задержки команды
from contextlib import closing, contextmanager


bot = telebot.TeleBot(token=secret.TOKEN)
DB_NAME = "VzorBelgorod.db"


class ComplexDriver:
    def __init__(self):
        self.db = sqlite3.connect(DB_NAME)  # TODO: move DB_NAME to secret.py

    def close(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def len_complecsov(self):
        # TODO: use single DB connection
        with closing(self.db.cursor()) as cursor:
            cursor.execute("SELECT COUNT(*) FROM VzorBel ")
            hostname = cursor.fetchall()
        return hostname[0][0]

    def delete_complecs(self, id_number_complecs):
        # TODO: use single DB connection
        with closing(self.db.cursor()) as cursor:
            cursor.execute(f"""
                DELETE from VzorBel WHERE id_number_complecs = {id_number_complecs}
            """)
            # TODO: use SQL parameters
            self.db.commit()
            # TODO: catch exceptions


def append_new(id_number_complecs, ip_912, ip_microPC, ip_cam, ip_750):
    # TODO: use single DB connection
    with closing(db.cursor()) as cursor:
        cursor.execute(f"""
            INSERT INTO VzorBel 
            VALUES ('{id_number_complecs}','{ip_912}','{ip_microPC}','{ip_cam}','{ip_750}')
        """)
        # TODO: use SQL parameters
        db.commit()


def one_complecs(id_number_complecs):
    # TODO: use single DB connection
    with closing(db.cursor()) as cursor:
        cursor.execute(f"SELECT * FROM VzorBel WHERE id_number_complecs = {id_number_complecs}")
        hostname = cursor.fetchone()

    is_down_oborud = []

    for i in hostname[1:5]:
        response = os.system("ping -c 3 " + i)

        if response != 0:
            is_down_oborud.append(i)

    return f'Нет доступа к {is_down_oborud}'


def all_complecs():
    # TODO: use single DB connection
    with closing(db.cursor()) as cursor:
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


def ip_complecs(id_number_complecs):
    # TODO: use single DB connection
    with closing(db.cursor()) as cursor:
        cursor.execute(f"SELECT * FROM VzorBel WHERE id_number_complecs = {id_number_complecs}")
        hostname = cursor.fetchall()
    print(hostname)
    return str(hostname[0])


def queue_complecs(ip_complecs):
    with paramiko.SSHClient() as ssh:
        # Политика paramiko.AutoAddPolicy() автоматически добавляет новое имя хоста и ключ в локальный объект HostKeys
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(f"{ip_complecs}", username=secret.COMPLEX_USER, password=secret.COMPLEX_PASSWORD, timeout=7)
        except socket.timeout:
            return "комплекс не доступен"
        else:
            print("connected")
            # TODO: extract command to const
            stdin, stdout, stderr = ssh.exec_command("ls /var/tmp/out -1 ./*.jpg | wc -l")
            time.sleep(5)  # дает время на выполнение строчки выше
            return stdout.read()


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    cmd, *args = message.text.split()
    cmd = cmd.lower()

    with ComplexDriver() as driver:
        # try:
        if cmd == 'ping':
            bot.send_message(message.from_user.id, one_complecs(args[0]))

        elif cmd == 'all':
            bot.send_message(message.from_user.id, all_complecs())

        elif cmd == 'new':
            append_new(*args)
            bot.send_message(message.from_user.id, "Добавленно")

        elif cmd == "delete":
            driver.delete_complecs(args[0])
            bot.send_message(message.from_user.id, "Удалено")

        elif cmd == "len":
            bot.send_message(message.from_user.id, str(driver.len_complecsov()))

        elif cmd == "ip":
            bot.send_message(message.from_user.id, ip_complecs(args[0]))

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
                )
            )

        elif cmd == "queue":
            cursor = db.cursor()
            cursor.execute(f"SELECT * FROM VzorBel WHERE id_number_complecs = {args[0]}")
            hostname = cursor.fetchall()
            bot.send_message(message.from_user.id,queue_complecs(hostname[0][2]))

        else:
            bot.send_message(message.from_user.id,"Команда отсутствует")
        # except BaseException:
        #     bot.send_message(message.from_user.id, "Ошибка")


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
