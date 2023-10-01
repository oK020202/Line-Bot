# 年度ごとの新しい検診データのアップロード用関数
# csvはスプレッドシートのフォーマットをcsvでダウンロードしたものを使用 "https://docs.google.com/spreadsheets/d/1Yk9nq6gZi3DorafkZkiQZKgUN9yRICs7LP3byn7AGLo/edit#gid=0"
# 新しいテーブルを作成後、Lambdaのdata_function.pyで参照しているCitiesテーブルを変更する。

import boto3
import csv
import ast
import time

import credentials

# アクセスキーの取得
access_key = credentials.access_key
secret_access_key = credentials.secret_access_key

# クライアントの定義
dynamodb = boto3.resource(
        "dynamodb", 
        region_name='ap-northeast-3',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_access_key,
        )

"""
# テーブル名の設定
"""
table_name = "Cities_20231001"
table_city = dynamodb.Table(table_name)


# csvデータの指定
csv_file = "examination_data_20231001.csv"

def create_table(table_name):
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'address',
                'KeyType': 'HASH'  # Partition key
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'address',
                'AttributeType': 'N'
            },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )



def main():
    # Create a new table
    # テーブルの作成
    create_table(table_name)
    print("Table Created!")

    # テーブルが作成されるまで待機
    time.sleep(5)

    # csvの読み込み
    with open(csv_file) as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i > 0:
                table_city.put_item(
                    Item = {
                        'address': int(row[0]),
                        'stomach': ast.literal_eval(row[2]),
                        'lung': ast.literal_eval(row[3]),
                        'colon': ast.literal_eval(row[4]),
                        'breast': ast.literal_eval(row[5]),
                        'cervical': ast.literal_eval(row[6]),
                        'prostate': ast.literal_eval(row[7]),
                        'oral': ast.literal_eval(row[8]),
                        'calendar': int(row[9]),
                        'url': row[10]
                    }
                )
    print("Data Uploaded!")
    
    return 0



if __name__ == '__main__':
    main()



