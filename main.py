import urllib3
http = urllib3.PoolManager()

import pandas as pd
import numpy as np
from sqlalchemy import create_engine

import streamlit as st
import plotly.express as px


def get_daily_datas(data_daily_names):
    for data_name in data_daily_names:
        url = f"https://csvex.com/kabu.plus/csv/{data_name}/daily/{data_name}.csv"
        headers = urllib3.util.make_headers(basic_auth="%s:%s" % (id, pw) )
        response = http.request("GET", url, headers=headers)
        f = open(f"{data_name}.csv", "wb")
        f.write(response.data)
        f.close()


def get_monthly_datas(data_monthly_names):
    for data_name in data_monthly_names:
        url = f"https://csvex.com/kabu.plus/csv/{data_name}/monthly/{data_name}.csv"
        headers = urllib3.util.make_headers(basic_auth="%s:%s" % (id, pw) )
        response = http.request("GET", url, headers=headers)
        f = open(f"{data_name}.csv", "wb")
        f.write(response.data)
        f.close()


def create_dataframes(csv_names):
    dataframes = {}  # データベースを格納するための辞書
    for csv_name in csv_names:
        # Pandasを使用してCSVファイルを読み込む
        df = pd.read_csv(f"{csv_name}.csv", encoding='shift_jis')
        df.replace('-', np.nan, inplace=True)
        # データ型を推測して変換（二回の変換は不要なので一度だけ行います）
        df = df.infer_objects()
        # ファイル名をキーとしてデータフレームを辞書に追加
        dataframes[csv_name] = df
    return dataframes


def edit_dataframes(csv_names, dataframes):
    edited_dataframes = {}
    for csv_name in csv_names:
        df = dataframes[csv_name]
        if csv_name == "japan-all-stock-data":
            # SCカラムで'0001'または'0002'を含む行を削除
            df = df[~df['SC'].isin(["0001", "0002"])]
            df['1株配当（予想）'] = pd.to_numeric(df['1株配当（予想）'], errors='coerce')
            df['EPS（予想）'] = pd.to_numeric(df['EPS（予想）'], errors='coerce')
            # NaN値を含む行を削除する（オプション）
            df.dropna(subset=['1株配当（予想）', 'EPS（予想）'], inplace=True)
            df['配当性向（予想）'] = (df['1株配当（予想）'] / df['EPS（予想）']) * 100
        edited_dataframes[csv_name] = df
    return edited_dataframes


def create_database_url():
    # データベースの設定
    host = "localhost"
    dbname = "stock"
    user = "miyaotakahiro"
    password = ""
    port = 5432
    database_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    return database_url


def create_databases(database_url, csv_names, dataframes):
    # SQLAlchemyエンジンの作成
    engine = create_engine(database_url)
    # DataFrameをPostgreSQLデータベースに挿入
    for csv_name in csv_names:
        modified_csv_name = csv_name.replace("-", "_")
        dataframes[csv_name].to_sql(modified_csv_name, engine, if_exists='replace', index=False)


def get_datas_databases(database_url, sql_query):
    engine = create_engine(database_url)
    df_sql = pd.read_sql_query(sql_query, con=engine)
    return df_sql


# 配当利回りをツリーマップで表示する関数
def plot_dividend_yield_treemap_grouped(df):
    df['配当利回り（予想）'] = df['配当利回り（予想）'].round(1)
    # ツリーマップの作成
    fig = px.treemap(df, path=['業種', '名称'], values='配当利回り（予想）',
                     color='配当利回り（予想）',
                     title="配当利回りによるツリーマップ（'業種区分'ごとにグループ化）",
                     hover_data={'配当利回り（予想）': True},
                     color_continuous_scale=['blue', 'red'])  # 配色の変更

    fig.update_traces(textinfo='label+value')
    return fig


if __name__ == '__main__':
    id = "t8a5k4a0"
    pw = "jR6qWmbP6"

    sql_query = """
    SELECT * FROM (
        SELECT *, RANK() OVER (PARTITION BY 業種 ORDER BY 配当利回り（予想） DESC) as rank
        FROM japan_all_stock_data
    ) as ranked
    WHERE CAST(配当利回り（予想） AS NUMERIC) >= 3.75;
    """
    database_url = create_database_url()

    data_daily_names = ["japan-all-stock-prices-2", "japan-all-stock-data"]
    data_monthly_names = ["japan-all-stock-financial-results"]

    if st.button('データ取得1'):
        get_daily_datas(data_daily_names)

    if st.button('データ取得2'):
        get_monthly_datas(data_monthly_names)

    if st.button('データベース保存'):

        # database_url = create_database_url()

        csv_names = ["japan-all-stock-prices-2", "japan-all-stock-data", "japan-all-stock-financial-results"]
        dataframes = create_dataframes(csv_names)
        edit_dataframes = edit_dataframes(csv_names, dataframes)
        create_databases(database_url, csv_names, dataframes)

    df_sql = get_datas_databases(database_url, sql_query)
    # Count the number of occurrences for each industry type
    industry_count = df_sql['業種'].value_counts()

    # Create a pie chart using Plotly
    fig = px.pie(industry_count, values=industry_count.values,
                 names=industry_count.index,
                 title="Number of Companies by Industry")

    # Display the chart in Streamlit
    st.plotly_chart(fig)
    st.plotly_chart(plot_dividend_yield_treemap_grouped(df_sql))
    st.dataframe(df_sql)

    # 一つのページでセッションステートに値を設定
    st.column_values_list = df_sql['SC'].tolist()
