import json
import data_function

def lambda_handler(event, context):
    
    NON = -1
    MAX = 200
    #市町村検診情報の登録(市町村番号, [胃], [肺], [大腸], [乳], [子宮頸], [前立腺], [口腔], 年度末, URL)
    #大阪市
    data_function.put_city_data(0, [40,1,MAX], [40,1,MAX], [40,1,MAX], [30,2,MAX], [20,2,MAX], [50,5,70], [NON,NON,NON], 0, 'https://www.city.osaka.lg.jp/kenko/page/0000008503.html')
    #堺市
    data_function.put_city_data(1, [50,2,MAX], [40,1,MAX], [40,1,MAX], [40,2,MAX], [20,2,MAX], [50,2,69], [NON,NON,NON], 1, 'https://www.city.sakai.lg.jp/kenko/kenko/kenshin/0923.html')
    
    
    #登録
    #ユーザ0a
    data_function.put_data('0a') #ユーザID:0a
    data_function.modify_data('0a', sex = 0) #性別:男
    data_function.modify_data('0a', birthday = '1969-11-23') #1969年11月23日生まれ
    data_function.modify_data('0a', address = 0) #大阪市在住
    #ユーザ1b
    data_function.put_data('1b', sex=1, birthday='1972-02-03', address=1)
    #ユーザ2c
    data_function.put_data('2c')
    #ユーザ3d
    data_function.put_data('3d', sex=2, birthday='1979-08-25', address=0)
    
    
    #発火(ユーザ指定)
    result_one = data_function.ignite_one('0a')
    print("ignite_one:")
    print(result_one) 
    #出力例：[[0, 0, 0, -1, -1, 3, -1], 'https://www.city.osaka.lg.jp/kenko/page/0000008503.html']
    
    result_one = data_function.ignite_one('2c')
    print("ignite_one:")
    print(result_one)
    #出力例：None
    
    #発火(全ユーザ:引数0)
    result_all = data_function.ignite_all(0)
    print("ignite_all")
    print(result_all) 
    #出力例：{'0a': [[0, 0, 0, -1, -1, 3, -1], 'https://www.city.osaka略'], '2c': [None], 以下略}
    
    #発火(誕生日orその半年後のユーザのみ:引数1)
    result_all = data_function.ignite_all(1)
    print("ignite_all_birth_only")
    print(result_all) 
    #出力例(8/25に実行)：{'3d': [[0, 0, 0, 1, 1, 7, -1], 'https://www.city.osaka略']}
    
    #変更
    #data_function.modify_data('0a', address = 1) #堺市に変更
    
    
    #削除
    #data_function.delete_data('0a')
    
    
    #取得
    #user = data_function.get_data('0a')
    #print("get_data")
    #print(user['Item'])
    
    
    return {
        'statusCode': 200
    }
    