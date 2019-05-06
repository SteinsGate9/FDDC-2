#-*- coding: utf-8 -*-

import re


BlankCharSet = set([' ', '\n', '\t'])
CommaNumberPattern = re.compile(u'\d{1,3}([,，]\d\d\d)+')
CommaCharInNumberSet = set([',', '，'])
NumberSet = set(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.'])
# ChineseNumber = {ord("一"):ord("1"), ord("二"):ord("2"), ord("三"):ord("3"), ord("四"):ord("4"), ord("五"):ord("5"), ord("六"):ord("6"), ord("七"):ord("7"), \
#                     ord("八"):ord("8"), ord("九"):ord("9")}
# EnglishCapital = {i:i+32 for i in range(ord('A'), ord('Z') + 1)}

def clean_text(text):
    return _clean_number_in_text(_remove_blank_chars(_strQ2B(_remove_blank_chars(text))))

def _strQ2B(ustring):
    ss = []
    for s in ustring:
        rstring = ""
        for uchar in str(s):
            inside_code = ord(uchar)
            # if inside_code in EnglishCapital.keys():
            #     inside_code = EnglishCapital[inside_code]
            # if inside_code in ChineseNumber.keys():
            #     inside_code = ChineseNumber[inside_code]
            if inside_code == 12288:  # 全角空格直接转换
                inside_code = 32
            elif (inside_code >= 65281 and inside_code <= 65374):  # 全角字符（除空格）根据关系转化
                inside_code -= 65248
            rstring += chr(inside_code)
        ss.append(rstring)
    return ss

def _clean_number_in_text(text):
    comma_numbers = CommaNumberPattern.finditer(text)
    new_text, start = [], 0
    for comma_number in comma_numbers:
        new_text.append(text[start:comma_number.start()])
        start = comma_number.end()
        new_text.append(__remove_comma_in_number(comma_number.group()))
    new_text.append(text[start:])
    return ''.join(new_text)

def _remove_blank_chars(text):
    new_text = []
    if text is not None:
        for ch in text:
            if ch not in BlankCharSet:
                new_text.append(ch)
    return ''.join(new_text)

def __remove_comma_in_number(text):
    new_text = []
    if text is not None:
        for ch in text:
            if ch not in CommaCharInNumberSet:
                new_text.append(ch)
    return ''.join(new_text)





def normalize(content): #per 单位 日期
    content=clean_text(content)
    # print("       content",content)
    money = re.compile(r'\d[\.|\d]*[亿|万|千|百|惩]?[美|港|欧|新]?[元|股|英镑](人民币)?')
    content=money.sub(_normalize_num, content)
    money_big = re.compile(r'(?P<num>([壹|贰|叁|肆|伍|陆|柒|捌|玖|玫].{1,15}?))[美|港|欧|新]?(元)(人民币)?(整)?')
    content = money_big.sub(_normalize_num_big, content)
    date = re.compile(r'((\d{4})[年](?P<month>\d{1,2})[月](\d{1,2})日?)|((\d{4})[-](\d{1,2})[-](\d{1,2})日?)|((\d{4})[\.](\d{1,2})[\.](\d{1,2})日?)')
    content=date.sub(_normalize_date,content)
    per = re.compile(r'([\.|\d]+\%)')
    content=per.sub(_normalize_per,content)
    return content

def _normalize_num(text):
    text=text.group(0)
    # print("       num",text)
    coeff = 1.0
    if '亿' in text:
        coeff *= 100000000
    if '万' in text:
        coeff *= 10000
    if '惩' in text:
        coeff *= 100000000
    if '千' in text or '仟' in text:
        coeff *= 1000
    if '百' in text or '佰' in text:
        coeff *= 100
    if '%' in text:
        coeff *= 0.01
    try:
        number = float(__extract_number(text))
        number_text = '%.4f' % (number * coeff)
        if number_text.endswith('.0'):
            return number_text[:-2]
        elif number_text.endswith('.00'):
            return number_text[:-3]
        elif number_text.endswith('.000'):
            return number_text[:-4]
        elif number_text.endswith('.0000'):
            return number_text[:-5]
        else:
            if '.' in number_text:
                idx = len(number_text)
                while idx > 1 and number_text[idx-1] == '0':
                    idx -= 1
                number_text = number_text[:idx]
            return number_text
    except:
        return text

def __extract_number(text):
    new_text = []
    for ch in text:
        if ch in NumberSet:
            new_text.append(ch)
    return ''.join(new_text)

def extract_number(text):
    return __extract_number(text)

def remove_comma_in_number(text):
    return __remove_comma_in_number(text)

def _normalize_num_big(text):
    text = text.group("num")
    # print("       bnum", text)
    CN_NUM = {
        '〇': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '零': 0,
        '壹': 1, '贰': 2, '叁': 3, '肆': 4, '伍': 5, '陆': 6, '柒': 7, '捌': 8, '玖': 9, '貮': 2, '两': 2,
        "玫":9, '5':5
    }
    CN_UNIT = {
        '十': 10,
        '拾': 10,
        '百': 100,
        '佰': 100,
        '千': 1000,
        '惩': 1000,
        '仟': 1000,
        '万': 10000,
        '萬': 10000,
        '亿': 100000000,
        '億': 100000000,
        '兆': 1000000000000,
    }
    def chinese_to_arabic(cn: str) -> int:
        unit = 0  # current
        ldig = []  # digest
        for cndig in reversed(cn):
            if cndig in CN_UNIT:
                unit = CN_UNIT.get(cndig)
                if unit == 10000 or unit == 100000000:
                    ldig.append(unit)
                    unit = 1
            else:
                dig = CN_NUM.get(cndig)
                if unit:
                    dig *= unit
                    unit = 0
                ldig.append(dig)
        if unit == 10:
            ldig.append(10)
        val, tmp = 0, 0
        for x in reversed(ldig):
            if x == 10000 or x == 100000000:
                val += tmp * x
                tmp = 0
            else:
                tmp += x
        val += tmp
        return val
    try :
        return str(chinese_to_arabic(text))
    except:
        print("error",text)
        return ""

def _normalize_date(date):
    char='年月./'
    char2='日'
    month = date.group("month")
    date=date.group(0)
    # print("       date",date)
    for ch in date:
        if ch in char:
            date = date.replace(ch,'-')
        if ch in char2:
            date = date.replace(ch,"")
    if month and len(month)==1:
        date=list(date)
        date.insert(5, '0')
        date=''.join(date)
    return date

def _normalize_per(text):
    text=text.group(0)
    # print("       per", text)
    try:
        return str(float(text[:-1])/100)
    except:
        print('normalize_per:\t',text)
        return text



if __name__ == "__main__":
    text = "拟中标金额人民币壹亿叁仟零柒拾壹万壹仟肆佰壹拾柒元整"
    # print(normalize(text))

