// ===========================================
// カテゴリ連動処理 (category → topic → group)
// create.html / edit.html 両方で使用可
// ===========================================

// create.html / edit.html に埋め込まれたデータを取得
// （Jinja2 などで window.categories 等として埋め込まれる前提）
const categories = window.categories || [];
const topics = window.topics || [];
const groups = window.groups || [];

// ==========================
// DOM 要素取得
// ==========================

// セレクトボックス（既存選択用）
const categorySelect = document.getElementById("category_select");
const topicSelect = document.getElementById("topic_select");
const groupSelect = document.getElementById("group_select");

// 新規入力用テキストボックス
const newCategoryInput = document.getElementById("new_category_input");
const newTopicInput = document.getElementById("new_topic_input");
const newGroupInput = document.getElementById("new_group_input");

// ラジオボタン（既存 / 新規 切り替え）
const categoryRadios = document.querySelectorAll("input[name='category_mode']");
const topicRadios = document.querySelectorAll("input[name='topic_mode']");
const groupRadios = document.querySelectorAll("input[name='group_mode']");


// ===========================================
// ラジオ切り替え：既存 / 新規
// ===========================================

/**
 * ラジオボタン切り替え時に
 * - 既存 → select 表示
 * - 新規 → input 表示
 * を制御する共通関数
 */
function setupRadioToggle(radioNodeList, selectEl, inputEl) {
    if (!radioNodeList) return;

    radioNodeList.forEach(r => {
        r.addEventListener("change", () => {
            const isNew = r.value === "new";

            // 新規選択時は select を隠して input を表示
            if (selectEl) selectEl.style.display = isNew ? "none" : "block";
            if (inputEl) inputEl.style.display = isNew ? "block" : "none";
        });
    });
}

// カテゴリ / トピック / グループの切替設定
setupRadioToggle(categoryRadios, categorySelect, newCategoryInput);
setupRadioToggle(topicRadios, topicSelect, newTopicInput);
setupRadioToggle(groupRadios, groupSelect, newGroupInput);


// ===========================================
// category → topic 連動
// ===========================================

/**
 * カテゴリ変更時に
 * - 選択されたカテゴリIDに紐づくトピックのみを表示
 */
function updateTopics() {
    if (!categorySelect || !topicSelect) return;

    // 現在選択されているカテゴリID
    const selectedCategory = parseInt(categorySelect.value);

    // 該当カテゴリに属するトピックだけ抽出
    const filteredTopics = topics.filter(t => t.category_id === selectedCategory);

    // トピックセレクトを初期化
    topicSelect.innerHTML = "";

    // 抽出したトピックを option として追加
    filteredTopics.forEach(t => {
        const opt = document.createElement("option");
        opt.value = t.id;
        opt.textContent = t.name;
        topicSelect.appendChild(opt);
    });

    // トピック変更に伴いグループも更新
    updateGroups();
}


// ===========================================
// topic → group 連動
// ===========================================

/**
 * トピック変更時に
 * - 選択されたトピックIDに紐づくグループのみを表示
 */
function updateGroups() {
    if (!topicSelect || !groupSelect) return;

    const selectedTopic = parseInt(topicSelect.value);

    // 該当トピックに属するグループのみ抽出
    const filteredGroups = groups.filter(g => g.topic_id === selectedTopic);

    // グループセレクトを初期化
    groupSelect.innerHTML = "";

    // option を再生成
    filteredGroups.forEach(g => {
        const opt = document.createElement("option");
        opt.value = g.id;
        opt.textContent = g.name;
        groupSelect.appendChild(opt);
    });
}


// ===========================================
// 初期設定（create/edit 両方対応）
// ===========================================

/**
 * 画面初期化処理
 *
 * - create：初期は先頭カテゴリを元に連動
 * - edit：既に選択値が入っている前提で再構築
 */
function initializeCategoryUI() {

    // category → topic → group を初期構築
    if (categorySelect) updateTopics();
    if (topicSelect) updateGroups();

    /**
     * 初期ラジオ状態に合わせて
     * input / select の表示状態を調整
     */
    function applyInitialRadioState(radioNodeList, selectEl, inputEl) {
        if (!radioNodeList) return;

        radioNodeList.forEach(r => {
            if (r.checked) {
                const isNew = r.value === "new";
                if (selectEl) selectEl.style.display = isNew ? "none" : "block";
                if (inputEl) inputEl.style.display = isNew ? "block" : "none";
            }
        });
    }

    applyInitialRadioState(categoryRadios, categorySelect, newCategoryInput);
    applyInitialRadioState(topicRadios, topicSelect, newTopicInput);
    applyInitialRadioState(groupRadios, groupSelect, newGroupInput);

    // 変更イベント登録
    if (categorySelect) categorySelect.addEventListener("change", updateTopics);
    if (topicSelect) topicSelect.addEventListener("change", updateGroups);
}


// 実行
initializeCategoryUI();
