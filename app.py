from flask import Flask, jsonify, request
import vnstock as vn
from datetime import datetime, timedelta
import pandas as pd

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "message": "VNStock API is running!",
        "endpoints": {
            "stock_price": "/api/stock/<symbol>",
            "stock_history": "/api/history/<symbol>",
            "market_overview": "/api/market",
            "company_info": "/api/company/<symbol>"
        }
    })

@app.route('/api/stock/<symbol>')
def get_stock_price(symbol):
    try:
        # Lấy giá cổ phiếu hiện tại
        price_data = vn.stock_historical_data(symbol, "2024-01-01", "2024-12-31")
        if price_data.empty:
            return jsonify({"error": "No data found for symbol"}), 404
        
        latest_data = price_data.iloc[-1]
        
        return jsonify({
            "symbol": symbol.upper(),
            "price": float(latest_data['close']),
            "open": float(latest_data['open']),
            "high": float(latest_data['high']),
            "low": float(latest_data['low']),
            "volume": int(latest_data['volume']),
            "date": latest_data.name.strftime('%Y-%m-%d')
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/history/<symbol>')
def get_stock_history(symbol):
    try:
        # Lấy tham số từ query string
        days = request.args.get('days', 30, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Lấy dữ liệu lịch sử
        history_data = vn.stock_historical_data(symbol, start_date, end_date)
        
        if history_data.empty:
            return jsonify({"error": "No data found"}), 404
        
        # Chuyển đổi dữ liệu
        history_list = []
        for date, row in history_data.iterrows():
            history_list.append({
                "date": date.strftime('%Y-%m-%d'),
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": int(row['volume'])
            })
        
        return jsonify({
            "symbol": symbol.upper(),
            "data": history_list
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/market')
def get_market_overview():
    try:
        # Lấy thông tin tổng quan thị trường
        market_data = vn.stock_ls_board()
        
        if market_data.empty:
            return jsonify({"error": "No market data available"}), 404
        
        # Chuyển đổi dữ liệu
        market_list = []
        for _, row in market_data.head(20).iterrows():  # Lấy top 20
            market_list.append({
                "symbol": row['symbol'],
                "price": float(row['price']) if pd.notna(row['price']) else 0,
                "change": float(row['change']) if pd.notna(row['change']) else 0,
                "change_percent": float(row['change_percent']) if pd.notna(row['change_percent']) else 0,
                "volume": int(row['volume']) if pd.notna(row['volume']) else 0
            })
        
        return jsonify({
            "market_data": market_list,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/company/<symbol>')
def get_company_info(symbol):
    try:
        # Lấy thông tin công ty
        company_data = vn.stock_fundamental_data(symbol)
        
        if company_data.empty:
            return jsonify({"error": "No company data found"}), 404
        
        # Lấy thông tin cơ bản
        latest_data = company_data.iloc[-1]
        
        return jsonify({
            "symbol": symbol.upper(),
            "company_info": {
                "market_cap": float(latest_data.get('market_cap', 0)),
                "pe_ratio": float(latest_data.get('pe', 0)),
                "pb_ratio": float(latest_data.get('pb', 0)),
                "eps": float(latest_data.get('eps', 0)),
                "roe": float(latest_data.get('roe', 0))
            },
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)