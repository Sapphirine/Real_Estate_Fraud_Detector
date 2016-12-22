import requests
import re
from bs4 import BeautifulSoup as bs4
import datetime
import time
import calendar

def remove_non_ascii(text):
    return ''.join(i for i in text if ord(i)<128)

while True:
    print('Waiting for 4pm local time...')
    while time.localtime().tm_hour != 16:
        time.sleep(60*5)
        
    startTime = time.time()
    s = ','
    n = 25
    number = 0
    constrainDate = True

    if constrainDate:
        filename = 'C:/Users/nathaniel.jones/Documents/Grad School/BigData/Craigslist Data/craigslist_data_' + datetime.date.today().isoformat() + '.csv'
    else:
        filename = 'C:/Users/nathaniel.jones/Documents/Grad School/BigData/Craigslist Data/craigslist_data_' + datetime.date.today().isoformat() + '_and-before.csv'

    f = open(filename,'w')

    items = ('ID', 'State', 'Region', 'Title', 'Price', 'Date', 'Bedrooms', 'Sqft', 'Neighborhood', 'URL') 
    line = s.join(items) + '\n';
    #f.write(line)

    rsp = requests.get('http://www.craigslist.org/about/sites')
    html = bs4(rsp.text, 'html.parser')
    header = html.find_all('a', attrs={'name': 'US'})[0].parent
    #print(header)
    usOnly = header.next_sibling.next_sibling
    #print(usOnly)
                
    regionList = usOnly.find_all('li')
    regions = []
    for region in regionList:
        inner = region.find_all('a')
        if len(inner) > 0:
            if 'www' not in inner[0]['href'] and 'forums' not in inner[0]['href']:
                regions.append(inner[0])
                #print(inner[0])

    try:
        idf = open('lastID.txt','r')
        number = int(idf.read())
        idf.close()
    except:
        pass

    page = 0
    for region in regions:
        for i in range(n):
            urlItems = region['href'].split('/')
            url_base = 'http://'+urlItems[2]+'/search/'+urlItems[3]+'/apa'
            params = dict(s=i*100)
            waitTime = 10
            success = False
            while waitTime < 2*3600:
                try:
                    rsp = requests.get(url_base, params=params)
                    success = True
                    break
                except:
                    print("Connection rejected, waiting " + str(waitTime) + " seconds")
                    time.sleep(waitTime)
                    waitTime = waitTime*2

            if not success:
                continue
                
            html = bs4(rsp.text, 'html.parser')
            #if html.head != None:
            if 'Page Not Found' in html.head.title.text:
                url_base = 'http://'+urlItems[2]+'/search/'+urlItems[3]+'/aap'
                waitTime = 10
                success = False
                while waitTime < 2*3600:
                    try:
                        rsp = requests.get(url_base, params=params)
                        success = True
                        break
                    except:
                        print("Connection rejected, waiting " + str(waitTime) + " seconds")
                        time.sleep(waitTime)
                        waitTime = waitTime*2

                if not success:
                    continue
                html = bs4(rsp.text, 'html.parser')
            if 'Page Not Found' in html.head.title.text:
                print('[ERROR] Could not get apartments page for region ' + region.text)
                print('Last attempted URL: ' + url_base)
                continue
            else:
                #print(url_base)
                page = page + 1
                print('Parsing page ' + str(page) + ' of ' + str(n*len(regions)) + ' for date ' + datetime.date.today().isoformat()) # + ' ' + str(page/(25*len(regions))) + '% complete')

            html = bs4(rsp.text, 'html.parser')
            listings = html.find_all('li', attrs={'class': 'result-row'})
            for apt in listings:
                priceList = apt.find_all('span', attrs={'class': 'result-price'})
                dateList = apt.find_all('time', attrs={'class': 'result-date'})
                bedroomsList = apt.find_all('span', attrs={'class': 'housing'})
                neighborhoodList = apt.find_all('span', attrs={'class': 'result-hood'})
                titleList = apt.find_all('a', attrs={'class': 'result-title hdrlnk'})

                price = 'null'
                date = 'null'
                bedrooms = 'null'
                sqft = 'null'
                neighborhood = 'null'
                title = 'null'
                link = 'null'

                if len(priceList) > 0:
                    price = priceList[0].text.strip()
                if len(dateList) > 0:
                    date = dateList[0]['datetime']
                if len(bedroomsList) > 0:
                    housingInfo = bedroomsList[0].text.split('\n')
                    for item in housingInfo:
                        if 'br' in item:
                            bedrooms = item.strip().replace(' -','')
                        elif 'ft' in item:
                            sqft = item.strip().replace(' -','')
                    
                if len(neighborhoodList) > 0:
                    neighborhood = neighborhoodList[0].text.strip()
                if len(titleList) > 0:
                    title = titleList[0].text.strip().replace(',',';')
                    link = 'http://'+urlItems[2] + titleList[0]['href']

                if constrainDate:
                    #postDate = int(date.split(' ')[0].split('-')[2])
                    #thisDate = int(datetime.date.today().isoformat().split('-')[2])
                    #if (postDate >= thisDate-5):
                    if datetime.date.today().isoformat() == date.split(' ')[0]:
                        continue

                items = (str(number), region.parent.parent.previous_sibling.previous_sibling.text, region.text, title, price, date, bedrooms, sqft, neighborhood, link) 
                line = s.join(items) + '\n';
                f.write(remove_non_ascii(line))
                number = number + 1
            #time.sleep(5)

    f.close()

    idf = open('lastID.txt','w')
    idf.write(str(number))
    idf.close()

    elapsedTime = time.time()-startTime
    print('Done - Elapsed time: ' + str(elapsedTime) + ' seconds')
    #time.sleep(3600*24-elapsedTime)

#        print(price)
#        print(date)
#        print(bedrooms)
#        print(sqft)
#        print(neighborhood)
#        print(title)
#        print(link)
#        print('------------------------------')
        
        
        
        
        
