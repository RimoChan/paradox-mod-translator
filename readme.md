# P社mod翻译器

在玩P社游戏的时候，我经常去下载一些外国人做的奇怪的mod，但是这些mod没有汉化，看起来非常费劲！

所以我就想，啊，不如写一个翻译器，大家就可以玩上机器翻译的奇怪的mod啦！

> 神秘翻译器  
> 效果:  
> 　破译: +1  
> 　幸福度: +5

## 使用方法

首先你需要1个Python3.7以上版本。

把这个仓库 `git clone` 回去，运行 `pip install -r requirements.txt`。

然后就可以import啦。

样例代码:

```python
import 龙
龙.龙('F:\\doc\\Paradox Interactive\\Crusader Kings III\\mod\\它的名字\\localization', 源语言='english', 目标语言='simp_chinese'))
```

## 接口

```python
def 龙(本地化文件夹路径: str, 源语言: str = 'english', 目标语言: str = 'simp_chinese'):
    ...
```

这个接口叫做龙，感觉很帅！其实是一条龙服务的意思。

`本地化文件夹路径` 就是mod的localization文件夹的路径啦。

`源语言` 和 `目标语言` 是字符串，不过我还没找到p社的语言代码和Google翻译的语言代码对应关系，所以这个接口只能翻译双向翻译英语和简体中文。

### 在后处理中替换文本

机器翻译经常会出现一些明显的错误，比如十字军之王的Court经常被翻译成「法庭」，但实际上是「宫廷」。

所以我提供了一个简单的设定，可以在后处理中替换文本。

要用的时候把全局变量替换掉。像是这样——

```python
import 龙
龙.替换 = {
    '法庭': '宫廷',
}
```

怪耶！

## 结束

就这样，大家88，我要回去玩十字军之王啦！