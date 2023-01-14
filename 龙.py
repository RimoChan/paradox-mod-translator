import re
import itertools
from pathlib import Path
from typing import List, Dict, Union, Any, Optional
from concurrent.futures import ThreadPoolExecutor

import yaml
from tqdm import tqdm
from rimo_storage.cache import disk_cache


替换 = {}


def 前处理(s):
    def findall(p, s):
        i = s.find(p)
        while i != -1:
            yield i
            i = s.find(p, i+1)
    ss = []
    切点定义 = [
        r'(?:\$.+?\$)',
        r'(?:\[.+?\])',
        r'(?:\@.+?\!)',
        r'(?:\#\!)',
        r'(?:\#(?:\w|;)* )',
        r'(?:£.+?£)',
        r'(?:\n)',
        r'(?:§.)',
    ]
    l = {*re.findall('|'.join(切点定义), s)}
    切点 = []
    for i in l:
        for t in findall(i, s):
            切点.append((t, t+len(i)))
    切点.sort()
    last = 0
    for (x, y) in 切点:
        ss.append(s[last:x])
        ss.append(s[x:y])
        last = y
    ss.append(s[last:])
    a = [x for i, x in enumerate(ss) if i % 2 == 0]
    b = [x for i, x in enumerate(ss) if i % 2 == 1]
    return a, b


def 后处理(s: List[str], extra: Any) -> str:
    # extra = [f'[{x}]' for x in extra]
    l = []
    for q, w in itertools.zip_longest(s, extra):
        l.append(q)
        if w:
            l.append(w)
    s = ''.join(l)
    for k, v in 替换.items():
        s = s.replace(k, v)
    return s


@disk_cache(path='_translate_cache')
def 上网(s: str, 源语言: str, 目标语言: str) -> str:
    import translators as ts
    语言表 = {
        'english': 'en',
        'simp_chinese': 'zh',
    }
    return ts.google(s, from_language=语言表[源语言], to_language=语言表[目标语言])


def 多重上网(s: List[str], 源语言: str, 目标语言: str) -> List[str]:
    return [上网(s, 源语言, 目标语言) for s in s]


def 翻译(s: str, 源语言: str, 目标语言: str) -> str:
    s, extra = 前处理(s)
    s = 多重上网(s, 源语言=源语言, 目标语言=目标语言)
    s = 后处理(s, extra)
    return s


A = Dict[str, Union[str, 'A']]
def 超翻译(q: A, 源语言: str, 目标语言: str, 文件名: Optional[str] = None) -> A:
    tq = tqdm(total=len(q), ncols=70, desc=文件名)
    def 换(item) -> Union[str, A]:
        tq.update(1)
        k, v = item
        if isinstance(v, str):
            return 翻译(v, 源语言=源语言, 目标语言=目标语言)
        elif isinstance(v, dict):
            return 超翻译(v, 源语言=源语言, 目标语言=目标语言)
        else:
            return v
    新q = {}
    for (k, v), 新v in zip(q.items(), ThreadPoolExecutor(max_workers=8).map(换, q.items())):
        if k == f'l_{源语言}':
            k = f'l_{目标语言}'
        新q[k] = 新v
    return 新q


def _龙(源: Path, 目标: Path, 源语言: str, 目标语言: str, 强制对齐):
    if 源.is_dir():
        目标.mkdir(exist_ok=True)
        for x in 源.iterdir():
            name = x.name
            name = name.replace(f'_l_{源语言}.', f'_l_{目标语言}.')
            _龙(x, 目标 / name, 源语言, 目标语言, 强制对齐)
    elif 源.is_file():
        if 源.suffix in ['.yaml', '.yml']:
            with open(源, encoding='utf-8') as f:
                print(f'开始处理 {源.name} 。')
                txt = f.read()
                if txt[0] == '\ufeff':
                    txt = txt[1:]
                # p社的yaml格式诡异，随便搞1搞
                txt = re.sub(r':\d* +', ': ', txt)   # 删除冒号后的数字
                txt = re.sub(r':\d+"', ': "', txt)   # 删除冒号后的数字
                txt = re.sub(r'''#[^"]*(?=(\n|$))''', '', txt)   # 删除注释
                txt = re.sub(r'(?<!(\: ))(?<!(\\))"(?!( *(\n|$)))', '\\"', txt)  # 为内部的双引号加上转义符
                if 强制对齐:
                    txt = txt.replace('\r', '\n')
                    lines = txt.split('\n')
                    new_lines = []
                    for line in lines:
                        line = line.strip()
                        if line == f'l_{源语言}:':
                            new_lines.append(line)
                        else:
                            new_lines.append('  '+line)
                    txt = '\n'.join(new_lines)
                x = yaml.safe_load(txt)
                x = 超翻译(x, 源语言=源语言, 目标语言=目标语言, 文件名=源.name)
                print(f'{源.name} -> {目标.name}，翻译好了！')

            # 默认格式游戏不识别，必须改成双引号
            dict_keys = set()
            def _a(d: dict):
                for k, v in d.items():
                    dict_keys.add(k)
                    if isinstance(v, dict):
                        _a(v)
            _a(x)
            def mk_double_quote(dumper, data):
                if data in dict_keys:
                    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='')
                else:
                    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')
            yaml.add_representer(str, mk_double_quote)

            with open(目标, 'w', encoding='utf-8-sig') as f:
                yaml.dump(x, f, allow_unicode=True, width=100000, default_flow_style=False, explicit_start=True)


def 龙(本地化文件夹路径: str, 源语言: str = 'english', 目标语言: str = 'simp_chinese', 强制对齐=True):
    本地化文件夹路径 = Path(本地化文件夹路径)
    _龙(本地化文件夹路径/源语言, 本地化文件夹路径/目标语言, 源语言, 目标语言, 强制对齐)
