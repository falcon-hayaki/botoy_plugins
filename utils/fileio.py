import json
import aiofiles
import asyncio
import os
import tempfile
from typing import Union


async def read_json(path: str):
    async with aiofiles.open(path, 'r') as f:
        lines = await f.read()
    data = json.loads(lines)
    return data


def _sync_write_atomic(path: str, content: str):
    # Write to a temp file on the same filesystem, flush and fsync, then atomically replace
    dirpath = os.path.dirname(path) or '.'
    with tempfile.NamedTemporaryFile('w', delete=False, dir=dirpath, encoding='utf-8') as tf:
        tf.write(content)
        tf.flush()
        os.fsync(tf.fileno())
        tmpname = tf.name
    os.replace(tmpname, path)


async def write_json(path: str, data: Union[dict, list]):
    line = json.dumps(data, ensure_ascii=False, indent=4)
    # Perform the write in a thread to allow fsync and atomic replace without blocking loop
    await asyncio.to_thread(_sync_write_atomic, path, line)

async def read_txt(path: str):
    async with aiofiles.open(path, 'r') as f:
        data = await f.read()
    return data

async def read_lines(path: str):
    async with aiofiles.open(path, 'r') as f:
        data = await f.readlines()
    return data

async def addline(path: str, line: str):
    async with aiofiles.open(path, 'a+') as f:
        await f.write(line)
        
async def clear_file(path: str):
    async with aiofiles.open(path, "w") as f:
        await f.truncate(0)