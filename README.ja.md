# カスタムレスポンスボット

正規表現パターンマッチングに基づいてメッセージに自動的に応答する Discord ボット。

[English](./README.md)

## 機能

- 正規表現トリガーに基づいた自動応答
- JSON5形式の簡単な設定
- Discordコマンドまたは直接編集で応答を追加・削除
- 埋め込みメッセージでトリガー一覧を表示
- 正規表現対応の柔軟なパターンマッチング

## クイックスタート

### インストール

```bash
pip install -r requirements.txt
```

uvの場合は

```bash
uv sync
```

### 設定

1. ルートディレクトリに `.env` ファイルを作成

```env
DISCORD_TOKEN=your_bot_token_here
```

2. `data/responses.json5` を編集してトリガーを追加

```json5
[
  {
    trigger: "こんにちは",
    response: "こんにちは！何かお手伝いできることはありますか？",
  },
  {
    trigger: "^ヘルプ$",
    response: "何かお困りですか？",
  }
]
```

`response` では通常のテキストに加えて、独自記法で画像を埋め込めます。

```json5
[
  {
    trigger: "猫",
    response: "猫画像はこちら imgs://example.com/cat.png",
  },
  {
    trigger: "2枚",
    response: "imgs://example.com/a.png imgs://example.com/b.png",
  }
]
```

- `img://...` は `http://...` の画像URLとして扱います
- `imgs://...` は `https://...` の画像URLとして扱います
- 画像URLはDiscordのEmbed画像として送信されます
- 通常テキストと文中で混在できます
- 同じ `response` に複数の画像を含められます

`func://...` で `function` フォルダ配下のカスタム関数も実行できます。

- `function/standard` は再利用前提の標準関数パッケージです
- `function/preset` は `func://...` を組み立てて標準関数を呼ぶ合成用パッケージです

```json5
[
  {
    trigger: "dice",
    response: "1d6: func://standard.random.randint?min=1&max=6",
  },
  {
    trigger: "placeholder",
    response: "func://standard.image.placeholder?width=600&height=400&text=%22Hello%22",
  },
  {
    trigger: "preset dice",
    response: "func://preset.mention.default_dice",
  }
]
```

- `func://standard.random.randint?min=1&max=6` は `function/standard/random.py` の `randint(ctx, *, min, max)` を呼び出します
- `func://preset.mention.default_dice` は `function/preset/mention.py` で `func://standard.random.roll?...` を組み立てて返します
- 位置引数は使わず、クエリ文字列のキーワード引数だけを使います
- クエリ値はURLエンコードされたPythonリテラルとして指定します
- 文字列は `text=%22hello%20world%22` のようにクォートごとURLエンコードしてください
- 同じ引数名を複数回指定するとエラーになります
- `def` と `async def` の両方に対応しています
- 関数には `ctx` としてBot、メッセージ、ユーザー、チャンネル、サーバー情報が渡されます
- 正規表現の一致結果は `ctx.trigger_match`、`ctx.group()`、`ctx.groupdict()` から参照できます
- 関数が返した `func://...`、`img://...`、`imgs://...` も再解析されます
- 再解析回数は `.env` の `RESPONSE_RENDER_RECURSION_LIMIT` で制限できます

動的な例として、トリガーで名前付きグループを使えば、メッセージ内容をそのまま関数へ渡せます。

```json5
{
  trigger: "(?=.*(?:<@!?123>|<@&456>))(?=.*(?:サイコロ|ダイス|dice))(?=.*?(?P<dice>\\d+d\\d+))",
  response: "func://preset.mention.dynamic_dice",
}
```

この場合 `func://preset.mention.dynamic_dice` は `func://standard.random.roll_from_match` を返し、`ctx.group("dice")` に入った `10d10` のような値を使ってロールします。

カスタム関数でユーザーへ表示するエラーを返したい場合は、`FunctionDirectiveError` を送出してください。

```python
from cr_bot.function_errors import FunctionDirectiveError


def example(ctx, *, value: int) -> str:
    if value < 0:
        raise FunctionDirectiveError("value は0以上で指定してください。")
    return str(value)
```

想定外の例外はログに記録され、ユーザーには `.env` の `FUNCTION_UNKNOWN_ERROR_MESSAGE` が表示されます。

`func://` はBotが読み込めるPython関数を実行する機能です。信頼できないユーザーに `/add_response` を使わせる運用では、任意の登録済み関数を呼び出せる点に注意してください。

### ボット起動

```bash
python main.py
```

## 必要な権限

- 通常の応答送信には `メッセージを送信` 権限が必要です
- `img://...` / `imgs://...` による画像埋め込みには、追加で `埋め込みリンク` 権限が必要です
- スラッシュコマンドを使う場合は、Botを招待するときに `applications.commands` スコープも付与してください
- `func://` の戻り値が画像Embedを生成する場合も `埋め込みリンク` 権限が必要です

## コマンド

- `/list_responses` - 設定済みトリガーをインタラクティブなブラウザで表示
- `/list_functions` - 利用可能な `func://` 関数をインタラクティブなブラウザで表示
- `/add_response` - Modalで新しいトリガー応答を追加

`/list_responses` と `/list_functions` は、実行者だけに表示されるDiscord UIを使います。

- Selectで項目を選択できます
- `Prev` / `Next` でページ移動できます
- `Back` / `Root` で階層を戻れます
- `/add_response` とレスポンス詳細の `Edit` は同じ形式のModalで入力できます
- 関数詳細では、`Copy` ボタンで `func://...` をプレーンテキスト表示できます
- レスポンス詳細では、`Copy` ボタンで `trigger` と `response` をラベル付きプレーンテキスト表示できます
- レスポンス詳細では、`Edit` で更新、`Delete` で確認画面付き削除ができます
- コピーモードからは `Back to Detail` で詳細画面に戻れます
