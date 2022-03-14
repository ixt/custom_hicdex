import hicdex.models as models
from dipdup.context import HandlerContext
from dipdup.models import Transaction

from hicdex.types.fxhash_moderation.parameter.moderate import ModerateParameter
from hicdex.types.fxhash_moderation.storage import FxhashModerationStorage


async def fxhash_moderated(
    ctx: HandlerContext,
    moderate: Transaction[ModerateParameter, FxhashModerationStorage],
) -> None:

    fa2_id = 'KT1XCoGnfupWk7Sp8536EfrxcP73LmT68Nyr'
    token_id = moderate.parameter.id
    moderated = moderate.parameter.state
    ctx.logger.info('Token `%s` flagged `%s`', token_id, moderated)

    token = await models.Token.filter(id=str(token_id), fa2_id=fa2_id).get_or_none()
    if token is not None:
        token.moderated = int(moderated)
        await token.save()
