# Custom Response Bot

A Discord bot that responds to messages by matching regular expressions and rendering configurable responses.

[日本語](./README.ja.md)

## Overview

The bot evaluates rules in `data/responses.json5` from top to bottom. The first rule whose `trigger` matches the incoming message sends its `response`.

Responses can include plain text and custom directives.

- `img://...`: converted to an `http://...` Discord embed image
- `imgs://...`: converted to an `https://...` Discord embed image
- `func://...`: executes a Python function under `function/`

If a function returns text containing `func://`, `img://`, or `imgs://`, the result is rendered again. The maximum number of render passes is controlled by `RESPONSE_RENDER_RECURSION_LIMIT` in `.env`.

## Features

- Automatic responses based on regular-expression triggers
- JSON5 response configuration
- Discord UI for adding, browsing, editing, and deleting responses
- Discord UI for browsing available `func://` functions
- Image URL embedding
- Dynamic responses powered by Python functions
- Regex named groups available from custom functions
- Reusable `standard` functions and composed `preset` functions

## Quick Start

### Installation

With uv:

```bash
uv sync
```

With pip:

```bash
pip install .
```

### Create `.env`

Create `.env` in the project root.

```env
DISCORD_TOKEN=your_bot_token_here
COMMAND_ENABLED=True
RESPONSE_RENDER_RECURSION_LIMIT=5
RESPONSE_RENDER_LIMIT_ERROR_MESSAGE=Response rendering reached the recursion limit.
FUNCTION_UNKNOWN_ERROR_MESSAGE=Function execution failed.
```

### Minimal Response Configuration

Create or edit `data/responses.json5`.

```json5
[
  {
    trigger: "hello",
    response: "Hello!",
  },
  {
    trigger: "^help$",
    response: "What do you need help with?",
  }
]
```

### Run The Bot

With uv:

```bash
uv run python main.py
```

If you manage the Python environment manually:

```bash
python main.py
```

## Basics

### Rule Structure

A response rule has this shape.

```json5
{
  trigger: "regular expression",
  response: "response content",
}
```

- `trigger` is treated as a Python regular expression
- `response` can include plain text, image directives, and function directives
- Rules are evaluated from top to bottom
- Only the first matching rule is executed

Order matters. Put specific rules before broad rules.

### Writing Triggers

Partial match:

```json5
{ trigger: "hello", response: "Hello!" }
```

Exact match:

```json5
{ trigger: "^help$", response: "Help message" }
```

Multiple keywords:

```json5
{ trigger: "hello|hi|hey", response: "Hello!" }
```

Mention and keyword at the same time:

```json5
{
  trigger: "(?=.*<@!?1234567890>)(?=.*(?:dice|roll))",
  response: "func://preset.mention.default_dice",
}
```

Including a role mention:

```json5
{
  trigger: "(?=.*(?:<@!?1234567890>|<@&9876543210>))(?=.*(?:dice|roll))",
  response: "func://preset.mention.default_dice",
}
```

Using a named group:

```json5
{
  trigger: "(?=.*(?:dice|roll))(?=.*?(?P<dice>\\d+d\\d+))",
  response: "func://preset.mention.dynamic_dice",
}
```

In this example, `dice 10d10` makes `10d10` available through `ctx.group("dice")`.

### Writing Responses

Plain text:

```json5
{
  trigger: "thanks",
  response: "You're welcome!",
}
```

Image mixed with text:

```json5
{
  trigger: "cat",
  response: "Here is a cat imgs://example.com/cat.png",
}
```

Function call:

```json5
{
  trigger: "random",
  response: "1 to 100: func://standard.random.randint?min=1&max=100",
}
```

## Image Directives

Write image URLs like this.

```json5
{
  trigger: "image",
  response: "Here is an image imgs://example.com/image.png",
}
```

- `img://example.com/a.png` becomes `http://example.com/a.png`
- `imgs://example.com/a.png` becomes `https://example.com/a.png`
- Images are sent as Discord embed images
- Multiple images can be included in one response
- Discord's `Embed Links` permission is required

## Function Directives

`func://` executes Python functions under `function/`.

```text
func://standard.random.randint?min=1&max=6
```

This calls `randint(ctx, *, min, max)` in `function/standard/random.py`.

### Arguments

`func://` does not support positional arguments. Use query-string keyword arguments only.

```text
func://standard.text.repeat?text=%22hello%22&count=3&separator=%22%20%22
```

Query values are URL-encoded Python literals.

- `min=1`: number
- `text=%22hello%20world%22`: string `"hello world"`
- `items=%5B%22A%22%2C%22B%22%5D`: list `["A", "B"]`
- Duplicate argument names are errors

Encode strings with their quotes. Use `%22hello%22`, not `hello`.

### Standard And Preset

`function/standard` contains reusable standard functions. Use them as small building blocks.

```text
func://standard.random.roll?dice=%222d6%22
```

`function/preset` contains composed functions for practical response rules. Users should usually look for a `preset` first, then call `standard` functions directly when needed.

```text
func://preset.mention.default_dice
```

This function returns `func://standard.random.roll?dice=%222d6%22`. The returned `func://` is rendered again, so the dice roll is executed.

### Recursive Rendering

Functions can return other directives.

```python
def default_dice(ctx):
    return "func://standard.random.roll?dice=%222d6%22"
```

```python
def image(ctx):
    return "imgs://placehold.co/400x200.png?text=Hello"
```

This lets you compose behavior by returning `func://` or `imgs://` from functions.

To avoid infinite loops, the render pass limit is controlled by `.env`.

```env
RESPONSE_RENDER_RECURSION_LIMIT=5
```

When the limit is reached, `RESPONSE_RENDER_LIMIT_ERROR_MESSAGE` is shown.

## User Tutorial

This section is for users who add, inspect, and edit responses from Discord.

### 1. Add A Response

Run `/add_response`. A modal opens with `Trigger` and `Response` fields.

Example:

```text
Trigger:
hello

Response:
Hello!
```

After saving, a `Response Added` detail screen is shown. Press `Copy` to display `trigger` and `response` as plain text.

### 2. Browse Responses

Run `/list_responses`.

- Select a response from the dropdown
- Use `Prev` / `Next` to move through pages
- Use filters to find responses using `func://` or images

### 3. Edit A Response

Select a response in `/list_responses`, then press `Edit`. The same modal style as `/add_response` opens.

After updating, the UI stays on a `Response Updated` detail screen.

### 4. Delete A Response

Select a response in `/list_responses`, then press `Delete`.

A confirmation screen appears. Press `Confirm Delete` to delete it. IDs after the deleted response shift down.

### 5. Browse Available Functions

Run `/list_functions`.

- Browse the `function/` tree
- Check your location with breadcrumbs
- Read signatures and docstrings on function details
- Press `Copy` on details to display a ready-to-use `func://...` as plain text

## Operator Tutorial

This section is for users who design response rules or add functions.

### 1. Fixed Text Response

```json5
{
  trigger: "^hello$",
  response: "Hello!",
}
```

Use `^` and `$` for exact matches.

### 2. Image Response

```json5
{
  trigger: "cat",
  response: "Cat image imgs://example.com/cat.png",
}
```

`imgs://` becomes `https://` and is sent as an embed image.

### 3. Call A Standard Function

```json5
{
  trigger: "random",
  response: "Today's number: func://standard.random.randint?min=1&max=100",
}
```

Use `standard` when you want to call a simple reusable function directly.

### 4. Use A Preset Function

```json5
{
  trigger: "dice",
  response: "func://preset.mention.default_dice",
}
```

`preset.mention.default_dice` returns `func://standard.random.roll?dice=%222d6%22`. The returned `func://` is rendered again.

Use `preset` as a short user-facing entry point.

### 5. Dynamic Dice With Message Content

Use a named group when the response should depend on the message, such as `dice 10d10`.

```json5
{
  trigger: "(?=.*(?:dice|roll))(?=.*?(?P<dice>\\d+d\\d+))",
  response: "func://preset.mention.dynamic_dice",
}
```

`preset.mention.dynamic_dice` returns `func://standard.random.roll_from_match`. `standard.random.roll_from_match` reads `ctx.group("dice")` and rolls values like `10d10`.

### 6. Return An Image From A Function

Functions can return image directives.

```python
def banner(ctx):
    return "imgs://placehold.co/600x240.png?text=Hello"
```

The returned text is rendered again and becomes an image embed.

### 7. Return Another Function Call

Functions can return `func://` directives.

```python
def today_roll(ctx):
    return "func://standard.random.roll?dice=%221d20%22"
```

This is useful for composing complex responses from small standard functions and short preset functions.

### 8. Add Your Own Function

Add a Python file under `function/standard` or `function/preset`.

```python
from cr_bot.function_context import FunctionContext


def hello(ctx: FunctionContext, *, name: str) -> str:
    """Return a greeting.

    Sample:
        func://standard.greeting.hello?name=%22Alice%22
    """
    return f"Hello, {name}!"
```

The first argument should be `ctx`. From `ctx`, functions can access the message, author, channel, guild, bot, and regex match data.

### 9. Raise User-Facing Errors

Raise `FunctionDirectiveError` when you want to show a controlled error message to users.

```python
from cr_bot.function_errors import FunctionDirectiveError


def positive(ctx, *, value: int) -> str:
    if value < 0:
        raise FunctionDirectiveError("value must be 0 or greater")
    return str(value)
```

Unexpected exceptions are logged, and users see `FUNCTION_UNKNOWN_ERROR_MESSAGE` from `.env`.

## Command UI Guide

### `/add_response`

Adds a rule through a modal with `Trigger` and `Response` fields. After saving, a detail screen is shown.

### `/list_responses`

Browses and manages response rules.

- Filters: `All`, `Uses func://`, `Uses img://`, `Uses preset`, `Uses standard`, `Plain text`
- `Copy`: shows labeled `trigger` and `response` plain text
- `Edit`: updates through a modal
- `Delete`: deletes with a confirmation screen
- `Back to List`: returns to the list
- `Close`: closes the UI

### `/list_functions`

Browses available functions.

- Shows the nested `function/` tree
- Move through folders, modules, and functions with Select
- Use `Back` / `Root` for navigation
- Press `Copy` on function details to display `func://...` as plain text

## Required Permissions

- Normal responses require `Send Messages`
- Image embeds from `img://...` / `imgs://...` require `Embed Links`
- `func://` results that create image embeds also require `Embed Links`
- Slash commands require the `applications.commands` scope when inviting the bot

If image embeds work in a test server but not in production, check whether `Embed Links` is disabled for the bot's role or the target channel.

## Troubleshooting

### The Bot Does Not Respond

- Check whether the `trigger` regex matches the message
- Check whether another rule matched first
- Check whether the `message_content` intent is enabled

### The Wrong Rule Responds

Rules are evaluated from top to bottom, and only the first match is used. Move more specific rules upward.

### Images Do Not Appear

- Check the `Embed Links` permission
- Check whether Discord can fetch the image URL
- Check whether `img://` and `imgs://` are used correctly

### func Does Not Work

- Check whether `/list_functions` shows the function
- Check whether the path is correct, such as `func://standard.random.randint`
- Check whether argument values are URL-encoded Python literals

### URL Encoding Is Confusing

Encode strings with their quotes.

```text
"hello world" -> %22hello%20world%22
```

### Render Limit Reached

If a function keeps returning another `func://`, rendering may hit the limit. Check `RESPONSE_RENDER_RECURSION_LIMIT` in `.env`.

## Security Notes

`func://` executes Python functions that the bot can import. Use it only in trusted servers or with trusted users. Permission management is planned for a future update.

## TODO

- [ ] Permission management
- [ ] Response ordering
- [ ] More standard functions
