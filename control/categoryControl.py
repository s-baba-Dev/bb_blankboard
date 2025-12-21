from util.dataLoader import load_categories, save_categories


class CategoryControl:
    """
    カテゴリ／トピック／グループの取得・新規作成を担当する制御クラス

    既存IDの利用と新規作成の分岐を共通化し、
    投稿作成時のカテゴリ関連処理を簡潔にする目的で使用される
    """

    def add_or_get_category(self, mode, category_id, new_name):
        """
        カテゴリIDを取得または新規作成する

        :param mode: "existing" または "new"
        :param category_id: 既存カテゴリID
        :param new_name: 新規カテゴリ名
        :return: カテゴリID
        """
        # カテゴリ関連データを読み込む
        cats = load_categories()

        # 既存カテゴリを使用する場合はそのままIDを返す
        if mode == "existing":
            return category_id

        # 新規カテゴリ作成処理
        new_name_lower = new_name.lower()

        # カテゴリ名の重複チェック（大文字小文字を区別しない）
        if any(c["name"].lower() == new_name_lower for c in cats["categories"]):
            raise ValueError("カテゴリ名が重複しています")

        # 新しいカテゴリIDを採番
        new_id = max([c["id"] for c in cats["categories"]], default=0) + 1

        # カテゴリを追加
        cats["categories"].append({
            "id": new_id,
            "name": new_name
        })

        # 更新内容を保存
        save_categories(cats)

        return new_id


    def add_or_get_topic(self, mode, topic_id, new_name, category_id):
        """
        トピックIDを取得または新規作成する

        :param mode: "existing" または "new"
        :param topic_id: 既存トピックID
        :param new_name: 新規トピック名
        :param category_id: 紐づけるカテゴリID
        :return: トピックID
        """
        # カテゴリ関連データを読み込む
        cats = load_categories()

        # 既存トピックを使用する場合はそのままIDを返す
        if mode == "existing":
            return topic_id

        # 新規トピック作成処理
        new_name_lower = new_name.lower()

        # トピック名の重複チェック
        if any(t["name"].lower() == new_name_lower for t in cats["topics"]):
            raise ValueError("トピック名が重複しています")

        # 新しいトピックIDを採番
        new_id = max([t["id"] for t in cats["topics"]], default=0) + 1

        # トピックを追加
        cats["topics"].append({
            "id": new_id,
            "name": new_name,
            "category_id": category_id
        })

        # 更新内容を保存
        save_categories(cats)

        return new_id


    def add_or_get_group(self, mode, group_id, new_name, topic_id):
        """
        グループIDを取得または新規作成する

        :param mode: "existing" または "new"
        :param group_id: 既存グループID
        :param new_name: 新規グループ名
        :param topic_id: 紐づけるトピックID
        :return: グループID
        """
        # カテゴリ関連データを読み込む
        cats = load_categories()

        # 既存グループを使用する場合はそのままIDを返す
        if mode == "existing":
            return group_id

        # 新規グループ作成処理
        new_name_lower = new_name.lower()

        # グループ名の重複チェック
        if any(g["name"].lower() == new_name_lower for g in cats["groups"]):
            raise ValueError("グループ名が重複しています")

        # 新しいグループIDを採番
        new_id = max([g["id"] for g in cats["groups"]], default=0) + 1

        # グループを追加
        cats["groups"].append({
            "id": new_id,
            "name": new_name,
            "topic_id": topic_id
        })

        # 更新内容を保存
        save_categories(cats)

        return new_id
