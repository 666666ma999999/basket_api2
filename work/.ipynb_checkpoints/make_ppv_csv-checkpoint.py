import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.sql import text
import pymysql
import subprocess
import time
from sshtunnel import SSHTunnelForwarder
from sqlalchemy.exc import SQLAlchemyError
import settings
import os

def ssh_request(local_port , remote_port):

    # 現在の作業ディレクトリの絶対パスを取得
    current_directory = os.getcwd()

    # SSH接続情報
    ssh_host = settings.SSH_HOST
    ssh_port = settings.SSH_PORT
    ssh_user = settings.SSH_USER
    ssh_key = current_directory + settings.SSH_KEY
    
    print(ssh_host, ssh_port, ssh_user, ssh_key)

    """SSHトンネルを確立する"""
    ssh_command = [
        'ssh',
        '-i', ssh_key,
        '-L', f'{local_port}:127.0.0.1:{remote_port}',
        '-N',  # コマンドを実行せずにフォアグラウンドで実行
        '-f',  # バックグラウンドで実行
        '-p', str(ssh_port),
        f'{ssh_user}@{ssh_host}'
    ]

    subprocess.run(ssh_command, check=True)
    
    # SSHトンネルが確立されるまで少し待つ
    time.sleep(5)

    print(f"SSH tunnel established on local port {local_port}")



def db_connect(local_port , site_id , start_day , end_day):

    # データベースの接続情報
    db_user = settings.DB_USER
    db_password = settings.DB_PASSWORD
    db_host = settings.DB_HOST
    db_port = settings.DB_PORT
    db_name = settings.DB_NAME

    try:
        # データベースに接続する　
        engine = create_engine(f'mysql+pymysql://{db_user}:{db_password}@127.0.0.1:{local_port}/{db_name}')
        print("Database connection established.")

        # DB取得クエリ
        subscribe_query = text("""
            SELECT *
            FROM swan_analyze.analyze_ppv_all
            WHERE public_flg = 1 AND site_id = :site_id AND date >= :start_day AND date <= :end_day
            """)

        # クエリ実行
        with engine.connect() as connection:
            result = connection.execute(
                subscribe_query,
                {"site_id": site_id , "start_day":start_day , "end_day":end_day }
                )
            print(result)

        return result

    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")


def convert_pandas(data):
    
    # クエリの結果をPandas DataFrameに変換
    columns = data.keys()
    df = pd.DataFrame(data.fetchall(), columns=columns)

    # エラーチェック
    print(df.isnull().sum())
    print(len(df))

    # DBデータをエクスポート
    df.to_csv('ppv_history_origin.csv', encoding='utf-8_sig')

    return df

def processing_data(df):
    
    '''新規データ作成'''
    # 全購入金額
    df_total_price = df[['member_id', 'price']].groupby('member_id').sum().reset_index()

    # 商品購入リスト
    data_item = df.groupby('member_id')['menuid'].apply(list).reset_index()

    # 日付リスト
    data_inflow = df.groupby('member_id')['start_date'].apply(list).reset_index()

    '''新規データを元データに統合'''
    # 上記のデータを元データにマージ
    df_add = pd.merge(df, df_total_price, on=['member_id'], how='outer')
    df_add = pd.merge(df_add, data_item, on=['member_id'], how='outer')
    df_add = pd.merge(df_add, data_inflow, on=['member_id'], how='outer')

    # 列名を変更
    df_add = df_add.rename(columns={
                'price_y': 'total_sale',
                'menuid_y': 'ppv_history',
                'start_date_y': 'date_history',
                }
        )

    '''データ整理'''
    # 重複データの削除
    df_add = df_add.drop_duplicates(subset=['member_id'])

    # 必要なカラムのみ抽出
    column_list = ['site_id', 'member_id', 'total_sale', 'ppv_history', 'date_history']
    df_add = df_add[column_list]

    return df_add


def sort_data(df):
    
    # 6000円以上の人を抽出
    df = df.query(' 6000 < total_sale ')
    print(df.tail(50), len(df))

    # 加工データをエクスポート
    df.to_csv('ppv_processing.csv', encoding='utf-8_sig')

    return df


def main():

    # port
    local_port = 3307
    remote_port = 3306

    # 集計期間と取得サイト
    target_day = ["2023-01-01", "2024-12-31"]
    siteid_list = [443, 427, 486, 423, 477, 483, 484, 486]

    for s in siteid_list[5:6]:

        # sshでトンネルを作り接続
        ssh_request(local_port, remote_port)
            
        # swan データベース接続
        data = db_connect(local_port , s , target_day[0] , target_day[1])
            
        # 取得データをpandasに
        df = convert_pandas(data)
            
        # データ加工処理
        df = processing_data(df)

        # data sort.完成データをexport
        df = sort_data(df)

        
if __name__ == "__main__":
    main()