import os
import json
from datetime import datetime
from control.postControlPublic import load_posts, get_post

BASE_DIR = os.path.dirname(__file__)  # app.py があるディレクトリ
DATA_PATH = os.path.join(BASE_DIR, "../data", "posts.json")

# 保存
def save_posts(posts):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=4, ensure_ascii=False)

# 追加
def add_post(title, content):
    posts = load_posts()

    if posts:
        new_id = posts[-1]["id"] + 1
    else:
        new_id = 1

    date = datetime.now().strftime("%Y-%m-%d %H:%M")

    new_article = {
        "id": new_id,
        "title": title,
        "created_at": date,
        "content": content
    }

    posts.append(new_article)

    save_posts(posts)

# 更新
def update_post(post_id, title, content):
    posts = load_posts()
    post = next((p for p in posts if p["id"] == post_id), None)

    # 更新処理
    post["title"] = title
    post["content"] = content

    save_posts(posts)

# 削除
def delete_post(post_id):
    posts = load_posts()
    post = [p for p in posts if p["id"] != post_id]
    save_posts(post)
