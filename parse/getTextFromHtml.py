import os
import random
import re
import time

import bs4
import jieba
import tqdm
from bs4 import BeautifulSoup
from parse.text_utils import clean_text, normalize
from parse.parseFromHtml import Parser
jieba.initialize()


# def testTable(filename):
#     rule = re.compile(r'\s+')
#     with open(filename, 'r') as fr:
#         soup = BeautifulSoup(fr.read(), 'lxml')
#         text = ""
#         for child in soup.descendants:
#             if isinstance(child, bs4.element.Tag):
#                 print(child.name)
#             elif isinstance(child, bs4.NavigableString):
#                 print(child)

# def test():
#     filename = 'test.html'
#     with open(filename,'r') as fr:
#         soup = BeautifulSoup(fr.read(),'html.parser')
#         table = soup.find_all('table')
#         if table:
#             tr = soup.find_all('tr')
#             for r in tr:
#                 td = r.find_all('td')
#                 for d in td:
#                     print(text_utils.clean_text(text_utils.normalize(d.text)))


def getDingZeng_html(filename):
    with open(filename,'r',encoding='UTF-8') as fr:
        soup=BeautifulSoup(fr.read(),'html.parser')
        text=""

        #################
        cutPage=False
        hidden = soup.findAll('hidden')
        if len(hidden)>3:
            cutPage=True
            last_hidden = int(int(hidden[-1]['name'][1:])*0.6)
        #################

        for child in soup.descendants:
            sentence=""

            #################
            if cutPage and child.name=='hidden' and int(child['name'][1:])>=last_hidden:
                print('break in\t',child['name'],'\tall\t',hidden[-1]['name'])
                break
            #################

            if child.name=='tr' or child.name=='td':
                if not text[-1] in CommaCharInNumberSet1:
                    sentence+=','
            if child.name == 'img':
                continue
            if isinstance(child,bs4.element.Tag) and child.attrs.get('title'):
                if 'title' in child.attrs:
                    sentence= clean_text(normalize(child['title']))
                    if not sentence.endswith(':'):
                        sentence+=':'
            elif isinstance(child,bs4.NavigableString) and len(child.string)>2:
                sentence= clean_text(normalize(child.string))
            text+=sentence
        return text

def getContentFromEveryDiv(filepath):
    with open(filepath,'r',encoding="UTF-8") as fr:
        soup=BeautifulSoup(fr.read(),'html.parser')
        text=""
        print(filepath)
        for child in soup.descendants:
            sentence=""
            if child.name=='tr' or child.name=='td':
                if not text[-1] in CommaCharInNumberSet1:
                    sentence+=','
            if isinstance(child,bs4.element.Tag) and child.attrs.get('title'):
                if 'title' in child.attrs:
                    sentence= clean_text(normalize(child['title']))
                    print("end", sentence)
                    if not sentence.endswith(':'):
                        sentence+=':'
            elif isinstance(child,bs4.NavigableString) and len(child.string)>2:
                sentence= clean_text(normalize(child.string))
                print("end",sentence)

            text+=sentence
        return text


def getContentWithoutTable(filename):
    res_text = ""
    filename=os.path.join(dirname,filename)
    with open(filename, 'r', encoding="UTF-8") as fr:
        html = BeautifulSoup(fr.read(), 'lxml')
        for div in html.select('div[type="content"]'):
            if isinstance(div.string, str):
                res_text+=(re.sub(re_replace_blank, '', div.string))
    return res_text


import threading
from main import FLAGS
def train_fasttext():
    # if FLAGS.resource.task == 'dingzeng':
    #     output = '../utils/dingzeng.true_false'
    #     output2 = '../utils/dingzeng.true'
    #     train = FLAGS.resource.train_dir+"/dingzeng_train.csv"
    #     dirname = FLAGS.resource.html_dir

    if FLAGS.resource.task == "hetong":
        output = '../utils/hetong.true_false'
        output2 = '../utils/hetong.true'
        train = FLAGS.resource.train_dir+"/hetong_train.csv"
        dirname = FLAGS.resource.text_dir

    res = {}
    global contents
    contents = []

    with open(train, 'r', encoding="UTF-8") as trainFr:
        trains = trainFr.readlines()
        for train in trains:
            train = train.split(',')
            res[train[0]] = train[1:]

    from tqdm import tqdm
    for root,dir,files in os.walk(dirname):
        for file in tqdm(files):
            t = threading.Thread(_getDataFromParserThread(dirname,file,res),name='file:'+file)
            t.start()
            t.join()
    if FLAGS.resource.task == "hetong":
        trueContent = [i for i in contents if i.endswith('\t__label__hetong\n')]
    elif FLAGS.resource.task == "dingzeng":
        trueContent = [i for i in contents if i.endswith('\t__label__dingzeng\n')]
    with open(output, 'w', encoding="UTF-8") as fw:
        fw.writelines(trueContent)
    falseContent = [i for i in contents if i.endswith('\t__label__useless\n')]
    random.shuffle(falseContent)
    trueContent.extend(falseContent)#[:len(trueContent)]
    random.shuffle(trueContent)
    with open(output2, 'w', encoding="UTF-8") as fw:
        fw.writelines(trueContent)

def _getDataFromParserThread(filename, file, res):
    start = time.time()
    sum = 0
    with open(os.path.join(filename, file), encoding="UTF-8",mode="r") as f:
        result = f.read()
    sentences = result.split('。')
    savename = file.split('.')[0]
    for sentence in sentences:
        if sentence == "":
            continue
        label = 0
        sum += 1
        if savename in res.keys():
            field = res.get(savename)

            ######## hetong_true_false
            if FLAGS.resource.task == "hetong":
                for v in field[1:]:
                    if len(v) > 1 and field[1] in sentence and v in sentence:
                        print('-' * 10,v)
                        label = 1
                        break

            ######## dingzeng_true
            # if FLAGS.task == "dingzeng":
            #     if field[0] in sentence and (len(field[4])>1 and field[4] in sentence or len(field[5])>1 and field[5] in sentence): # 兩個主鍵
            #         print('-' * 10, sentence.find(field[0]), sentence.find(field[4]), len(sentence))
            #         label = 1

        seg = jieba.cut(sentence)
        res_sentence = " ".join(seg)
        res_sentence = " ".join(res_sentence.split())
        if FLAGS.resource.task == "hetong":
            res_sentence += '\t__label__hetong\n' if label else '\t__label__useless\n'
        else:
            res_sentence += '\t__label__dingzeng\n' if label else '\t__label__useless\n'
        contents.append(res_sentence)
    print(file, ' spend ', time.time() - start, '!' * 10)



def getFasttextData():
    dirname = '../FDDC/dingzeng/html'
    output = '../FDDC/dingzeng/result/fasttext.train'
    res={}
    contents=[]
    sum=0

    with open(os.path.join(dirname,'dingzeng.train'),'r') as trainFr:
        trains=trainFr.readlines()
        for train in trains:
            train=train.split('\t')
            res[train[0]]=train[1:]

    for root,dir,files in os.walk(os.path.join(dirname,'data')):
        for file in tqdm.tqdm(files):
            with open(os.path.join(dirname,'data',file),'r') as fr:
                text=fr.read()
                sentences=text.split('。')
                filename=file.split('.')[0]
                for sentence in sentences:
                    if sentence=="":
                        continue
                    label=0
                    sum+=1
                    if filename in res.keys():
                        field = res.get(filename)
                        for v in field[1:]:
                            if len(v)>1 and field[0] in sentence and v in sentence:
                                print('-'*10,v,sentence.find(field[0]),sentence.find(v),len(sentence))
                                label=1
                                break

                    seg=jieba.cut(sentence)
                    res_sentence=" ".join(seg)
                    res_sentence=" ".join(res_sentence.split())
                    res_sentence += '\t__label__dingzeng\n' if label else '\t__label__useless\n'
                    contents.append(res_sentence)
    trueContent = [i for i in contents if i.endswith('\t__label__dingzeng\n')]
    falseContent=[i for i in contents if i.endswith('\t__label__useless\n')]
    random.shuffle(falseContent)
    trueContent.extend(falseContent)#[:len(trueContent)]
    random.shuffle(trueContent)
    with open(os.path.join(dirname,output),'w') as fw:
        fw.writelines(trueContent)

if __name__ == '__main__':
    # getContentFromEveryDiv("../../FDDC/dingzeng/html/7880.html")
    # print(getDingZeng_html('../data/text_data/test/6927.html'))
    # getDataFromParser()
    train_fasttext()



