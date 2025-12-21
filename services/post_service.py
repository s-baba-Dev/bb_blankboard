from util.dataLoader import load_posts, save_posts
from util.post_status import (
    STATUS_PUBLIC,
    STATUS_PRIVATE,
    STATUS_DRAFT,
)

# =====================================
# 公開 / 非公開トグル
# =====================================
def toggle_status(post_id: int, status: str) -> bool:
    """
    記事の公開 / 非公開ステータスを切り替える

    - 下書き（STATUS_DRAFT）の記事は対象外
    - status は "public" または "private" のみ許可
    - 成功時は True、失敗時は False を返す
    """

    # 許可されていないステータス値は即時拒否
    if status not in ("public", "private"):
        return False

    # 全記事データを読み込む
    posts = load_posts()

    for post in posts:
        # 対象の記事IDでなければスキップ
        if post.get("id") != post_id:
            continue

        # 下書き状態の記事は公開・非公開の切り替え不可
        if post.get("status") == STATUS_DRAFT:
            return False

        # 既に同じ状態の場合は何もせず成功扱い（冪等性の確保）
        if status == "public" and post["status"] == STATUS_PUBLIC:
            return True
        if status == "private" and post["status"] == STATUS_PRIVATE:
            return True

        # ステータスを更新
        post["status"] = (
            STATUS_PUBLIC if status == "public"
            else STATUS_PRIVATE
        )

        # 更新後の記事データを保存
        save_posts(posts)
        return True

    # 対象の記事が見つからなかった場合
    return False


# =====================================
# 関連記事取得（公開記事のみ）
# =====================================
def get_related_posts(post, limit: int = 3):
    """
    同一カテゴリに属する公開記事から関連記事を取得する

    - 自分自身の記事は除外
    - 作成日時の新しい順に並べ替える
    """

    # 公開記事のみを取得
    posts = load_posts(public_only=True)

    # 同一カテゴリかつ自分以外の記事を抽出
    related = [
        p for p in posts
        if p.get("id") != post.get("id")
        and p.get("category_id") == post.get("category_id")
    ]

    # 作成日時の新しい順にソート
    related.sort(
        key=lambda x: x.get("created_at", ""),
        reverse=True
    )

    # 指定件数分だけ返却
    return related[:limit]
