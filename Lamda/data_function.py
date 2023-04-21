"""
データベース操作用のパッケージ by
"""
import json
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr
import time
import datetime
from datetime import timedelta

#ユーザデータベース
table = boto3.resource('dynamodb').Table('Users')
#市町村データベース
table_city = boto3.resource('dynamodb').Table('Cities')
#重複実行防止用データベース
table_event = boto3.resource('dynamodb').Table('eventHistory')

cancer_list = ['stomach', 'lung', 'colon', 'breast', 'cervical', 'prostate', 'oral']


#登録
def put_data(user_id, address = None, sex = None, birthday = None):
    table.put_item(
        Item = {
            'user_id': user_id,
            'timestamp': int(time.time()),
            'address': address,
            'sex': sex,
            'birthday': birthday
        }
    )


#修正
def modify_data(user_id, address = None, sex = None, birthday = None):
    if address is not None:
        option_a = {
            'Key': {'user_id': user_id},
            'UpdateExpression': 'set #address = :address',
            'ExpressionAttributeNames': {
                '#address': 'address'
            },
            'ExpressionAttributeValues': {
                ':address': address
            }
        }
        table.update_item(**option_a)
        
    if sex is not None:
        option_s = {
            'Key': {'user_id': user_id},
            'UpdateExpression': 'set #sex = :sex',
            'ExpressionAttributeNames': {
                '#sex': 'sex'
            },
            'ExpressionAttributeValues': {
                ':sex': sex
            }
        }
        table.update_item(**option_s)
    
    if birthday is not None:
        option_b = {
            'Key': {'user_id': user_id},
            'UpdateExpression': 'set #birthday = :birthday',
            'ExpressionAttributeNames': {
                '#birthday': 'birthday'
            },
            'ExpressionAttributeValues': {
                ':birthday': birthday
            }
        }
        table.update_item(**option_b)
        
    option_t = {
        'Key': {'user_id': user_id},
        'UpdateExpression': 'set #timestamp = :timestamp',
        'ExpressionAttributeNames': {
            '#timestamp': 'timestamp'
        },
        'ExpressionAttributeValues': {
            ':timestamp': int(time.time())
        }
    }
    table.update_item(**option_t)
    

#削除
def delete_data(user_id):
    table.delete_item(
        Key = {
            'user_id': user_id
        }
    )


#取得
def get_data(user_id):
    user = table.get_item(
        Key = {
            'user_id': user_id
        }
    )
    
    return user


#発火(全ユーザ)
def ignite_all(birth_only):
    #全ユーザ情報の取得
    data = get_all_data()
        
    result = {}
    for item in data:
        if birth_only == 1:
            #誕生日orその半年後のユーザ以外無視
            if item['birthday'] == None:
                continue
            birthday = datetime.date.fromisoformat(item['birthday'])
            half_later_birthday = birthday + timedelta(days=182)
            today = datetime.date.today()
            if birthday.month != today.month and half_later_birthday.month != today.month:
                continue
            if birthday.day != today.day and half_later_birthday.day != today.day:
                continue
            
        #辞書に追加
        key = item['user_id']
        result[key] = []
        
        #未入力ユーザ属性の確認
        if item['sex'] == None:
            #print("No sex")
            result[key].append(None)
            continue
        if item['birthday'] == None:
            #print("No birthday")
            result[key].append(None)
            continue
        if item['address'] == None:
            #print("No address")
            result[key].append(None)
            continue
        
        #市町村の検診情報の取得
        city = get_city_data(item['address'])
        if 'Item' not in city:
            #print("No information of the city")
            result[key].append(None)
            continue
        
        #性別ごとの実施検診
        sex = item['sex']
        exam = set_exam(sex)
        
        #誕生日から年齢に変換
        old = calc_old(datetime.date.fromisoformat(item['birthday']), city['Item']['calendar'])
        
        result_list = make_possible_list(city, exam, old)
            
        result[key].append(result_list)
        result[key].append(city['Item']['url'])
        
        if sex == 2:
            exam = set_exam(1)
            result_list = make_possible_list(city, exam, old)
            result[key].append(result_list)
    
    return result


#発火(ユーザ指定)
def ignite_one(user_id):
    #ユーザ情報の取得
    user = get_data(user_id)
    if 'Item' not in user:
        #print("No information of the user")
        return None
        
    #未入力ユーザ属性の確認
    if user['Item']['sex'] == None:
        #print("No sex")
        return None
    if user['Item']['birthday'] == None:
        #print("No birthday")
        return None
    if user['Item']['address'] == None:
        #print("No address")
        return None

    #市町村の検診情報の取得
    city = get_city_data(user['Item']['address'])
    if 'Item' not in city:
        #print("No information of the city")
        return None
    
    #性別ごとの実施検診
    sex = user['Item']['sex']
    exam = set_exam(sex)
    
    #誕生日から年齢に変換
    old = calc_old(datetime.date.fromisoformat(user['Item']['birthday']), city['Item']['calendar'])
    
    result_list = make_possible_list(city, exam, old)
    result = [result_list, city['Item']['url']]
    
    if sex == 2:
        exam = set_exam(1)
        result_list = make_possible_list(city, exam, old)
        result.append(result_list)
    
    return result


#各検診の受診可を判定(内部関数)
def make_possible_list(city, exam, old):
    result_list = []
    
    for i in range(len(exam)):
        #性別で未実施の検診は-1
        if exam[i] == False:
            result_list.append(-1)
            continue
        
        cancer = city['Item'][cancer_list[i]]
        
        #市町村で未実施の検診も-1
        if cancer[0] < 0:
            result_list.append(-1)
            continue
        
        #年齢が満たない場合は、受けられるようになるまでの年
        diff = cancer[0] - old
        if diff > 0:
            result_list.append(int(cancer[0]))
            continue
        
        #終了年齢を超えている場合も-1
        if old - cancer[2] > 0:
            result_list.append(-1)
            continue
        
        #受けられるようになるまでの年(0なら現在受診可)
        diff = diff * (-1)
        interval = cancer[1]
        
        address = city['Item']['address'] #途中で間隔が変わる市町村対応
        if len(cancer) == 5:
            if old >= cancer[3]:
                diff = old - cancer[3]
                interval = cancer[4]
                
        if diff % interval != 0:
            result_list.append(int(old + interval - (diff % interval)))
        else:
            result_list.append(0)
        
    return result_list


#全ユーザ情報の取得(内部関数)
def get_all_data():
    response = table.scan()
    data = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])
    
    return data


#性別ごとの実施検診(内部関数)
def set_exam(sex):
    exam = [True, True, True, True, True, True, True]
    if sex == 0 or sex == 2:
        exam[3] = False
        exam[4] = False
    elif sex == 1:
        exam[5] = False
    
    return exam


#市町村の検診情報の取得(内部関数)
def get_city_data(address):

    city = table_city.get_item(
        Key = {
            'address': address
        }
    )
    
    return city


#誕生日から満年齢or実年齢に変換(内部関数)
def calc_old(birthday, calendar):
    today = datetime.date.today()
    if calendar == 0:
        if today.month >= 4:
            fy_end = today.replace(year=today.year+1, month=3, day=31)
        else:
            fy_end = today.replace(month=3, day=31)
        return (int(fy_end.strftime("%Y%m%d")) - int(birthday.strftime("%Y%m%d"))) // 10000
    else:
        return (int(today.strftime("%Y%m%d")) - int(birthday.strftime("%Y%m%d"))) // 10000


#市町村検診情報の登録
def put_city_data(address, stomach, lung, colon, breast, cervical, prostate, oral, calendar, url):
    table_city.put_item(
        Item = {
            'address': address,
            'stomach': stomach,
            'lung': lung,
            'colon': colon,
            'breast': breast,
            'cervical': cervical,
            'prostate': prostate,
            'oral': oral,
            'calendar': calendar,
            'url': url
        }
    )
    

#重複実行のチェック
def duplication_check():
    dt_now = datetime.datetime.now()
    event_id = str(dt_now.year) +"-"+ str(dt_now.month) +"-"+ str(dt_now.day)
    try:
        item = {
            'eventId': event_id
        }
        response = table_event.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(eventId)'
        )
        duplication_flg = 0
    except Exception:
        duplication_flg = 1
    
    return duplication_flg


'''
def decimal_default_proc(obj):
    
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError
'''
