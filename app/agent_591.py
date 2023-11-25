import requests
from bs4 import BeautifulSoup
import pandas as pd
from dataclasses import dataclass
import time
from datetime import datetime
import logging
logging.basicConfig(filename='../log/tmp.log', encoding='utf-8', level=logging.INFO)

import configparser
config = configparser.ConfigParser()
config.read('../config/setting.ini')

@dataclass
class House:
    # LINK,售價,權狀坪數,單價,格局,主建物,屋齡,社區,車位,地區,樓層,POST ID
    link: str = None
    price: int = -1
    area: float = 0.0
    unit_price: float = 0.0
    room: str = None
    mainarea: float = 0.0
    houseage: float = 0.0
    community_name: str = None
    cartmodel: str = None
    address: str = None
    floor: str = None
    post_id: str = None
    cdate: datetime = datetime.now()
    title: str = None

class Agent():
    def __init__(self):
        # session = requests.Session()
        self.lineToken = config['line']['token']
        self.lineUrl = config['line']['url']
        self.userAgent = config['line']['useragent']
        print(self.lineToken, self.lineUrl, self.userAgent)
        exit
        pass

    def send_to_line_notify(self, line_message:str):
        logging.info('send_to_line_notify / {}'.format(line_message))
        res = requests.post(self.lineUrl, headers = { "Authorization": "Bearer " + self.lineToken }, data = { 'message': line_message })
        print(res, res.text)

    def createMessage(self, hInfo:House) -> str:
        line_message = '{house_community_name}\n{house_title}\n{house_url}\n {house_price} 萬 / {house_area} 坪\n單價 {house_unit_price}\n{house_room} {house_floor}\n{house_address}\n{house_cartmodel}'.format(
                house_community_name=hInfo.community_name,
                house_title=hInfo.title,
                house_url=hInfo.link,
                house_price=hInfo.price,
                house_area=hInfo.area,
                house_unit_price=hInfo.unit_price,
                house_room=hInfo.room,
                house_floor=hInfo.floor,
                # house_section_name=hInfo.community_name,
                house_address=hInfo.address,
                house_cartmodel=hInfo.cartmodel
            )
        return line_message

    def refresh(self):
        session = requests.Session()
        res = session.get("https://sale.591.com.tw", headers={'User-Agent': self.userAgent})
        soup = BeautifulSoup(res.text, features="html.parser")
        csrf = soup.find('meta', attrs={'name': 'csrf-token'})['content']
        url = "https://sale.591.com.tw/home/search/list?type=2&shType=list&regionid=8&section=104,103,105&price=50$_2000$&pattern=2,3,4,5,6&houseage=$_20$&label=7&order=posttime_desc&timestamp=1694872798593&recom_community=1"
        headers = {
            # 'Host': 'www.591.com.tw',
            # 'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            # 'Content-Type': 'application/json',
            # 'Device':'pc',
            # 'Deviceid': '',
            # 'Referer':'https://sale.591.com.tw/?type=2&shType=list&section=104,103,105&regionid=8&pattern=2,3,4,5,6&price=50$_1500$&houseage=$_20$&label=7&order=posttime_desc&timestamp=1689409388199',
            'X-Csrf-Token':csrf,
            'Cache-Control': 'no-cache'
            # 'X-Requested-With':'XMLHttpRequest',
            # 'Cookie':''
            }
        # res = requests.get(url, headers=headers)
        res = session.get(url, headers=headers)
        # print(res)
        res_json = res.json()
        # print(res_json)
        print(len(res_json['data']['house_list']))
        df = pd.read_csv("../log/house.csv")
        logging.info('before / house.csv len {}'.format(len(df)))
        tmpdatas = []
        for rj in res_json['data']['house_list']:
            if 'is_newhouse' in rj: continue
            # print(rj)
            post_id = rj['houseid']
            if post_id in df['post_id'].values: 
                # print('bypass', post_id)
                continue
            house_title = rj['title']
            house_price = rj['price']
            house_url = 'https://sale.591.com.tw/home/house/detail/2/{post_id}.html'.format(post_id=post_id)
            house_hyperlink = '=HYPERLINK("{house_url}", "{house_title}")'.format(house_url=house_url, house_title=house_title)
            house_section_name = rj['section_name']
            house_address = rj['address']
            house_floor = rj["floor"]
            house_community_name = rj["community_name"]
            house_cartmodel = rj["cartmodel"]
            house_room = rj["room"]
            house_area = rj["area"]
            house_houseage = rj["houseage"]
            house_unit_price = rj["unit_price"]
            house_mainarea = rj["mainarea"]
            # tmpary = [house_hyperlink, house_price, house_area, house_unit_price, house_room, house_mainarea, house_houseage, house_community_name, house_cartmodel, house_section_name+house_section_name, house_floor, post_id]
            tmpdata = House(
                house_url,
                house_price,
                house_area, house_unit_price, house_room, house_mainarea, house_houseage, house_community_name, house_cartmodel, house_section_name+" "+house_address, house_floor, post_id,
                title=house_title)
            print(tmpdata)
            tmpdatas.append(tmpdata)
            line_message = self.createMessage(hInfo=tmpdata)
            print(line_message)
            logging.info('add link {}'.format(post_id))
            self.send_to_line_notify(line_message)
        df = pd.concat([df, pd.DataFrame(tmpdatas)])
        print('end', len(df))
        logging.info('after / house.csv len {}'.format(len(df)))
        df.to_csv('../log/house.csv', index=False)

class Agent591(Agent):
    def __init__(self):
        super().__init__()
        self.mainUrl = "https://sale.591.com.tw/home/search/list?type=2&shType=list&regionid=8&section=104,103,105&price=50$_2000$&pattern=2,3,4,5,6&houseage=$_20$&label=7&order=posttime_desc&timestamp=1694872798593&recom_community=1"
        self.baseUrl = "https://sale.591.com.tw"
        self.mainHeader = {
            'User-Agent': self.userAgent,
            'X-Csrf-Token': None,
            'Cache-Control': 'no-cache'
            }
        pass

    def refresh(self):
        try:
            session = requests.Session()
            res = session.get(self.baseUrl, headers={'User-Agent': self.userAgent})
            soup = BeautifulSoup(res.text, features="html.parser")
            csrf = soup.find('meta', attrs={'name': 'csrf-token'})['content']
            self.mainHeader['X-Csrf-Token'] = csrf
            res = session.get(self.mainUrl, headers=self.mainHeader)
            res_json = res.json()
            print(res_json)
        except Exception as ex:
            print(ex)

    def parsing(self):
        pass

if __name__ == '__main__':
    agent = Agent()
    # while True:
    print('start')
    # df = pd.DataFrame([House()])
    # df.to_csv('../log/house.csv', index=False)
    try:
        print(datetime.now())
        logging.info("start {}".format(datetime.now()))
        agent.refresh()
    except Exception as ex:
        logging.error("error {}".format(ex))
        print(ex)
        # time.sleep(300)  # 暫停 5 秒
    
    
