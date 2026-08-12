
import threading
import webview
from app import app


def run_flask():
    app.run(debug=False, port=5000, use_reloader=False)


if __name__ == "__main__":
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
    webview.create_window("스크린 야구장 회원관리", "none", width=1100, height=780)
    webview.start()
