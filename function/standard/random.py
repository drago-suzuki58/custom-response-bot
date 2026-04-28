import random as random_module
import re

from cr_bot.function_context import FunctionContext
from cr_bot.function_errors import FunctionDirectiveError


def randint(ctx: FunctionContext, *, min: int, max: int) -> int:
    """Return a random integer in the inclusive range.

    Standard package function.

    Sample:
        func://standard.random.randint?min=1&max=6

    Args:
        min: Minimum integer value.
        max: Maximum integer value.

    Raises:
        FunctionDirectiveError: If min is greater than max.
    """
    if min > max:
        raise FunctionDirectiveError("min は max 以下で指定してください。")

    return random_module.randint(min, max)


def choice(ctx: FunctionContext, *, items: list[object]) -> object:
    """Return one random item from a list.

    Standard package function.

    Sample:
        func://standard.random.choice?items=%5B%22red%22%2C%22blue%22%5D

    Args:
        items: Non-empty list of selectable values.

    Raises:
        FunctionDirectiveError: If items is empty.
    """
    if not items:
        raise FunctionDirectiveError("items には1件以上の値を指定してください。")

    return random_module.choice(items)


def roll(ctx: FunctionContext, *, dice: str = "1d6") -> str:
    """Roll dice written in NdM format.

    Standard package function.

    Sample:
        func://standard.random.roll?dice=%222d6%22

    Args:
        dice: Dice expression such as "1d6" or "2d20".

    Returns:
        A text result containing each roll and the total.
    """
    return _roll_dice_expression(dice)


def roll_from_match(ctx: FunctionContext, *, group: str = "dice") -> str:
    """Roll dice using a named regex group from the matched trigger.

    Standard package function.

    Trigger example:
        (?=.*(?:<@!?123>|<@&456>))(?=.*(?:dice|ダイス|サイコロ))(?=.*?(?P<dice>\\d+d\\d+))

    Sample:
        func://standard.random.roll_from_match
        func://standard.random.roll_from_match?group=%22dice%22

    Args:
        group: Named regex group that contains the dice expression.
    """
    dice = ctx.group(group)
    if not isinstance(dice, str) or not dice:
        raise FunctionDirectiveError(
            f"トリガーの一致結果に `{group}` グループが見つかりません。"
        )

    return _roll_dice_expression(dice)


def _roll_dice_expression(dice: str) -> str:
    match = re.fullmatch(r"(\d+)d(\d+)", dice)
    if match is None:
        raise FunctionDirectiveError("dice は `1d6` のような形式で指定してください。")

    count = int(match.group(1))
    sides = int(match.group(2))
    if count < 1 or count > 100:
        raise FunctionDirectiveError("ダイスの個数は1から100の範囲で指定してください。")
    if sides < 2 or sides > 1000:
        raise FunctionDirectiveError("ダイスの面数は2から1000の範囲で指定してください。")

    rolls = [random_module.randint(1, sides) for _ in range(count)]
    return f"{dice}: {rolls} = {sum(rolls)}"
