import csv
import ast
import pprint

table_name = "examination_data_20231001.csv"

with open(table_name) as f:
    reader = csv.reader(f)
    for i, row in enumerate(reader):
        if i > 0:
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
            #print(Item)