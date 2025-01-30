import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.sql import text
import pymysql
import subprocess
import time
import os
from sshtunnel import SSHTunnelForwarder
from sqlalchemy.exc import SQLAlchemyError
import settings

# Get absolute path of current working directory
current_directory = os.getcwd()

# SSH connection info
ssh_host = settings.SSH_HOST
ssh_port = settings.SSH_PORT
ssh_user = settings.SSH_USER
ssh_key = current_directory + settings.SSH_KEY

# Port configuration
local_port = 3307  # Local port
remote_port = 3306  # Remote MySQL server port

# Database connection info
db_user = settings.DB_USER
db_password = settings.DB_PASSWORD
db_host = settings.DB_HOST
db_port = settings.DB_PORT
db_name = settings.DB_NAME

# Collection period and target sites
collect_term = ["2023-01-01", "2024-12-31"]
siteid_list = [443, 427, 486, 423, 477, 483, 484, 486]

def ssh_request():
    """Establish SSH tunnel"""
    ssh_command = [
        'ssh',
        '-i', ssh_key,
        '-L', f'{local_port}:127.0.0.1:{remote_port}',
        '-N',  # Run in foreground without executing command
        '-f',  # Run in background
        '-p', str(ssh_port),
        f'{ssh_user}@{ssh_host}'
    ]
    
    subprocess.run(ssh_command, check=True)
    print(f"SSH tunnel established on local port {local_port}")

def db_connect(db_user, db_password, local_port, db_name, site_id, startday, endday):
    """Connect to database and retrieve data"""
    engine = create_engine(f'mysql+pymysql://{db_user}:{db_password}@127.0.0.1:{local_port}/{db_name}')
    print("Database connection established.")

    subscribe_query = text("""
        SELECT *
        FROM swan_analyze.analyze_ppv_all
        WHERE public_flg = 1 
        AND site_id = :site_id 
        AND date >= :start_day 
        AND date <= :end_day
    """)
    
    with engine.connect() as connection:
        result = connection.execute(subscribe_query, {
            "site_id": site_id,
            "start_day": startday,
            "end_day": endday
        })
        
    return result

def main():
    try:
        # Process only site ID 483 for this example
        site_id = siteid_list[5]
        
        ssh_request()
        time.sleep(5)  # Wait for SSH tunnel establishment
        
        data = db_connect(
            db_user, 
            db_password, 
            local_port, 
            db_name, 
            site_id, 
            collect_term[0], 
            collect_term[1]
        )

        # Convert to DataFrame
        columns = data.keys()
        df = pd.DataFrame(data.fetchall(), columns=columns)

        # Check for errors
        print(df.isnull().sum())
        print(f"Total rows: {len(df)}")

        # Export original data
        df.to_csv('ppv_history_origin.csv', encoding='utf-8_sig')

        # Data processing
        # Calculate total price per member
        df_total_price = df[['member_id', 'price']].groupby('member_id').sum().reset_index()

        # Get purchase history lists
        data_item = df.groupby('member_id')['menuid'].apply(list).reset_index()
        data_inflow = df.groupby('member_id')['start_date'].apply(list).reset_index()

        # Merge data
        df_add = pd.merge(df, df_total_price, on=['member_id'], how='outer')
        df_add = pd.merge(df_add, data_item, on=['member_id'], how='outer')
        df_add = pd.merge(df_add, data_inflow, on=['member_id'], how='outer')

        # Rename columns
        df_add = df_add.rename(columns={
            'price_y': 'total_sale',
            'menuid_y': 'ppv_history',
            'start_date_y': 'date_history',
        })

        # Select needed columns and process data
        column_list = ['site_id', 'member_id', 'total_sale', 'ppv_history', 'date_history']
        df_add = df_add[column_list]
        df_add = df_add.drop_duplicates(subset=['member_id'])
        df_add = df_add.query('6000 < total_sale')

        # Export processed data
        df_add.to_csv('ppv_processing.csv', encoding='utf-8_sig')
        
    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()