import json
import logging
import time
import datetime
import re
import math

from json import dumps as dump_json

from pathlib import Path

import aiohttp
from tortoise.query_utils import Q

import hicdex.models as models
from hicdex.utils import clean_null_bytes, http_request

from inspect import getmembers
from pprint import pprint

BASE_PATH = '/home/dipdup/metadata'
TOKEN_PATH = '/home/dipdup/metadata/tokens'
SUBJKT_PATH = '/home/dipdup/metadata/subjkts'
IPFS_PATH = '/home/dipdup/metadata/ipfs'
BROKEN_JSON_URL = 'https://raw.githubusercontent.com/bikerworld/broken-objkt/main/broken.json'

_logger = logging.getLogger(__name__)

broken_ids = []
last_fix = 0
last_download = 0

HEN_MINTER = 'KT1RJ6PbjHpwc3M5rw5s2Nbmefwbuwbdxton'
VERSUM_MINTER = 'KT1LjmAdYQCLBjwv4S2oFkEzyHVkomAf5MrW'
MAX_INTEGER = math.pow(10, 18)


# we want to break things if broken.json is not here
# try:
with open(f'{TOKEN_PATH}/broken.json') as broken_list:
    broken_ids = json.load(broken_list)


def dump(obj):
    for attr in dir(obj):
        try:
            print("obj.%s = %r" % (attr, getattr(obj, attr)))
        except Exception:
            pass


def proper_integer(value):
    new_value = int(value)
    if new_value > MAX_INTEGER:
        _logger.error(f'Invalid nteger over max : {value} -> {MAX_INTEGER}')
        return MAX_INTEGER
    elif new_value < -MAX_INTEGER:
        _logger.error(f'Invalid integer over min : {value} -> -{MAX_INTEGER}')
        return -MAX_INTEGER
    else:
        return new_value


async def fetch_broken_json():
    try:
        session = aiohttp.ClientSession()
        resp = await session.get(BROKEN_JSON_URL)
        data = await resp.json(content_type=None)
        await session.close()
        if data and isinstance(data, list):
            _logger.info(f'Reloaded broken list: {len(data)} objkts')
            with open(f'{TOKEN_PATH}/broken.json', 'w') as write_file:
                json.dump(data, write_file)
            return data
    except Exception:
        _logger.info('Unable to retrieve broken.json')
        await session.close()
    return False


async def get_fa2_metadata(token):
    metadata = await get_metadata(token)
    token.title = get_name(metadata)
    token.description = get_description(metadata)
    token.artifact_uri = get_artifact_uri(metadata)
    token.display_uri = get_display_uri(metadata)
    if token.fa2_id == VERSUM_MINTER:
        token.thumbnail_uri = get_poster_uri(metadata)
    else:
        token.thumbnail_uri = get_thumbnail_uri(metadata)
    token.mime = get_mime(metadata)

    img = get_image_uri(metadata)
    if token.artifact_uri == '' and img != '':
        token.artifact_uri = img
        token.mime = 'image/png'
    if token.display_uri == '' and img != '':
        token.display_uri = img

    token.extra = metadata.get('extra', {})
    val = get_royalties(metadata)
    if val > 0 and token.royalties == 0:
        token.royalties = get_royalties(metadata)

    token.fixed = token.artifact_uri != ''
    await add_tags(token, metadata)
    await token.save()
    return metadata != {}


async def fix_token_metadata(token):
    if token.pk_id in broken_ids:
        token.fixed = True
        await token.save()
        return False

    metadata = await get_metadata(token)
    token.title = get_name(metadata)
    token.description = get_description(metadata)
    token.artifact_uri = get_artifact_uri(metadata)
    token.display_uri = get_display_uri(metadata)
    if token.fa2_id == VERSUM_MINTER:
        token.thumbnail_uri = get_poster_uri(metadata)
    else:
        token.thumbnail_uri = get_thumbnail_uri(metadata)
    token.mime = get_mime(metadata)
    token.extra = metadata.get('extra', {})
    token.fixed = token.artifact_uri != ''
    await add_tags(token, metadata)
    await token.save()
    return metadata != {}


async def fix_other_metadata(limit):
    global last_download
    global broken_ids
    now = int(time.time())
    # download updated broken.json once per hour
    overtime = now - 3600
    if last_download < overtime:
        last_download = int(time.time())
        data = await fetch_broken_json()
        if data:
            broken_ids = data

    # we fix meta for tokens older than 60 sec
    min_time = datetime.datetime.now() - datetime.timedelta(minutes=1)
    tokens = await models.Token.filter(Q(fixed=False) & Q(timestamp__lt=min_time)).all().order_by('-level').limit(limit)
    _logger.info(
        f'{len(tokens)} tokens created before {min_time} need to be fixed')
    for token in tokens:
        if (token.fa2_id == HEN_MINTER):
            fixed = await fix_token_metadata(token)
        else:
            fixed = await get_fa2_metadata(token)

        if fixed:
            _logger.info(f'fixed metadata for {token.id} - {token.fa2_id}')
        else:
            _logger.info(
                f'failed to fix metadata for {token.id} - {token.fa2_id}')


async def add_tags(token, metadata):
    tags = [await get_or_create_tag(tag) for tag in get_tags(metadata)]
    for tag in tags:
        token_tag = await models.TokenTag(token=token, tag=tag)
        await token_tag.save()


async def get_or_create_tag(tag_name):
    tag, _ = await models.Tag.get_or_create(name=tag_name)
    return tag


async def get_subjkt_metadata(holder):
    failed_attempt = 0
    addr = holder.metadata_file.replace('ipfs://', '')
    try:
        with open(subjkt_path(addr)) as json_file:
            metadata = json.load(json_file)
            failed_attempt = metadata.get('__failed_attempt')
            if failed_attempt and failed_attempt > 10:
                return {}
            if not failed_attempt:
                return metadata
    except Exception:
        pass

    data = await fetch_subjkt_metadata_cf_ipfs(holder, failed_attempt)

    return data


async def get_metadata(token):
    failed_attempt = 0
    try:
        with open(ipfs_path(token.metadata)) as json_file:
            metadata = json.load(json_file)
            failed_attempt = metadata.get('__failed_attempt')
            if failed_attempt and failed_attempt > 10:
                return {}
            if not failed_attempt:
                # check that recorded ipfs key is the same as current token
                memoized_meta = metadata.get('metadata', '')
                if (memoized_meta == '' and token.fa2_id == HEN_MINTER):
                    return metadata
                elif token.metadata == memoized_meta:
                    return metadata

    except Exception:
        pass

    if (failed_attempt == None):
        failed_attempt = 0

    data = await fetch_metadata_cf_ipfs(token, failed_attempt)
    if data != {}:
        _logger.info(f'metadata for {token.id} {token.metadata} from IPFS')
    elif (token.fa2_id == HEN_MINTER):
        data = await fetch_metadata_bcd(token, failed_attempt)
        if data != {}:
            _logger.info(f'metadata for {token.id} {token.metadata} from BCD')

    return data


def normalize_metadata(token, metadata):
    n = {
        '__version': 1,
        'metadata': token.metadata,
        'token_id': token.id,
        'symbol': metadata.get('symbol', 'OBJKT'),
        'name': get_name(metadata),
        'description': get_description(metadata),
        'artifact_uri': get_artifact_uri(metadata),
        'display_uri': get_display_uri(metadata),
        'thumbnail_uri': get_thumbnail_uri(metadata),
        'image': get_image_uri(metadata),
        'formats': get_formats(metadata),
        'creators': get_creators(metadata),
        'generative_uri': get_generative_uri(metadata),
        # not cleaned / not lowercased, store as-is
        'tags': metadata.get('tags', []),
        'royalties': metadata.get('royalties', {}),
        'attributes': metadata.get('attributes', []),
        'extra': {},
    }

    return n


def write_subjkt_metadata_file(holder, metadata):
    addr = holder.metadata_file.replace('ipfs://', '')
    with open(subjkt_path(addr), 'w') as write_file:
        json.dump(metadata, write_file)


def write_metadata_file(token, metadata):
    with open(ipfs_path(token.metadata), 'w') as write_file:
        json.dump(normalize_metadata(token, metadata), write_file)


async def fetch_metadata_bcd(token, failed_attempt=0):
    if (token.fa2_id != HEN_MINTER):
        return {}

    session = aiohttp.ClientSession()
    data = await http_request(
        session,
        'get',
        url=f'https://api.better-call.dev/v1/tokens/mainnet/metadata?contract:KT1Hkg5qeNhfwpKW4fXvq7HGZB9z2EnmCCA9&token_id={token.id}',
    )
    await session.close()

    data = [
        obj for obj in data if 'symbol' in obj and (obj['symbol'] == 'OBJKT' or obj['contract'] == HEN_MINTER)
    ]
    try:
        if data and not isinstance(data[0], list):
            write_metadata_file(token, data[0])
            return data[0]
        with open(ipfs_path(token.metadata), 'w') as write_file:
            json.dump({'__failed_attempt': failed_attempt + 1}, write_file)
    except FileNotFoundError:
        pass
    return {}


async def fetch_subjkt_metadata_cf_ipfs(holder, failed_attempt=0, alternative=False):
    addr = holder.metadata_file.replace('ipfs://', '')
    url = f'https://cloudflare-ipfs.com/ipfs/{addr}'
    if alternative:
        url = f'https://ipfs.io/ipfs/{addr}'

    try:
        session = aiohttp.ClientSession()
        data = await http_request(session, 'get', url=url, timeout=10)
        await session.close()
        if data and not isinstance(data, list):
            write_subjkt_metadata_file(holder, data)
            return data

        if not alternative:
            data = await fetch_subjkt_metadata_cf_ipfs(token, failed_attempt, True)
            return data

        with open(subjkt_path(addr), 'w') as write_file:
            json.dump({'__failed_attempt': failed_attempt + 1}, write_file)
    except Exception:
        await session.close()
        if not alternative:
            data = await fetch_subjkt_metadata_cf_ipfs(token, failed_attempt, True)
            return data
    return {}


async def fetch_metadata_cf_ipfs(token, failed_attempt=0, alternative=False):
    addr = token.metadata.replace('ipfs://', '')
    url = f'https://cloudflare-ipfs.com/ipfs/{addr}'
    if alternative:
        url = f'https://ipfs.io/ipfs/{addr}'

    try:
        session = aiohttp.ClientSession()
        data = await http_request(session, 'get', url=url, timeout=10)
        await session.close()

        if data and not isinstance(data, list):
            write_metadata_file(token, data)
            return data

        if not alternative:
            data = await fetch_metadata_cf_ipfs(token, failed_attempt, True)
            return data

        with open(ipfs_path(token.metadata), 'w') as write_file:
            json.dump({'__failed_attempt': failed_attempt + 1}, write_file)
    except Exception as err:
        await session.close()
        # print(f"Unexpected {err=}, {type(err)=}")
        if not alternative:
            data = await fetch_metadata_cf_ipfs(token, failed_attempt, True)
            return data

    return {}


def get_mime(metadata):
    if ('formats' in metadata) and metadata['formats'] and ('mimeType' in metadata['formats'][0]):
        return metadata['formats'][0]['mimeType']
    return ''


def get_tags(metadata):
    tags = metadata.get('tags', [])
    try:
        cleaned = [clean_null_bytes(tag) for tag in tags]
        lowercased = [tag.lower() for tag in cleaned]
        uniqued = list(set(lowercased))
        return [tag for tag in uniqued if len(tag) < 255]
    except Exception:
        return []


def get_name(metadata):
    return clean_null_bytes(metadata.get('name', ''))


def get_description(metadata):
    return clean_null_bytes(metadata.get('description', ''))


def get_image_uri(metadata):
    return clean_null_bytes(metadata.get('image', ''))


def get_artifact_uri(metadata):
    return clean_null_bytes(metadata.get('artifact_uri', '') or metadata.get('artifactUri', ''))


def get_generative_uri(metadata):
    return clean_null_bytes(metadata.get('generative_uri', '') or metadata.get('generativeUri', ''))


def get_display_uri(metadata):
    return clean_null_bytes(metadata.get('display_uri', '') or metadata.get('displayUri', ''))


def get_thumbnail_uri(metadata):
    return clean_null_bytes(metadata.get('thumbnail_uri', '') or metadata.get('thumbnailUri', ''))


def get_poster_uri(metadata):
    # next(obj for obj in objs if obj.val == 5)
    formats = get_formats(metadata)
    if formats:
        filtered_img = filter(lambda obj: re.search(r'image', obj['mimeType']) != None and re.search(
            r'preview', obj['fileName']) != None, get_formats(metadata))
        first = next(filtered_img, None)
        if first != None:
            return clean_null_bytes(first['uri'])
        else:
            return get_thumbnail_uri(metadata)
            # print(metadata)
            # print(get_formats(metadata))
            # print(list(filtered_img))
            # abort
    else:
        return get_thumbnail_uri(metadata)


def get_royalties(metadata):
    data = metadata.get('royalties', {})
    try:
        if data and data['shares']:
            try:
                if type(data['shares']) is dict:
                    values = data['shares'].values()
                    return sum(values)
                elif type(data['shares']) is list:
                    values = [sum(x.values()) for x in data['shares']]
                    return sum(values)
                else:
                    return 0
            except Exception as e:
                _logger.error(f'Invalid royalties - skipped')
                return 0
        else:
            return 0
    except TypeError as e:
        _logger.error(f'Invalid royalties - skipped')
        return 0


def get_formats(metadata):
    return metadata.get('formats', [])


def get_minter(metadata):
    return metadata.get('minter', HEN_MINTER)


def get_creators(metadata):
    return [clean_null_bytes(x) for x in metadata.get('creators', [])]


def get_creator(metadata):
    return [clean_null_bytes(x) for x in metadata.get('creator', [])]


def token_path(token_id: str):
    token_id_int = int(token_id)
    lvl2 = token_id_int % 10
    lvl1 = int((token_id_int % 100 - lvl2) / 10)
    return f'{TOKEN_PATH}/{lvl1}/{lvl2}/{token_id}.json'


def ipfs_path(ipfs_url: str):
    ipfs = ipfs_url.replace('ipfs://', '').replace('/', '_')
    lvl = ipfs[-1]
    folder = f'{IPFS_PATH}/{lvl}'.lower()
    Path(folder).mkdir(parents=True, exist_ok=True)
    return f'{folder}/{ipfs}.json'


def subjkt_path(addr: str):
    lvl = addr[-1]
    folder = f'{SUBJKT_PATH}/{lvl}'.lower()
    Path(folder).mkdir(parents=True, exist_ok=True)
    return f'{folder}/{addr}.json'
