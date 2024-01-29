import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import numpy as np


def mk_df_target(df, code_value):
    df_target = df[df["コード"] == code_value]
    return df_target


def remove_negative_dividend_rows(df, target):
    # '-' を含む行を除外
    df = df[df[target] != np.nan]
    df = df.drop_duplicates(subset="年度")
    return df


def get_annual_closing_prices(ticker_symbol):
    # 開始日と終了日の設定
    start_date = '2010-01-01'
    end_date = '2023-12-31'

    try:
        # Yahoo Financeからデータを取得
        data = yf.download(f"{ticker_symbol}.T", start=start_date, end=end_date)

        # 年ごとの期末株価を取得
        annual_closing_prices = data['Close'].resample('Y').last()
        annual_closing_prices.name = ticker_symbol
        df = annual_closing_prices
    except Exception as e:
        print(f"Failed to download {ticker_symbol}: {e}")
        return None

    # シリーズをデータフレームに変換
    df = annual_closing_prices.to_frame()

    # 列名を設定
    df.columns = ['株価']

    # 年度列を追加
    df['年度'] = df.index.year

    return df


def get_df_dividend_yield(df_target,ticker_symbol):
    df_target_price = get_annual_closing_prices(ticker_symbol)
    df_dividend_yield = df_target[["年度","一株配当"]]
    df_dividend_yield['年度'] = df_dividend_yield['年度'].str.split('/').str[0]
    df_dividend_yield['年度'] = df_dividend_yield['年度'].astype(int)
    df_merged = pd.merge(df_dividend_yield, df_target_price, on='年度', how='outer')
    df_merged = df_merged.dropna(subset=["一株配当", "株価"])
    df_merged["一株配当"] = df_merged["一株配当"].astype(float)
    df_merged["配当利回り"] = df_merged["一株配当"] / df_merged["株価"] * 100
    df_merged = df_merged.sort_values(by='年度')
    df_merged = df_merged.reset_index(drop=True)
    df_merged["年度"] = pd.to_datetime(df_merged["年度"].astype(str) + '-01-01')
    return df_merged


def mk_graph_bar(df, target):
    df = remove_negative_dividend_rows(df, target)
    df["年度"] = pd.to_datetime(df["年度"])
    # 日付データを文字列に変換
    df["年度_str"] = df["年度"].astype(str)
    df[f"{target}"] = df[f"{target}"].astype(float)
    df = df.sort_values(by='年度')
    df[f"{target}増加率"] = df[f"{target}"].diff().fillna(0)
    df[f"{target}維持or増加"] = df[f"{target}増加率"] >= 0
    # print(df["配当増加率"])
    # データの準備
    df_graph = df
    categories = df_graph["年度_str"]
    # categories = df_graph["年度"].dt.strftime('%Y')
    values = df_graph[f"{target}"]
    # print(values)
    # 棒グラフの作成
    fig = go.Figure(data=[
        go.Bar(x=categories, y=values)
    ])

    # X軸の設定
    fig.update_xaxes(
        tickmode='array',
        tickvals=df_graph['年度'],
        ticktext=df_graph['年度_str']
    )

    # グラフのタイトルと軸ラベルの設定
    fig.update_layout(
        title=f"{target}",
        xaxis_title="年度",
        yaxis=dict(range=[0, df_graph[f"{target}"].max() * 1.2]),
        # Y軸の最大値をデータの最大値よりも20%大きく設定
        margin=dict(l=50, r=50, t=50, b=50)  # マージンの調整
    )
    return fig  # この行を追加


def mk_graph_scatter(df, target):
    df = remove_negative_dividend_rows(df, target)
    df["年度"] = pd.to_datetime(df["年度"])
    # 日付データを文字列に変換
    df["年度_str"] = df["年度"].astype(str)
    df[f"{target}"] = df[f"{target}"].astype(float)
    df = df.sort_values(by='年度')
    df[f"{target}増加率"] = df[f"{target}"].diff().fillna(0)
    df[f"{target}維持or増加"] = df[f"{target}増加率"] >= 0
    # データの準備
    df_graph = df
    categories = df_graph["年度_str"]
    # categories = df_graph["年度"].dt.strftime('%Y')
    values = df_graph[f"{target}"]

    # 折れ線グラフの作成
    fig = go.Figure(data=[
        go.Scatter(
            x=categories,
            y=values,
            mode='lines+markers+text',  # 'text' を追加
            text=[f"{v:.2f}" for v in values],  # 各データポイントに表示するテキスト
            textposition='top center'  # テキストの位置
        )
    ])

    # X軸の設定
    fig.update_xaxes(
        tickmode='array',
        tickvals=df_graph['年度'],
        ticktext=df_graph['年度_str']
    )

    # グラフのタイトルと軸ラベルの設定
    fig.update_layout(
        title=f"{target}",
        xaxis_title="年度",
        yaxis=dict(range=[0, df_graph[f"{target}"].max() * 1.2]),
        # Y軸の最大値をデータの最大値よりも20%大きく設定
        margin=dict(l=50, r=50, t=50, b=50)  # マージンの調整
    )
    return fig  # この行を追加


# Streamlitアプリのメイン関数
def main():
    st.title("財務データの可視化")

    fandamental_options = ["売上高","EPS","一株配当","営業CF","営業利益率"]

    selected_op = st.sidebar.radio("項目を選択して下さい",fandamental_options)

    # # ユーザーに検索コードの入力を求める
    # ticker_symbol = st.text_input("検索コードを入力してください（例：9251）", "")

    if selected_op == "売上高":
        revenue_lists = st.revenue_lists
        # ユーザーに検索コードの入力を求める
        ticker_symbol = st.sidebar.selectbox("売上高リスト", revenue_lists)

    if selected_op == "EPS":
        esp_lists = st.eps_lists
        # ユーザーに検索コードの入力を求める
        ticker_symbol = st.sidebar.selectbox("EPSリスト", esp_lists)

    if selected_op == "一株配当":
        dps_lists = st.dps_lists
        # ユーザーに検索コードの入力を求める
        ticker_symbol = st.sidebar.selectbox("一株配当リスト", dps_lists)

    if selected_op == "営業CF":
        scf_lists = st.scf_lists
        # ユーザーに検索コードの入力を求める
        ticker_symbol = st.sidebar.selectbox("営業CF", scf_lists)

    if selected_op == "営業利益率":
        opm_lists = st.opm_lists
        # ユーザーに検索コードの入力を求める
        ticker_symbol = st.sidebar.selectbox("営業利益率", opm_lists)

    # ユーザーが何か入力した場合のみ処理を進める
    if ticker_symbol:
        try:
            # 入力されたコードを整数に変換
            ticker_symbol = int(ticker_symbol)

            # 以前のコードを実行
            df_stock_dividend = pd.read_pickle("stock_dividend.pkl")
            df_profit_and_loss = pd.read_pickle("profit_and_loss.pkl")
            df_cash_flow_statement = pd.read_pickle("cash_flow_statement.pkl")
            df_balance_sheet = pd.read_pickle("balance_sheet.pkl")

            common_lists = ['日付', 'コード', '銘柄名', '市場・商品区分', '33業種コード', '33業種区分',
                            '17業種コード', '17業種区分', '規模コード', '規模区分', '年度']

            df_marged_stock_profit = pd.merge(df_stock_dividend,
                                              df_profit_and_loss,
                                              on=common_lists, how='inner')
            df_marged_stock_profit_cash = pd.merge(df_marged_stock_profit,
                                                   df_cash_flow_statement,
                                                   on=common_lists, how='inner')
            df_marged_stock_profit_cash_balance = pd.merge(
                df_marged_stock_profit_cash,
                df_balance_sheet,
                on=common_lists, how='inner')

            df = df_marged_stock_profit_cash_balance

            df = df.replace('-', np.nan)
            df["営業利益"] = pd.to_numeric(df["営業利益"], errors='coerce',
                                       downcast='integer')
            df["売上高"] = pd.to_numeric(df["売上高"], errors='coerce',
                                      downcast='integer')
            df["営業利益率"] = df["営業利益"] / df["売上高"] * 100
            df_target = mk_df_target(df, ticker_symbol)
            # st.dataframe(df_target)

        except ValueError:
            st.error("有効なコードを入力してください。")

        # 各グラフの表示


        if selected_op == "売上高":
            # 売上高
            fig_revenue = mk_graph_bar(df_target, "売上高")
            st.plotly_chart(fig_revenue)

        if selected_op == "EPS":
            # EPS(１株当たり純利益)
            fig_eps = mk_graph_bar(df_target, "EPS")
            st.plotly_chart(fig_eps)

        if selected_op == "一株配当":
            # 一株当たり配当金
            fig_dividend = mk_graph_bar(df_target, "一株配当")
            st.plotly_chart(fig_dividend)
            # 配当性向
            fig_dividend_payout_ratio = mk_graph_scatter(df_target, "配当性向")
            st.plotly_chart(fig_dividend_payout_ratio)


        if selected_op == "営業CF":
            # 営業利益率
            fig_operating_cf = mk_graph_bar(df_target, "営業CF")
            st.plotly_chart(fig_operating_cf)

        if selected_op == "営業利益率":
            # 営業利益率
            fig_operating_profit_margin = mk_graph_scatter(df_target, "営業利益率")
            st.plotly_chart(fig_operating_profit_margin)

        # # ROE
        # fig_ROE = mk_graph_scatter(df_target, "ROE")
        # st.plotly_chart(fig_ROE)


if __name__ == "__main__":
    main()
