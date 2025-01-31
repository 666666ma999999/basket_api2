# FastAPIとその他必要なモジュールをインポート
from fastapi import FastAPI, Request, Form  # FastAPIフレームワークの主要コンポーネントをインポート
from fastapi.templating import Jinja2Templates  # HTMLテンプレートエンジンのJinja2をインポート
from fastapi.staticfiles import StaticFiles  # 静的ファイル配信用モジュールをインポート
from fastapi.exceptions import RequestValidationError

from fastapi.responses import HTMLResponse  # HTML形式のレスポンス用モジュールをインポート
from datetime import date  # 日付処理用のdateクラスをインポート
import requests

# FastAPIアプリケーションのインスタンスを作成
#app = FastAPI()


def read_json(json_filename):
    import json

    # JSONファイルの読み込み
    with open(json_filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    #print("方法1で読み込んだデータ:" , data[0:2])

    return data


def response_id(ppv_id , ref_data):

    #ユーザー個人情報 (まだ実装できず)
    member_id = '' 
    ppv_paid = ['005', '026' , '036']

    # 該当するエントリを検索
    for entry in ref_data:
        if entry['Key'] == ppv_id:
            value = entry['Value']

            '''
            #購入したid を除外。
            data = [v for v in value if v not in ppv_paid ] 
            '''

            break

            print(f"キー '{ppv_id}' に対応する値: {value}")
    
        else:
            value = 0
            print(f"キー '{ppv_id}' は見つかりませんでした。")

    return value

def main():
    json_ref = read_json('output_basket.json')

    recommend_id = response_id('099' , json_ref)
    print(recommend_id)


if __name__ == "__main__":
    main()
