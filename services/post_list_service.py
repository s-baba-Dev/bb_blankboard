from util.dataLoader import load_posts, load_categories
from math import ceil


def build_post_list(
    page: int,
    limit: int,
    sort: str,
    q: str | None = None,
    category_id: int | None = None,
    topic_id: int | None = None,
    group_id: int | None = None,
    public=False
):
    """
    投稿一覧画面用のデータを構築する共通処理

    - 検索・絞り込み・ソート・ページネーションを一括で行う
    - public=True の場合は公開記事のみを対象とする
    """

    # =========================
    # ① データ読み込み
    # =========================
    # 公開画面の場合は公開記事のみ、それ以外は全記事を取得
    if public:
        posts = load_posts(public_only=True)
    else:
        posts = load_posts()

    # カテゴリ・トピック・グループ情報を取得
    cats = load_categories()

    # =========================
    # ② ID → 名前 map 作成
    # =========================
    # 表示用に ID から名前へ変換するためのマップを作成
    category_map = {c["id"]: c["name"] for c in cats["categories"]}
    topic_map = {t["id"]: t["name"] for t in cats["topics"]}
    group_map = {g["id"]: g["name"] for g in cats["groups"]}

    # 検索状態を示すフラグと検索クエリ
    searched = False
    search_query = None

    # =========================
    # ③ 検索（キーワード）
    # =========================
    # タイトルまたは本文にキーワードが含まれる記事を抽出
    if q is not None:
        q = q.strip()
        if q != "":
            searched = True
            search_query = q
            q_lower = q.lower()

            posts = [
                p for p in posts
                if q_lower in p["title"].lower()
                or q_lower in p["content"].lower()
            ]

    # =========================
    # ④ 絞り込み（カテゴリ / トピック / グループ）
    # =========================
    filtered = False

    # カテゴリで絞り込み
    if category_id is not None:
        filtered = True
        posts = [p for p in posts if p.get("category_id") == category_id]

    # トピックで絞り込み
    if topic_id is not None:
        filtered = True
        posts = [p for p in posts if p.get("topic_id") == topic_id]

    # グループで絞り込み
    if group_id is not None:
        filtered = True
        posts = [p for p in posts if p.get("group_id") == group_id]

    # =========================
    # ⑤ ソート
    # =========================
    # 作成日時で並び替え
    if sort == "created_asc":
        posts.sort(key=lambda x: x["created_at"])
    else:
        posts.sort(key=lambda x: x["created_at"], reverse=True)

    # =========================
    # ⑥ ページネーション
    # =========================
    total = len(posts)
    total_pages = ceil(total / limit) if total > 0 else 1

    # 表示対象の開始・終了インデックスを計算
    start = (page - 1) * limit
    end = start + limit
    page_posts = posts[start:end]

    # =========================
    # ⑦ 表示用データ付与（name）
    # =========================
    # ID をもとにカテゴリ・トピック・グループ名を付与
    for p in page_posts:
        p["category_name"] = category_map.get(p.get("category_id"), "")
        p["topic_name"] = topic_map.get(p.get("topic_id"), "")
        p["group_name"] = group_map.get(p.get("group_id"), "")

    # =========================
    # ⑧ return
    # =========================
    # 一覧表示に必要な情報をまとめて返却
    return {
        "posts": page_posts,
        "total_pages": total_pages,
        "searched": searched,
        "search_query": search_query,
        "total": total,
        "filtered": filtered,
    }
