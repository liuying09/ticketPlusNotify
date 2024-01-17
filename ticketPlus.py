import json
import requests
import re
import time
import pygsheets
from decouple import config


#想要的場次就下下面那樣輸入網址即可(也可刪除) ["網址1","網址2","網址3"] 也可以先加入有票的網址看呈現效果

site = ["https://ticketplus.com.tw/order/c752489ad3e922cbd8943deccdd22696/f985a29962a5b0072d835d6e70190183" #Yoasobi
]

# site = ["https://ticketplus.com.tw/order/c752489ad3e922cbd8943deccdd22696/f985a29962a5b0072d835d6e70190183", #Yoasobi
#         "https://ticketplus.com.tw/order/a4c7ba719f9b7dfd2cd49035acb6d5ce/f067ac3bf62e0f5cd53ad265805545f8"  #有票場測試呈現效果，不需要可刪除。
# ]

url = 'https://notify-api.line.me/api/notify'
sheet_url = config('SHEET_URL')


def read_column_a():
    gc = pygsheets.authorize(service_file='/pythonWorkspace/ticketPlusNotify/ticketplus-20240116-5e97307fdce6.json')

    sht = gc.open_by_url(
        sheet_url
    )

    wks_list = sht.worksheets()
    print(wks_list)

    #選取by順序
    wks = sht[0]
 
    #選取by名稱
    wks2 = sht.worksheet_by_title("database")

   # 讀取 A 欄的所有資料
    column_a_data = wks2.get_col(1)  # 1 代表 A 欄
    # 過濾掉空值
    datasheet = [value for value in column_a_data[1:] if value]
    print(datasheet)
    return datasheet

returned_datasheet = read_column_a()


while True:
    for auth in returned_datasheet:
        token = auth # 權杖
        headers = {
            'Authorization': 'Bearer ' + token    # 設定權杖
        }


        for m in site:

            match1 = re.search(r'/order/([^/]+)/([^/]+)', m)
            eventId = match1.group(1)
            sessionId = match1.group(2)

            # print("match1= " + match1.group())
            # print("eventId= " , eventId)
            # print("sessionId= " , sessionId)

            ticketAreaId = []
            productId = []
            price = []


            p = requests.get(f"https://apis.ticketplus.com.tw/config/api/v1/getS3?path=event/{eventId}/event.json")
            title_data = json.loads(p.content)
            print(title_data["title"])
            print("")

            a = requests.get(f"https://apis.ticketplus.com.tw/config/api/v1/getS3?path=event/{eventId}/products.json")
            products_data = json.loads(a.content)
            # print("products_data =", products_data)
            try:
                for x in products_data['products']:
                    if x["sessionId"] == sessionId:
                            ticketAreaId.append(x['ticketAreaId'])
                            productId.append(x['productId'])
                            if x['price'] not in price:
                                price.append(x['price'])
                    sub = f"ticketAreaId={'%2C'.join(ticketAreaId)}&productId={'%2C'.join(productId)}"
                    # print("sub= ", sub)
            except:
                for x in products_data['products']:
                    if x["sessionId"] == sessionId:
                        productId.append(x['productId'])
                        if x['price'] not in price:
                            price.append(x['price'])
                sub = f"productId={'%2C'.join(productId)}"



            w = requests.get(f"https://apis.ticketplus.com.tw/config/api/v1/get?{sub}")
            data = json.loads(w.content)
            # print("data= ", data)




            try:
                for c in price:
                    for i in data['result']['product']:
                        if i['price'] == c:
                            for b in data['result']['ticketArea']:
                                if b['id'] == i['ticketAreaId']:
                                    try:
                                        print(f"{b['ticketAreaName']} = {b['count']}" , end = "  ")
                                        if b['count'] > 0:
                                            print(f"{m} 有票!")
                                            linedata = {
                                                    'message':f"{m} 有票!"     # 設定要發送的訊息
                                            }
                                            linedata = requests.post(url, headers=headers, data=linedata)   # 使用 POST 方法
                                    except:
                                        print(f"{b['ticketAreaName']} = 0" , end = "  ")

                    print("")

            except:
                for c in price:
                    for i in data['result']['product']:
                        if i['price'] == c:
                            for w in products_data['products']:
                                if i['id'] == w['productId']:
                                    try:
                                        print(f"{w['name']} = {i['count']}", end = "  ")
                                        if i['count'] > 0:
                                                print(f"{m} 有票!")
                                    except:
                                        print(f"{w['name']} = 0", end = "  ")

                    print("")
            print("")

    else:
        time.sleep(2)
    