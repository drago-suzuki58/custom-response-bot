# Custom Response Bot

A Discord bot that automatically responds to messages based on customizable triggers with regex pattern matching.

[日本語](./README.ja.md)

## Features

- Automatic message responses based on regex triggers
- Easy JSON5-based configuration
- Add/remove responses via Discord commands or direct file editing
- View all triggers with embedded messages
- Flexible pattern matching with regex support

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

or with uv:

```bash
uv sync
```

### Configuration

1. Create a `.env` file in the root directory

```
DISCORD_TOKEN=your_bot_token_here
```

2. Edit `data/responses.json5` to add triggers

```json5
[
  {
    trigger: "hello",
    response: "Hello! How can I assist you today?"
  },
  {
    trigger: "^help$",
    response: "What do you need help with?"
  }
]
```

In `response`, you can embed images with custom directives alongside normal text.

```json5
[
  {
    trigger: "cat",
    response: "Here is a cat imgs://example.com/cat.png"
  },
  {
    trigger: "two images",
    response: "imgs://example.com/a.png imgs://example.com/b.png"
  }
]
```

- `img://...` is treated as an `http://...` image URL
- `imgs://...` is treated as an `https://...` image URL
- Image URLs are sent as Discord embed images
- Directives can be mixed into normal text
- Multiple images can be included in one `response`

You can also run custom functions from the `function` folder with `func://...`.

- `function/standard` contains reusable standard functions
- `function/preset` contains composed functions that build `func://...` directives and call standard functions

```json5
[
  {
    trigger: "dice",
    response: "1d6: func://standard.random.randint?min=1&max=6"
  },
  {
    trigger: "placeholder",
    response: "func://standard.image.placeholder?width=600&height=400&text=%22Hello%22"
  },
  {
    trigger: "preset dice",
    response: "func://preset.mention.default_dice"
  }
]
```

- `func://standard.random.randint?min=1&max=6` calls `randint(ctx, *, min, max)` in `function/standard/random.py`
- `func://preset.mention.default_dice` builds and returns `func://standard.random.roll?...` from `function/preset/mention.py`
- Positional arguments are not supported; use query-string keyword arguments only
- Query values must be URL-encoded Python literals
- Strings should be encoded with quotes, such as `text=%22hello%20world%22`
- Duplicate argument names are treated as errors
- Both `def` and `async def` functions are supported
- Functions receive `ctx`, which includes the bot, message, author, channel, and guild
- Regex match data is available through `ctx.trigger_match`, `ctx.group()`, and `ctx.groupdict()`
- Returned `func://...`, `img://...`, and `imgs://...` directives are parsed again
- The re-render limit is controlled by `RESPONSE_RENDER_RECURSION_LIMIT` in `.env`

For dynamic behavior, you can capture values in the trigger and read them inside a function.

```json5
{
  trigger: "(?=.*(?:<@!?123>|<@&456>))(?=.*(?:サイコロ|ダイス|dice))(?=.*?(?P<dice>\\d+d\\d+))",
  response: "func://preset.mention.dynamic_dice"
}
```

In this case `func://preset.mention.dynamic_dice` returns `func://standard.random.roll_from_match`, which reads `ctx.group("dice")` and rolls values such as `10d10`.

Raise `FunctionDirectiveError` from custom functions to show a user-facing error message.

```python
from cr_bot.function_errors import FunctionDirectiveError


def example(ctx, *, value: int) -> str:
    if value < 0:
        raise FunctionDirectiveError("value must be 0 or greater")
    return str(value)
```

Unexpected exceptions are logged, and users see `FUNCTION_UNKNOWN_ERROR_MESSAGE` from `.env`.

`func://` executes Python functions that the bot can import. If untrusted users can use `/add_response`, they can call any registered function, so be careful with production permissions.

### Running the Bot

```bash
python main.py
```

## Required Permissions

- Normal responses require the `Send Messages` permission
- Image embeds created from `img://...` / `imgs://...` also require the `Embed Links` permission
- If you use slash commands, include the `applications.commands` scope when inviting the bot
- `func://` results that create image embeds also require the `Embed Links` permission

If image embeds work in a test server but not in production, check whether `Embed Links` is disabled for the bot's role or for the target channel.

## Commands

- `/list_responses` - Browse configured triggers with an interactive browser
- `/list_functions` - Browse available `func://` functions with an interactive browser
- `/add_response` - Add a new trigger response with a modal

`/list_responses` and `/list_functions` use Discord UI components and are visible only to the command user.

- Select items from dropdowns
- Move through pages with `Prev` / `Next`
- Navigate function folders with `Back` / `Root`
- `/add_response` and response `Edit` use the same modal-style input
- Function details include a `Copy` button that shows `func://...` as plain text
- Response details include a `Copy` button that shows labeled `trigger` and `response` plain text
- Response details include `Edit` for updates and `Delete` with a confirmation screen
- Use `Back to Detail` to return from copy mode
