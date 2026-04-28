from cr_bot.function_context import FunctionContext


def default_dice(ctx: FunctionContext) -> str:
    """Return a standard 2d6 roll directive.

    Preset package function.

    Sample:
        func://preset.mention.default_dice

    Returns:
        A func:// directive that calls the standard random roll function.
    """
    return "func://standard.random.roll?dice=%222d6%22"


def dynamic_dice(ctx: FunctionContext) -> str:
    """Build a dice roll directive from the matched trigger groups.

    Preset package function.

    Trigger example:
        (?=.*(?:<@!?123>|<@&456>))(?=.*(?:dice|ダイス|サイコロ))(?=.*?(?P<dice>\\d+d\\d+))

    Sample:
        func://preset.mention.dynamic_dice

    Returns:
        A func:// directive that calls standard.random.roll_from_match.
    """
    return "func://standard.random.roll_from_match"


def random_100(ctx: FunctionContext) -> str:
    """Return a 1-100 random number directive.

    Preset package function.

    Sample:
        func://preset.mention.random_100
    """
    return "func://standard.random.randint?min=1&max=100"


def greeting(ctx: FunctionContext) -> str:
    """Return a greeting directive using the standard template function.

    Preset package function.

    Sample:
        func://preset.mention.greeting
    """
    return (
        "func://standard.text.template?"
        "text=%22%7Bmention%7D%20さん、呼びましたか？%22"
    )
