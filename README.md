

make_ppvcsv.ipynd
→自社DBの購入データDBにアクセスし、当該サイトの全購入データを取得
(DB connect)  (output)ppv_processing.csv

make_basket.py
→全購入データをアポリオリを使用し、該当商品のレコメンドデータを作る
(input)ppv_processing.csv (output) output_basket.json

api_basket.py
→作り途中なので今回のレビュー対象外