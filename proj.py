from flask import Flask, request
import logging
import json
import requests
import sqlite3
import chardet


class DB:
    def __init__(self):
        connection = sqlite3.connect('otzivy.db', check_same_thread=False)
        self.connection = connection
        self.init_table()

    def get_connection(self):
        return self.connection

    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS otzivy 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             user_name VARCHAR(256),
                             orgid VARCHAR(64),
                             otziv VARCHAR(8192)
                             )''')
        cursor.close()
        self.connection.commit()

    def insert(self, username, org, otzyv):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO otzivy 
                          (user_name, orgid, otziv) 
                          VALUES (?,?,?)''', (username, org, otzyv))
        cursor.close()
        self.connection.commit()

    def get(self, org):
        cursor = self.connection.cursor()
        req1 = "SELECT * FROM otzivy WHERE orgid = '" + str(org) + "'"
        logging.error(req1)
        cursor.execute(req1)
        row = cursor.fetchone()
        logging.error(row)
        return row

    def __del__(self):
        self.connection.close()

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

sessionStorage = {}

db = DB()

otziv = db.get('1072147459')
print(otziv)

@app.route('/post', methods=['POST'])
def main():
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(response, request.json)
    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    search_params = {
        "apikey": "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3",
        "text": req['request']['command'],
        "lang": "ru_RU",
        "results": "1",
        "type": "biz"
    }
    respo = requests.get("https://search-maps.yandex.ru/v1/", params=search_params)
    resp = json.loads(respo.content.decode(chardet.detect(respo.content)["encoding"]))
    try:
        if resp['features']:
            orgid = resp["features"][0]["properties"]["CompanyMetaData"]["id"]
            logging.error(orgid)
            otziv = db.get(str(orgid))
            logging.error(otziv)
            if otziv:
                stroka = "Найдено место: " + \
                         str(resp['features'][0]['properties']['CompanyMetaData']['name']) + \
                         " по адресу " + \
                         str(resp['features'][0]['properties']['CompanyMetaData']['address']) + \
                         ". Случайный отзыв: " + \
                         str(otziv[3]) + ". Пользователь: " + str(otziv[1])
            else:
                stroka = "Найдено место: " + \
                         str(resp['features'][0]['properties']['CompanyMetaData']['name']) + \
                         " по адресу " + \
                         str(resp['features'][0]['properties']['CompanyMetaData']['address']) + \
                         ". Отзывов еще нет."
            res['response']['text'] = stroka
        elif req['session']['new'] is True:
            res['response']['text'] = 'Привет. Я показываю тебе честные отзывы. Назови место и город.'
        else:
            res['response']['text'] = "Я не нашла такого места."
    except KeyError:
        if req['session']['new'] is True:
            res['response']['text'] = 'Привет. Я показываю тебе честные отзывы. Назови место и город.'
        else:
            res['response']['text'] = "Я не нашла такого места."

if __name__ == '__main__':
    app.run()