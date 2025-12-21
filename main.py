"""
FastAPI アプリケーションのエントリーポイント

このファイルは以下の役割を持つ。
- URL と処理（関数）を結びつけるルーティング定義
- 一般ユーザー向け画面と管理者向け画面の入口
- 認証チェックやリクエストパラメータの受け渡し

※ 実際の業務ロジックやデータ操作は control / services / util に委譲している
"""

import os
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi import FastAPI, Request, Form, Depends, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi import Body
from dotenv import load_dotenv

from control.postControlPublic import PostPublicControl
from control.postControlAdmin import PostAdminControl
from services.post_service import toggle_status, get_related_posts
from util.post_status import STATUS_PUBLIC, STATUS_PRIVATE, STATUS_DRAFT
from util.dataLoader import (
    load_posts,
    load_categories,
    save_categories,
    load_topics_by_category,
    load_groups_by_topic,
    get_post_detail_public,
    get_post_detail_admin,
)

# -----------------------------
# FastAPI 初期設定
# -----------------------------
load_dotenv()

# FastAPI アプリケーションのインスタンスを生成
app = FastAPI()

# 静的ファイル（CSS / JavaScript / 画像など）を配信するための設定
# URL の /static にアクセスすると static ディレクトリ配下が参照される
app.mount("/static", StaticFiles(directory="static"), name="static")

# このファイル自身の絶対パスを基準にしたベースディレクトリ
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Jinja2 テンプレートの読み込み設定
# templates ディレクトリ配下の HTML をレンダリングする
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# 一般ユーザー向けの記事制御クラスのインスタンス
public_control = PostPublicControl()

# 管理者向けの記事制御クラスのインスタンス
post_admin = PostAdminControl()

# ====================================
# 一般ユーザー
# ====================================

# ルートアクセスは /posts にリダイレクト
@app.get("/", include_in_schema=False)
def root():
    # トップページへの直接アクセス時は記事一覧ページへ遷移させる
    return RedirectResponse("/posts")

@app.get("/posts", response_class=HTMLResponse)
def public_list(
    request: Request,
    page: int = Query(1, ge=1),                                     # ページ番号（1以上のみ許可）
    limit: int = Query(10, ge=1),                                   # 1ページあたりの表示件数
    sort: str = Query("created_desc"),                              # 並び順（作成日降順がデフォルト）
    q: str | None = Query(None),                                    # 検索キーワード
    category_id: str | None = Query(None),                          # カテゴリID（文字列で受け取る）
    topic_id: str | None = Query(None),                             # トピックID（文字列で受け取る）
    group_id: str | None = Query(None),                             # グループID（文字列で受け取る）
):
    """
    一般ユーザー向けの記事一覧ページを表示する

    クエリパラメータによるページネーション、検索、
    カテゴリ／トピック／グループでの絞り込みに対応する
    """

    # クエリパラメータのIDを int または None に正規化する
    # 未指定や空文字の場合は None として扱う
    def normalize_id(v):
        return int(v) if v not in (None, "") else None

    # 各IDパラメータを正規化
    category_id = normalize_id(category_id)
    topic_id = normalize_id(topic_id)
    group_id = normalize_id(group_id)

    # 実際の記事取得・一覧生成処理は公開用コントローラに委譲
    return public_control.list_posts(
        request=request,
        page=page,
        limit=limit,
        sort=sort,
        q=q,
        category_id=category_id,
        topic_id=topic_id,
        group_id=group_id,
    )

@app.get("/posts/{post_id}", response_class=HTMLResponse)
def read_post_public(request: Request, post_id: int):
    """
    一般ユーザー向けの記事詳細ページを表示する

    指定された post_id の記事を取得し、
    記事本文と関連記事を含めてテンプレートに渡す
    """

    # 公開状態の記事詳細を取得
    post = get_post_detail_public(post_id)
    if not post:
        # 記事が存在しない場合は 404 エラーを返す
        raise HTTPException(status_code=404)

    # 現在の記事に関連する記事を取得
    related_posts = get_related_posts(post)

    # 記事詳細ページをレンダリングして返却
    return templates.TemplateResponse(
        "post_detail_public.html",
        {
            "request": request,
            "post": post,
            "post_html": post["html_content"],  # HTML変換済みの記事本文
            "related_posts": related_posts,     # 関連記事一覧
        },
    )

# ====================================
# 管理者ログイン
# ====================================

# 管理者アカウント情報（簡易実装）
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


def verify_admin(request: Request):
    """
    管理者としてログイン済みかを確認する依存関数

    Cookie に保存されている admin_session を確認し、
    未ログインの場合はログイン画面へリダイレクトする
    """
    # 管理者セッション Cookie を取得
    session = request.cookies.get("admin_session")
    if session != "valid":
        # 未ログイン時はログイン画面へ遷移
        raise HTTPException(
            status_code=303,
            headers={"Location": "/admin/login"}
        )


@app.get("/admin/login", response_class=HTMLResponse)
def admin_login_page(request: Request, error: str | None = None):
    """
    管理者ログイン画面を表示する

    ログイン失敗時は error メッセージをテンプレートに渡す
    """
    return templates.TemplateResponse(
        "admin/login.html",
        {
            "request": request,
            "error": error,
        },
    )


# ログイン失敗回数の上限
FAILED_LOGIN_LIMIT = 5

# IP アドレスごとのログイン失敗回数を保持する辞書
failed_login_count = {}


@app.post("/admin/login")
def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    """
    管理者ログイン処理

    - IP アドレスごとにログイン失敗回数を管理
    - 一定回数以上失敗した場合はログインを一時的に制限する
    """
    # クライアントの IP アドレスを取得
    ip = request.client.host

    # 初回アクセス時は失敗回数を 0 で初期化
    failed_login_count.setdefault(ip, 0)

    # 失敗回数が上限を超えている場合はログイン不可
    if failed_login_count[ip] >= FAILED_LOGIN_LIMIT:
        return templates.TemplateResponse(
            "admin/login.html",
            {
                "request": request,
                "error": "ログイン試行回数が多すぎます。しばらく待ってください。",
            },
            status_code=403,
        )

    # 認証成功時の処理
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        # 失敗回数をリセット
        failed_login_count[ip] = 0

        # 管理者投稿一覧へリダイレクト
        res = RedirectResponse("/admin/posts", status_code=303)

        # 管理者ログイン状態を示す Cookie を設定
        res.set_cookie(
            "admin_session",
            "valid",
            max_age=60 * 60,   # 有効期限（1時間）
            httponly=True,     # JavaScript から参照不可
            samesite="lax",    # CSRF 対策
        )
        return res

    # 認証失敗時は失敗回数を加算
    failed_login_count[ip] += 1

    # エラーメッセージ付きでログイン画面を再表示
    return templates.TemplateResponse(
        "admin/login.html",
        {
            "request": request,
            "error": "ユーザーIDまたはパスワードが違います。",
        },
        status_code=400,
    )


@app.get("/admin/logout")
def admin_logout():
    """
    管理者ログアウト処理

    管理者セッション用 Cookie を削除し、
    ログイン画面へリダイレクトする
    """
    # ログイン画面へリダイレクト
    res = RedirectResponse("/admin/login", status_code=303)

    # 管理者セッション Cookie を削除
    res.delete_cookie("admin_session")

    return res

# ====================================
# 管理者：投稿一覧（ページネーション対応）
# ====================================
@app.get("/admin/posts", response_class=HTMLResponse)
def admin_list(
    request: Request,
    admin: None = Depends(verify_admin),
    page: int = Query(1),                                           # ページ番号（クエリパラメータ）
    limit: int = Query(10),                                         # 1ページあたりの表示件数
    sort: str = Query("created_desc"),                              # 並び順（作成日降順）
    q: str | None = None,                                           # 検索キーワード
    category_id: str | None = Query(None),                          # カテゴリID（文字列）
    topic_id: str | None = Query(None),                             # トピックID（文字列）
    group_id: str | None = Query(None),                             # グループID（文字列）
):
    """
    管理者向けの記事一覧ページを表示する

    - 下書き・非公開記事も含めて一覧表示
    - ページネーション、検索、カテゴリ／トピック／グループ絞り込みに対応
    """

    # クエリパラメータのIDを int または None に正規化する
    def normalize_id(v):
        return int(v) if v not in (None, "") else None

    # 各IDを正規化
    category_id = normalize_id(category_id)
    topic_id = normalize_id(topic_id)
    group_id = normalize_id(group_id)

    # 実際の記事一覧取得処理は管理者用コントローラに委譲
    return post_admin.list_posts(
        request=request,
        page=page,
        limit=limit,
        sort=sort,
        q=q,
        category_id=category_id,
        topic_id=topic_id,
        group_id=group_id,
    )

# ====================================
# 管理者：投稿一覧・新規作成
# ====================================

@app.get("/admin/posts/new", response_class=HTMLResponse)
def new_post_form(request: Request, admin=Depends(verify_admin)):
    """
    新規投稿作成フォームを表示する（管理者専用）

    事前にカテゴリ・トピック・グループ情報を読み込み、
    入力フォームで選択できるようにする
    """
    # カテゴリ・トピック・グループ情報を読み込む
    cats = load_categories()

    # 新規作成フォームを表示
    return post_admin.show_create_form(request, cats)


@app.post("/admin/posts/new")
def create_post(
    request: Request,
    title: str = Form(...),                 # 記事タイトル
    content: str = Form(...),               # 記事本文（Markdown 等）
    action: str = Form(...),                # 保存／公開などのアクション種別
    category_mode: str = Form(...),         # 既存カテゴリ or 新規カテゴリ選択
    category_id: int | None = Form(None),   # 既存カテゴリID
    new_category_name: str | None = Form(None), # 新規カテゴリ名
    topic_mode: str = Form(...),            # 既存トピック or 新規トピック選択
    topic_id: int | None = Form(None),      # 既存トピックID
    new_topic_name: str | None = Form(None),# 新規トピック名
    group_mode: str = Form(...),            # 既存グループ or 新規グループ選択
    group_id: int | None = Form(None),      # 既存グループID
    new_group_name: str | None = Form(None),# 新規グループ名
    admin=Depends(verify_admin),
):
    """
    新規投稿を作成する処理（管理者専用）

    入力内容に応じてカテゴリ／トピック／グループの新規作成や紐付けを行い、
    記事データを保存する
    """
    # 実際の投稿作成処理は管理者用コントローラに委譲
    return post_admin.create_post(
        title,
        content,
        action,
        category_mode,
        category_id,
        new_category_name,
        topic_mode,
        topic_id,
        new_topic_name,
        group_mode,
        group_id,
        new_group_name,
    )

# ====================================
# カテゴリ管理ページ（1画面）
# ====================================
@app.get("/admin/posts/category_manage", response_class=HTMLResponse)
def show_category_manage(request: Request, admin: None = Depends(verify_admin)):
    """
    カテゴリ・トピック・グループを一括で管理する画面を表示する（管理者専用）

    1画面でカテゴリ／トピック／グループの一覧・編集・削除を行う想定
    """
    # 現在登録されているカテゴリ関連データをすべて読み込む
    cats = load_categories()

    # 管理画面用テンプレートをレンダリング
    return templates.TemplateResponse(
        "admin/category_manage.html",
        {
            "request": request,
            "categories": cats["categories"],  # カテゴリ一覧
            "topics": cats["topics"],          # トピック一覧
            "groups": cats["groups"],          # グループ一覧
        },
    )


# -----------------------------
# API：カテゴリ → トピック一覧
# -----------------------------
@app.get("/admin/api/topics")
def api_get_topics(category_id: int = Query(...), admin: None = Depends(verify_admin)):
    """
    指定されたカテゴリに紐づくトピック一覧を返す API（管理者専用）

    カテゴリ選択時の動的UI更新用
    """
    return JSONResponse(load_topics_by_category(category_id))

# -----------------------------
# API：トピック → グループ一覧
# -----------------------------
@app.get("/admin/api/groups")
def api_get_groups(topic_id: int = Query(...), admin: None = Depends(verify_admin)):
    """
    指定されたトピックに紐づくグループ一覧を返す API（管理者専用）

    トピック選択時の動的UI更新用
    """
    return JSONResponse(load_groups_by_topic(topic_id))

# -----------------------------
# API：カテゴリ作成
# -----------------------------
@app.post("/admin/api/category_create")
def api_create_category(
    category_name: str = Form(...),   # 新規カテゴリ名
    topic_name: str = Form(""),       # 新規トピック名（任意）
    group_name: str = Form(""),       # 新規グループ名（任意）
    admin: None = Depends(verify_admin),
):
    """
    カテゴリを新規作成する API（管理者専用）

    必要に応じて、同時にトピック・グループも作成する
    """
    # 現在のカテゴリ・トピック・グループ情報を読み込む
    cats = load_categories()

    # カテゴリ作成
    # 既存IDの最大値 + 1 を新しいカテゴリIDとする
    new_cat_id = max([c["id"] for c in cats["categories"]], default=0) + 1
    cats["categories"].append({"id": new_cat_id, "name": category_name})

    # トピック作成（任意）
    new_topic_id = None
    if topic_name:
        # 新規トピックIDを採番
        new_topic_id = max([t["id"] for t in cats["topics"]], default=0) + 1
        cats["topics"].append(
            {"id": new_topic_id, "name": topic_name, "category_id": new_cat_id}
        )

    # グループ作成（任意）
    # トピックが作成された場合のみグループを作成する
    if group_name and new_topic_id:
        new_group_id = max([g["id"] for g in cats["groups"]], default=0) + 1
        cats["groups"].append(
            {"id": new_group_id, "name": group_name, "topic_id": new_topic_id}
        )

    # 更新後のカテゴリ情報を保存
    save_categories(cats)

    return JSONResponse({"status": "ok"})


# -----------------------------
# API：カテゴリ更新
# -----------------------------
@app.post("/admin/api/category_update")
def api_update_category(
    category_id: int = Form(...),  # 更新対象のカテゴリID
    name: str = Form(...),         # 新しいカテゴリ名
    admin: None = Depends(verify_admin),
):
    """
    カテゴリ名を更新する API（管理者専用）
    """
    # カテゴリ情報を読み込む
    cats = load_categories()

    # 対象カテゴリを検索して名前を更新
    for c in cats["categories"]:
        if c["id"] == category_id:
            c["name"] = name
            break

    # 更新内容を保存
    save_categories(cats)

    return JSONResponse({"status": "ok"})


# -----------------------------------------
# API：カテゴリ削除（配下も削除）
# -----------------------------------------
@app.post("/admin/api/category_delete")
def api_delete_category(category_id: int = Form(...), admin: None = Depends(verify_admin)):
    """
    カテゴリを削除する API（管理者専用）

    - 記事で使用されているカテゴリは削除不可
    - 削除時は配下のトピック・グループも同時に削除する
    """
    # カテゴリ情報と記事一覧を読み込む
    cats = load_categories()
    posts = load_posts()

    # 投稿で使用されているかチェック
    used = any(p.get("category_id") == category_id for p in posts)
    if used:
        # 使用中の場合はエラーを返す
        return JSONResponse(
            {"status": "error", "message": "このカテゴリを使用している記事があるため削除できません。"},
            status_code=400,   # クライアント側で判定しやすいようにエラーコードを返す
        )

    # --- 使用されていなければ削除 ---
    # カテゴリを削除
    cats["categories"] = [c for c in cats["categories"] if c["id"] != category_id]

    # 配下のトピックIDを取得
    deleted_topics = [t["id"] for t in cats["topics"] if t["category_id"] == category_id]

    # トピックを削除
    cats["topics"] = [t for t in cats["topics"] if t["category_id"] != category_id]

    # トピックに紐づくグループも削除
    cats["groups"] = [g for g in cats["groups"] if g["topic_id"] not in deleted_topics]

    # 更新内容を保存
    save_categories(cats)

    return JSONResponse({"status": "ok"})

# -----------------------------
# API：トピック作成
# -----------------------------
@app.post("/admin/api/topic_create")
def api_create_topic(
    category_id: int = Form(...),  # 紐づけるカテゴリID
    name: str = Form(...),         # 新規トピック名
    admin: None = Depends(verify_admin),
):
    """
    トピックを新規作成する API（管理者専用）

    指定されたカテゴリに紐づくトピックを追加する
    """
    # カテゴリ情報を読み込む
    cats = load_categories()

    # 新しいトピックIDを採番（最大ID + 1）
    new_topic_id = max([t["id"] for t in cats["topics"]], default=0) + 1

    # トピックを追加
    cats["topics"].append(
        {"id": new_topic_id, "name": name, "category_id": category_id}
    )

    # 更新内容を保存
    save_categories(cats)

    return JSONResponse({"status": "ok"})


# -----------------------------
# API：トピック更新
# -----------------------------
@app.post("/admin/api/topic_update")
def api_update_topic(
    topic_id: int = Form(...),  # 更新対象のトピックID
    name: str = Form(...),      # 新しいトピック名
    admin: None = Depends(verify_admin),
):
    """
    トピック名を更新する API（管理者専用）
    """
    # カテゴリ情報を読み込む
    cats = load_categories()

    # 対象トピックを検索して名前を更新
    for t in cats["topics"]:
        if t["id"] == topic_id:
            t["name"] = name
            break

    # 更新内容を保存
    save_categories(cats)

    return JSONResponse({"status": "ok"})


# -----------------------------------------
# API：トピック削除（配下グループも削除）
# -----------------------------------------
@app.post("/admin/api/topic_delete")
def api_delete_topic(topic_id: int = Form(...), admin: None = Depends(verify_admin)):
    """
    トピックを削除する API（管理者専用）

    - 記事で使用されているトピックは削除不可
    - 削除時は配下のグループも同時に削除する
    """
    # カテゴリ情報と記事一覧を読み込む
    cats = load_categories()
    posts = load_posts()

    # 投稿で使用されているかチェック
    used = any(p.get("topic_id") == topic_id for p in posts)
    if used:
        return JSONResponse(
            {"status": "error", "message": "このトピックを使用している記事があるため削除できません。"},
            status_code=400,   # 使用中のため削除不可
        )

    # トピックを削除
    cats["topics"] = [t for t in cats["topics"] if t["id"] != topic_id]

    # トピックに紐づくグループも削除
    cats["groups"] = [g for g in cats["groups"] if g["topic_id"] != topic_id]

    # 更新内容を保存
    save_categories(cats)

    return JSONResponse({"status": "ok"})


# -----------------------------
# API：グループ作成
# -----------------------------
@app.post("/admin/api/group_create")
def api_create_group(
    topic_id: int = Form(...),  # 紐づけるトピックID
    name: str = Form(...),      # 新規グループ名
    admin: None = Depends(verify_admin),
):
    """
    グループを新規作成する API（管理者専用）

    指定されたトピックに紐づくグループを追加する
    """
    # カテゴリ情報を読み込む
    cats = load_categories()

    # 新しいグループIDを採番（最大ID + 1）
    new_group_id = max([g["id"] for g in cats["groups"]], default=0) + 1

    # グループを追加
    cats["groups"].append(
        {"id": new_group_id, "name": name, "topic_id": topic_id}
    )

    # 更新内容を保存
    save_categories(cats)

    return JSONResponse({"status": "ok"})


# -----------------------------
# API：グループ更新
# -----------------------------
@app.post("/admin/api/group_update")
def api_update_group(
    group_id: int = Form(...),  # 更新対象のグループID
    name: str = Form(...),      # 新しいグループ名
    admin: None = Depends(verify_admin),
):
    """
    グループ名を更新する API（管理者専用）
    """
    # カテゴリ情報を読み込む
    cats = load_categories()

    # 対象グループを検索して名前を更新
    for g in cats["groups"]:
        if g["id"] == group_id:
            g["name"] = name
            break

    # 更新内容を保存
    save_categories(cats)

    return JSONResponse({"status": "ok"})


# -----------------------------------------
# API：グループ削除
# -----------------------------------------
@app.post("/admin/api/group_delete")
def api_delete_group(group_id: int = Form(...), admin: None = Depends(verify_admin)):
    """
    グループを削除する API（管理者専用）

    記事で使用されているグループは削除不可
    """
    # カテゴリ情報と記事一覧を読み込む
    cats = load_categories()
    posts = load_posts()

    # 投稿で使用されているかチェック
    used = any(p.get("group_id") == group_id for p in posts)
    if used:
        return JSONResponse(
            {"status": "error", "message": "このグループを使用している記事があるため削除できません。"},
            status_code=400,   # 使用中のため削除不可
        )

    # グループを削除
    cats["groups"] = [g for g in cats["groups"] if g["id"] != group_id]

    # 更新内容を保存
    save_categories(cats)

    return JSONResponse({"status": "ok"})

# ====================================
# 管理者：投稿詳細・編集・削除
# ====================================

@app.get("/admin/posts/{post_id}", response_class=HTMLResponse)
def read_post_admin(request: Request, post_id: int, admin=Depends(verify_admin)):
    """
    管理者向けの記事詳細ページを表示する

    下書き・非公開を含む記事の詳細情報を取得して表示する
    """
    # 管理者用の記事詳細取得処理をコントローラに委譲
    return post_admin.post_detail_admin(request, post_id)


@app.get("/admin/posts/{post_id}/edit", response_class=HTMLResponse)
def edit_post_admin(request: Request, post_id: int, admin=Depends(verify_admin)):
    """
    管理者向けの記事編集画面を表示する

    編集対象の記事情報と、カテゴリ／トピック／グループ一覧を読み込む
    """
    # 管理者用の記事詳細を取得
    post = get_post_detail_admin(post_id)

    # カテゴリ・トピック・グループ情報を取得
    cats = load_categories()

    # 編集画面をレンダリング
    return templates.TemplateResponse(
        "admin/edit.html",
        {
            "request": request,
            "post": post,                     # 編集対象の記事
            "categories": cats["categories"], # カテゴリ一覧
            "topics": cats["topics"],         # トピック一覧
            "groups": cats["groups"],         # グループ一覧
        },
    )


@app.post("/admin/posts/{post_id}/edit")
async def update_post_admin(
    request: Request,
    post_id: int,
    admin=Depends(verify_admin),
):
    """
    記事編集内容を保存する処理（管理者専用）

    フォームデータを受け取り、記事情報を更新する
    """
    # フォーム送信データを取得
    form = await request.form()

    # 実際の更新処理は管理者用コントローラに委譲
    return post_admin.update_post(request, post_id, form)


@app.post("/admin/posts/{post_id}/delete")
def delete_post_admin(request: Request, post_id: int, admin=Depends(verify_admin)):
    """
    記事を削除する処理（管理者専用）
    """
    # 記事削除処理をコントローラに委譲
    return post_admin.delete_post(post_id)


@app.post("/admin/api/posts/{post_id}/status")
def api_update_post_status(
    post_id: int,
    payload: dict = Body(...),
    admin=Depends(verify_admin),
):
    """
    記事の公開ステータスを更新する API（管理者専用）

    public / private の切り替えを行う
    """
    # リクエストボディからステータスを取得
    status = payload.get("status")

    # 不正なステータス値はエラーとする
    if status not in ("public", "private"):
        return JSONResponse(
            {"message": "invalid status"},
            status_code=400
        )

    # ステータス更新処理（失敗しても例外は投げない）
    toggle_status(post_id, status)

    return JSONResponse({"ok": True})
