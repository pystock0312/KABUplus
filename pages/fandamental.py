import streamlit as st
import pandas as pd
import numpy as np

from sklearn.linear_model import LinearRegression
# 正規化のためのMin-Maxスケーリングをインポート
from sklearn.preprocessing import MinMaxScaler


@st.cache_data
def IRBANK_data():
    df_stock_dividend = pd.read_pickle("stock_dividend.pkl")
    df_profit_and_loss = pd.read_pickle("profit_and_loss.pkl")
    df_cash_flow_statement = pd.read_pickle("cash_flow_statement.pkl")
    df_balance_sheet = pd.read_pickle("balance_sheet.pkl")

    common_lists = ['日付', 'コード', '銘柄名', '市場・商品区分', '33業種コード', '33業種区分',
                    '17業種コード', '17業種区分', '規模コード', '規模区分', '年度']

    df_marged_stock_profit = pd.merge(df_stock_dividend, df_profit_and_loss,
                                      on=common_lists, how='inner')
    df_marged_stock_profit_cash = pd.merge(df_marged_stock_profit,
                                           df_cash_flow_statement,
                                           on=common_lists, how='inner')
    df_marged_stock_profit_cash_balance = pd.merge(df_marged_stock_profit_cash,
                                                   df_balance_sheet,
                                                   on=common_lists, how='inner')

    df = df_marged_stock_profit_cash_balance

    df = df.replace('-', np.nan)
    df["営業利益"] = pd.to_numeric(df["営業利益"], errors='coerce', downcast='integer')
    df["売上高"] = pd.to_numeric(df["売上高"], errors='coerce', downcast='integer')
    df["営業利益率"] = df["営業利益"] / df["売上高"] * 100

    return df






def normalize_and_calculate_slope(df, codes, target,limitde_year):
    slopes = []
    scaler = MinMaxScaler()
    model = LinearRegression()

    for code in codes:
        try:
            df_filtered = df[df["コード"] == code]
            stockname = df[df["コード"] == code]["銘柄名"].unique()
            df_filtered["年度"] = pd.to_datetime(df_filtered["年度"]).dt.year
            df_filtered_sorted = df_filtered.sort_values(by="年度").reset_index(drop=True)

            start_year = int(df_filtered_sorted["年度"].min())
            end_year = int(df_filtered_sorted["年度"].max())
            df_filtered_sorted['Number'] = df_filtered_sorted["年度"] - start_year + 1

            df_filtered_scaled = pd.DataFrame(scaler.fit_transform(df_filtered_sorted[[target]]), columns=[target])
            X = df_filtered_sorted[['Number']]
            y = df_filtered_scaled[target]
            model.fit(X, y)
            slope = model.coef_[0]

            slopes.append({'コード': code,"銘柄名":stockname, f'スコア_{target}': slope, '最小年度': start_year, '最大年度': end_year})
        except:
            slopes.append({'コード': code,"銘柄名":stockname, f'スコア_{target}': None, '最小年度': None, '最大年度': None})

    df_slopes = pd.DataFrame(slopes)
    # 傾きでソート（降順）

    df_slopes['年度範囲'] = df_slopes['最大年度'] - df_slopes['最小年度'] + 1
    # 年度が10以上のデータをフィルタリング
    df_filtered = df_slopes[df_slopes['年度範囲'] >= limitde_year]
    # スコアでソート（降順）
    df_sorted = df_filtered.sort_values(by=f'スコア_{target}', ascending=False)
    # ランク付け
    df_sorted[f'ランク_{target}'] = df_sorted[f'スコア_{target}'].rank(ascending=False)
    df_slopes_sorted = df_sorted.sort_values(by=f'スコア_{target}', ascending=False)
    return df_slopes_sorted


def merge_multiple_dataframes(*dataframes, key):
    """
    可変数のデータフレームを指定されたキーで内部結合します。

    :param dataframes: 結合するデータフレームのリスト
    :param key: 結合するためのキー
    :return: 結合されたデータフレーム
    """
    merged_df = dataframes[0]
    for df in dataframes[1:]:
        merged_df = merged_df.merge(df, on=key, how='inner')
    return merged_df


def merge_multiple_dataframes(*dataframes, key):
    """
    可変数のデータフレームを指定されたキーで内部結合します。
    各結合ステップでサフィックスを更新して重複を避けます。

    :param dataframes: 結合するデータフレームのリスト
    :param key: 結合するためのキー
    :return: 結合されたデータフレーム
    """
    merged_df = dataframes[0]
    suffix_num = 1
    for df in dataframes[1:]:
        suffixes = ('', f'_merge{suffix_num}')
        merged_df = merged_df.merge(df, on=key, how='inner', suffixes=suffixes)
        suffix_num += 1
    return merged_df

if __name__ == '__main__':
    st.text("売上高、EPS、一株配当、営業CF、営業利益率の傾きをスコア付け")
    # 別のページでその値を取得
    codes = st.column_values_list
    # st.title(codes)
    df = IRBANK_data()
    st.df_bank = df

    df_revenue = normalize_and_calculate_slope(df, codes, "売上高",10)
    # 一つのページでセッションステートに値を設定
    st.revenue_lists = df_revenue['コード'].tolist()

    df_eps = normalize_and_calculate_slope(df, codes, "EPS",10)
    st.eps_lists = df_eps['コード'].tolist()

    df_dps = normalize_and_calculate_slope(df, codes, "一株配当",10)
    st.dps_lists = df_dps['コード'].tolist()

    df_scf = normalize_and_calculate_slope(df, codes, "営業CF",10)
    st.scf_lists = df_scf['コード'].tolist()

    df_opm = normalize_and_calculate_slope(df, codes, "営業利益率",10)
    st.opm_lists = df_opm['コード'].tolist()

    # データフレームの結合
    df_merged = merge_multiple_dataframes(df_revenue, df_eps, df_dps, df_scf,df_opm,
                                          key='コード')

    # df_merged = pd.merge(pd.merge(pd.merge(df_revenue, df_eps, on='コード', how='inner'), df_dps, on='コード', how='inner'), df_scf, on='コード', how='inner')
    df_merged["最終ランク"] = df_merged["ランク_売上高"] + df_merged["ランク_EPS"] + df_merged["ランク_一株配当"] + df_merged["ランク_営業CF"] + df_merged["ランク_営業利益率"]

    df_result = df_merged[["コード","銘柄名","最終ランク","ランク_売上高","ランク_EPS","ランク_一株配当","ランク_営業CF","ランク_営業利益率"]]

    # 結合されたデータフレームの表示
    st.dataframe(df_merged)
    st.dataframe(df_result)
    # データフレームの表示
    st.dataframe(df_revenue)
    # データフレームの表示
    st.dataframe(df_eps)
    # データフレームの表示
    st.dataframe(df_dps)
    # データフレームの表示
    st.dataframe(df_scf)
    # データフレームの表示
    st.dataframe(df_opm)
