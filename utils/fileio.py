import json
import aiofiles
from typing import Union

async def read_json(path: str):
    async with aiofiles.open(path, 'r') as f:
        lines = await f.read()
    data = json.loads(lines)
    return data

async def write_json(path: str, data: Union[dict, list]):
    line = json.dumps(data)
    async with aiofiles.open(path, 'w') as f:
        await f.write(line)

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