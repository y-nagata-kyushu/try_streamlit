import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ページ設定
st.set_page_config(
    page_title="株価比較ダッシュボード",
    page_icon="📈",
    layout="wide"
)

# タイトル
st.title("📈 株価比較ダッシュボード")
st.markdown("複数の銘柄を簡単に比較できるツールです")

# サイドバー設定
st.sidebar.header("設定")

# デフォルト銘柄リスト
default_tickers = "AAPL, MSFT, GOOGL, AMZN"

# 銘柄入力
tickers_input = st.sidebar.text_input(
    "銘柄シンボル（カンマ区切り）",
    value=default_tickers,
    help="例: AAPL, MSFT, TSLA"
)

# 銘柄リストを作成
tickers = [ticker.strip().upper() for ticker in tickers_input.split(",")]

# 期間選択
period_options = {
    "1ヶ月": 30,
    "3ヶ月": 90,
    "6ヶ月": 180,
    "1年": 365,
    "3年": 1095,
    "5年": 1825
}

selected_period = st.sidebar.selectbox(
    "表示期間",
    options=list(period_options.keys()),
    index=3  # デフォルトは1年
)

# チャートタイプ選択
chart_type = st.sidebar.radio(
    "チャートタイプ",
    options=["ラインチャート", "ローソク足チャート"],
    index=0
)

# データ取得ボタン
if st.sidebar.button("データ取得", type="primary"):
    st.session_state.fetch_data = True

# 初期化
if 'fetch_data' not in st.session_state:
    st.session_state.fetch_data = False

# メイン処理
if st.session_state.fetch_data and len(tickers) > 0:
    
    # 期間計算
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period_options[selected_period])
    
    # プログレスバー
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # データ格納用
    stock_data = {}
    stock_info = {}
    
    # 各銘柄のデータ取得
    for i, ticker in enumerate(tickers):
        try:
            status_text.text(f"データ取得中... {ticker}")
            
            # データ取得
            stock = yf.Ticker(ticker)
            df = stock.history(start=start_date, end=end_date)
            
            if not df.empty:
                stock_data[ticker] = df
                
                # 銘柄情報取得
                try:
                    info = stock.info
                    stock_info[ticker] = {
                        "名称": info.get("longName", "N/A"),
                        "セクター": info.get("sector", "N/A"),
                        "通貨": info.get("currency", "N/A")
                    }
                except:
                    stock_info[ticker] = {
                        "名称": ticker,
                        "セクター": "N/A",
                        "通貨": "USD"
                    }
            
            progress_bar.progress((i + 1) / len(tickers))
            
        except Exception as e:
            st.error(f"❌ {ticker} のデータ取得に失敗しました: {str(e)}")
    
    progress_bar.empty()
    status_text.empty()
    
    if stock_data:
        st.success(f"✅ {len(stock_data)}銘柄のデータを取得しました")
        
        # タブ作成
        tab1, tab2, tab3, tab4 = st.tabs(["📊 チャート", "📈 騰落率比較", "📋 統計情報", "💾 データダウンロード"])
        
        # タブ1: チャート
        with tab1:
            st.subheader("株価チャート")
            
            if chart_type == "ラインチャート":
                # ラインチャート
                fig = go.Figure()
                
                for ticker in stock_data.keys():
                    df = stock_data[ticker]
                    fig.add_trace(go.Scatter(
                        x=df.index,
                        y=df['Close'],
                        name=ticker,
                        mode='lines',
                        hovertemplate='<b>%{fullData.name}</b><br>' +
                                    '日付: %{x|%Y-%m-%d}<br>' +
                                    '終値: %{y:.2f}<br>' +
                                    '<extra></extra>'
                    ))
                
                fig.update_layout(
                    title="株価推移",
                    xaxis_title="日付",
                    yaxis_title="株価",
                    hovermode='x unified',
                    height=600,
                    template="plotly_white"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                # ローソク足チャート（1銘柄ずつ表示）
                selected_ticker = st.selectbox(
                    "表示する銘柄を選択",
                    options=list(stock_data.keys())
                )
                
                df = stock_data[selected_ticker]
                
                fig = go.Figure(data=[go.Candlestick(
                    x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name=selected_ticker
                )])
                
                fig.update_layout(
                    title=f"{selected_ticker} ローソク足チャート",
                    xaxis_title="日付",
                    yaxis_title="株価",
                    height=600,
                    template="plotly_white",
                    xaxis_rangeslider_visible=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # タブ2: 騰落率比較
        with tab2:
            st.subheader("騰落率比較")
            st.markdown("各銘柄の開始時点を100として正規化")
            
            # 正規化データ作成
            fig = go.Figure()
            
            for ticker in stock_data.keys():
                df = stock_data[ticker]
                normalized = (df['Close'] / df['Close'].iloc[0]) * 100
                
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=normalized,
                    name=ticker,
                    mode='lines',
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                '日付: %{x|%Y-%m-%d}<br>' +
                                '騰落率: %{y:.2f}%<br>' +
                                '<extra></extra>'
                ))
            
            fig.update_layout(
                title="騰落率推移（開始時点=100）",
                xaxis_title="日付",
                yaxis_title="騰落率指数",
                hovermode='x unified',
                height=600,
                template="plotly_white"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 騰落率サマリー
            st.subheader("📊 騰落率サマリー")
            
            summary_data = []
            for ticker in stock_data.keys():
                df = stock_data[ticker]
                start_price = df['Close'].iloc[0]
                end_price = df['Close'].iloc[-1]
                change_pct = ((end_price - start_price) / start_price) * 100
                
                summary_data.append({
                    "銘柄": ticker,
                    "名称": stock_info[ticker]["名称"],
                    "開始価格": f"{start_price:.2f}",
                    "終了価格": f"{end_price:.2f}",
                    "騰落率(%)": f"{change_pct:+.2f}"
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df = summary_df.sort_values("騰落率(%)", ascending=False)
            
            st.dataframe(
                summary_df,
                use_container_width=True,
                hide_index=True
            )
        
        # タブ3: 統計情報
        with tab3:
            st.subheader("統計情報")
            
            stats_data = []
            for ticker in stock_data.keys():
                df = stock_data[ticker]
                
                stats_data.append({
                    "銘柄": ticker,
                    "名称": stock_info[ticker]["名称"],
                    "セクター": stock_info[ticker]["セクター"],
                    "最高値": f"{df['High'].max():.2f}",
                    "最安値": f"{df['Low'].min():.2f}",
                    "平均値": f"{df['Close'].mean():.2f}",
                    "標準偏差": f"{df['Close'].std():.2f}",
                    "出来高平均": f"{df['Volume'].mean():,.0f}",
                    "データ期間": f"{len(df)}日"
                })
            
            stats_df = pd.DataFrame(stats_data)
            
            st.dataframe(
                stats_df,
                use_container_width=True,
                hide_index=True
            )
            
            # 個別銘柄の詳細情報
            st.subheader("詳細情報")
            selected_detail = st.selectbox(
                "詳細を表示する銘柄",
                options=list(stock_data.keys()),
                key="detail_select"
            )
            
            col1, col2, col3 = st.columns(3)
            
            df_detail = stock_data[selected_detail]
            
            with col1:
                st.metric(
                    "現在価格",
                    f"{df_detail['Close'].iloc[-1]:.2f}",
                    f"{((df_detail['Close'].iloc[-1] - df_detail['Close'].iloc[-2]) / df_detail['Close'].iloc[-2] * 100):+.2f}%"
                )
            
            with col2:
                st.metric(
                    "期間最高値",
                    f"{df_detail['High'].max():.2f}"
                )
            
            with col3:
                st.metric(
                    "期間最安値",
                    f"{df_detail['Low'].min():.2f}"
                )
        
        # タブ4: データダウンロード
        with tab4:
            st.subheader("データダウンロード")
            
            download_ticker = st.selectbox(
                "ダウンロードする銘柄",
                options=list(stock_data.keys()),
                key="download_select"
            )
            
            df_download = stock_data[download_ticker].copy()
            df_download.index.name = "Date"
            
            # CSVダウンロード
            csv = df_download.to_csv()
            
            st.download_button(
                label=f"📥 {download_ticker} のデータをダウンロード (CSV)",
                data=csv,
                file_name=f"{download_ticker}_{selected_period}.csv",
                mime="text/csv"
            )
            
            # プレビュー表示
            st.subheader("データプレビュー")
            st.dataframe(df_download.tail(10), use_container_width=True)
    
    else:
        st.error("❌ データを取得できませんでした。銘柄シンボルを確認してください。")

else:
    # 初期表示
    st.info("👈 左側のサイドバーで銘柄と期間を設定し、「データ取得」ボタンを押してください")
    
    # 使い方説明
    with st.expander("📖 使い方"):
        st.markdown("""
        ### 基本的な使い方
        
        1. **銘柄シンボルを入力**
           - 米国株の場合: AAPL, MSFT, GOOGL など
           - 日本株の場合: 7203.T (トヨタ), 9984.T (ソフトバンク) など
           - 複数銘柄をカンマで区切って入力
        
        2. **表示期間を選択**
           - 1ヶ月〜5年まで選択可能
        
        3. **チャートタイプを選択**
           - ラインチャート: 複数銘柄を重ねて表示
           - ローソク足チャート: 1銘柄の詳細な値動きを表示
        
        4. **データ取得ボタンをクリック**
        
        ### 主な機能
        
        - **チャート**: 株価推移を視覚的に確認
        - **騰落率比較**: 複数銘柄のパフォーマンスを比較
        - **統計情報**: 最高値、最安値、平均値などの統計データ
        - **データダウンロード**: CSVファイルとしてダウンロード可能
        
        ### おすすめ銘柄例
        
        - **米国テック株**: AAPL, MSFT, GOOGL, AMZN, NVDA
        - **日本主要株**: 7203.T, 6758.T, 9984.T, 8306.T
        - **インデックス**: ^GSPC (S&P500), ^DJI (ダウ), ^N225 (日経平均)
        """)
    
    with st.expander("⚠️ 注意事項"):
        st.markdown("""
        - データはYahoo Financeから取得しています
        - リアルタイムデータではなく、15-20分程度の遅延があります
        - このツールは情報提供を目的としており、投資助言ではありません
        - 投資判断は自己責任でお願いします
        """)

# フッター
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info("""
このアプリはyfinanceライブラリを使用して
株価データを取得・可視化します。

データ提供: Yahoo Finance
""")