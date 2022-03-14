import hicdex.models as models
from dipdup.context import HookContext
from hicdex.models import Token

from hicdex.metadata_utils import fix_token_metadata


async def get_token_meta(
    ctx: HookContext,
    token: Token
) -> None:

    await fix_token_metadata(token)
