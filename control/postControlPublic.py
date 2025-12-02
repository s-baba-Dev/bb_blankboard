import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)  # app.py があるディレクトリ
DATA_PATH = os.path.join(BASE_DIR, "../data", "posts.json")

# 読み込み
def load_posts():
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

# 詳細情報取得
def get_post(post_id):
    posts = load_posts()
    post = next((p for p in posts if p["id"] == post_id), None)
    return post

