from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ TradingView Webhook Server đang chạy thành công!"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        print("📩 Received webhook:", data)  # In ra terminal Logs Render

        # Ghi lại tín hiệu vào file tạm signals.txt
        with open("signals.txt", "a") as f:
            f.write(f"{data}\n")

        return jsonify({"status": "success", "message": "Signal received"}), 200

    except Exception as e:
        print("❌ Error processing webhook:", e)
        return jsonify({"status": "error", "message": str(e)}), 400


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
