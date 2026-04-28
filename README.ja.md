# カスタムレスポンスボット

Discord のメッセージを正規表現で判定し、一致した内容に応じて自動応答するBotです。

[English](./README.md)

## 概要

このBotは、`data/responses.json5` に定義したルールを上から順に評価します。最初に `trigger` が一致したルールの `response` を返します。

`response` には通常のテキストだけでなく、独自記法を混ぜられます。

- `img://...`: `http://...` の画像URLとしてDiscord Embed画像に変換します
- `imgs://...`: `https://...` の画像URLとしてDiscord Embed画像に変換します
- `func://...`: `function/` 配下のPython関数を実行します

`func://` が返した文字列にさらに `func://`、`img://`、`imgs://` が含まれている場合も再解析されます。再解析回数は `.env` の `RESPONSE_RENDER_RECURSION_LIMIT` で制限できます。

## 機能

- 正規表現トリガーに基づいた自動応答
- JSON5形式の設定ファイル
- Discord UIによるレスポンスの追加、閲覧、編集、削除
- Discord UIによる利用可能な `func://` 関数のブラウズ
- 画像URLのEmbed化
- Python関数による動的レスポンス
- 正規表現の名前付きグループを関数から利用可能
- `standard` と `preset` による再利用しやすい関数構成

## クイックスタート

### インストール

uvを使う場合:

```bash
uv sync
```

pipを使う場合:

```bash
pip install .
```

### `.env` の作成

ルートディレクトリに `.env` を作成します。

```env
DISCORD_TOKEN=your_bot_token_here
COMMAND_ENABLED=True
RESPONSE_RENDER_RECURSION_LIMIT=5
RESPONSE_RENDER_LIMIT_ERROR_MESSAGE=レスポンスの展開回数が上限に達しました。
FUNCTION_UNKNOWN_ERROR_MESSAGE=関数の実行に失敗しました。
```

### 最小のレスポンス設定

`data/responses.json5` を作成または編集します。

```json5
[
  {
    trigger: "こんにちは",
    response: "こんにちは！",
  },
  {
    trigger: "^ヘルプ$",
    response: "何かお困りですか？",
  }
]
```

### 起動

uvを使う場合:

```bash
uv run python main.py
```

手動でPython環境を管理している場合:

```bash
python main.py
```

## 基本

### ルール構造

レスポンスルールは次の形です。

```json5
{
  trigger: "正規表現",
  response: "返答内容",
}
```

- `trigger` はPythonの正規表現として扱われます
- `response` は通常テキスト、画像ディレクティブ、関数ディレクティブを含められます
- ルールは上から順に評価されます
- 最初に一致した1件だけが実行されます

ルール順は重要です。具体的なルールを上に、広く一致するルールを下に置くと扱いやすくなります。

### triggerの書き方

部分一致:

```json5
{ trigger: "hello", response: "Hello!" }
```

完全一致:

```json5
{ trigger: "^help$", response: "Help message" }
```

複数キーワード:

```json5
{ trigger: "hello|hi|こんにちは", response: "Hello!" }
```

メンションとキーワードの両方を含む場合:

```json5
{
  trigger: "(?=.*<@!?1234567890>)(?=.*(?:dice|ダイス|サイコロ))",
  response: "func://preset.mention.default_dice",
}
```

ロールメンションも含める場合:

```json5
{
  trigger: "(?=.*(?:<@!?1234567890>|<@&9876543210>))(?=.*(?:dice|ダイス|サイコロ))",
  response: "func://preset.mention.default_dice",
}
```

名前付きグループを使う場合:

```json5
{
  trigger: "(?=.*(?:サイコロ|ダイス|dice))(?=.*?(?P<dice>\\d+d\\d+))",
  response: "func://preset.mention.dynamic_dice",
}
```

この例では `サイコロ10d10` の `10d10` が `ctx.group("dice")` で参照できます。

### responseの書き方

通常テキスト:

```json5
{
  trigger: "ありがとう",
  response: "どういたしまして！",
}
```

画像とテキストの混在:

```json5
{
  trigger: "猫",
  response: "猫です imgs://example.com/cat.png",
}
```

関数呼び出し:

```json5
{
  trigger: "乱数",
  response: "1から100: func://standard.random.randint?min=1&max=100",
}
```

## 画像ディレクティブ

画像URLは次のように書きます。

```json5
{
  trigger: "画像",
  response: "画像はこちら imgs://example.com/image.png",
}
```

- `img://example.com/a.png` は `http://example.com/a.png` として扱われます
- `imgs://example.com/a.png` は `https://example.com/a.png` として扱われます
- 画像はDiscord Embed画像として送信されます
- 同じ `response` に複数の画像を含められます
- 画像表示にはDiscordの `埋め込みリンク` 権限が必要です

## 関数ディレクティブ

`func://` は `function/` 配下のPython関数を実行します。

```text
func://standard.random.randint?min=1&max=6
```

この例では、`function/standard/random.py` の `randint(ctx, *, min, max)` を呼び出します。

### 引数

`func://` は位置引数を使いません。クエリ文字列のキーワード引数だけを使います。

```text
func://standard.text.repeat?text=%22hello%22&count=3&separator=%22%20%22
```

クエリ値はURLエンコードされたPythonリテラルです。

- `min=1`: 数値
- `text=%22hello%20world%22`: 文字列 `"hello world"`
- `items=%5B%22A%22%2C%22B%22%5D`: リスト `["A", "B"]`
- 同じ引数名を複数回書くとエラーになります

文字列はクォートごとURLエンコードしてください。`hello` ではなく `%22hello%22` のように書きます。

### standardとpreset

`function/standard` は再利用しやすい標準関数パッケージです。単機能の部品として使います。

```text
func://standard.random.roll?dice=%222d6%22
```

`function/preset` は実運用向けに `func://` を組み立てる合成用パッケージです。利用者はまず `preset` を探し、足りない場合に `standard` を直接使うのがおすすめです。

```text
func://preset.mention.default_dice
```

この関数は `func://standard.random.roll?dice=%222d6%22` を返します。返された `func://` は再解析され、最終的にダイスが振られます。

### 再解析

関数はテキストだけでなく、別のディレクティブを返せます。

```python
def default_dice(ctx):
    return "func://standard.random.roll?dice=%222d6%22"
```

```python
def image(ctx):
    return "imgs://placehold.co/400x200.png?text=Hello"
```

このように、関数から `func://` や `imgs://` を返すことで処理を組み合わせられます。

無限ループを防ぐため、再解析回数は `.env` で制限します。

```env
RESPONSE_RENDER_RECURSION_LIMIT=5
```

上限に達すると `RESPONSE_RENDER_LIMIT_ERROR_MESSAGE` が表示されます。

## 利用者チュートリアル

このセクションは、Discord上でルールを追加・確認・編集する人向けです。

### 1. レスポンスを追加する

`/add_response` を実行します。Modalが開くので、`Trigger` と `Response` を入力します。

例:

```text
Trigger:
こんにちは

Response:
こんにちは！
```

追加後は `Response Added` の詳細画面が表示されます。`Copy` を押すと、`trigger` と `response` がプレーンテキストで表示されます。

### 2. レスポンス一覧を見る

`/list_responses` を実行します。

- Selectでレスポンスを選択できます
- `Prev` / `Next` でページ移動できます
- フィルタで `func://` や画像を使っているレスポンスを絞り込めます

### 3. レスポンスを編集する

`/list_responses` でレスポンスを選択し、詳細画面の `Edit` を押します。`/add_response` と同じ形式のModalが開きます。

更新後は `Response Updated` の詳細画面に留まります。

### 4. レスポンスを削除する

`/list_responses` でレスポンスを選択し、`Delete` を押します。

削除確認画面が出るので、問題なければ `Confirm Delete` を押します。削除後は後続のIDが詰まります。

### 5. 利用可能な関数を探す

`/list_functions` を実行します。

- `function/` 配下をツリー形式で閲覧できます
- パンくずで現在位置を確認できます
- 関数詳細でシグネチャとdocstringを確認できます
- 詳細画面の `Copy` で、そのまま使える `func://...` をプレーンテキスト表示できます

## 運用者チュートリアル

このセクションは、Botのレスポンス設計や関数追加を行う人向けです。

### 1. 固定テキスト応答

```json5
{
  trigger: "^こんにちは$",
  response: "こんにちは！",
}
```

`^` と `$` を使うと完全一致になります。

### 2. 画像応答

```json5
{
  trigger: "猫",
  response: "猫画像です imgs://example.com/cat.png",
}
```

`imgs://` は `https://` に変換され、Embed画像として送信されます。

### 3. 標準関数を直接呼ぶ

```json5
{
  trigger: "乱数",
  response: "今日の数字: func://standard.random.randint?min=1&max=100",
}
```

`standard` は単機能の関数を直接呼びたいときに使います。

### 4. presetで応答を組み立てる

```json5
{
  trigger: "サイコロ",
  response: "func://preset.mention.default_dice",
}
```

`preset.mention.default_dice` は `func://standard.random.roll?dice=%222d6%22` を返します。返された `func://` は再解析されます。

このように、`preset` は利用者向けの短い入口として使えます。

### 5. メッセージ内容で応答を変える

`サイコロ10d10` のような入力に応じて結果を変えたい場合は、名前付きグループを使います。

```json5
{
  trigger: "(?=.*(?:サイコロ|ダイス|dice))(?=.*?(?P<dice>\\d+d\\d+))",
  response: "func://preset.mention.dynamic_dice",
}
```

`preset.mention.dynamic_dice` は `func://standard.random.roll_from_match` を返します。`standard.random.roll_from_match` は `ctx.group("dice")` を読み、`10d10` などの値でダイスを振ります。

### 6. 関数から画像を返す

関数は画像ディレクティブを返せます。

```python
def banner(ctx):
    return "imgs://placehold.co/600x240.png?text=Hello"
```

この場合、関数の戻り値が再解析されて画像Embedになります。

### 7. 関数から別の関数を呼ぶ

関数は `func://` を返すこともできます。

```python
def today_roll(ctx):
    return "func://standard.random.roll?dice=%221d20%22"
```

複雑な応答を小さな標準関数に分け、`preset` 側で組み立てると再利用しやすくなります。

### 8. 自作関数を追加する

`function/standard` または `function/preset` にPythonファイルを追加します。

```python
from cr_bot.function_context import FunctionContext


def hello(ctx: FunctionContext, *, name: str) -> str:
    """Return a greeting.

    Sample:
        func://standard.greeting.hello?name=%22Alice%22
    """
    return f"Hello, {name}!"
```

関数の第1引数は `ctx` にしてください。`ctx` からメッセージ、ユーザー、チャンネル、サーバー、正規表現の一致結果を参照できます。

### 9. ユーザー向けエラーを返す

関数内でユーザーに見せたいエラーがある場合は `FunctionDirectiveError` を送出します。

```python
from cr_bot.function_errors import FunctionDirectiveError


def positive(ctx, *, value: int) -> str:
    if value < 0:
        raise FunctionDirectiveError("value は0以上で指定してください。")
    return str(value)
```

想定外の例外はログに記録され、ユーザーには `.env` の `FUNCTION_UNKNOWN_ERROR_MESSAGE` が表示されます。

## コマンドUIガイド

### `/add_response`

Modalで `Trigger` と `Response` を入力してルールを追加します。追加後は詳細画面が表示されます。

### `/list_responses`

レスポンスを閲覧・管理するUIです。

- フィルタ: `All`、`Uses func://`、`Uses img://`、`Uses preset`、`Uses standard`、`Plain text`
- `Copy`: `trigger` と `response` をラベル付きプレーンテキストで表示
- `Edit`: Modalで更新
- `Delete`: 確認画面付きで削除
- `Back to List`: 一覧へ戻る
- `Close`: UIを閉じる

### `/list_functions`

利用可能な関数を閲覧するUIです。

- `function/` 配下をネストしたまま表示します
- Selectでフォルダ、モジュール、関数へ移動できます
- `Back` / `Root` で戻れます
- 関数詳細の `Copy` で `func://...` をプレーンテキスト表示できます

## 必要な権限

- 通常の応答送信には `メッセージを送信` 権限が必要です
- `img://...` / `imgs://...` による画像埋め込みには `埋め込みリンク` 権限が必要です
- `func://` の戻り値が画像Embedを生成する場合も `埋め込みリンク` 権限が必要です
- スラッシュコマンドを使う場合は、Bot招待時に `applications.commands` スコープも付与してください

テストサーバーで動いて本番サーバーで画像埋め込みだけ動かない場合は、対象チャンネルまたはロールで `埋め込みリンク` 権限が無効になっていないか確認してください。

## トラブルシュート

### 反応しない

- `trigger` の正規表現がメッセージに一致しているか確認してください
- 先に別のルールが一致していないか確認してください
- `message_content` Intentが有効か確認してください

### 期待したルールではないものが反応する

ルールは上から順に評価され、最初に一致した1件だけが実行されます。具体的なルールを上に移動してください。

### 画像が表示されない

- Botに `埋め込みリンク` 権限があるか確認してください
- URLが画像としてDiscordから取得できるか確認してください
- `img://` と `imgs://` の使い分けを確認してください

### funcが動かない

- `/list_functions` で関数が表示されるか確認してください
- 関数名が `func://standard.random.randint` のように正しいか確認してください
- 引数値がURLエンコードされたPythonリテラルになっているか確認してください

### URLエンコードが難しい

文字列はクォートごとエンコードします。

```text
"hello world" -> %22hello%20world%22
```

### 再解析上限に達する

関数が別の `func://` を返し続けると上限に達します。`.env` の `RESPONSE_RENDER_RECURSION_LIMIT` を確認してください。

## セキュリティメモ

`func://` はBotが読み込めるPython関数を実行する機能です。信頼できるサーバーや信頼できるユーザーの範囲で運用してください。権限制御は今後追加予定です。

## TODO

- [ ] 権限管理
- [ ] レスポンスの並び替え
- [ ] その他の標準function追加
