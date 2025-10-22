from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("📩 Nhận tín hiệu:", data)
    # Ở đây bạn có thể ghi vào file signals.txt hoặc gửi sang MT5 EA
    return jsonify({"status": "ok"}), 200

@app.route('/', methods=['GET'])
def home():
    return "TradingView Webhook Server đang chạy ✅"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
