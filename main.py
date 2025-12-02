import os
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import FastAPI, Request, Form, Depends, Cookie
from fastapi import HTTPException
from markdown import markdown

from control.postControlPublic import load_posts, get_post
from control.postControlAdmin import add_post, update_post, delete_post

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


# ====================================
# 一般ユーザー
# ====================================

# 一覧
@app.get("/", response_class=HTMLResponse)
def public_list(request: Request):
    posts = load_posts()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "B.B. BlankBoard", "posts": posts}
    )


# 記事詳細
@app.get("/posts/{post_id}", response_class=HTMLResponse)
def read_post_public(request: Request, post_id: int):
    posts = load_posts()
    post = next((p for p in posts if p["id"] == post_id), None)
    if not post:
        return HTMLResponse("記事が見つかりませんでした。", status_code=404)

    post_html = markdown(post["content"], extensions=["fenced_code", "codehilite"])

    return templates.TemplateResponse(
        "post_detail_public.html",
        {"request": request, "post": post, "post_html": post_html}
    )


# 検索
@app.get("/search", response_class=HTMLResponse)
def search_posts(request: Request, q: str = ""):
    posts = load_posts()
    q_lower = q.lower()

    filtered = [p for p in posts if q_lower in p["title"].lower() or q_lower in p["content"].lower()]

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": f"検索結果: {q}", "posts": filtered, "search_query": q}
    )


# ====================================
# 管理者認証
# ====================================

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123"


# 🔐 共通認証チェック（※この1つでOK）
def verify_admin(request: Request):
    session = request.cookies.get("admin_session")
    if session != "valid":
        raise HTTPException(status_code=303, headers={"Location": "/admin/login"})


# ログイン画面
@app.get("/admin/login", response_class=HTMLResponse)
def admin_login_page(request: Request, error: str = None):
    return templates.TemplateResponse(
        "admin/login.html",
        {"request": request, "error": error}
    )


# ログイン処理
@app.post("/admin/login")
def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        response = RedirectResponse("/admin/posts", status_code=303)
        response.set_cookie("admin_session", "valid")
        return response

    return templates.TemplateResponse(
        "admin/login.html",
        {"request": request, "error": "ユーザーIDまたはパスワードが違います。"},
        status_code=400
    )


# ログアウト
@app.get("/admin/logout")
def admin_logout():
    response = RedirectResponse("/admin/login", status_code=303)
    response.delete_cookie("admin_session")
    return response


# ====================================
# 管理者用ページ
# ====================================

# 一覧
@app.get("/admin/posts", response_class=HTMLResponse)
def admin_list(request: Request, admin=Depends(verify_admin)):
    posts = load_posts()
    return templates.TemplateResponse(
        "admin/index.html",
        {"request": request, "title": "管理者記事一覧", "posts": posts}
    )


# 新規投稿ページ
@app.get("/admin/posts/new", response_class=HTMLResponse)
def new_post_form(request: Request, admin=Depends(verify_admin)):
    return templates.TemplateResponse(
        "admin/create.html",
        {"request": request}
    )


# 新規投稿処理
@app.post("/admin/posts/new")
def create_admin(request: Request, title: str = Form(...), content: str = Form(...), admin=Depends(verify_admin)):
    add_post(title, content)
    return RedirectResponse("/admin/posts", status_code=303)


# 管理者用記事詳細
@app.get("/admin/posts/{post_id}", response_class=HTMLResponse)
def read_post_admin(request: Request, post_id: int, admin=Depends(verify_admin)):
    posts = load_posts()
    post = next((p for p in posts if p["id"] == post_id), None)
    if not post:
        return HTMLResponse("記事が見たかりませんでした。", status_code=404)

    post_html = markdown(post["content"], extensions=["fenced_code", "codehilite"])

    return templates.TemplateResponse(
        "admin/post_detail_admin.html",
        {"request": request, "post": post, "post_html": post_html}
    )


# 編集画面
@app.get("/admin/posts/{post_id}/edit", response_class=HTMLResponse)
def edit_post_admin(request: Request, post_id: int, admin=Depends(verify_admin)):
    post = get_post(post_id)
    return templates.TemplateResponse(
        "admin/edit.html",
        {"request": request, "post": post}
    )


# 編集処理
@app.post("/admin/posts/{post_id}/edit")
def update_post_admin(request: Request, post_id: int, title: str = Form(...), content: str = Form(...),
                      admin=Depends(verify_admin)):
    update_post(post_id, title, content)
    return RedirectResponse(f"/admin/posts/{post_id}", status_code=303)


# 削除
@app.post("/admin/posts/{post_id}/delete")
def delete_post_admin(request: Request, post_id: int, admin=Depends(verify_admin)):
    delete_post(post_id)
    return RedirectResponse("/admin/posts", status_code=303)
