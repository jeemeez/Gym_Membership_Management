import sys  # [추가] exe 실행 경로 추적을 위해 필요합니다
import os
import shutil
import time
from datetime import datetime, timedelta
import pandas as pd
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# ==============================================================================
# [핵심 수정] .exe 파일 또는 스크립트가 실행되는 실제 폴더 경로를 완벽하게 잡아냅니다.
if getattr(sys, 'frozen', False):
    # PyInstaller로 빌드된 .exe 파일로 실행 중일 때 (.exe 파일이 있는 실제 폴더)
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # 파이썬 스크립트(python app.py)로 실행 중일 때 (현재 파일이 있는 폴더)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# [안내 사항 맞춤] 장부 파일 이름을 안내서에 적으신 대로 변경합니다.
CSV_PATH = os.path.join(BASE_DIR, "homerun_coin_records.csv")
BACKUP_DIR = os.path.join(BASE_DIR, "backup")
# ==============================================================================

COLUMNS = ["이름", "전화번호", "코인개수", "보관일", "수령일", "비고"]


def load_data():
    # 1. 오늘 자 자동 백업 로직
    if os.path.exists(CSV_PATH):
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)

        today_date = datetime.now().strftime("%Y-%m-%d")
        backup_path = os.path.join(BACKUP_DIR, f"coin_{today_date}.csv")

        if not os.path.exists(backup_path):
            shutil.copy2(CSV_PATH, backup_path)

        # 2. [추가] 30일이 지난 오래된 백업 파일 자동 삭제 로직
        try:
            now = time.time()
            # 30일을 초 단위로 계산 (30일 * 24시간 * 60분 * 60초)
            cutoff = now - (30 * 24 * 60 * 60)

            for filename in os.listdir(BACKUP_DIR):
                file_path = os.path.join(BACKUP_DIR, filename)
                
                # 파일이 맞고, 파일의 수정 시간(mtime)이 30일 전(cutoff)보다 과거라면 삭제
                if os.path.isfile(file_path):
                    if os.path.getmtime(file_path) < cutoff:
                        os.remove(file_path)
                        print(f"[백업 관리] 오래된 백업 파일 삭제됨: {filename}")
        except Exception as e:
            # 백업 청소 중 에러가 나더라도 프로그램 본 기능은 멈추지 않게 예외 처리
            print(f"[백업 관리 에러] {e}")

    if not os.path.exists(CSV_PATH):
        df = pd.DataFrame(columns=COLUMNS)
        df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
    df = pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False)
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = ""
    return df[COLUMNS]


def save_data(df):
    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")


def today_str():
    return datetime.now().strftime("%Y-%m-%d")


def normalize_phone(p):
    return "".join(ch for ch in p if ch.isdigit())


def format_phone(p):
    # 입력값 없거나 공백이면 빈 문자열로 정상 리턴
    if not p or str(p).strip() == "":
        return ""
    
    d = normalize_phone(p)
    if len(d) != 8 and len(d) != 11:
        return None
    
    if len(d) == 11:
        return f"{d[0:3]}-{d[3:7]}-{d[7:]}"
    elif len(d) == 8:
        return f"010-{d[0:4]}-{d[4:]}"
    
    return p


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/search")
def search_page():
    return render_template("search.html")


@app.route("/edit")
def edit_page():
    return render_template("edit.html")


@app.route("/api/register", methods=["POST"])
def api_register():
    # 이제 data는 고객 객체들이 담긴 리스트(배열)입니다.
    customer_list = request.json
    
    if not customer_list or not isinstance(customer_list, list):
        return jsonify({"ok": False, "msg": "등록할 고객 데이터가 올바르지 않습니다."})

    df = load_data()
    results = []

    # 1단계: 모든 고객 데이터 유효성 검사 (한 명이라도 에러가 있으면 진행을 막음)
    for i, item in enumerate(customer_list):
        name = str(item.get("name", "")).strip()
        phone_raw = str(item.get("phone", "")).strip()
        coin_raw = str(item.get("coin", "")).strip()
        memo = str(item.get("memo", "")).strip()
        row_num = i + 1

        if not name:
            return jsonify({"ok": False, "msg": f"[{row_num}번째 줄] 이름은 반드시 입력해주세요."})
        if not coin_raw.isdigit():
            return jsonify({"ok": False, "msg": f"[{row_num}번째 줄] 코인 개수는 숫자로 입력해주세요."})

        phone = format_phone(phone_raw)
        if phone is None:
            return jsonify({"ok": False, "msg": f"[{row_num}번째 줄] 전화번호를 8자리 또는 11자리 숫자로 정확히 입력해주세요."})

        coin = int(coin_raw)
        
        # 중복 여부 확인
        match = df[(df["이름"] == name) & (df["전화번호"] == phone)]
        
        if not match.empty:
            idx = match.index[0]
            old_coin = int(df.at[idx, "코인개수"]) if str(df.at[idx, "코인개수"]).isdigit() else 0
            results.append({
                "exists": True, "idx": int(idx), "name": name, "phone": phone,
                "old_coin": old_coin, "add_coin": coin, "new_coin": old_coin + coin,
                "memo": memo, "today": today_str()
            })
        else:
            results.append({
                "exists": False, "name": name, "phone": phone, 
                "coin": coin, "memo": memo, "today": today_str()
            })

    # 모든 검증을 통과하면 최종 확인창을 띄우기 위해 프론트엔드로 목록 전달
    return jsonify({"ok": True, "results": results})



@app.route("/api/register/confirm", methods=["POST"])
def api_register_confirm():
    data = request.json
    df = load_data()

    if data.get("exists"):
        idx = int(data["idx"])
        df.at[idx, "코인개수"] = str(data["new_coin"])
        df.at[idx, "보관일"] = today_str()
        if data.get("update_memo") and data.get("memo"):
            df.at[idx, "비고"] = data["memo"]
        save_data(df)
        return jsonify({"ok": True, "msg": f"{data['name']} 고객님의 코인이 합산 처리되었습니다."})
    else:
        new_row = {"이름": data["name"], "전화번호": data["phone"], "코인개수": str(data["coin"]),
                   "보관일": today_str(), "수령일": "", "비고": data.get("memo", "")}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        return jsonify({"ok": True, "msg": f"{data['name']} 고객님이 신규 등록되었습니다."})


@app.route("/api/search", methods=["POST"])
def api_search():
    data = request.json
    name = str(data.get("name", "")).strip()
    last4 = str(data.get("last4", "")).strip()

    if not name:
        return jsonify({"ok": False, "msg": "이름을 정확히 입력해주세요."})
        
    if last4 and (len(last4) != 4 or not last4.isdigit()):
        return jsonify({"ok": False, "msg": "전화번호 뒷자리는 숫자 4개로 정확히 입력해주세요."})

    df = load_data()
    matched = df[df["이름"] == name]
    
    if last4:
        matched = matched[(matched["전화번호"] != "") & (matched["전화번호"].str.endswith(last4))]

    results = []
    for idx, row in matched.iterrows():
        results.append({
            "idx": int(idx), "name": row["이름"], "phone": row["전화번호"] if row["전화번호"] else "전화번호 없음",
            "coin": int(row["코인개수"]) if str(row["코인개수"]).isdigit() else 0,
            "stock_date": row["보관일"], "receipt_date": row["수령일"], "memo": row["비고"]
        })
    return jsonify({"ok": True, "results": results})


@app.route("/api/withdraw", methods=["POST"])
def api_withdraw():
    data = request.json
    idx = int(data["idx"])
    amount_raw = str(data.get("amount", "")).strip()

    df = load_data()
    row = df.loc[idx]
    current_coin = int(row["코인개수"]) if str(row["코인개수"]).isdigit() else 0

    if not amount_raw.isdigit():
        return jsonify({"ok": False, "msg": "수령할 코인 개수는 숫자로 입력해주세요."})
    amount = int(amount_raw)

    if amount <= 0:
        return jsonify({"ok": False, "msg": "1개 이상 입력해주세요."})
    if amount > current_coin:
        return jsonify({"ok": False, "msg": f"현재 남은 코인({current_coin}개)보다 많이 입력하셨습니다."})

    new_coin = current_coin - amount
    return jsonify({
        "ok": True, "confirm_needed": True, "idx": idx, "name": row["이름"],
        "current_coin": current_coin, "amount": amount, "new_coin": new_coin, "today": today_str()
    })


@app.route("/api/withdraw/confirm", methods=["POST"])
def api_withdraw_confirm():
    data = request.json
    idx = int(data["idx"])
    new_coin = int(data["new_coin"])

    df = load_data()
    df.at[idx, "코인개수"] = str(new_coin)
    df.at[idx, "수령일"] = today_str()
    if new_coin == 0:
        df.at[idx, "비고"] = "수령완료"
    save_data(df)
    return jsonify({"ok": True, "msg": "수령 처리가 완료되었습니다.", "new_coin": new_coin})


@app.route("/api/edit_search", methods=["POST"])
def api_edit_search():
    return api_search()


@app.route("/api/edit", methods=["POST"])
def api_edit():
    data = request.json
    idx = int(data["idx"])
    new_coin_raw = str(data.get("coin", "")).strip()
    new_memo = str(data.get("memo", "")).strip()

    if not new_coin_raw.isdigit():
        return jsonify({"ok": False, "msg": "코인 개수는 숫자로 입력해주세요."})

    df = load_data()
    old_coin = str(df.at[idx, "코인개수"])
    old_memo = str(df.at[idx, "비고"])

    if new_coin_raw == old_coin and new_memo == old_memo:
        return jsonify({"ok": True, "no_change": True})

    return jsonify({
        "ok": True, "confirm_needed": True, "idx": idx,
        "name": df.at[idx, "이름"], "old_coin": old_coin, "old_memo": old_memo,
        "new_coin": new_coin_raw, "new_memo": new_memo
    })


@app.route("/api/edit/confirm", methods=["POST"])
def api_edit_confirm():
    data = request.json
    idx = int(data["idx"])
    df = load_data()
    df.at[idx, "코인개수"] = str(data["new_coin"])
    df.at[idx, "비고"] = data["new_memo"]
    save_data(df)
    return jsonify({"ok": True, "msg": "고객 정보가 변경되었습니다."})


if __name__ == "__main__":
    app.run(debug=False, port=5000)
