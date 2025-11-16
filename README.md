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

### Running the Bot

```bash
python main.py
```

## Commands

- `/list_responses` - Display all configured triggers
- `/add_response <trigger> <response>` - Add a new trigger response
- `/remove_response <id>` - Remove a trigger response by ID (ID can be found using `/list_responses`)
