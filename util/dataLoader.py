import os
import json
import markdown
from fastapi import HTTPException
from util.post_status import STATUS_PUBLIC

# プロジェクトのルートディレクトリ
# util ディレクトリの1階層上を基準にする
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# data フォルダのパス
DATA_DIR = os.path.join(BASE_DIR, "data")

# 投稿データ（記事一覧）JSON のパス
POSTS_PATH = os.path.join(DATA_DIR, "posts.json")

# カテゴリ／トピック／グループ管理用 JSON のパス
CATEGORIES_PATH = os.path.join(DATA_DIR, "categories.json")

# -----------------------------
# Posts 読み書き
# -----------------------------
def load_posts(*, public_only=False):
    """
    投稿データを JSON ファイルから読み込む

    :param public_only: True の場合は公開状態の記事のみを返す
    :return: 投稿データのリスト
    """
    try:
        # posts.json を読み込む
        with open(POSTS_PATH, "r", encoding="utf-8") as f:
            posts = json.load(f)

        # 公開記事のみ取得する場合はステータスでフィルタリング
        if public_only:
            posts = [
                p for p in posts
                if p.get("status") == STATUS_PUBLIC
            ]

        return posts

    except Exception:
        # ファイルが存在しない・JSON が壊れている等の場合は空リストを返す
        return []


def save_posts(posts):
    """
    投稿データを JSON ファイルに保存する

    :param posts: 投稿データのリスト
    """
    with open(POSTS_PATH, "w", encoding="utf-8") as f:
        # 日本語をそのまま保持し、整形して保存
        json.dump(posts, f, ensure_ascii=False, indent=2)


# -----------------------------
# Categories 読み書き
# -----------------------------
def load_categories():
    """
    カテゴリ／トピック／グループ情報を JSON ファイルから読み込む

    :return: categories / topics / groups を含む辞書
    """
    try:
        # categories.json を読み込む
        with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                "categories": data.get("categories", []),
                "topics": data.get("topics", []),
                "groups": data.get("groups", [])
            }
    except FileNotFoundError:
        # ファイルが存在しない場合は空データを返す
        return {"categories": [], "topics": [], "groups": []}


def save_categories(data):
    """
    カテゴリ／トピック／グループ情報を JSON ファイルに保存する

    :param data: categories / topics / groups を含む辞書
    """
    with open(CATEGORIES_PATH, "w", encoding="utf-8") as f:
        # 日本語を保持し、整形して保存
        json.dump(data, f, ensure_ascii=False, indent=2)

# -----------------------------
# 投稿記事詳細（public 用）
# -----------------------------
def get_post_detail_public(post_id):
    """
    一般ユーザー向けの記事詳細を取得する

    - 指定された post_id の記事を取得
    - 公開状態（STATUS_PUBLIC）の記事のみを対象とする
    - 表示用に加工した記事データを返す
    """
    # 投稿データとカテゴリ関連データを読み込む
    posts = load_posts()
    cats = load_categories()

    # 対象の記事を検索
    post = next((p for p in posts if p["id"] == post_id), None)
    if not post or post.get("status") != STATUS_PUBLIC:
        # 記事が存在しない、または非公開の場合は 404
        raise HTTPException(status_code=404)

    # 表示用に加工して返却
    return _decorate_post(post, cats)


# -----------------------------
# 投稿記事詳細（admin 用）
# -----------------------------
def get_post_detail_admin(post_id):
    """
    管理者向けの記事詳細を取得する

    公開・非公開・下書きを問わず記事を取得する
    """
    # 投稿データとカテゴリ関連データを読み込む
    posts = load_posts()
    cats = load_categories()

    # 対象の記事を検索
    post = next((p for p in posts if p["id"] == post_id), None)
    if not post:
        # 記事が存在しない場合は None を返す
        return None

    # 表示用に加工して返却
    return _decorate_post(post, cats)


# -----------------------------
# 表示用共通加工
# -----------------------------
def _decorate_post(post, cats):
    """
    記事データを表示用に加工する共通処理

    - カテゴリ／トピック／グループ名を付与
    - Markdown を HTML に変換
    """
    # ID → 名前変換用のマップを作成
    category_map = {c["id"]: c["name"] for c in cats["categories"]}
    topic_map = {t["id"]: t["name"] for t in cats["topics"]}
    group_map = {g["id"]: g["name"] for g in cats["groups"]}

    # 元データを破壊しないためコピーを作成
    post = post.copy()  # ★ 破壊防止（重要）

    # カテゴリ／トピック／グループ名を付与
    post["category_name"] = category_map.get(post["category_id"], "未分類")
    post["topic_name"] = topic_map.get(post["topic_id"], "-")
    post["group_name"] = group_map.get(post["group_id"], "-")

    # Markdown を HTML に変換
    post["html_content"] = markdown.markdown(
        post["content"],
        extensions=["fenced_code", "tables", "toc", "nl2br"]
    )

    return post


# --------------------------------------
#  トピック一覧取得（カテゴリIDで絞る）
# --------------------------------------
def load_topics_by_category(category_id: int):
    """
    指定されたカテゴリIDに紐づくトピック一覧を取得する
    """
    # カテゴリ情報を読み込む
    cats = load_categories()
    topics = cats["topics"]

    # 指定カテゴリに属するトピックのみ返す
    return [t for t in topics if t["category_id"] == category_id]


# --------------------------------------
#  グループ一覧取得（トピックIDで絞る）
# --------------------------------------
def load_groups_by_topic(topic_id: int):
    """
    指定されたトピックIDに紐づくグループ一覧を取得する
    """
    # カテゴリ情報を読み込む
    cats = load_categories()
    groups = cats["groups"]

    # 指定トピックに属するグループのみ返す
    return [g for g in groups if g["topic_id"] == topic_id]
