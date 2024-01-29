import pandas as pd
from sqlalchemy import create_engine
import streamlit as st

def create_database_url():
    # データベースの設定
    host = "localhost"
    dbname = "stock"
    user = "miyaotakahiro"
    password = ""
    port = 5432
    database_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    return database_url


def get_datas_databases(database_url, sql_query):
    engine = create_engine(database_url)
    df_sql = pd.read_sql_query(sql_query, con=engine)
    return df_sql


if __name__ == '__main__':
    sql_query = """
    SELECT 
        data."SC",
        data."名称",
        data."市場",
        data."業種",
        data."時価総額（百万円）",
        data."発行済株式数",
        data."配当利回り（予想）",
        data."1株配当（予想）",
        data."PER（予想）",
        data."PBR（実績）",
        data."EPS（予想）",
        data."BPS（実績）",
        data."最低購入額",
        data."単元株",
        data."高値日付",
        data."年初来高値",
        data."安値日付",
        data."年初来安値",
        prices."日付",
        prices."株価",
        prices."前日比",
        prices."前日比（％）",
        prices."前日終値",
        prices."始値",
        prices."高値",
        prices."安値",
        prices."VWAP",
        prices."出来高",
        prices."出来高率",
        prices."売買代金（千円）",
        prices."値幅下限",
        prices."値幅上限",
        prices."年初来高値乖離率",
        prices."年初来安値乖離率",
        financial."決算期",
        financial."決算発表日（本決算）",
        financial."売上高（百万円）",
        financial."営業利益（百万円）",
        financial."経常利益（百万円）",
        financial."当期利益（百万円）",
        financial."総資産（百万円）",
        financial."自己資本（百万円）",
        financial."資本金（百万円）",
        financial."有利子負債（百万円）",
        financial."自己資本比率",
        financial."ROE",
        financial."ROA"
    FROM 
        japan_all_stock_data data
    JOIN 
        japan_all_stock_prices_2 prices 
    ON 
        data."SC" = prices."SC"
        AND data."名称" = prices."名称"
        AND data."市場" = prices."市場"
        AND data."業種" = prices."業種"
    JOIN 
        japan_all_stock_financial_results financial
    ON 
        data."SC" = financial."SC"
        AND data."名称" = financial."名称"
    """

    database_url = create_database_url()
    df_sql = get_datas_databases(database_url, sql_query)
    st.dataframe(df_sql)
