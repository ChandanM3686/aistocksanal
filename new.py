import streamlit as st
import pandas as pd
import numpy as np
# Removing problematic imports
# import matplotlib.pyplot as plt
# import seaborn as sns
import google.generativeai as genai
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from plotly.subplots import make_subplots

# ------------------ Configuration ------------------ #


genai.configure(api_key="AIzaSyB5Jw-XclWu8jlQdvP83QTkL1Z89P72QSE")



# Initialize the model
model = genai.GenerativeModel('gemini-2.0-flash')

# ------------------ Streamlit Layout ------------------ #

st.set_page_config(page_title="Stock Analysis AI Agent", layout="wide")
st.markdown("""
<style>
.main {padding: 1rem;}
.stApp {max-width: 1200px; margin: 0 auto;}
.stock-card {background-color: #f5f5f5; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem;}
.profit {color: green;}
.loss {color: red;}
</style>
""", unsafe_allow_html=True)

st.sidebar.header("SMTP Settings")
smtp_server = st.sidebar.text_input("SMTP Server", value="smtp.gmail.com")
smtp_port = st.sidebar.text_input("SMTP Port", value="587")
sender_email = st.sidebar.text_input("Sender Email")
sender_password = st.sidebar.text_input("Sender Email Password", type="password")

# ------------------------------------------------------ #

# Add these imports at the top of your file
import yfinance as yf
import requests
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta


def fetch_stock_news(ticker_symbol, days=7):
    """Fetch recent news for a stock using a financial news API"""
    try:
        # You'll need to sign up for a free API key from a service like Alpha Vantage, Finnhub, or News API
        # This is a placeholder - replace with your actual API implementation
        api_key = "YOUR_API_KEY"  # Replace with your actual API key
        url = f"https://financialmodelingprep.com/api/v3/stock_news?tickers={ticker_symbol}&limit=10&apikey={api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            news_data = response.json()
            return news_data
        else:
            return []
    except Exception as e:
        print(f"Error fetching news: {str(e)}")
        return []

def get_analyst_ratings(ticker_symbol):
    """Get analyst ratings and price targets for a stock"""
    try:
        # Placeholder - replace with actual API call
        api_key = "YOUR_API_KEY"  # Replace with your actual API key
        url = f"https://financialmodelingprep.com/api/v3/analyst-stock-recommendations/{ticker_symbol}?apikey={api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            ratings_data = response.json()
            return ratings_data
        else:
            return {}
    except Exception as e:
        print(f"Error fetching analyst ratings: {str(e)}")
        return {}

def create_advanced_charts(ticker_symbol):
    """Create advanced stock charts using Plotly"""
    try:
        # Get historical data
        stock = yf.Ticker(ticker_symbol)
        hist = stock.history(period="1y")
        
        if hist.empty:
            return None
        
        # Create candlestick chart
        fig = go.Figure(data=[go.Candlestick(
            x=hist.index,
            open=hist['Open'],
            high=hist['High'],
            low=hist['Low'],
            close=hist['Close'],
            name='Candlestick'
        )])
        
        # Add moving averages
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=hist['Close'].rolling(window=20).mean(),
            line=dict(color='purple', width=1),
            name='20-day MA'
        ))
        
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=hist['Close'].rolling(window=50).mean(),
            line=dict(color='orange', width=1),
            name='50-day MA'
        ))
        
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=hist['Close'].rolling(window=200).mean(),
            line=dict(color='green', width=1),
            name='200-day MA'
        ))
        
        # Calculate and add RSI (Relative Strength Index)
        delta = hist['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # Add volume bars
        volume_colors = ['green' if close >= open else 'red' for close, open in zip(hist['Close'], hist['Open'])]
        
        # Create a subplot with 3 rows
        fig = make_subplots(rows=3, cols=1, 
                           shared_xaxes=True,
                           vertical_spacing=0.05,
                           row_heights=[0.6, 0.2, 0.2],
                           subplot_titles=(f'{ticker_symbol} Price', 'Volume', 'RSI'))
        
        # Add candlestick to first row
        fig.add_trace(go.Candlestick(
            x=hist.index,
            open=hist['Open'],
            high=hist['High'],
            low=hist['Low'],
            close=hist['Close'],
            name='Candlestick'
        ), row=1, col=1)
        
        # Add moving averages to first row
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=hist['Close'].rolling(window=20).mean(),
            line=dict(color='purple', width=1),
            name='20-day MA'
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=hist['Close'].rolling(window=50).mean(),
            line=dict(color='orange', width=1),
            name='50-day MA'
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=hist['Close'].rolling(window=200).mean(),
            line=dict(color='green', width=1),
            name='200-day MA'
        ), row=1, col=1)
        
        # Add volume to second row
        fig.add_trace(go.Bar(
            x=hist.index,
            y=hist['Volume'],
            marker_color=volume_colors,
            name='Volume'
        ), row=2, col=1)
        
        # Add RSI to third row
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=rsi,
            line=dict(color='blue', width=1),
            name='RSI'
        ), row=3, col=1)
        
        # Add RSI overbought/oversold lines
        fig.add_trace(go.Scatter(
            x=[hist.index[0], hist.index[-1]],
            y=[70, 70],
            line=dict(color='red', width=1, dash='dash'),
            name='Overbought'
        ), row=3, col=1)
        
        fig.add_trace(go.Scatter(
            x=[hist.index[0], hist.index[-1]],
            y=[30, 30],
            line=dict(color='green', width=1, dash='dash'),
            name='Oversold'
        ), row=3, col=1)
        
        # Update layout
        fig.update_layout(
            title=f'{ticker_symbol} Technical Analysis',
            yaxis_title='Price',
            xaxis_title='Date',
            template='plotly_white',
            height=800,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # Update y-axis labels
        fig.update_yaxes(title_text="Price", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        fig.update_yaxes(title_text="RSI", row=3, col=1)
        
        return fig
    except Exception as e:
        print(f"Error creating charts: {str(e)}")
        return None

def calculate_buffett_metrics(ticker_symbol):
    """Calculate Warren Buffett's key metrics for a stock"""
    try:
        # Get financial data
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        financials = stock.financials
        balance_sheet = stock.balance_sheet
        cashflow = stock.cashflow
        
        # Calculate key metrics
        metrics = {}
        
        # ROE (Return on Equity)
        if 'returnOnEquity' in info:
            metrics['ROE'] = info['returnOnEquity']
        else:
            metrics['ROE'] = None
            
        # Debt to Equity
        if 'debtToEquity' in info:
            metrics['DebtToEquity'] = info['debtToEquity']
        else:
            metrics['DebtToEquity'] = None
            
        # Profit Margins
        if 'profitMargins' in info:
            metrics['ProfitMargin'] = info['profitMargins']
        else:
            metrics['ProfitMargin'] = None
            
        # Free Cash Flow
        if not cashflow.empty and 'Free Cash Flow' in cashflow.index:
            metrics['FreeCashFlow'] = cashflow.loc['Free Cash Flow'].iloc[0]
        else:
            metrics['FreeCashFlow'] = None
            
        # Earnings Growth (5yr)
        if 'earningsGrowth' in info:
            metrics['EarningsGrowth'] = info['earningsGrowth']
        else:
            metrics['EarningsGrowth'] = None
            
        return metrics
    except Exception as e:
        print(f"Error calculating Buffett metrics: {str(e)}")
        return {}

def summarize_report_with_gemini(full_report: str) -> str:
    """
    Use Google Gen AI to produce a concise summary of the full analysis.
    """
    try:
        prompt = f"""
Please summarize the following detailed stock analysis into a concise report (around 100–150 words). Keep all key recommendations, outlooks, and risk highlights. Here is the full analysis:

{full_report}
"""
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error summarizing report: {str(e)}"

def send_email(recipient: str, subject: str, body: str) -> bool:
    """
    Sends an email using SMTP. Returns True on success, False on failure.
    """
    try:
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error sending email: {str(e)}")
        return False

def analyze_stock_with_gemini(stock_data: dict, stock_name: str) -> str:
    """Use Google Gen AI to generate a professional analysis for the selected stock."""
    try:
        # Format ticker symbol
        ticker_symbol = stock_name.strip()
        if not (ticker_symbol.endswith('.NS') or ticker_symbol.endswith('.BO')):
            ticker_symbol = f"{ticker_symbol}.NS"

        # P/L calculations
        invested_value = stock_data.get('Invested Value', 0)
        current_value = stock_data.get('Current Value', 0)
        profit_loss = current_value - invested_value
        profit_loss_percent = (profit_loss / invested_value * 100) if invested_value > 0 else 0

        # Construct professional and compact prompt
        prompt = f"""
        You are a professional equity analyst. Provide a structured analysis for stock: {stock_name} ({ticker_symbol}).

        🔹 **Position Details**
        - Quantity: {stock_data.get('Quantity')}
        - Avg Buy Price: ₹{stock_data.get('Avg. Price')}
        - Last Traded Price (LTP): ₹{stock_data.get('LTP')}
        - Invested Value: ₹{invested_value}
        - Current Value: ₹{current_value}
        - Net P/L: ₹{profit_loss:.2f} ({profit_loss_percent:.2f}%)
        - Today’s P/L: {stock_data.get('Todays Profit/Loss')} ({stock_data.get('Todays Profit/Loss %')})

        🔹 **Expert Recommendation**
        - Buy / Sell / Hold recommendation
        - Expert rating (out of 5)
        - Target price for 1M, 3M, 1Y
        - Suggested position sizing

        🔹 **Latest News Impact (max 3)**
        - Headline
        - Brief summary
        - Sentiment: Positive / Neutral / Negative

        🔹 **Key Financial Indicators**
        - P/E Ratio (vs Industry)
        - Debt-to-Equity Ratio
        - Return on Equity (ROE)
        - Free Cash Flow trend (last 3 years)
        - Dividend Yield
        - EPS Growth (YoY)

        🔹 **Technical Indicators**
        - Support & Resistance levels
        - 50 / 200-day Moving Averages
        - RSI value (indicate overbought/oversold)
        - MACD signal
        - Volume trend

        🔹 **Buffett Checklist (Rate 1–5)**
        - Simple business model
        - Economic moat
        - Strong management
        - Consistent earnings
        - Conservative debt
        - Long-term growth visibility
        - Valuation margin of safety

        🔹 **Risk Overview**
        - Sector-related risks
        - Regulatory threats
        - Competitive intensity
        - Volatility/Price risk

        🔹 **Multibagger Potential**
        - Yes / No with justification

        🔸 Bullet points only. Avoid theory. Give crisp, data-backed insights only.
        """
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"Error analyzing stock: {str(e)}"



# Move these functions before main()
def fetch_live_prices_with_gemini(stock_symbols):
    """
    Use Gemini to fetch live prices for a list of stock symbols
    """
    try:
        # Clean up stock symbols by removing trailing spaces
        cleaned_symbols = [symbol.strip() for symbol in stock_symbols]
        
        # Add proper suffix for Indian stocks if not already present
        formatted_symbols = []
        for symbol in cleaned_symbols:
            if not (symbol.endswith('.NS') or symbol.endswith('.BO')):
                # Default to NSE for Indian stocks
                formatted_symbol = f"{symbol.strip()}.NS"
            else:
                formatted_symbol = symbol.strip()
            formatted_symbols.append(formatted_symbol)
            
        # Create a prompt for Gemini to fetch live prices
        symbols_str = ", ".join(formatted_symbols)
        prompt = f"""
        Please provide the current live prices for the following stocks: {symbols_str}.
        Return the data in this exact format - a JSON object where keys are stock symbols and values are their current prices:
        {{"SYMBOL1": price1, "SYMBOL2": price2, ...}}
        Only return the JSON object, nothing else.
        """
        
        # Get response from Gemini
        response = model.generate_content(prompt)
        response_text = response.text
        
        # Extract the JSON object from the response
        import json
        import re
        
        # Try to find a JSON object in the response
        json_match = re.search(r'\{[^\{\}]*\}', response_text)
        if json_match:
            json_str = json_match.group(0)
            prices_dict = json.loads(json_str)
            return prices_dict
        else:
            # If no JSON object is found, try to parse the entire response
            try:
                prices_dict = json.loads(response_text)
                return prices_dict
            except:
                print("Could not parse Gemini response as JSON")
                return {}
    except Exception as e:
        print(f"Error fetching live prices with Gemini: {str(e)}")
        return {}

# Modify the track_daily_profits function to use Gemini for live prices
def track_daily_profits(df, days=30, use_gemini_for_live=True):
    """Track daily profits for stocks in the portfolio with cumulative trend using Gemini for live prices"""
    try:
        # Create a dictionary to store results
        tracking_data = {}
        
        # Get today's date and the date from 'days' days ago
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get list of stock symbols
        stock_symbols = df['Name'].tolist()
        
        # Fetch live prices using Gemini if requested
        live_prices = {}
        if use_gemini_for_live:
            live_prices = fetch_live_prices_with_gemini(stock_symbols)
        
        # Process each stock in the portfolio
        for _, row in df.iterrows():
            stock_name = row['Name']
            avg_price = row['Avg. Price']
            quantity = row['Quantity']
            
            # Format ticker symbol correctly for yfinance
            ticker_symbol = stock_name.strip()
            if not (ticker_symbol.endswith('.NS') or ticker_symbol.endswith('.BO')):
                ticker_symbol = f"{ticker_symbol}.NS"  # Default to NSE
            
            try:
                ticker = yf.Ticker(ticker_symbol)
                hist = ticker.history(start=start_date, end=end_date)
                
                if not hist.empty:
                    if use_gemini_for_live and stock_name in live_prices and live_prices[stock_name] is not None:
                        if datetime.now().date() not in hist.index:
                            last_row = hist.iloc[-1].copy()
                            new_index = pd.DatetimeIndex([datetime.now()])
                            new_row = pd.DataFrame([last_row], index=new_index)
                            hist = pd.concat([hist, new_row])
                        
                        hist.loc[hist.index[-1], 'Close'] = live_prices[stock_name]
                    
                    hist['Daily_PL'] = (hist['Close'] - avg_price) * quantity
                    hist['Daily_PL_Pct'] = ((hist['Close'] - avg_price) / avg_price) * 100
                    
                    hist['Month'] = hist.index.month
                    hist['Year'] = hist.index.year
                    hist['Monthly_Cumulative_PL'] = hist.groupby(['Year', 'Month'])['Daily_PL'].cumsum()
                    
                    tracking_data[stock_name] = {
                        'dates': hist.index.tolist(),
                        'close_prices': hist['Close'].tolist(),
                        'daily_pl': hist['Daily_PL'].tolist(),
                        'daily_pl_pct': hist['Daily_PL_Pct'].tolist(),
                        'monthly_cumulative_pl': hist['Monthly_Cumulative_PL'].tolist(),
                        'month': hist['Month'].tolist(),
                        'year': hist['Year'].tolist(),
                        'live_price': live_prices.get(stock_name, None) if use_gemini_for_live else None
                    }
            except Exception as e:
                print(f"Error fetching data for {stock_name}: {str(e)}")
                continue
                
        return tracking_data
    except Exception as e:
        print(f"Error in track_daily_profits: {str(e)}")
        return {}

def calculate_profit_loss_metrics(df):
    """Calculate proper profit/loss metrics"""
    try:
        # Ensure numeric types
        df['Invested Value'] = pd.to_numeric(df['Invested Value'], errors='coerce')
        df['Current Value'] = pd.to_numeric(df['Current Value'], errors='coerce')
        df['LTP'] = pd.to_numeric(df['LTP'], errors='coerce')
        df['Avg. Price'] = pd.to_numeric(df['Avg. Price'], errors='coerce')
        
        # Calculate P/L
        df['Profit/Loss'] = df['Current Value'] - df['Invested Value']
        
        # Calculate P/L % properly
        df['Profit/Loss %'] = (df['Profit/Loss'] / df['Invested Value'] * 100).round(2)
        
        # Calculate today's P/L
        df['Todays Profit/Loss'] = (df['LTP'] - df['Avg. Price']) * df['Quantity']
        df['Todays Profit/Loss %'] = ((df['LTP'] - df['Avg. Price']) / df['Avg. Price'] * 100).round(2)
        
        # Replace inf and -inf with NaN
        df = df.replace([np.inf, -np.inf], np.nan)
        
        return df
    except Exception as e:
        print(f"Error calculating P/L metrics: {str(e)}")
        return df

def main():
    st.title("Stock Portfolio Analysis AI Agent")

    # File uploader
    uploaded_file = st.file_uploader("Upload your stock portfolio CSV file", type="csv")

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            
            # Convert numeric columns
            numeric_cols = [
                "Quantity", "Avg. Price", "LTP", "Invested Value", "Current Value"
            ]
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            
            # Calculate proper P/L metrics
            df = calculate_profit_loss_metrics(df)

            # Portfolio summary
            st.subheader("Portfolio Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                total_invested = df["Invested Value"].sum()
                st.metric("Total Invested", f"₹{total_invested:,.2f}")
            with col2:
                total_current = df["Current Value"].sum()
                st.metric("Current Value", f"₹{total_current:,.2f}")
            with col3:
                # Calculate total profit/loss directly from the difference
                total_profit = total_current - total_invested
                profit_percent = (total_profit / total_invested) * 100 if total_invested > 0 else 0
                st.metric(
                    "Overall Profit/Loss",
                    f"₹{total_profit:,.2f} ({profit_percent:.2f}%)",
                    delta=f"{profit_percent:.2f}%"
                )

            # In the main() function, replace the existing visualization code with this:
            
            # Visualization
            st.subheader("Portfolio Visualization")
            tab1, tab2, tab3 = st.tabs(["Portfolio Allocation", "Daily Profit Tracking", "Raw Data"])
            with tab1:
                # Create a more attractive pie chart with Plotly
                fig = px.pie(
                    df, 
                    values="Current Value", 
                    names="Name",
                    title="Portfolio Allocation by Current Value",
                    hole=0.4,  # Donut chart
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(height=600)
                st.plotly_chart(fig, use_container_width=True)
                
                # Add a treemap as an alternative view
                fig2 = px.treemap(
                    df,
                    path=["Name"],
                    values="Current Value",
                    color="Profit/Loss %",
                    color_continuous_scale="RdYlGn",
                    title="Portfolio Treemap by Value and Performance"
                )
                fig2.update_layout(height=500)
                st.plotly_chart(fig2, use_container_width=True)
                
            # Replace the Performance tab with Daily Profit Tracking
            with tab2:
                st.subheader("Daily Profit Tracking")
                days_to_track = st.slider("Number of days to track", min_value=7, max_value=90, value=30)
                
                with st.spinner("Fetching daily profit data..."):
                    daily_tracking = track_daily_profits(df, days=days_to_track)
                    
                    if daily_tracking:
                        # Create tabs for each stock
                        stock_tabs = st.tabs(list(daily_tracking.keys()))
                        
                        for i, stock_name in enumerate(daily_tracking.keys()):
                            with stock_tabs[i]:
                                data = daily_tracking[stock_name]
                                
                                # Create a figure with secondary y-axis
                                fig = make_subplots(specs=[[{"secondary_y": True}]])
                                
                                # Add daily profit/loss bars
                                fig.add_trace(
                                    go.Bar(
                                        x=data['dates'],
                                        y=data['daily_pl'],
                                        name="Daily P/L (₹)",
                                        marker_color=['green' if pl >= 0 else 'red' for pl in data['daily_pl']]
                                    ),
                                    secondary_y=False
                                )
                                
                                # Add monthly cumulative trend line
                                fig.add_trace(
                                    go.Scatter(
                                        x=data['dates'],
                                        y=data['monthly_cumulative_pl'],
                                        name="Monthly Cumulative P/L (₹)",
                                        line=dict(color="blue", width=3)
                                    ),
                                    secondary_y=True
                                )
                                
                                # Add zero line
                                fig.add_trace(
                                    go.Scatter(
                                        x=[data['dates'][0], data['dates'][-1]],
                                        y=[0, 0],
                                        name="Break-even",
                                        line=dict(color="black", dash="dash")
                                    ),
                                    secondary_y=True
                                )
                                
                                # Set titles
                                fig.update_layout(
                                    title=f"{stock_name} - Daily Profit/Loss with Monthly Cumulative Trend",
                                    height=500,
                                    hovermode="x unified"
                                )
                                
                                # Set y-axes titles
                                fig.update_yaxes(title_text="Daily P/L (₹)", secondary_y=False)
                                fig.update_yaxes(title_text="Cumulative P/L (₹)", secondary_y=True)
                                
                                st.plotly_chart(fig, use_container_width=True)
                                
                                # Add month-to-date summary
                                current_month = datetime.now().month
                                current_year = datetime.now().year
                                
                                # Filter data for current month
                                current_month_indices = [i for i, (m, y) in enumerate(zip(data['month'], data['year'])) 
                                                        if m == current_month and y == current_year]
                                
                                if current_month_indices:
                                    mtd_pl = data['monthly_cumulative_pl'][current_month_indices[-1]]
                                    mtd_color = "green" if mtd_pl >= 0 else "red"
                                    
                                    st.markdown(f"### Month-to-Date Summary")
                                    st.markdown(f"<span style='color:{mtd_color}; font-size:24px;'>MTD P/L: ₹{mtd_pl:,.2f}</span>", 
                                                unsafe_allow_html=True)
                                    
                                    # Calculate daily average profit/loss for current month
                                    daily_pls = [data['daily_pl'][i] for i in current_month_indices]
                                    avg_daily_pl = sum(daily_pls) / len(daily_pls) if daily_pls else 0
                                    avg_color = "green" if avg_daily_pl >= 0 else "red"
                                    
                                    st.markdown(f"<span style='color:{avg_color}; font-size:18px;'>Avg. Daily P/L: ₹{avg_daily_pl:,.2f}</span>", 
                                                unsafe_allow_html=True)
                                    
                                    # Show profitable vs loss-making days
                                    profit_days = sum(1 for pl in daily_pls if pl > 0)
                                    loss_days = sum(1 for pl in daily_pls if pl < 0)
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.markdown(f"<span style='color:green; font-size:16px;'>Profitable Days: {profit_days}</span>", 
                                                    unsafe_allow_html=True)
                                    with col2:
                                        st.markdown(f"<span style='color:red; font-size:16px;'>Loss-making Days: {loss_days}</span>", 
                                                    unsafe_allow_html=True)
                    else:
                        st.warning("Could not fetch daily tracking data. Please check your stock symbols.")
                    if not daily_tracking:
                        st.warning("No tracking data available for the selected period.")

                with tab3:
                    st.dataframe(df, use_container_width=True)

            # AI Stock Analysis
            st.subheader("AI Stock Analysis")
            selected_stock = st.selectbox("Select a stock to analyze", df["Name"].tolist())

            if selected_stock:
                stock_data = df[df["Name"] == selected_stock].iloc[0].to_dict()

                col1, col2 = st.columns([1, 2])
                with col1:
                    st.subheader(f"{selected_stock} Details")
                    st.write(f"**Quantity:** {stock_data.get('Quantity', 0):,.0f}")
                    st.write(f"**Avg. Price:** ₹{stock_data.get('Avg. Price', 0):,.2f}")
                    st.write(f"**LTP:** ₹{stock_data.get('LTP', 0):,.2f}")
                    st.write(f"**Invested Value:** ₹{stock_data.get('Invested Value', 0):,.2f}")
                    st.write(f"**Current Value:** ₹{stock_data.get('Current Value', 0):,.2f}")
                    
                    # Format profit/loss with proper percentage
                    profit_loss = stock_data.get("Profit/Loss", 0)
                    profit_loss_percent = stock_data.get("Profit/Loss %", 0)
                    
                    if pd.notnull(profit_loss) and pd.notnull(profit_loss_percent):
                        color_class = 'profit' if profit_loss >= 0 else 'loss'
                        st.write(
                            f"**Profit/Loss:** <span class='{color_class}'>₹{profit_loss:,.2f} ({profit_loss_percent:+.2f}%)</span>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.write("**Profit/Loss:** Data unavailable")

                with col2:
                    st.subheader("AI Analysis")
                    analyze_button = st.button("Generate AI Analysis")
                    if analyze_button:
                        with st.spinner("Analyzing stock data..."):
                            analysis_text = analyze_stock_with_gemini(stock_data, selected_stock)
                            st.markdown(analysis_text)

                        st.markdown("---")
                        st.subheader("Summarize & Email")
                        recipient_email = st.text_input("Recipient Email (for sending summary)")
                        summarize_button = st.button("Generate & Send Summary")

                        if summarize_button:
                            if not recipient_email:
                                st.error("Please provide a recipient email address.")
                            elif not smtp_server or not sender_email or not sender_password:
                                st.error("Please configure SMTP settings (server, port, sender email, password) in the sidebar.")
                            else:
                                with st.spinner("Generating summary..."):
                                    summary_text = summarize_report_with_gemini(analysis_text)
                                st.markdown("**Summary:**")
                                st.write(summary_text)

                                subject = f"Summary of {selected_stock} Analysis"
                                body = f"Here is the concise summary of the analysis for {selected_stock}:\n\n{summary_text}"
                                sent = send_email(recipient_email, subject, body)
                                if sent:
                                    st.success(f"Summary sent to {recipient_email} successfully.")
                                else:
                                    st.error("Failed to send the summary email.")

        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.info("Please ensure your CSV has these columns: Name, Quantity, Avg. Price, LTP, Invested Value, Current Value, Profit/Loss, Profit/Loss %, Todays Profit/Loss, Todays Profit/Loss %")

# Move the main() function to the end of the file
if __name__ == "__main__":
    main()

def create_correlation_heatmap(df):
    """Create an enhanced correlation heatmap using plotly"""
    try:
        # Select only relevant numeric columns for correlation
        numeric_cols = ['Quantity', 'Avg. Price', 'LTP', 'Invested Value', 
                       'Current Value', 'Profit/Loss', 'Profit/Loss %']
        correlation_matrix = df[numeric_cols].corr()
        
        # Create heatmap with improved styling
        fig = go.Figure(data=go.Heatmap(
            z=correlation_matrix,
            x=numeric_cols,
            y=numeric_cols,
            colorscale='RdBu_r',  # Reversed RdBu for better visualization
            zmin=-1,
            zmax=1,
            text=np.round(correlation_matrix, 2),
            texttemplate='%{text:.2f}',
            textfont={"size": 12, "color": "black"},
            hoverongaps=False
        ))
        
        # Update layout with better formatting
        fig.update_layout(
            title={
                'text': 'Portfolio Correlation Matrix',
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=18)
            },
            height=700,
            width=900,
            xaxis={'side': 'bottom', 'tickangle': 45},
            yaxis={'autorange': 'reversed'},
            margin=dict(t=100, l=100, r=50, b=100)
        )
        
        return fig
    except Exception as e:
        print(f"Error creating heatmap: {str(e)}")
        return None

def calculate_mtd_metrics(df: pd.DataFrame) -> dict:
    """Calculate Month-to-Date metrics with enhanced statistics"""
    today = datetime.now()
    month_start = datetime(today.year, today.month, 1)
    
    mtd_metrics = {
        'total_pl': 0,
        'avg_daily_pl': 0,
        'winning_days': 0,
        'losing_days': 0,
        'best_performer': '',
        'worst_performer': '',
        'volatility': 0,
        'sharpe_ratio': 0
    }
    
    try:
        # Filter for current month's data
        mtd_data = df[df.index >= month_start]
        
        if not mtd_data.empty:
            # Calculate basic P&L metrics
            mtd_metrics['total_pl'] = mtd_data['Profit/Loss'].sum()
            mtd_metrics['avg_daily_pl'] = mtd_data['Profit/Loss'].mean()
            mtd_metrics['winning_days'] = len(mtd_data[mtd_data['Profit/Loss'] > 0])
            mtd_metrics['losing_days'] = len(mtd_data[mtd_data['Profit/Loss'] < 0])
            
            # Calculate advanced metrics
            returns = mtd_data['Profit/Loss %'].pct_change()
            mtd_metrics['volatility'] = returns.std() * np.sqrt(252)  # Annualized volatility
            risk_free_rate = 0.05  # Assume 5% risk-free rate
            excess_returns = returns - risk_free_rate/252
            mtd_metrics['sharpe_ratio'] = np.sqrt(252) * excess_returns.mean() / returns.std()
            
            # Identify best and worst performers
            performance_by_stock = mtd_data.groupby('Name')['Profit/Loss %'].sum()
            mtd_metrics['best_performer'] = performance_by_stock.idxmax()
            mtd_metrics['worst_performer'] = performance_by_stock.idxmin()
            
        return mtd_metrics
    
    except Exception as e:
        print(f"Error calculating MTD metrics: {str(e)}")
        return mtd_metrics
