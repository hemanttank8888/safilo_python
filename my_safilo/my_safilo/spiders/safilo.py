import json
import scrapy
import os
import requests
from bs4 import BeautifulSoup


class SafiloSpider(scrapy.Spider):
    name = "safilo"
    data_list = []

    def get_cookie(self):
        login_url = "https://www.mysafilo.com/US/login/login"

        session = requests.Session()
        response = session.get(login_url)
        soup = BeautifulSoup(response.text, "html.parser")
        form = soup.find("form", class_="login-form")
        login_data = {}
        for input_field in form.find_all("input"):
            name = input_field.get("name")
            value = input_field.get("value")
            print(name,"???",value,"?>>>>>>>>>>>>>>>>>>>>>>>>>")
            if name and value:
                print("uyes")
                login_data[name] = value
        print(login_data,"><<<<<<<")
        # Add your login credentials
        login_data["Identifier"] = "0001119227"
        login_data["Password"] = "Joel@6840"

        response = session.post(login_url, data=login_data)
        cookies = session.cookies
        return cookies

    def start_requests(self):
        new_cookies = self.get_cookie()
        print(new_cookies,"new cokkies is >>>>>>>>>>>")
        url = 'https://www.mysafilo.com/US/catalog/index'
        cookies_str = "; ".join([f"{cookie.name}={cookie.value}" for cookie in new_cookies])
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            'cookie': cookies_str
        }
        cookies = {cookie.name: cookie.value for cookie in new_cookies}

        yield scrapy.Request(url,headers=headers,cookies=cookies,callback=self.parse,dont_filter=True,meta = {'cookies':cookies})

    def parse(self, response):
        brand_names = [i.strip() for i in response.xpath("//ul[@class='nav-ul nav-ul-brands b2b']//li//text()").getall() if i.strip()]
        for brand in brand_names:
            data_url = "https://www.mysafilo.com/US/api/CatalogAPI/filter"
            body = {
            "Collections": [
                f"{brand}"
            ],
            "ColorFamily": [],
            "Price": {
                "min": -1,
                "max": -1
            },
            "Shapes": [],
            "FrameTypes": [],
            "Genders": [],
            "FrameMaterials": [],
            "FrontMaterials": [],
            "HingeTypes": [],
            "RimTypes": [],
            "TempleMaterials": [],
            "NewStyles": False,
            "BestSellers": False,
            "RxAvailable": False,
            "InStock": False,
            "ASizes": {
                "min": -1,
                "max": -1
            },
            "BSizes": {
                "min": -1,
                "max": -1
            },
            "EDSizes": {
                "min": -1,
                "max": -1
            },
            "DBLSizes": {
                "min": -1,
                "max": -1
            },
            "brandName": f"{brand}"
            }
            headers = {
                "content-type": "application/json",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
            }

            cookies = response.meta['cookies']

            yield scrapy.Request(data_url,method='POST',headers=headers,body=json.dumps(body),cookies=cookies,callback=self.fetch_data,dont_filter=True)
            

    def fetch_data(self, response):
        get_json_respone = response.json()
        for product in get_json_respone:
            for colors in product['colorGroup']:
                for sizes in colors['sizes']:
                    upc = sizes['frameId']
                    color = sizes['color']
                    size = sizes['size']
                    lens = sizes['lens']
                    lens_material = sizes['lensMaterial']
                    availability = sizes['availableStatus']
                    available_date = sizes['availableDate']
                    best_seller = sizes['isBestSeller']
                    frame_type = sizes['frameType']
                    gender = sizes['gender']
                    can_RX = sizes['canRX']
                    front_material = sizes['frontMaterial']
                    temple_material = sizes['templeMaterial']
                    shape = sizes['shape']
                    hinge_type = sizes['hingeType']
                    rim_type = sizes['rimType']
                    a = sizes['a']
                    b = sizes['b']
                    ed = sizes['ed']
                    dbl = sizes['dbl']
                    base_curve = sizes['baseCurve']
                    frame_material = sizes['material']
                    styleName = sizes['styleName']
                    images = [i['id'] for i in sizes['imageIds']]

                    data_dict = {
                        'upc': upc,
                        'color': color,
                        'size': size,
                        'lens': lens,
                        'lens material': lens_material,
                        'availability': availability,
                        'available_date': available_date,
                        'best seller': best_seller,
                        'frame type': frame_type,
                        'gender': gender,
                        'can RX': can_RX,
                        'front material': front_material,
                        'temple material': temple_material,
                        'shape': shape,
                        'hinge type': hinge_type,
                        'rim type': rim_type,
                        'a': a,
                        'b': b,
                        'ed': ed,
                        'dbl': dbl,
                        'base curve': base_curve,
                        'frame material': frame_material,
                        'styleName' : styleName
                    }

                    for url in images:
                        url = "https://www.mysafilo.com/US/api/catalogapi/imagebyid/" + url
                        yield scrapy.Request(url,callback = self.image_response,meta = {"data_dict":data_dict,'styleName':styleName})
    
    def image_response(self, response):
        data_dict = response.meta["data_dict"]
        styleName = response.meta["styleName"]

        image_data = response.body
        image_filename = f"image_output/{styleName}/{data_dict['upc']}.jpg"
        os.makedirs(os.path.dirname(image_filename), exist_ok=True)
        with open(image_filename, 'wb') as image_file:
            image_file.write(image_data)

        self.data_list.append(data_dict)

    def closed(self, reason):
        with open("output.json", "w") as output_file:
            json.dump(self.data_list, output_file)
        


