import json
import os
import telebot
import sqlite3
import paramiko
# импорт библиотеки для работы с ssh
import socket
import time
# импорт библ для задержки команды


bot = telebot.TeleBot()
# тоекн

def delete_complecs(id_number_complecs):
    try:
        conn = sqlite3.connect("VzorBelgorod.db")
        cursor = conn.cursor()
        cursor.execute(f"""DELETE from VzorBel WHERE id_number_complecs = {id_number_complecs}
        """)
        conn.commit()
    except BaseException:
        return "Ошибка"


def append_new(id_number_complecs, ip_912,ip_microPC,ip_cam,ip_750):
    try:
        conn = sqlite3.connect("VzorBelgorod.db")
        cursor = conn.cursor()
        cursor.execute(f"""INSERT INTO VzorBel VALUES ('{id_number_complecs}','{ip_912}','{ip_microPC}','{ip_cam}','{ip_750}')
        """)
        conn.commit()
    except BaseException:
        return "Ошибка"


def one_complecs(id_number_complecs):
    try:
        conn = sqlite3.connect("VzorBelgorod.db")
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM VzorBel WHERE id_number_complecs = {id_number_complecs}")
        hostname = cursor.fetchone()

        is_down_oborud = []

        for i in hostname[1:5]:
            response = os.system("ping -c 3 " + i)

            if response != 0:
                is_down_oborud.append(i)

        return f'Нет доступа к {is_down_oborud}'

    except BaseException:
        return "Ошибка"


def all_complecs():
    try:
        conn = sqlite3.connect("VzorBelgorod.db")
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM VzorBel ")
        hostname = cursor.fetchall()

        is_down_complecs = []

        for i in hostname:
            for j in i[1:5]:
                response = os.system("ping -c 3 " + j)

                if response != 0:
                    is_down_complecs.append(i[0])
                    break
    except BaseException:
        return "Ошибка"

    return f"Не работают {is_down_complecs}"


def len_complecsov():
    conn = sqlite3.connect("VzorBelgorod.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM VzorBel ")
    hostname = cursor.fetchall()
    return hostname[0][0]


def ip_complecs(id_number_complecs):
    try:
        conn = sqlite3.connect("VzorBelgorod.db")
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM VzorBel WHERE id_number_complecs = {id_number_complecs}")
        hostname = cursor.fetchall()
        print(hostname)
        return str(hostname[0])
    except BaseException:
        return "Ошибка"


def queue_complecs(ip_complecs):
    try:
        ssh=paramiko.SSHClient()
        # Я создал объект ssh класса SSHClient
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # Политика paramiko.AutoAddPolicy() автоматически добавляет новое имя хоста и ключ в локальный объект HostKeys
        ssh.connect(f"{ip_complecs}",username="root",password="ghjnjnbgGfhjkm",timeout=7)
        print("connected")
        stdin, stdout, stderr = ssh.exec_command("ls /var/tmp/out -1 ./*.jpg | wc -l")
        time.sleep(5) # дает время на выполнение строчки выше
        ssh.close()  # Метод close закрывает сессию
        return stdout.read()
    except socket.timeout:
        return "комплекс не доступен"



@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    try:
        if 'Ping' in message.text:

            x = [i for i in message.text.split()]
            bot.send_message(message.from_user.id, one_complecs(x[1]))

        elif 'All' in message.text:
            bot.send_message(message.from_user.id, all_complecs())

        elif 'New' in message.text:
            x = [i for i in message.text.split()]
            append_new(x[1], x[2], x[3], x[4], x[5])
            bot.send_message(message.from_user.id, "Добавленно")

        elif "Delete" in message.text:
            x = [i for i in message.text.split()]
            delete_complecs(x[1])
            bot.send_message(message.from_user.id, "Удалено")


        elif "Len" in message.text:
            len = str(len_complecsov())
            bot.send_message(message.from_user.id, len)

        elif "Ip" in message.text:
            x = [i for i in message.text.split()]
            bot.send_message(message.from_user.id, ip_complecs(x[1]))


        elif "Hellp" in message.text:
            bot.send_message(message.from_user.id,"""
            Delete (номер комплекса) - удаление комплекса из БД
            Ping (номер комплекса) - узнать доступность оборудования 
            Len - узнать количество комплексов в БД 
            All - узнать какие из комплексов не доступны 
            New (id_complecs   ip_912   ip_microPC   ip_cam   ip_750 ) - ввод через пробел. Добавление нового комплекса
            Ip (номер комплекса) - Узнать все Ip комплекса
            """)


        elif "Queue" in message.text:
            x = message.text.split()
            conn = sqlite3.connect("VzorBelgorod.db")
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM VzorBel WHERE id_number_complecs = {x[1]}")
            hostname = cursor.fetchall()

            bot.send_message(message.from_user.id,queue_complecs(hostname[0][2]))


        else:
            bot.send_message(message.from_user.id,"Команда отсутствует")



    except BaseException:
        bot.send_message(message.from_user.id, "Ошибка")


bot.polling(none_stop=True, interval=0)



