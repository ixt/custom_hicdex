import hicdex.models as models
from dipdup.context import HookContext
from hicdex.metadata_utils import fix_other_metadata


async def failed_metas(
    ctx: HookContext
) -> None:
    ctx.logger.info('Recheck failed token metadatas')
    await fix_other_metadata(100)
