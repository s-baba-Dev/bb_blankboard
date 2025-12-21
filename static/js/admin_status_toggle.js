// ===============================
// ステータス定数（Python 側と対応）
// ===============================
const STATUS_PUBLIC = 0;
const STATUS_PRIVATE = 1;

/**
 * トグルUIの見た目を現在のステータスに合わせて更新する
 *
 * @param {HTMLElement} toggleEl - .status-toggle 要素
 * @param {number|string} current - 現在のステータス（0 or 1）
 */
function applyActiveState(toggleEl, current) {
  // 数値として正規化（data属性は文字列のため）
  const currentStatus = Number(current);

  // 各ボタン（公開 / 非公開）を走査
  toggleEl.querySelectorAll(".status-btn").forEach((btn) => {
    // ボタンが表すステータスを数値に変換
    const btnStatus =
      btn.dataset.status === "public"
        ? STATUS_PUBLIC
        : STATUS_PRIVATE;

    // 現在のステータスと一致するボタンだけ is-active を付与
    btn.classList.toggle("is-active", btnStatus === currentStatus);
  });

  // 現在の状態をトグル要素自体に保持
  toggleEl.dataset.current = currentStatus;
}

/**
 * ステータス更新APIを呼び出す
 *
 * @param {number|string} postId - 投稿ID
 * @param {"public"|"private"} statusStr - 送信するステータス文字列
 */
async function updateStatus(postId, statusStr) {
  const res = await fetch(`/admin/api/posts/${postId}/status`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: statusStr }),
  });

  // HTTPエラー時は例外を投げる
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.message || "更新に失敗しました");
  }
}

// ===============================
// 初期化処理
// ===============================
document.addEventListener("DOMContentLoaded", () => {
  // ページ内のすべてのステータストグルを初期化
  document.querySelectorAll(".status-toggle").forEach((toggleEl) => {
    // 初期状態を反映
    applyActiveState(toggleEl, toggleEl.dataset.current);

    // 各ボタンにクリックイベントを登録
    toggleEl.querySelectorAll(".status-btn").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        e.preventDefault();
        e.stopPropagation();

        const postId = toggleEl.dataset.postId;

        // 次に設定されるステータス（数値）
        const nextStatus =
          btn.dataset.status === "public"
            ? STATUS_PUBLIC
            : STATUS_PRIVATE;

        // すでに同じ状態なら何もしない（冪等性）
        if (Number(toggleEl.dataset.current) === nextStatus) return;

        // 失敗時に戻すため現在の状態を保存
        const prev = toggleEl.dataset.current;

        // UIを先に更新（楽観的UI）
        applyActiveState(toggleEl, nextStatus);

        try {
          // APIへステータス更新リクエスト
          await updateStatus(
            postId,
            nextStatus === STATUS_PUBLIC ? "public" : "private"
          );
        } catch (err) {
          // 失敗したらUIを元に戻す
          applyActiveState(toggleEl, prev);
          alert(err.message);
        }
      });
    });
  });
});
