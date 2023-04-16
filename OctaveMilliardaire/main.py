
import json
import imaplib
import traceback
import email
import time
import socket
import http.client

socket.getaddrinfo('localhost', 8080)

CAPITAL_ADDR = "demo-api-capital.backend-capital.com"
ORG_EMAIL = "@gmail.com"
FROM_EMAIL = "<EMAIL WHERE YOU GETT INSTRUCTION>"
print(FROM_EMAIL)
MDP = "PASSWORD"
OPEN_POSITION = False
ORDER_TYPE = -1
DEAL_ID = -1
DEAL_REF = 0
SMTP_SERVER = "imap.outlook.com" # change depending on your email provider
SMTP_PORT = 1143


def read_mail_order():
    try:
        mail = imaplib.IMAP4_SSL(SMTP_SERVER)
        mail.login(FROM_EMAIL, MDP)
        mail.select('inbox')
        data = mail.search(None, 'ALL')
        mail_ids = data[1]
        id_list = mail_ids[0].split()
        last_email_id = int(id_list[-1])
        data = mail.fetch(str(last_email_id), '(RFC822)')  #
        for response_part in data:
            arr = response_part[0]
            if isinstance(arr, tuple):
                msg = email.message_from_string(str(arr[1], 'utf-8'))
                email_subject = msg['subject']
                email_from = msg['from']
                print('From : ' + email_from + '\n')
                print('Subject : ' + email_subject + '\n')
                if email_subject == "Alerte: BUY":
                    print("buy order")
                    return 0
                if email_subject == "Alert: SELL":
                    print("sell order")
                    return 1
                if email_subject == "KILL":
                    print("shutdown")
                    return -2

                print("invalid order")
                return -1

    except Exception as e:
        traceback.print_exc()
        print(str(e))
        return -1


def deal_confirmation(TOK, CST, DEAL_REF):
    conn = http.client.HTTPSConnection(CAPITAL_ADDR)
    payload = ''
    headers = {
        'X-SECURITY-TOKEN': TOK,
        'CST': CST
    }
    conn.request("GET", f"/api/v1/confirms/{DEAL_REF}", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))
    temp = data.decode("utf-8")
    d = json.loads(temp)
    if res.status == 200:
        print("position confirmed success")
        t = d["affectedDeals"]
        t1 = d["dealId"]
        try:
            print(t[0])
            return t[0]["dealId"]

        except Exception as e:
            print(e)
            print(f"returning other id :{t1}")
            return -1
       
    else:
        print("error detected status=" + str(res.status))
        return -1


def close_position(Token, CST, dealid):
    conn = http.client.HTTPSConnection(CAPITAL_ADDR)
    payload = ''
    headers = {
        'X-SECURITY-TOKEN': Token,
        'CST': CST
    }
    conn.request("DELETE", f"/api/v1/positions/{dealid}", payload, headers)
    res = conn.getresponse()
    data = res.read()
    #print(res.headers)
    print(dealid)
    print(data.decode("utf-8"))
    if res.status == 200:
        print("position closed success")
    else:
        print("error detected status=" + str(res.status))


def buy_position(Token, CST):
    conn = http.client.HTTPSConnection(CAPITAL_ADDR)
    payload = json.dumps({
        "epic": "US500",
        "direction": "BUY",
        "size": 1,
        "guaranteedStop": True,
        "stopLevel": 1800,

    })
    headers = {
        'X-SECURITY-TOKEN': Token,
        'CST': CST,
        'Content-Type': 'application/json'
    }
    conn.request("POST", "/api/v1/positions", payload, headers)
    res = conn.getresponse()
    data = res.read()
    #print(res.headers)
    print(res.status)
    print(data.decode("utf-8"))
    temp = data.decode("utf-8")
    d = json.loads(temp)
    if res.status == 200:
        print("position buyed success")

        return d["dealReference"]
    else:
        print("error detected status=" + str(res.status))


def sell_position(Token, CST):
    conn = http.client.HTTPSConnection(CAPITAL_ADDR)
    payload = json.dumps({
        "epic": "US500",
        "direction": "SELL",
        "size": 1,
        "guaranteedStop": True,
        "stopLevel": 4000.5,

    })
    headers = {
        'X-SECURITY-TOKEN': Token,
        'CST': CST,
        'Content-Type': 'application/json'
    }
    conn.request("POST", "/api/v1/positions", payload, headers)
    res = conn.getresponse()
    data = res.read()
    #print(res.headers)
    print(res.status)
    print(data.decode("utf-8"))
    temp = data.decode("utf-8")
    d = json.loads(temp)
    if res.status == 200:
        print("position sell success")

        return d["dealReference"]
    else:
        print("error detected status=" + str(res.status))
        return 0


def start_session():
    conn = http.client.HTTPSConnection(CAPITAL_ADDR)
    payload = json.dumps({
        "identifier": "<YOUR CAPITAL.COM USERNAME>",
        "password":"<YOUR PASSWORD>"
    })
    headers = {
        'X-CAP-API-KEY': '<API-KEY>',
        'Content-Type': 'application/json'
    }
    print(payload)
    conn.request("POST", "/api/v1/session", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))
    #print(res.headers)
    CST = res.headers.get("CST")
    Token = res.headers.get("X-SECURITY-TOKEN")

    return (Token , CST)

def ping_service(TOK, CST):
    conn = http.client.HTTPSConnection(CAPITAL_ADDR)
    payload = ''
    headers = {
        'X-SECURITY-TOKEN': TOK,
        'CST': CST
    }
    conn.request("GET", "/api/v1/ping", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))


if __name__ == '__main__':

    print("Demarage bot trading")
    print("Connection a CAPITAL...")
    TOK, CST = start_session()

    retry = 0
    while True:
        #email reading
        for i in range(3):
            print("refreshing in " + str(60 - i * 20))
            print(time.asctime(time.gmtime()))
            time.sleep(20)
        print("en attente d'instruction")
        for retry in range(5):
            ORDER_TYPE = read_mail_order()
            if ORDER_TYPE == -1:
                print("instruction invalide retry : " + str(retry))
                time.sleep(5)
            else:
                if ORDER_TYPE == -2:
                    print("shutting down")
                    close_position(TOK, CST, DEAL_ID)
                    exit(0)
                break
        print("pinging service")
        ping_service(TOK, CST)

        #Sell order
        if OPEN_POSITION:
            if ORDER_TYPE == 1:
                print("nous devons vendre")
                if DEAL_ID != -1:
                    close_position(TOK, CST, DEAL_ID)
                else:
                    print("pas de position ouverte")
                DEAL_REF = sell_position(TOK, CST)
                print(DEAL_REF)
                for i in range(10):
                    DEAL_ID = deal_confirmation(TOK, CST, DEAL_REF)
                    if DEAL_ID == -1:
                        print("deal cannot be confirmed retrying in 5 seconds : " + str(i))
                        print(DEAL_ID)
                        time.sleep(5)
                    else:
                        print(DEAL_ID)
                        OPEN_POSITION = False
                        break
        #Buy order
        if not OPEN_POSITION and ORDER_TYPE == 0:
            print("nous devons acheter")
            if DEAL_ID != -1:
                close_position(TOK, CST, DEAL_ID)
            else:
                print("pas de position ouverte")
            DEAL_REF = buy_position(TOK, CST)
            print(DEAL_REF)
            for i in range(10):
                DEAL_ID = deal_confirmation(TOK, CST, DEAL_REF)
                if DEAL_ID == -1:
                    print("deal cannot be confirmed retrying in 5 seconds : " + str(i))
                    print(DEAL_ID)
                    time.sleep(5)
                else:
                    print(DEAL_ID)
                    OPEN_POSITION = True
                    break




