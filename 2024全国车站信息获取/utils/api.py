# coding:utf-8

from urllib import parse
import urllib.request as req
import json
import sys

def openurl(url):
    res = req.Request(url)
    response = req.urlopen(res)
    content = response.read().decode("utf-8")
    return content

def search(key):
    name = key
    key = parse.quote(key)
    search_url = f'http://cnrail.geogv.org/api/v1/match_feature/{key}?locale=zhcn&query-override='
    result = openurl(search_url)
    result = json.loads(result)
    for data in result['data']:
        if data[2] == name:
            return data
    return result['data'][0] # [id, type, name]

def station(key, search_type = 'ilt'): # i: infomation l: link t:trainlist
    if key.isdigit() == False:
        key = search(key)[0]
    
    result = {}
    if 'i' in search_type: # 车站信息查询
        station_url = f'http://cnrail.geogv.org/api/v1/station/{key}?locale=zhcn&query-override=&requestGeom=true'
        station_info = openurl(station_url)
        station_info = json.loads(station_info)
        result.update({'info':station_info})
    if 'l' in search_type: # 车站连接查询
        link_url = f'http://cnrail.geogv.org/api/v1/station-link/{key}?locale=zhcn&query-override='
        link = openurl(link_url)
        link = json.loads(link)
        result.update({'link':link})
    if 't' in search_type: # 车站车次查询
        trainlist_url = f'http://cnrail.geogv.org/api/v1/station_route/{key}?locale=zhcn&query-override='
        trainlist = openurl(trainlist_url)
        trainlist = json.loads(trainlist)
        result.update({'trainlist':trainlist})
    return result

def rail(key):
    if key.isdigit() == False:
        key = search(key)[0]
    rail_url = f'http://cnrail.geogv.org/api/v1/rail/{key}?locale=zhcn'
    rail_info = openurl(rail_url)
    rail_info = json.loads(rail_info)
    return rail_info

def train(key):
    if '~' not in key:
        if key.isdigit() == False:
            key = list(key)
            while len(key) < 5:
                key.insert(1,'0')
        key = ''.join(key)
        key = key.upper()
        key = 'CN~' + key
    train_url = f'http://cnrail.geogv.org/api/v1/route/{key}?locale=zhcn&query-override=&requestGeom=true'
    train_info = openurl(train_url)
    train_info = json.loads(train_info)
    return train_info


def print_help():
    msg = '\n--search [key]: search for the id and the type for the key'
    msg += '\n--station [name] [-i,-l,-t]: show the infomation for the station'
    msg += '\n\t-i: infomation, -l: linked railway, -t: related train'
    msg += '\n--rail [name]: show the infomation for the railway'
    msg += '\n--train [name]: show the infomation for the train'
    print(msg)

def main():
    argv = sys.argv
    if len(argv) < 2 or (len(argv) == 2 and argv[1] in ('-h','--help')) or argv[1] not in ('--search','--station','--rail','--train'):
        print_help()
        return
    key = argv[2]
    if argv[1] == '--search':
        ID, Type, name= search(key)
        print(f'name: {name}\ntype: {Type}\nid: {ID}')
    elif argv[1] == '--station':
        k = ''.join(argv[3:])
        if k == '':
            k = 'ilt'
        result = station(key,k)
        msg = ''
        if 'i' in k:
            info = result['info']
            name = info['localName']
            sedname = info['sedName']
            bureau = info['bureau']['name']
            location = info['location']
            longititude = info['x']
            latitude = info['y']
            station_id = info['id']
            
            msg += f'\nname: {name}'
            msg += f'\nEnglish name: {sedname}'
            msg += f'\nstation id: {station_id}'
            msg += f'\nbureau: {bureau}'
            msg += f'\nlocation: {location}'
            msg += f'\nlongtitude: {longititude}'
            msg += f'\nlatitude: {latitude}'

        if 'l' in k:
            link = result['link']['data']
            for l in link:
                
                subline = l['subLine']
                rail_name = l['railName']
                msg += f'\nrail name: {rail_name}({subline})'
                for next_stat in l['next']:
                    next_stat_name = next_stat[2]
                    sub = next_stat[3]
                    terminal = next_stat[8]
                    if terminal == '*':
                        msg += '\n\tnext station: terminal'
                    else:
                        msg += f'\n\tnext station({sub}): {next_stat_name} terminal: {terminal}'
                for prev_stat in l['prev']:
                    prev_stat_name = prev_stat[2]
                    sub = prev_stat[3]
                    terminal = prev_stat[8]
                    if terminal == '*':
                        msg += '\n\tprevious station: terminal'
                    else:
                        msg += f'\n\tprevious station({sub}): {prev_stat_name} terminal: {terminal}'
        
        if 't' in k:
            trainlist = result['trainlist']['data']['trains']
            for train_id in trainlist:
                train_no = train_id[1]
                arr = train_id[3][1:3] + ':' + train_id[3][3:5]
                depart = train_id[4][1:3] + ':' + train_id[4][3:5]
                start = train_id[7]
                end = train_id[8]
                msg += f'\ntrain: {train_no} arrival: {arr} departure: {depart} from: {start} to: {end}'
        print(msg)

    elif argv[1] == '--rail':
        info = rail(key)
        info = info['data']
        name = info['name']
        line_num = info['lineNum']
        speed = info['designSpeed']
        elec = info['elec']

        msg = ''
        msg += f'\nname: {name}'
        msg += f'\nline num: {line_num}'
        msg += f'\ndesign speed: {speed}'
        msg += f'\nelectrification: {elec}'
                
        record = info['diagram']['records']
        msg += f'\nkm\ttype\tname'
        for p in record:
            #print(p)
            if p[0] in  {'STR','CONTg','CONTf'}:
                continue
            miles = p[1]
            tp = p[3][0][0]
            point = p[3][0][2]
            msg += f'\n{miles}\t{tp}\t{point}'
        print(msg)

    elif argv[1] == '--train':
        info = train(key)
        info = info['data']
        name = info['operationId']

        msg = ''
        msg += f'\nname: {name}'
        msg += f'\nstation\tarrival\tdeparture\tlocation'
        for stop in info['stops']:
            stat = stop[1]
            arr = stop[2][1:3] + ':' + stop[2][3:5]
            depart = stop[3][1:3] + ':' + stop[3][3:5]
            location = stop[4]
            msg+=f'\n{stat}\t{arr}\t{depart}\t\t{location}'

        print(msg)
            


if __name__ == '__main__':
    main()