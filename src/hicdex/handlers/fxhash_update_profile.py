import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction

from hicdex.types.fxhash_user.parameter.update_profile import UpdateProfileParameter
from hicdex.types.fxhash_user.storage import FxhashUserStorage

from hicdex.utils import fromhex
from hicdex.metadata_utils import dump
import urllib


async def fxhash_update_profile(
    ctx: HandlerContext,
    update_profile: Transaction[UpdateProfileParameter, FxhashUserStorage],
) -> None:

    addr = update_profile.data.sender_address
    name = update_profile.parameter.name
    if name:
        name = urllib.parse.unquote_plus(fromhex(name)).strip()

    holder, _ = await models.Holder.get_or_create(address=addr)
    if holder:
        if not(holder.name) or (holder.name is None):
            holder.name = name
        elif (holder.fxname is not None) and (holder.name.lower() == holder.fxname.lower()):
            holder.name = name

        holder.fxname = name
        ctx.logger.info('Link `%s` to name `%s`', addr, name)
        await holder.save()
