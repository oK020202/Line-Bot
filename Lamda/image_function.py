import boto3
from PIL import Image
import io
import random, string

from botocore.client import Config


#s3 = boto3.client('s3')
s3 = boto3.client('s3', config=Config(signature_version='s3v4')) # V4を使うと明示的に宣言する必要がある

BUCKET = 'ganjiinstant'


#imgをS3バケットに保存して、署名付きURLを取得
def get_presigned_url(pil_image):
    KEY = 'tmp/' + randomname(10) + '.png'
    
    # 保存領域を用意
    buf = io.BytesIO()
    
    # 用意したメモリに保存
    pil_image.save(buf, 'PNG')
    
    # バイトデータをアップロード
    s3.put_object(Bucket=BUCKET, Key=KEY, Body=buf.getvalue())
    
    header_location = s3.generate_presigned_url(
        ClientMethod = 'get_object',
        Params = {'Bucket' : BUCKET, 'Key' : KEY},
        ExpiresIn = 3600,
        HttpMethod = 'GET'
        )
    
    result = {"Location": header_location}
    return result


#引数のファイル名の画像をimgに読み込み
def download_file(img_name):
    KEY = img_name
    
    # オブジェクトデータを取得
    s3_object = s3.get_object(Bucket=BUCKET, Key=KEY)
    
    # バイトデータを読み込み
    image_data = io.BytesIO(s3_object['Body'].read())
    
    # 画像に変換
    pil_image = Image.open(image_data)
    
    return pil_image


#ランダムな文字列生成
def randomname(n):
   randlst = [random.choice(string.ascii_letters + string.digits) for i in range(n)]
   return ''.join(randlst)
