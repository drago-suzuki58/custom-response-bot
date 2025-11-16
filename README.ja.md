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

### ボット起動

```bash
python main.py
```

## コマンド

- `/list_responses` - 設定済みトリガーをすべて表示
- `/add_response <trigger> <response>` - 新しいトリガー応答を追加
- `/remove_response <id>` - 指定したトリガー応答をIDで削除(IDは`/list_responses`で確認可能です)
