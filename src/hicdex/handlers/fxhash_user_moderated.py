import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction

from hicdex.types.fxhash_user_moderation.storage import FxhashUserModerationStorage
from hicdex.types.fxhash_user_moderation.parameter.moderate import ModerateParameter


async def fxhash_user_moderated(
    ctx: HandlerContext,
    moderate: Transaction[ModerateParameter, FxhashUserModerationStorage],
) -> None:

    addr = moderate.parameter.address
    holder, _ = await models.Holder.get_or_create(address=addr)
    if holder:
        holder.fxflag = int(moderate.parameter.state)
        ctx.logger.info('Address `%s` moderated : `%s`', addr, holder.fxflag)
        await holder.save()
