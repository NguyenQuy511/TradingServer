from flask import Flask, request, jsonify
import os
import json
import time
from threading import Lock

app = Flask(__name__)

# Lưu tín hiệu cuối cùng trong RAM + lock để thread-safe
_last_signal = {}
_lock = Lock()

def _now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def _normalize_signal(obj):
    """
    Chuẩn hoá tín hiệu về dạng:
    {
      "symbol": "XAUUSDm",
      "action": "buy" | "sell" | "close_all",
      "lot": float (optional),
      "price": float|str (optional),
      "time": "ISO-8601" (server sẽ bổ sung nếu thiếu)
    }
    """
    if not isinstance(obj, dict):
        return None

    # chấp nhận "signal" hoặc "action"
    action = obj.get("action") or obj.get("signal")
    if not action or not isinstance(action, str):
        return None
    action = action.lower().strip()

    # các action hợp lệ
    if action not in ("buy", "sell", "close_all"):
        return None

    symbol = obj.get("symbol") or obj.get("sym") or ""
    symbol = str(symbol).strip()

    lot = obj.get("lot")
    try:
        lot = float(lot) if lot is not None else None
    except Exception:
        lot = None

    price = obj.get("price")
    # price có thể là số hoặc chuỗi (ví dụ "{{close}}")
    if price is not None:
        try:
            price = float(price)
        except Exception:
            price = str(price)

    when = obj.get("time")
    if not when:
        when = _now_iso()

    out = {
        "symbol": symbol,
        "action": action,
        "time": when
    }
    if lot is not None:
        out["lot"] = lot
    if price is not None:
        out["price"] = price
    return out

def _extract_payload(req_json):
    """
    Hỗ trợ cả 2 kiểu TradingView gửi:
    1) JSON trực tiếp: { "symbol":"...", "action":"buy", ... }
    2) JSON nằm trong trường "message": { "message":"{...json...}" }
    """
    if isinstance(req_json, dict):
        # TH1: JSON trực tiếp
        sig = _normalize_signal(req_json)
        if sig:
            return sig

        # TH2: JSON lồng trong "message"
        msg = req_json.get("message")
        if isinstance(msg, str):
            msg = msg.strip()
            # thử parse JSON trong message
            try:
                inner = json.loads(msg)
                sig = _normalize_signal(inner)
                if sig:
                    return sig
            except Exception:
                pass

    # không nhận diện được
    return None

@app.route("/")
def home():
    return "TradingView Webhook Server is running ✅", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    # nhận JSON (silent để không raise nếu sai header)
    data = request.get_json(silent=True)
    sig = _extract_payload(data)

    if not sig:
        return jsonify({
            "status": "error",
            "message": "Invalid payload. Expect JSON with fields like symbol/action/lot/price/time or a 'message' containing JSON."
        }), 400

    with _lock:
        global _last_signal
        _last_signal = sig

    print("📩 Received signal:", sig)
    return jsonify({"status": "success", "message": "Signal received", "data": sig}), 200

@app.route("/signals", methods=["GET"])
def get_signals():
    with _lock:
        if not _last_signal:
            return jsonify({"status": "empty"}), 200
        # trả về signal hiện có
        return jsonify(_last_signal), 200

@app.route("/clear", methods=["POST"])
def clear_signal():
    with _lock:
        global _last_signal
        _last_signal = {}
    return jsonify({"status": "cleared"}), 200

if __name__ == "__main__":
    # Render sẽ set PORT; khi chạy local thì dùng 10000
    port = int(os.environ.get("PORT", 10000))
    # host 0.0.0.0 để Render/public truy cập được
    app.run(host="0.0.0.0", port=port)
