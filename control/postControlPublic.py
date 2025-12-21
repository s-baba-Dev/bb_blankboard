from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import HTTPException, Request
from util.dataLoader import load_posts, load_categories, get_post_detail_public
from services.post_list_service import build_post_list

# Jinja2 テンプレート設定（一般ユーザー向け画面）
templates = Jinja2Templates(directory="templates")


class PostPublicControl:
    """
    一般ユーザー向けの投稿表示を制御するクラス

    記事一覧表示・記事詳細表示の責務を持ち、
    具体的なデータ構築処理は service 層に委譲する
    """

    def __init__(self):
        # 現状は初期化処理なし（将来拡張用）
        pass

    def list_posts(
        self,
        request,
        page,
        limit,
        sort,
        q=None,
        category_id=None,
        topic_id=None,
        group_id=None,
    ):
        """
        一般ユーザー向けの記事一覧ページを表示する

        - 検索、絞り込み、ソート、ページネーションに対応
        - 公開記事のみを対象とする
        """
        # 投稿一覧用のデータを構築（公開記事のみ）
        data = build_post_list(
            page=page,
            limit=limit,
            sort=sort,
            q=q,
            category_id=category_id,
            topic_id=topic_id,
            group_id=group_id,
            public=True
        )

        # カテゴリ・トピック・グループ情報を取得
        categories = load_categories()

        # 記事一覧ページをレンダリング
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                **data,

                # カテゴリ関連データ
                "categories": categories["categories"],
                "topics": categories["topics"],
                "groups": categories["groups"],

                # 状態保持用（ページ遷移・再検索用）
                "page": page,
                "limit": limit,
                "sort": sort,
                "q": q,
                "category_id": category_id,
                "topic_id": topic_id,
                "group_id": group_id,
                "query_params": dict(request.query_params),
                "query_string": request.url.query,
            }
        )

    def read_post(self, request: Request, post_id: int):
        """
        一般ユーザー向けの記事詳細ページを表示する
        """
        # 公開記事の詳細を取得
        post = get_post_detail_public(post_id)
        if not post:
            # 記事が存在しない場合は 404
            raise HTTPException(status_code=404)

        # クエリパラメータを保持（一覧画面へ戻るため）
        query_params = dict(request.query_params)

        # 記事詳細ページをレンダリング
        return templates.TemplateResponse(
            "post_detail_public.html",
            {
                "request": request,
                "post": post,
                "query_string": request.url.query,
            }
        )
