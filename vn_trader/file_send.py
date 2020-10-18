import requests
import json


def send_wechat(msg):
    url = "https://sc.ftqq.com/SCU117954T89c5fb8776dad557532bd156ec1300af5f84fe6d09444.send"
    data= {'text':msg}
    #content ='?desp=strategy id'
    try:
        res = requests.post(url=url, data= data)
    except:
        pass