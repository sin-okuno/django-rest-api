# 製品構成管理画面 仕様書

本仕様書は、製品構成（ツリー）と製品詳細を編集する画面を定義する。
コード生成基盤の入力として使用する。

## 画面概要

| 項目 | 値 |
| --- | --- |
| 画面ID | product-structure |
| 画面名 | 製品構成管理画面 |
| ルート | product-structure |
| ページタイプ | tree-detail |
| 機能名 | product-structure |

## 権限制御

| 権限コード | 用途 |
| --- | --- |
| PRODUCT_VIEW | 画面表示、ツリー参照、詳細参照 |
| PRODUCT_UPDATE | 詳細編集、Save、Cancel |

## 画面操作

| 操作ID | 操作名 | 説明 | 必要権限 |
| --- | --- | --- | --- |
| enterPage | Enter Page | 画面初期表示 | PRODUCT_VIEW |
| search | Search | 検索条件でツリーを取得 | PRODUCT_VIEW |
| clear | Clear | 検索条件をクリア | PRODUCT_VIEW |
| selectNode | Select Node | ツリーノードを選択 | PRODUCT_VIEW |
| toggleNode | Toggle Node | ノードの展開・折りたたみ | PRODUCT_VIEW |
| save | Save Product | 製品詳細を保存 | PRODUCT_UPDATE |
| cancel | Cancel Edit | 編集内容を破棄 | PRODUCT_UPDATE |
| reloadDetail | Reload Detail | 最新の製品詳細を再取得 | PRODUCT_VIEW |

## 検索条件

| 項目 | 値 |
| --- | --- |
| 条件型 | ProductStructureApiRequest |

| フィールド | ラベル | 型 | 必須 |
| --- | --- | --- | --- |
| keyword | キーワード | string | false |
| categoryId | カテゴリID | string \| null | false |

## 製品構成ツリー

| 項目 | 値 |
| --- | --- |
| ノード型 | ProductTreeNode |
| IDフィールド | productId |
| 詳細IDフィールド | productId |
| 表示フィールド | productName<br>productCode |

| ルールID | 内容 |
| --- | --- |
| tree-rule-1 | 子ノードは親ノードの配下に表示する |
| tree-rule-2 | 選択中のノードを強調表示する |

## 製品詳細項目

| 項目 | 値 |
| --- | --- |
| モデル型 | ProductDetail |
| フォーム状態管理 | local |

| フィールド | ラベル | 型 | 必須 | 編集可 |
| --- | --- | --- | --- | --- |
| productName | 製品名 | string | true | true |
| productCode | 製品コード | string | true | false |
| price | 価格 | number | true | true |
| description | 説明 | string \| null | false | true |
| revision | リビジョン | number | true | false |

## API一覧

| API ID | API名 | メソッド | パス | リクエスト型 | レスポンス型 | 説明 |
| --- | --- | --- | --- | --- | --- | --- |
| loadTree | 構成ツリー取得 | GET | /api/products/tree | ProductStructureApiRequest | ProductTreeResponseDto | 検索条件でツリーを取得する |
| loadDetail | 製品詳細取得 | GET | /api/products/{productId} | - | ProductDetailApiResponse | 製品詳細を取得する |
| updateDetail | 製品詳細更新 | PUT | /api/products/{productId} | ProductUpdateApiRequest | ProductDetailApiResponse | 製品詳細を更新する |

## Store構成

| 項目 | 値 |
| --- | --- |
| フィーチャーキー | productStructure |

| フィールド | 型 | 初期値 | 説明 |
| --- | --- | --- | --- |
| treeNodes | ProductTreeNode[] | [] | 構成ツリー |
| selectedNodeId | string \| null | null | 選択中のノードID |
| detail | ProductDetail \| null | null | 選択中の製品詳細 |
| loading | boolean | false | ローディング状態 |
| saving | boolean | false | 保存処理中 |
| error | ApiError \| null | null | APIエラー |
| concurrentUpdate | boolean | false | 同時更新の発生状態 |
| permissions | string[] | [] | 保有権限コード |
| pendingOperation | PendingOperation \| null | null | 確認待ちの保留操作 |

## 型定義

| カテゴリー | 型名 | プロパティ | 型 | 任意 | 最大桁数 | 小数桁 | 説明 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| api | ProductStructureApiRequest | keyword | string | false | 100 | - | 検索キーワード |
| api | ProductStructureApiRequest | categoryId | string \| null | false | 50 | - | カテゴリID |
| api | ProductTreeResponseDto | nodes | ProductTreeNodeDto[] | false | - | - | ツリーノード一覧 |
| api | ProductTreeNodeDto | productId | string | false | 50 | - | 製品ID |
| api | ProductTreeNodeDto | productName | string | false | 100 | - | 製品名 |
| api | ProductTreeNodeDto | productCode | string | false | 30 | - | 製品コード |
| api | ProductTreeNodeDto | parentId | string \| null | false | 50 | - | 親製品ID |
| api | ProductTreeNodeDto | children | ProductTreeNodeDto[] | false | - | - | 子ノード |
| api | ProductDetailApiResponse | productId | string | false | 50 | - | 製品ID |
| api | ProductDetailApiResponse | productName | string | false | 100 | - | 製品名 |
| api | ProductDetailApiResponse | productCode | string | false | 30 | - | 製品コード |
| api | ProductDetailApiResponse | price | number | false | 12 | 2 | 価格 |
| api | ProductDetailApiResponse | description | string \| null | false | 500 | - | 説明 |
| api | ProductDetailApiResponse | revision | number | false | 10 | 0 | リビジョン |
| api | ProductUpdateApiRequest | productName | string | false | 100 | - | 製品名 |
| api | ProductUpdateApiRequest | price | number | false | 12 | 2 | 価格 |
| api | ProductUpdateApiRequest | description | string \| null | false | 500 | - | 説明 |
| api | ProductUpdateApiRequest | revision | number | false | 10 | 0 | リビジョン |
| view | ProductTreeNode | productId | string | false | 50 | - | 製品ID |
| view | ProductTreeNode | productName | string | false | 100 | - | 製品名 |
| view | ProductTreeNode | productCode | string | false | 30 | - | 製品コード |
| view | ProductTreeNode | parentId | string \| null | false | 50 | - | 親製品ID |
| view | ProductTreeNode | children | ProductTreeNode[] | false | - | - | 子ノード |
| view | ProductDetail | productId | string | false | 50 | - | 製品ID |
| view | ProductDetail | productName | string | false | 100 | - | 製品名 |
| view | ProductDetail | productCode | string | false | 30 | - | 製品コード |
| view | ProductDetail | price | number | false | 12 | 2 | 価格 |
| view | ProductDetail | description | string \| null | false | 500 | - | 説明 |
| view | ProductDetail | revision | number | false | 10 | 0 | リビジョン |
| view | ApiError | code | string | false | 50 | - | エラーコード |
| view | ApiError | message | string | false | 200 | - | エラーメッセージ |
| view | PendingOperation | operationId | string | false | 50 | - | 保留中の操作ID |
| view | PendingOperation | payload | string \| null | true | 500 | - | 保留中の操作ペイロード |
| action | LoadTreePayload | keyword | string | false | 100 | - | 検索キーワード |
| action | LoadTreePayload | categoryId | string \| null | false | 50 | - | カテゴリID |
| action | LoadTreeSuccessPayload | nodes | ProductTreeNode[] | false | - | - | 取得したツリー |
| action | SelectNodePayload | productId | string | false | 50 | - | 選択した製品ID |
| action | LoadDetailPayload | productId | string | false | 50 | - | 取得する製品ID |
| action | LoadDetailSuccessPayload | detail | ProductDetail | false | - | - | 取得した製品詳細 |
| action | SaveProductPayload | productId | string | false | 50 | - | 製品ID |
| action | SaveProductPayload | productName | string | false | 100 | - | 製品名 |
| action | SaveProductPayload | price | number | false | 12 | 2 | 価格 |
| action | SaveProductPayload | description | string \| null | false | 500 | - | 説明 |
| action | SaveProductPayload | revision | number | false | 10 | 0 | リビジョン |
| action | SaveProductSuccessPayload | detail | ProductDetail | false | - | - | 保存後の製品詳細 |
| action | ReloadDetailPayload | productId | string | false | 50 | - | 再取得する製品ID |
| action | LoadPermissionsSuccessPayload | permissions | string[] | false | - | - | 取得した権限コード |
| action | SetPendingOperationPayload | pending | PendingOperation | false | - | - | 保留操作 |
| action | ApiErrorPayload | error | ApiError | false | - | - | APIエラー |

## Action一覧・Store更新内容

| アクションID | アクション名 | カテゴリー | ペイロード型 | API | 成功アクション | 失敗アクション | 関連操作 | Store更新内容 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| enterPage | Enter Page | page | - | - | - | - | enterPage | loading=true<br>error=null |
| loadPermissions | Load Permissions | permission | - | - | loadPermissionsSuccess | loadPermissionsFailure | enterPage | - |
| loadPermissionsSuccess | Load Permissions Success | permission | LoadPermissionsSuccessPayload | - | - | - | - | permissions=action.permissions |
| loadPermissionsFailure | Load Permissions Failure | permission | ApiErrorPayload | - | - | - | - | error=action.error |
| loadTree | Load Tree | tree | LoadTreePayload | loadTree | loadTreeSuccess | loadTreeFailure | search | loading=true<br>error=null |
| loadTreeSuccess | Load Tree Success | tree | LoadTreeSuccessPayload | - | - | - | - | treeNodes=action.nodes<br>loading=false |
| loadTreeFailure | Load Tree Failure | tree | ApiErrorPayload | - | - | - | - | error=action.error<br>loading=false |
| clearSearch | Clear Search | search | - | - | - | - | clear | selectedNodeId=null<br>detail=null |
| selectNode | Select Node | tree | SelectNodePayload | - | - | - | selectNode | selectedNodeId=action.productId |
| loadDetail | Load Detail | detail | LoadDetailPayload | loadDetail | loadDetailSuccess | loadDetailFailure | selectNode | loading=true<br>error=null |
| loadDetailSuccess | Load Detail Success | detail | LoadDetailSuccessPayload | - | - | - | - | detail=action.detail<br>loading=false<br>concurrentUpdate=false |
| loadDetailFailure | Load Detail Failure | detail | ApiErrorPayload | - | - | - | - | error=action.error<br>loading=false |
| saveProduct | Save Product | detail | SaveProductPayload | updateDetail | saveProductSuccess | saveProductFailure | save | saving=true<br>error=null |
| saveProductSuccess | Save Product Success | detail | SaveProductSuccessPayload | - | - | - | - | detail=action.detail<br>saving=false<br>concurrentUpdate=false |
| saveProductFailure | Save Product Failure | detail | ApiErrorPayload | - | - | - | - | error=action.error<br>saving=false |
| concurrentUpdateDetected | Concurrent Update Detected | detail | ApiErrorPayload | - | - | - | save | concurrentUpdate=true<br>saving=false<br>error=action.error |
| reloadDetail | Reload Detail | detail | ReloadDetailPayload | loadDetail | reloadDetailSuccess | loadDetailFailure | reloadDetail | loading=true |
| reloadDetailSuccess | Reload Detail Success | detail | LoadDetailSuccessPayload | - | - | - | - | detail=action.detail<br>loading=false<br>concurrentUpdate=false |
| cancelEdit | Cancel Edit | detail | - | - | - | - | cancel | - |
| setPendingOperation | Set Pending Operation | unsaved | SetPendingOperationPayload | - | - | - | - | pendingOperation=action.pending |
| clearPendingOperation | Clear Pending Operation | unsaved | - | - | - | - | - | pendingOperation=null |

## 未保存変更

| 項目 | 値 |
| --- | --- |
| 有効 | true |
| 判定元 | form.dirty |
| 確認メッセージ | 編集内容が保存されていません。変更を破棄してよろしいですか？ |

| 対象操作 |
| --- |
| selectNode |
| search |
| clear |
| cancel |

## 同時更新

| 項目 | 値 |
| --- | --- |
| 有効 | true |
| リビジョン項目 | revision |
| ステータスコード | 409 |
| エラーコード | CONCURRENT_UPDATE |
| メッセージ | 他の利用者によって製品情報が更新されています。最新情報を再取得してください。 |

## 表示ルール

| ルールID | 条件 | 挙動 |
| --- | --- | --- |
| rule-empty | treeNodes が 0 件 | 0件メッセージを表示する |
| rule-loading | loading が true | ローディング表示にする |
| rule-error | error が存在する | エラーメッセージを表示する |
| rule-readonly | PRODUCT_UPDATE を持たない | フォームを読み取り専用にする |
| rule-concurrent | concurrentUpdate が true | 同時更新エラーと再取得ボタンを表示する |

## 入力チェック

| フィールド | ルール | メッセージ |
| --- | --- | --- |
| productName | required | 製品名は必須です |
| price | required | 価格は必須です |
| price | min:0 | 価格は0以上で入力してください |

## 主なテスト観点

| テストID | 対象 | 内容 |
| --- | --- | --- |
| test-enter | component | enterPage で権限とツリーを取得する |
| test-search | effects | search でツリーを再取得する |
| test-save | effects | save で更新APIを呼び出す |
| test-concurrent | reducer | concurrentUpdateDetected で同時更新状態にする |
| test-readonly | selectors | PRODUCT_UPDATE が無い場合に編集不可と判定する |
| test-unsaved | guard | dirty 時に画面離脱で確認する |
