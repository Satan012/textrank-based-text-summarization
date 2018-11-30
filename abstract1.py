# coding=utf-8
import re

import time
from textrank4zh import TextRank4Sentence


def countChineseWords(text):
    regex = '[^。，、＇：∶；?‘’“”〝〞ˆˇ﹕︰﹔﹖﹑·¨….¸;！´？！～—ˉ｜‖＂〃｀@﹫¡¿﹏﹋﹌︴々﹟#﹩$﹠&﹪%*﹡﹢﹦﹤‐￣¯―﹨ˆ˜﹍﹎+=<­­＿_-\ˇ~﹉﹊（）〈〉‹›﹛﹜『』〖〗［］《》〔〕{' \
            '}「」【】︵︷︿︹︽_﹁﹃︻︶︸﹀︺︾ˉ﹂﹄︼; a-zA-Z]'
    length = len(re.findall(regex, text))
    return length


def countArticleLen(text):
    s = ''
    for t in text:
        t = t.split('\n')[0].strip()
        s += t
    return countChineseWords(s)


def splitPart(text, step):  # 增加顺序重置
    text = text.strip()
    pattern1 = '[。；！～]'
    sentences = re.split(pattern1, text)
    head = sentences[0] + '。'
    middle = '。'.join(sentences[1:-2])
    last = '。'.join(sentences[-2:])
    middle = middle.split('。')
    middles = []
    start = 0
    for i in range(len(middle) // step):
        middles.append('。'.join(middle[start: start + step]) + '。')
        start = start + step
    if start < len(middle):
        middles.append('。'.join(middle[start:]) + '。')
    return head, middles, last


def extractShort(lst, tr4s):
    r = []
    for l in lst:
        l = l['sentence'].replace('，', '。') + '。'
        tr4s.analyze(l, lower=True, source='no_filter', pagerank_config={'alpha': 0.85, })
        tmp = tr4s.get_key_sentences(num=3)
        tmp1 = []
        flag = False
        for t in tmp:
            if t['index'] == 0:
                flag = True
            if t['weight'] == 1 / len(l):  # 均等概率，全部保留
                tmp1.append(l.replace('。', '，')[:-1])  # 因为末尾多一个逗号，因此需要去除最后的逗号
                break
            else:
                tmp1.append(t['sentence'])
        if not flag:
            tmp1 = [l.split('。')[0]] + tmp1
        r.append('，'.join(tmp1))

    return r


def splitAllSentence(text, flag):
    # print(type(text))
    if flag:
        lst = re.split('[，。；！～;]', text)
        # print(lst)
        # exit(0)
    else:
        lst = re.split('[。；！～;]', text)
    result = []
    register = {}
    for l in lst:
        if l != '':
            if register.__contains__(l):
                index = text.find(l, register[l] + 1)
            else:
                index = text.find(l)
                while index != 0 and (
                        text[index - 1] != '，' and text[index - 1] != '。' and text[index - 1] != '；' and text[
                    index - 1] != '！' and text[index - 1] != '～' and text[index - 1] != ';'):
                    index = text.find(l, index + 1)
                register[l] = index
            result.append({'sentence': l, 'index': index})
    result = sorted(result, key=lambda x: x['index'])
    # print('result:', result)
    return result


def keepOrder(lst, result):
    lst = splitAllSentence(lst, True)
    lst = [s['sentence'] for s in lst]

    tmp = []
    for l in lst:
        if len(l) > 0:
            tmp.append(l)
    lst = tmp
    idxs = []
    result = result.split('，')
    register = []
    for idx, s in enumerate(lst):
        if s in result:
            if not register.__contains__(s):
                idxs.append(idx)
                register.append(s)

    if len(idxs) > 0:
        if max(idxs) - min(idxs) + 1 < 4:  # 若摘出的句子跨度太长，则没必要加上中间的句子进行过渡，否则添加中间句子增强语意连贯性
            tmp = lst[idxs[0]:idxs[-1] + 1]
        else:
            tmp = []
            for i in idxs:
                tmp.append(lst[i])
        return tmp


def keepWholeSentenceOrder(text, result):
    splited = splitAllSentence(text, False)
    splitedLst = [s['sentence'] for s in splited]
    result = [r['sentence'] for r in result]
    ordered = [{'sentence': sent} for sent in splitedLst if sent in result]
    return ordered


def mergeAbstract(tr4s, text, head, middles, last):
    result = ''
    # 开头
    tr4s.analyze(head, lower=True, source='no_filter', pagerank_config={'alpha': 0.85, })
    head_result = tr4s.get_key_sentences(num=1)
    # result += extractShort(head_result, tr4s)
    result += ('，'.join(keepOrder(head_result[0]['sentence'], extractShort(head_result, tr4s)[0])) + '。')
    # 中部
    for m in middles:
        tr4s.analyze(m, lower=True, source='no_filter', pagerank_config={'alpha': 0.85, })
        middle_result = tr4s.get_key_sentences(num=1)
        # result += extractShort(middle_result, tr4s)
        result += ('，'.join(keepOrder(middle_result[0]['sentence'], extractShort(middle_result, tr4s)[0])) + '。')
    # 尾部
    tr4s.analyze(last, lower=True, source='no_filter', pagerank_config={'alpha': 0.85, })
    last_result = tr4s.get_key_sentences(num=2)
    last_result = keepWholeSentenceOrder(last, last_result)
    # result += extractShort(last_result, tr4s)
    # result += keepOrder(last_result, extractShort(last_result, tr4s))
    for i in range(len(last_result)):
        result += ('，'.join(keepOrder(last_result[i]['sentence'], extractShort(last_result, tr4s)[i])) + '。')
    final = result
    # result += keepOrder(last_result[0]['sentence'], extractShort(last_result, tr4s)[0])
    # print('result:', result)
    # final = ''
    # for r in result:
    #     tmp = keepOrder(text, r)
    #     try:
    #         tmp = '，'.join(tmp) + '。'
    #         final += tmp
    #     except BaseException:
    #         pass
    return 0, result


def paragramAbstarct(tr4s, text):
    result = []
    linked = ''.join(text)
    for t in text:
        t = t.strip()
        t = t.replace('……', '，')
        t = [splitAllSentence(t, False)[0]]
        tmp = extractShort(t, tr4s)
        for tt in tmp:
            # print('t:', t)
            if keepOrder(linked, tt) is not None:
                keep = '，'.join(keepOrder(linked, tt))
                # print('keep:', keep)
                result.append(keep)
    result = '。'.join(result)
    return 1, result


def judge(text):
    if len(text) < 3:
        return False
    else:
        lenCount = 0
        for t in text[1:-1]:  # 查看中间段落
            tmp = re.split('[。；！～;]', t)
            if len(tmp) >= 3:
                lenCount += 1
        if lenCount / len(text) >= 0.5:
            return True  # 如果中间部分的段落的长度超过一半不短于三句话，进入分段式
        else:
            return False


def abstract(fileName, step):
    tr4s = TextRank4Sentence()
    f = open(fileName, 'r')
    text = f.readlines()
    articleLen = countArticleLen(text)
    text = [t.split('\n')[0].strip() for t in text]
    if not judge(text):  # 如果judge返回False则进入合并方法
        text = ''.join(text)
        text = text.replace('……', '，')
        head, middles, last = splitPart(text, step)
        cate, result = mergeAbstract(tr4s, text, head, middles, last)
    else:
        cate, result = paragramAbstarct(tr4s, text)
    return cate, result, articleLen


def finalProcess(ab):  # 去除括号，默认括号成对出现，存在一定问题
    while '(' in ab:
        index1 = ab.find('(')
        index2 = ab.find(')')
        ab = ab.replace(ab[index1: index2 + 1], '')
    while '（' in ab:
        index1 = ab.find('（')
        index2 = ab.find('）')
        ab = ab.replace(ab[index1: index2 + 1], '')
    return ab

def show(text):
    f = open('show.txt', 'w')
    f.write(text)
    f.close()
    # fileName = 'test.txt'
    fileName = 'show.txt'
    step = 5
    length = 200
    result = ''
    flag = 0
    _, _, articleLen = abstract(fileName, 1)
    while length > 120:
        cate, result, _ = abstract(fileName, step)
        if cate == 0:  # merge
            tmp = countChineseWords(result)
            if tmp != length:
                length = tmp
                flag = 0
            else:
                flag += 1
            step += 1
            if flag == 15:
                break
        else:
            # print('进入')
            tmp = countArticleLen(result)
            if tmp > 120:
                tmpFile = open('tmpFile.txt', 'w')
                tmpFile.write(result)
                tmpFile.close()
                fileName = 'tmpFile.txt'
            else:
                length = tmp
    end = time.time()
    result = finalProcess(result)
    return result + '\n(' + str(articleLen) + '-->' + str(length) + ')'


if __name__ == '__main__':
    start = time.time()
    preFix = 'data/'
    name = 'test.txt'
    fileName = preFix + name
    step = 5
    length = 200
    result = ''
    flag = 0
    _, _, articleLen = abstract(fileName, 1)
    while length > 120:
        cate, result, _ = abstract(fileName, step)
        if cate == 0:  # merge
            tmp = countChineseWords(result)
            if tmp != length:
                length = tmp
                flag = 0
            else:
                flag += 1
            step += 1
            if flag == 15:
                break
        else:
            # print('进入')
            tmp = countArticleLen(result)
            if tmp > 120:
                tmpFile = open('tmpFile.txt', 'w')
                tmpFile.write(result)
                tmpFile.close()
                fileName = 'tmpFile.txt'
            else:
                length = tmp
    end = time.time()
    result = finalProcess(result)
    print('result:', cate, length, articleLen, result)  # 0代表merge方法，1代表paragram方法
    runTime = end - start
    print('%5.3fs' % runTime)
