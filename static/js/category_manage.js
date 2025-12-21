// ===========================================
// カテゴリ管理（管理画面）
// ・カテゴリ / トピック / グループ管理画面用 JS
// ・カテゴリ列の操作を担当
// ===========================================


// -----------------------------
// 現在選択中のID・名称を保持
// ・右ペイン表示更新
// ・再読み込み後の状態復元用
// -----------------------------
let currentCategoryId = null;
let currentCategoryName = "";
let currentTopicId = null;
let currentTopicName = "";


// -----------------------------
// 初期化処理
// -----------------------------
document.addEventListener("DOMContentLoaded", () => {
  // カテゴリ一覧の各行にイベントを設定
  attachCategoryRowEvents();

  // カテゴリ新規追加ボタン
  document
    .getElementById("create-category-btn")
    .addEventListener("click", handleCreateCategory);

  // トピック新規追加ボタン
  document
    .getElementById("create-topic-btn")
    .addEventListener("click", handleCreateTopic);

  // グループ新規追加ボタン
  document
    .getElementById("create-group-btn")
    .addEventListener("click", handleCreateGroup);
});


// =====================================================
// カテゴリ列
// =====================================================

// カテゴリ一覧の各行にイベントを設定
function attachCategoryRowEvents() {

  // -----------------------------
  // カテゴリ名クリック
  // → 対応するトピック一覧を読み込む
  // -----------------------------
  document.querySelectorAll(".category-name").forEach((span) => {
    const id = Number(span.dataset.id);
    const name = span.textContent.trim();

    span.addEventListener("click", () => {
      loadTopics(id, name);
    });
  });

  // -----------------------------
  // 編集開始（カテゴリ）
  // ・表示用 span を非表示
  // ・input と保存／キャンセルボタンを表示
  // -----------------------------
  document.querySelectorAll(".edit-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.id;

      const nameSpan = document.querySelector(
        `.category-name[data-id="${id}"]`
      );
      const input = document.querySelector(
        `.category-edit[data-id="${id}"]`
      );
      const saveBtn = document.querySelector(
        `.save-btn[data-id="${id}"]`
      );
      const cancelBtn = document.querySelector(
        `.cancel-btn[data-id="${id}"]`
      );
      const deleteBtn = document.querySelector(
        `.delete-btn[data-id="${id}"]`
      );

      // 現在のカテゴリ名を input に反映
      input.value = nameSpan.textContent.trim();

      // 表示切り替え
      nameSpan.classList.add("hidden");
      btn.classList.add("hidden");
      deleteBtn.classList.add("hidden");
      input.classList.remove("hidden");
      saveBtn.classList.remove("hidden");
      cancelBtn.classList.remove("hidden");
    });
  });

  // -----------------------------
  // 編集キャンセル（カテゴリ）
  // -----------------------------
  document.querySelectorAll(".cancel-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.id;
      resetCategoryRow(id);
    });
  });

  // -----------------------------
  // 保存（カテゴリ更新）
  // -----------------------------
  document.querySelectorAll(".save-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.id;
      const input = document.querySelector(
        `.category-edit[data-id="${id}"]`
      );
      const name = input.value.trim();

      // 入力チェック
      if (!name) {
        alert("カテゴリ名を入力してください");
        return;
      }

      // API送信用 FormData
      const formData = new FormData();
      formData.append("category_id", id);
      formData.append("name", name);

      const res = await fetch("/admin/api/category_update", {
        method: "POST",
        body: formData,
      });

      // レスポンス解析（失敗時ログ保持）
      let data;
      let raw;
      try {
        raw = await res.text();
        data = JSON.parse(raw);
      } catch (e) {
        console.error("カテゴリ更新レスポンス解析エラー:", e, "raw=", raw);
        alert("カテゴリを更新できませんでした。");
        return;
      }

      // APIエラー判定
      if (!res.ok || data.status !== "ok") {
        const msg =
          data.message ||
          data.detail ||
          "カテゴリを更新できませんでした。";
        alert(msg);
        return;
      }

      // 表示更新
      document.querySelector(
        `.category-name[data-id="${id}"]`
      ).textContent = name;

      resetCategoryRow(id);

      // 現在選択中カテゴリなら表示ラベルも更新
      if (Number(id) === currentCategoryId) {
        currentCategoryName = name;
        const label = document.getElementById("current-category");
        label.textContent = `選択中カテゴリ：${name}`;
      }
    });
  });

  // -----------------------------
  // 削除（カテゴリ）
  // ・配下のトピック／グループも含め削除
  // -----------------------------
  document.querySelectorAll(".delete-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (
        !confirm(
          "このカテゴリと配下のトピック／グループを削除します。よろしいですか？"
        )
      ) {
        return;
      }

      const id = btn.dataset.id;
      const formData = new FormData();
      formData.append("category_id", id);

      let res, data, raw;
      try {
        res = await fetch("/admin/api/category_delete", {
          method: "POST",
          body: formData,
        });
        raw = await res.text();
        data = JSON.parse(raw);
      } catch (e) {
        console.error("カテゴリ削除レスポンス解析エラー:", e, "raw=", raw);
        alert("カテゴリを削除できませんでした。");
        return;
      }

      if (!res.ok || data.status !== "ok") {
        const msg =
          data.message ||
          data.detail ||
          "カテゴリを削除できませんでした。";
        alert(msg);
        return;
      }

      // 正常時は画面全体を再読み込み
      location.reload();
    });
  });
}


// -----------------------------
// カテゴリ行を通常表示に戻す
// -----------------------------
function resetCategoryRow(id) {
  const nameSpan = document.querySelector(
    `.category-name[data-id="${id}"]`
  );
  const input = document.querySelector(
    `.category-edit[data-id="${id}"]`
  );
  const saveBtn = document.querySelector(
    `.save-btn[data-id="${id}"]`
  );
  const cancelBtn = document.querySelector(
    `.cancel-btn[data-id="${id}"]`
  );
  const editBtn = document.querySelector(
    `.edit-btn[data-id="${id}"]`
  );
  const deleteBtn = document.querySelector(
    `.delete-btn[data-id="${id}"]`
  );

  input.classList.add("hidden");
  saveBtn.classList.add("hidden");
  cancelBtn.classList.add("hidden");

  nameSpan.classList.remove("hidden");
  editBtn.classList.remove("hidden");
  deleteBtn.classList.remove("hidden");
}


// -----------------------------
// カテゴリ新規追加
// -----------------------------
async function handleCreateCategory() {
  const input = document.getElementById("new-category");
  const name = input.value.trim();

  // 入力チェック
  if (!name) {
    alert("カテゴリ名は必須です");
    return;
  }

  const formData = new FormData();
  formData.append("category_name", name);
  formData.append("topic_name", "");
  formData.append("group_name", "");

  // API呼び出し
  await fetch("/admin/api/category_create", {
    method: "POST",
    body: formData,
  });

  // 追加後は画面全体を再読み込み
  location.reload();
}

// =====================================================
// トピック列
// ・カテゴリ配下のトピック管理
// ・一覧表示 / 編集 / 削除 / 追加
// =====================================================


// ---------------------------------
// カテゴリ選択時：トピック一覧を読み込む
// ---------------------------------
async function loadTopics(categoryId, categoryName) {
  // 選択中カテゴリ情報を保持
  currentCategoryId = Number(categoryId);
  currentCategoryName = categoryName;

  // トピックは未選択状態に戻す
  currentTopicId = null;
  currentTopicName = "";

  // 選択中カテゴリ表示を更新
  document.getElementById(
    "current-category"
  ).textContent = `選択中カテゴリ：${categoryName}`;

  // トピック追加エリアを表示
  document.getElementById("topic-create-area").classList.remove("hidden");

  // -----------------------------
  // トピック一覧取得
  // -----------------------------
  const res = await fetch(
    `/admin/api/topics?category_id=${categoryId}`
  );
  const topics = await res.json();

  // 表示初期化
  const topicList = document.getElementById("topic-list");
  topicList.innerHTML = "";
  document.getElementById("group-list").innerHTML = "";

  document.getElementById(
    "current-topic"
  ).textContent = "トピックを選択してください";

  // グループ追加エリアは非表示
  document.getElementById("group-create-area").classList.add("hidden");

  // -----------------------------
  // トピック行を生成
  // -----------------------------
  topics.forEach((t) => {
    const li = document.createElement("li");
    li.classList.add(
      "flex",
      "justify-between",
      "items-center",
      "bg-gray-100",
      "p-2",
      "rounded"
    );

    li.innerHTML = `
      <div class="flex-1">
        <span
          class="topic-name cursor-pointer"
          data-id="${t.id}"
          data-name="${t.name}"
        >
          ${t.name}
        </span>
        <input
          type="text"
          value="${t.name}"
          class="topic-edit hidden border rounded px-2 py-1 w-full"
          data-id="${t.id}"
        >
      </div>
      <div class="ml-4 flex items-center space-x-2 text-sm whitespace-nowrap">
        <button class="topic-edit-btn text-blue-500" data-id="${t.id}">編集</button>
        <button class="topic-save-btn hidden text-blue-500" data-id="${t.id}">保存</button>
        <button class="topic-cancel-btn hidden text-gray-500" data-id="${t.id}">キャンセル</button>
        <button class="topic-delete-btn text-red-500" data-id="${t.id}">削除</button>
      </div>
    `;
    topicList.appendChild(li);
  });

  // 行イベントを再設定
  attachTopicRowEvents();
}


// ---------------------------------
// トピック行のイベント設定
// ---------------------------------
function attachTopicRowEvents() {

  // トピック名クリック → グループ一覧読み込み
  document.querySelectorAll(".topic-name").forEach((span) => {
    const id = Number(span.dataset.id);
    const name = span.dataset.name || span.textContent.trim();

    span.addEventListener("click", () => {
      loadGroups(id, name);
    });
  });

  // -----------------------------
  // 編集開始（トピック）
  // -----------------------------
  document.querySelectorAll(".topic-edit-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.id;

      const nameSpan = document.querySelector(
        `.topic-name[data-id="${id}"]`
      );
      const input = document.querySelector(
        `.topic-edit[data-id="${id}"]`
      );
      const saveBtn = document.querySelector(
        `.topic-save-btn[data-id="${id}"]`
      );
      const cancelBtn = document.querySelector(
        `.topic-cancel-btn[data-id="${id}"]`
      );
      const deleteBtn = document.querySelector(
        `.topic-delete-btn[data-id="${id}"]`
      );

      // 現在の名前を input に反映
      input.value = nameSpan.textContent.trim();

      // 表示切り替え
      nameSpan.classList.add("hidden");
      btn.classList.add("hidden");
      deleteBtn.classList.add("hidden");
      input.classList.remove("hidden");
      saveBtn.classList.remove("hidden");
      cancelBtn.classList.remove("hidden");
    });
  });

  // -----------------------------
  // 編集キャンセル（トピック）
  // -----------------------------
  document.querySelectorAll(".topic-cancel-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      resetTopicRow(btn.dataset.id);
    });
  });

  // -----------------------------
  // 保存（トピック更新）
  // -----------------------------
  document.querySelectorAll(".topic-save-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.id;
      const input = document.querySelector(
        `.topic-edit[data-id="${id}"]`
      );
      const name = input.value.trim();

      if (!name) {
        alert("トピック名を入力してください");
        return;
      }

      const formData = new FormData();
      formData.append("topic_id", id);
      formData.append("name", name);

      const res = await fetch("/admin/api/topic_update", {
        method: "POST",
        body: formData,
      });

      let data, raw;
      try {
        raw = await res.text();
        data = JSON.parse(raw);
      } catch (e) {
        console.error("トピック更新レスポンス解析エラー:", e, "raw=", raw);
        alert("トピックを更新できませんでした。");
        return;
      }

      if (!res.ok || data.status !== "ok") {
        alert(data.message || data.detail || "トピックを更新できませんでした。");
        return;
      }

      // 表示更新
      document.querySelector(
        `.topic-name[data-id="${id}"]`
      ).textContent = name;

      resetTopicRow(id);

      // 選択中トピックなら表示も更新
      if (Number(id) === currentTopicId) {
        currentTopicName = name;
        document.getElementById(
          "current-topic"
        ).textContent = `選択中トピック：${name}`;
      }
    });
  });

  // -----------------------------
  // 削除（トピック）
  // -----------------------------
  document.querySelectorAll(".topic-delete-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!confirm("このトピックと配下グループを削除します。よろしいですか？")) {
        return;
      }

      const id = btn.dataset.id;
      const formData = new FormData();
      formData.append("topic_id", id);

      let res, data, raw;
      try {
        res = await fetch("/admin/api/topic_delete", {
          method: "POST",
          body: formData,
        });
        raw = await res.text();
        data = JSON.parse(raw);
      } catch (e) {
        console.error("トピック削除レスポンス解析エラー:", e, "raw=", raw);
        alert("トピックを削除できませんでした。");
        return;
      }

      if (!res.ok || data.status !== "ok") {
        alert(data.message || data.detail || "トピックを削除できませんでした。");
        return;
      }

      // 削除後はカテゴリ配下のトピック一覧を再読み込み
      if (currentCategoryId != null) {
        loadTopics(currentCategoryId, currentCategoryName);
      }
    });
  });
}


// ---------------------------------
// トピック行を通常表示に戻す
// ---------------------------------
function resetTopicRow(id) {
  const nameSpan = document.querySelector(
    `.topic-name[data-id="${id}"]`
  );
  const input = document.querySelector(
    `.topic-edit[data-id="${id}"]`
  );
  const saveBtn = document.querySelector(
    `.topic-save-btn[data-id="${id}"]`
  );
  const cancelBtn = document.querySelector(
    `.topic-cancel-btn[data-id="${id}"]`
  );
  const editBtn = document.querySelector(
    `.topic-edit-btn[data-id="${id}"]`
  );
  const deleteBtn = document.querySelector(
    `.topic-delete-btn[data-id="${id}"]`
  );

  input.classList.add("hidden");
  saveBtn.classList.add("hidden");
  cancelBtn.classList.add("hidden");

  nameSpan.classList.remove("hidden");
  editBtn.classList.remove("hidden");
  deleteBtn.classList.remove("hidden");
}


// ---------------------------------
// トピック新規追加
// ---------------------------------
async function handleCreateTopic() {
  if (currentCategoryId == null) {
    alert("先にカテゴリを選択してください");
    return;
  }

  const input = document.getElementById("new-topic");
  const name = input.value.trim();

  if (!name) {
    alert("トピック名を入力してください");
    return;
  }

  const formData = new FormData();
  formData.append("category_id", currentCategoryId);
  formData.append("name", name);

  const res = await fetch("/admin/api/topic_create", {
    method: "POST",
    body: formData,
  });
  const json = await res.json();

  if (json.status === "ok") {
    input.value = "";
    loadTopics(currentCategoryId, currentCategoryName);
  } else {
    alert(json.message || "トピックを追加できませんでした。");
  }
}


// =====================================================
// グループ列
// ・トピック配下のグループ管理
// =====================================================


// ---------------------------------
// トピック選択時：グループ一覧を読み込む
// ---------------------------------
async function loadGroups(topicId, topicName) {
  currentTopicId = Number(topicId);
  currentTopicName = topicName;

  document.getElementById(
    "current-topic"
  ).textContent = `選択中トピック：${topicName}`;

  document.getElementById("group-create-area").classList.remove("hidden");

  const res = await fetch(`/admin/api/groups?topic_id=${topicId}`);
  const groups = await res.json();

  const list = document.getElementById("group-list");
  list.innerHTML = "";

  groups.forEach((g) => {
    const li = document.createElement("li");
    li.classList.add(
      "flex",
      "justify-between",
      "items-center",
      "bg-gray-100",
      "p-2",
      "rounded"
    );

    li.innerHTML = `
      <div class="flex-1">
        <span
          class="group-name"
          data-id="${g.id}"
        >
          ${g.name}
        </span>
        <input
          type="text"
          value="${g.name}"
          class="group-edit hidden border rounded px-2 py-1 w-full"
          data-id="${g.id}"
        >
      </div>
      <div class="ml-4 flex items-center space-x-2 text-sm whitespace-nowrap">
        <button class="group-edit-btn text-blue-500" data-id="${g.id}">編集</button>
        <button class="group-save-btn hidden text-blue-500" data-id="${g.id}">保存</button>
        <button class="group-cancel-btn hidden text-gray-500" data-id="${g.id}">キャンセル</button>
        <button class="group-delete-btn text-red-500" data-id="${g.id}">削除</button>
      </div>
    `;
    list.appendChild(li);
  });

  attachGroupRowEvents();
}


// ---------------------------------
// グループ行のイベント設定
// ---------------------------------
function attachGroupRowEvents() {

  // 編集開始
  document.querySelectorAll(".group-edit-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.id;

      const nameSpan = document.querySelector(
        `.group-name[data-id="${id}"]`
      );
      const input = document.querySelector(
        `.group-edit[data-id="${id}"]`
      );
      const saveBtn = document.querySelector(
        `.group-save-btn[data-id="${id}"]`
      );
      const cancelBtn = document.querySelector(
        `.group-cancel-btn[data-id="${id}"]`
      );
      const deleteBtn = document.querySelector(
        `.group-delete-btn[data-id="${id}"]`
      );

      input.value = nameSpan.textContent.trim();

      nameSpan.classList.add("hidden");
      btn.classList.add("hidden");
      deleteBtn.classList.add("hidden");
      input.classList.remove("hidden");
      saveBtn.classList.remove("hidden");
      cancelBtn.classList.remove("hidden");
    });
  });

  // 編集キャンセル
  document.querySelectorAll(".group-cancel-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      resetGroupRow(btn.dataset.id);
    });
  });

  // 保存（グループ更新）
  document.querySelectorAll(".group-save-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.id;
      const input = document.querySelector(
        `.group-edit[data-id="${id}"]`
      );
      const name = input.value.trim();

      if (!name) {
        alert("グループ名を入力してください");
        return;
      }

      const formData = new FormData();
      formData.append("group_id", id);
      formData.append("name", name);

      const res = await fetch("/admin/api/group_update", {
        method: "POST",
        body: formData,
      });

      let data, raw;
      try {
        raw = await res.text();
        data = JSON.parse(raw);
      } catch (e) {
        console.error("グループ更新レスポンス解析エラー:", e, "raw=", raw);
        alert("グループを更新できませんでした。");
        return;
      }

      if (!res.ok || data.status !== "ok") {
        alert(data.message || data.detail || "グループを更新できませんでした。");
        return;
      }

      document.querySelector(
        `.group-name[data-id="${id}"]`
      ).textContent = name;

      resetGroupRow(id);
    });
  });

  // 削除（グループ）
  document.querySelectorAll(".group-delete-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!confirm("このグループを削除します。よろしいですか？")) return;

      const id = btn.dataset.id;
      const formData = new FormData();
      formData.append("group_id", id);

      let res, data, raw;
      try {
        res = await fetch("/admin/api/group_delete", {
          method: "POST",
          body: formData,
        });
        raw = await res.text();
        data = JSON.parse(raw);
      } catch (e) {
        console.error("グループ削除レスポンス解析エラー:", e, "raw=", raw);
        alert("グループを削除できませんでした。");
        return;
      }

      if (!res.ok || data.status !== "ok") {
        alert(data.message || data.detail || "グループを削除できませんでした。");
        return;
      }

      // 削除後は同トピック配下を再読み込み
      if (currentTopicId != null) {
        loadGroups(currentTopicId, currentTopicName);
      }
    });
  });
}


// ---------------------------------
// グループ行を通常表示に戻す
// ---------------------------------
function resetGroupRow(id) {
  const nameSpan = document.querySelector(
    `.group-name[data-id="${id}"]`
  );
  const input = document.querySelector(
    `.group-edit[data-id="${id}"]`
  );
  const saveBtn = document.querySelector(
    `.group-save-btn[data-id="${id}"]`
  );
  const cancelBtn = document.querySelector(
    `.group-cancel-btn[data-id="${id}"]`
  );
  const editBtn = document.querySelector(
    `.group-edit-btn[data-id="${id}"]`
  );
  const deleteBtn = document.querySelector(
    `.group-delete-btn[data-id="${id}"]`
  );

  input.classList.add("hidden");
  saveBtn.classList.add("hidden");
  cancelBtn.classList.add("hidden");

  nameSpan.classList.remove("hidden");
  editBtn.classList.remove("hidden");
  deleteBtn.classList.remove("hidden");
}


// ---------------------------------
// グループ新規追加
// ---------------------------------
async function handleCreateGroup() {
  if (currentTopicId == null) {
    alert("先にトピックを選択してください");
    return;
  }

  const input = document.getElementById("new-group");
  const name = input.value.trim();

  if (!name) {
    alert("グループ名を入力してください");
    return;
  }

  const formData = new FormData();
  formData.append("topic_id", currentTopicId);
  formData.append("name", name);

  const res = await fetch("/admin/api/group_create", {
    method: "POST",
    body: formData,
  });
  const json = await res.json();

  if (json.status === "ok") {
    input.value = "";
    loadGroups(currentTopicId, currentTopicName);
  } else {
    alert(json.message || "グループを追加できませんでした。");
  }
}
