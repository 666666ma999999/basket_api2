import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
import json

#ワンホット用にpandasをseriesデータに加工
def convert_transaction(df):

    """
    ワンホット用にpandasをseriesデータに加工

    """


    import ast #商品IDに””がついてしまうので除去
    df['ppv_history'] = df['ppv_history'].apply(lambda x: ast.literal_eval(x))
    
    transactions = df['ppv_history'].values.tolist()#[:100]
    #print(transactions)
    return transactions

# アポリオリアルゴリズム学習用のデータセットを作成
def encode_transactions(transactions):

    """
    アポリオリアルゴリズム学習用のデータセットを作成
    """

    all_items = sorted(set(item for sublist in transactions for item in sublist))
    encoded_df = pd.DataFrame([[int(item in transaction) for item in all_items] for transaction in transactions], columns=all_items)
    return encoded_df

# アポリオリアルゴリズムを実行
def apriori_algorithm(transactions):
    
    """
    アポリオリ用の値を設定し、アルゴリズムを実行し、アポリオリデータのマスターデータを作成する

    """


    df_encoded = encode_transactions(transactions)
    frequent_itemsets = apriori(df_encoded, min_support=0.02, use_colnames=True)
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.1, num_itemsets=len(frequent_itemsets))
    rules_set = rules.sort_values(by='support', ascending=False)
    return rules_set

# ルールから特定の商品に関連する信頼度TOP10を抽出
def get_top_10_confidence_items(item_list, rules):
    
    """
    アポリオリのマスターデータから、併売が多い商品を、商品IDごとに羅列したデータを作る

    """


    #データを格納する空リスト
    recommendations = []

    #商品IDごとに信頼度TOP10を作成
    for item_id in item_list:

        # antecedentsが1つのアイテムだけで構成されているルールをフィルタリング
        filtered_rules = rules[rules['antecedents'].apply(lambda x: len(x) == 1 and item_id in list(x))]

        #　信頼度をもとにしてtop10を表示
        top_10 = filtered_rules.sort_values(by='confidence', ascending=False)#.head(200)
        associated_items = [list(rule['consequents'])[0] for _, rule in top_10.iterrows() if len(rule['consequents']) == 1]   #return [item for sublist in associated_items for item in sublist]
        print(item_id , filtered_rules , top_10)

        recommendations.append({'Key': item_id, 'Value': associated_items})
        #recommendations.append([item_id , associated_items])

    return recommendations


# jsonに変換
def convert_json(recommendations):

    """
    データをjsonに変換
    """

    # ファイル名の定義
    json_filename = 'output_basket.json'

    # リスト内包表記を使用して辞書のリストに変換
    # data_dict_list = [{'Key': key, 'Value': values} for key, values in recommendations]
    
    with open(json_filename, 'w', encoding='utf-8') as f:
        #json.dump(data_dict_list, f, ensure_ascii=False, indent=4)
        json.dump(recommendations, f, ensure_ascii=False, indent=4)


    print(f"データを '{json_filename}' に保存しました。")

    return


def main():

    #read csv -> pandas
    df = pd.read_csv('./ppv_processing.csv', index_col=0)

    # pandas -> transaction
    transction = convert_transaction(df)

    # machine learnig
    rules_set = apriori_algorithm(transction)
    #print(df[:10] , transction , encoded_df , rules_set)
 
    # TODO: listはppv_processing.csvのppv_history　colmunから生成する
    # 商品作成する商品IDリスト
    item_list = ['002', '003', '009', '403', '035', '036', '008', '001', '010', '020', '024', '026', '025', '052', '402', '5', '027', '028', '021', '022', '061', '055', '046', '004', '015', '016', '031', '032', '059', '049', '058', '610', '060', '041', '029', '006', '007', '012', '018', '019', '023', '051', '045']

    basket_data = get_top_10_confidence_items(item_list , rules_set)

    convert_json(basket_data)


if __name__ == "__main__":
    main()