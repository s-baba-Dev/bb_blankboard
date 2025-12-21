from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from control.categoryControl import CategoryControl
from datetime import datetime
from fastapi import HTTPException, Request, Query
from util.dataLoader import load_posts, save_posts, load_categories, save_categories, get_post_detail_admin
from util.post_status import STATUS_PUBLIC, STATUS_PRIVATE, STATUS_DRAFT
from services.post_list_service import build_post_list

# Jinja2 テンプレート設定（管理者画面用）
templates = Jinja2Templates(directory="templates")


class PostAdminControl:
    """
    管理者向けの投稿管理を担当するコントローラクラス

    投稿一覧・詳細表示・作成・更新・削除といった
    管理者操作をまとめて扱う
    """

    def __init__(self):
        # カテゴリ／トピック／グループ制御用クラス
        self.cat = CategoryControl()

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
        管理者向けの記事一覧ページを表示する

        - 公開／非公開／下書きすべてを対象
        - 検索、絞り込み、ページネーション対応
        """
        # 一覧表示用データを構築
        data = build_post_list(
            page=page,
            limit=limit,
            sort=sort,
            q=q,
            category_id=category_id,
            topic_id=topic_id,
            group_id=group_id,
        )

        # カテゴリ関連データを取得
        categories = load_categories()

        # 管理者用一覧テンプレートをレンダリング
        return templates.TemplateResponse(
            "admin/index.html",
            {
                "request": request,
                **data,

                # カテゴリ関連データ
                "categories": categories["categories"],
                "topics": categories["topics"],
                "groups": categories["groups"],

                # ステータス定数（テンプレート内判定用）
                "STATUS_PUBLIC": STATUS_PUBLIC,
                "STATUS_PRIVATE": STATUS_PRIVATE,
                "STATUS_DRAFT": STATUS_DRAFT,

                # 状態保持用パラメータ
                "page": page,
                "limit": limit,
                "sort": sort,
                "q": q,
                "category_id": category_id,
                "topic_id": topic_id,
                "group_id": group_id,
                "query_params": dict(request.query_params),
            }
        )

    def post_detail_admin(self, request, post_id: int):
        """
        管理者向けの記事詳細ページを表示する
        """
        # 管理者用の記事詳細を取得
        post = get_post_detail_admin(post_id)
        if not post:
            raise HTTPException(status_code=404)

        # 記事詳細テンプレートをレンダリング
        return templates.TemplateResponse(
            "admin/post_detail_admin.html",
            {
                "request": request,
                "post": post,
                "post_html": post["html_content"],  # HTML変換済み本文
            }
        )


    # --------------------------------
    # 新規投稿フォーム
    # --------------------------------
    def show_create_form(self, request, cats):
        """
        新規投稿作成フォームを表示する
        """
        return templates.TemplateResponse(
            "admin/create.html",
            {
                "request": request,
                "categories": cats["categories"],
                "topics": cats["topics"],
                "groups": cats["groups"]
            }
        )

    # --------------------------------
    # 投稿作成
    # --------------------------------
    def create_post(
        self, title, content, action,
        category_mode, category_id, new_category_name,
        topic_mode, topic_id, new_topic_name,
        group_mode, group_id, new_group_name
    ):
        """
        新規投稿を作成する処理

        - カテゴリ／トピック／グループの新規作成にも対応
        - action に応じて公開／下書き状態を設定
        """
        # 保存ステータスを決定
        if action == "draft":
            status = STATUS_PRIVATE
        elif action == "public":
            status = STATUS_PUBLIC
        else:
            raise ValueError("invalid action")

        print("保存ステータス =", status)

        # カテゴリ取得または新規作成
        category_id = self.cat.add_or_get_category(
            category_mode, category_id, new_category_name
        )

        # カテゴリを新規作成した場合はトピックも新規扱い
        if category_mode == "new":
            topic_mode = "new"

        # トピック取得または新規作成
        topic_id = self.cat.add_or_get_topic(
            topic_mode, topic_id, new_topic_name, category_id
        )

        # グループ取得または新規作成
        group_id = self.cat.add_or_get_group(
            group_mode, group_id, new_group_name, topic_id
        )

        # 既存投稿を読み込む
        posts = load_posts()

        # 新しい投稿IDを採番
        new_id = posts[-1]["id"] + 1 if posts else 1

        # 作成日時を文字列で保存
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        # 新規投稿データ
        new_post = {
            "id": new_id,
            "title": title,
            "content": content,
            "category_id": category_id,
            "topic_id": topic_id,
            "group_id": group_id,
            "status": status,
            "created_at": now,
        }

        # 投稿を追加して保存
        posts.append(new_post)
        save_posts(posts)

        # 投稿一覧へリダイレクト
        return RedirectResponse("/admin/posts", status_code=303)

    # --------------------------------
    # 投稿削除
    # --------------------------------
    def delete_post(self, post_id):
        """
        投稿を削除する処理
        """
        posts = load_posts()
        posts = [p for p in posts if p["id"] != post_id]
        save_posts(posts)

        return RedirectResponse("/admin/posts", status_code=303)

    # --------------------------------
    # 投稿更新
    # --------------------------------
    def update_post(self, request, post_id, form):
        """
        投稿内容を更新する処理

        カテゴリ／トピック／グループの新規追加にも対応する
        """

        # フォーム入力値を取得
        title = form.get("title", "").strip()
        content = form.get("content", "")

        category_mode = form.get("category_mode")
        topic_mode = form.get("topic_mode")
        group_mode = form.get("group_mode")

        category_id = form.get("category_id")
        topic_id = form.get("topic_id")
        group_id = form.get("group_id")

        new_category_name = form.get("new_category_name", "").strip()
        new_topic_name = form.get("new_topic_name", "").strip()
        new_group_name = form.get("new_group_name", "").strip()

        # 投稿・カテゴリ情報を読み込む
        posts = load_posts()
        cats = load_categories()

        categories = cats["categories"]
        topics = cats["topics"]
        groups = cats["groups"]

        # 更新対象の記事を取得
        post = next((p for p in posts if p["id"] == post_id), None)
        if not post:
            raise HTTPException(status_code=404, detail="投稿が見つかりません。")

        # -------------------------------------------------------
        # カテゴリ処理
        # -------------------------------------------------------
        if category_mode == "new":
            if new_category_name == "":
                return self._error_response(request, post, cats, "カテゴリ名が空です。")
            if any(c["name"].lower() == new_category_name.lower() for c in categories):
                return self._error_response(request, post, cats, "既に同名カテゴリがあります。")

            new_id = max([c["id"] for c in categories], default=0) + 1
            categories.append({"id": new_id, "name": new_category_name})
            category_id = new_id
        else:
            category_id = int(category_id)

        # -------------------------------------------------------
        # トピック処理
        # -------------------------------------------------------
        if topic_mode == "new":
            if new_topic_name == "":
                return self._error_response(request, post, cats, "トピック名が空です。")
            if any(t["name"].lower() == new_topic_name.lower() for t in topics):
                return self._error_response(request, post, cats, "既に同名トピックがあります。")

            new_id = max([t["id"] for t in topics], default=0) + 1
            topics.append({
                "id": new_id,
                "name": new_topic_name,
                "category_id": category_id
            })
            topic_id = new_id
        else:
            topic_id = int(topic_id)

        # -------------------------------------------------------
        # グループ処理
        # -------------------------------------------------------
        if group_mode == "new":
            if new_group_name == "":
                return self._error_response(request, post, cats, "グループ名が空です。")
            if any(g["name"].lower() == new_group_name.lower() for g in groups):
                return self._error_response(request, post, cats, "既に同名グループがあります。")

            new_id = max([g["id"] for g in groups], default=0) + 1
            groups.append({
                "id": new_id,
                "name": new_group_name,
                "topic_id": topic_id
            })
            group_id = new_id
        else:
            group_id = int(group_id)

        # 投稿内容を更新
        post["title"] = title
        post["content"] = content
        post["category_id"] = category_id
        post["topic_id"] = topic_id
        post["group_id"] = group_id

        # 更新時は下書き状態に戻す
        post["status"] = STATUS_DRAFT

        # 更新内容を保存
        save_posts(posts)
        save_categories(cats)

        return self._success_response(request, post, cats, "更新しました！")

    # --------------------------------
    # エラー応答
    # --------------------------------
    def _error_response(self, request, post, cats, message):
        """
        編集画面にエラーメッセージを表示する
        """
        return templates.TemplateResponse(
            "admin/edit.html",
            {
                "request": request,
                "post": post,
                "categories": cats["categories"],
                "topics": cats["topics"],
                "groups": cats["groups"],
                "error": message
            }
        )

    # --------------------------------
    # 成功応答
    # --------------------------------
    def _success_response(self, request, post, cats, msg):
        """
        編集画面に成功メッセージを表示する
        """
        return templates.TemplateResponse(
            "admin/edit.html",
            {
                "request": request,
                "post": post,
                "categories": cats["categories"],
                "topics": cats["topics"],
                "groups": cats["groups"],
                "success": msg
            }
        )
