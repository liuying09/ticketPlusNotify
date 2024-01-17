import pygsheets
import os, urllib
import flask
from flask import Flask
import importlib.metadata
from flask import request, abort
from flask import redirect
from decouple import config

app = Flask(__name__)

client_id = config('CLIENT_ID')                 # Notify 的 Clinet_ID
client_secret = config('CLIENT_SECRET')         # Notify 的 Clinet_Secret

redirect_uri = config('REDIRECT_URI') #回傳地點,你的 Notify 的網址


#使用者進入連結後進行綁定動作
#==============================================================================================#
def create_auth_link(client_id=client_id, redirect_uri=redirect_uri):

    data = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'notify',
        'state': 'NO_STATE'
    }
    query_str = urllib.parse.urlencode(data)

    return f'https://notify-bot.line.me/oauth/authorize?{query_str}'


#拿取使用者綁訂後的 Access_token
#==============================================================================================#

import json
def get_token(code, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri):
    url = 'https://notify-bot.line.me/oauth/token'
    headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'client_secret': client_secret
    }
    data = urllib.parse.urlencode(data).encode() #將data參數轉換為url

    try:
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req) as response:
            page = response.read()
            res = json.loads(page.decode('utf-8'))
            return res['access_token']
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        print(e.read())  # 印出響應內容


#儲存token進google sheet
#==============================================================================================#
sheet_url = config('SHEET_URL')
def google_sheet(client_id,access_token):
    gc = pygsheets.authorize(service_file='/pythonWorkspace/ticketplus-20240116-5e97307fdce6.json')

    sht = gc.open_by_url(
        sheet_url
    )

    wks_list = sht.worksheets()
    print(wks_list)

    #選取by順序
    wks = sht[0]
 
    #選取by名稱
    wks2 = sht.worksheet_by_title("database")

    datas = [access_token,client_id]

    wks2.append_table(values=datas)

#==============================================================================================#
@app.route("/auth", methods=['GET'])  #當進入 /auth 頁面時，會跳轉到notify綁定服務的頁面
def auth():
    auth_link = create_auth_link(client_id, redirect_uri)
    return redirect(auth_link)



@app.route("/callback/notify", methods=['GET'])  #當 /callback/notify 這個網頁收到 GET 時會做動
def callback_notify():
    code = request.args.get('code')

    # Get Access-Token
    access_token = get_token(code, client_id, client_secret, redirect_uri)

    google_sheet(client_id,access_token)    #回傳 Client_id and Access_Token 去紀錄
    return '恭喜完成 LINE Notify 連動！請關閉此視窗。'  #網頁顯示

if __name__ == '__main__':
    flask_version = importlib.metadata.version("flask")
    print(f"Flask 版本：{flask_version}")

    app.run(debug=True)