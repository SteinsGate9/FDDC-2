#-*- coding: utf-8 -*-

import codecs
import json
import re

from parse.parseFromHtml import Parser
from parse.text_utils import remove_comma_in_number, extract_number
from ner import NERTagger
from tqdm import tqdm
import os
import pandas as pd
from main import FLAGS
from parse.text_utils import normalize
class ZengJianChiRecord(object):
    def __init__(self, shareholderFullName, shareholderShortName, finishDate, sharePrice, shareNum, shareNumAfterChg, sharePcntAfterChg):
        # 股东
        self.shareholderFullName = shareholderFullName
        # 股东
        self.shareholderShortName = shareholderShortName
        # 结束日期
        self.finishDate = finishDate
        # 增减持股价
        self.sharePrice = sharePrice
        # 增减持股数
        self.shareNum = shareNum
        # 增减持变动后股数
        self.shareNumAfterChg = shareNumAfterChg
        # 增减持变动后持股比例
        self.sharePcntAfterChg = sharePcntAfterChg

    def __str__(self):
        return json.dumps(self.__dict__, ensure_ascii=False)

    def __normalize_finish_date(self, text):
        pattern = re.compile('(\d\d\d\d)[-.年](\d{1,2})[-.月](\d{1,2})日?')
        match = pattern.search(text)
        if match:
            if len(match.groups()) == 3:
                year = int(match.groups()[0])
                month = int(match.groups()[1])
                day = int(match.groups()[2])
                return '%d-%02d-%02d' % (year, month, day)
        return text

    def __normalize_num(self, text):
        if text in ["","其中:","非公开发行","股份","股份有限公司",""]:
            return None
        coeff = 1.0
        if '亿' in text:
            coeff *= 100000000
        if '万' in text:
            coeff *= 10000
        if '千' in text or '仟' in text:
            coeff *= 1000
        if '百' in text or '佰' in text:
            coeff *= 100
        if '%' in text:
            coeff *= 0.01
        try:
            number = float(extract_number(text))
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


    def _normalize(self):
        if self.finishDate is not None:
            self.finishDate = self.__normalize_finish_date(self.finishDate)
        if self.shareNum is not None:
            self.shareNum = self.__normalize_num(self.shareNum)
        if self.shareNumAfterChg is not None:
            self.shareNumAfterChg = self.__normalize_num(self.shareNumAfterChg)
        if self.sharePcntAfterChg is not None:
            self.sharePcntAfterChg = self.__normalize_num(self.sharePcntAfterChg)

    def to_result(self):
        self._normalize()
        return "%s\t%s\t%s\t%s\t%s\t%s\t%s" % (
        # return "%s(full)\t%s(short)\t%s(date)\t%s(price)\t%s(num)\t%s(numAfter)\t%s(pcntAfter)" % (
            self.shareholderFullName if self.shareholderFullName is not None else '',
            self.shareholderShortName if self.shareholderShortName is not None else '',
            self.finishDate if self.finishDate is not None else '',
            self.sharePrice if self.sharePrice is not None else '',
            self.shareNum if self.shareNum is not None else '',
            self.shareNumAfterChg if self.shareNumAfterChg is not None else '',
            self.sharePcntAfterChg if self.sharePcntAfterChg is not None else '')


class ZengJianChiExtractor(object):

    def __init__(self, ner_model_dir_path, ner_blacklist_file_path):
        self.html_parser = Parser()
        self.config = None
        self.ner_tagger = NERTagger.NERTagger(ner_model_dir_path, ner_blacklist_file_path)
        self.com_abbr_dict = {}
        self.com_full_dict = {}
        self.com_abbr_ner_dict = {}

        with codecs.open(FLAGS.resource.config_file, encoding='utf-8', mode='r') as fp:
            self.config = json.loads(fp.read())
        self.table_dict_field_pattern_dict = {}
        for table_dict_field in self.config['table_dict']['fields']:
            field_name = table_dict_field['fieldName']
            if field_name is None:
                continue
            convert_method = table_dict_field['convertMethod']
            if convert_method is None:
                continue
            pattern = table_dict_field['pattern']
            if pattern is None:
                continue
            col_skip_pattern = None
            if 'colSkipPattern' in table_dict_field:
                col_skip_pattern = table_dict_field['colSkipPattern']
            row_skip_pattern = None
            if 'rowSkipPattern' in table_dict_field:
                row_skip_pattern = table_dict_field['rowSkipPattern']
            self.table_dict_field_pattern_dict[field_name] = \
                TableDictFieldPattern(field_name=field_name, convert_method=convert_method,
                                      pattern=pattern, col_skip_pattern=col_skip_pattern,
                                      row_skip_pattern=row_skip_pattern)

    def extract_from_html_dir(self, html_dir_path):
        map = {"公告id": [], "股东全称": [], "股东简称": [], "变动截止日期": [], "变动价格": [], "变动数量": [], "变动后持股数": [], "变动后持股比例": []}
        for html_id in tqdm(os.listdir(html_dir_path)):
            self._extract_from_html_dir(html_dir_path, html_id, map)
        dataframe = pd.DataFrame(data=map,
                                 columns=["公告id", "股东全称", "股东简称", "变动截止日期", "变动价格", "变动数量", "变动后持股数", "变动后持股比例"],
                                 dtype=None, copy=False)
        if os.path.exists('zjc_result.csv'):
            os.remove('zjc_result.csv')
        dataframe.to_csv("zjc_result.csv", encoding="utf_8_sig")

    def _extract_from_html_dir(self, html_dir_path, html_id, map):
        record_list = []
        for record in self.extract(os.path.join(html_dir_path, html_id)):
            if record is not None and \
                            record.shareholderFullName is not None and \
                            len(record.shareholderFullName) > 1 and \
                            record.finishDate is not None and \
                            len(record.finishDate) >= 6 and\
                            record.shareholderFullName not in ["股东名称","董事、监事、高级管理人员本次增持情况","久立集团增持前后持股明细","久立集团以及董事、监事、高级管理人员本次增持总体情况"]:
                record_list.append("%s\t%s" % (html_id[:-5], record.to_result()))

        for record in record_list:
            records = record.split('\t')
            map['公告id'].append(records[0])
            map['股东全称'].append(records[1])
            map['股东简称'].append(records[2])
            map['变动截止日期'].append(records[3])
            map['变动价格'].append(records[4])
            map['变动数量'].append(records[5])
            map['变动后持股数'].append(records[6])
            map['变动后持股比例'].append(records[7])
        return record_list

    def extract(self, html_file_path):
        # 1. 解析 Table Dict
        rs = []
        paragraphs = self.html_parser.parse_content(html_file_path)
        rs_paragraphs = self._extract_from_paragraphs(paragraphs)
        for table_dict in self.html_parser.parse_table(html_file_path):
            rs_table = self._extract_from_table_dict(table_dict)
            if len(rs_table) > 0:
                if len(rs) > 0:
                    self.__mergeRecord(rs, rs_table)
                    break
                else:
                    rs.extend(rs_table)
        # 2. 如果没有 Table Dict 则解析文本部分
        if len(rs) <= 0:
            return rs_paragraphs
        else:
            for record in rs:
                full_company_name, abbr_company_name = self.getShareholder(record.shareholderFullName)
                if full_company_name is not None and len(full_company_name) > 0 \
                        and abbr_company_name is not None and len(abbr_company_name) > 0:
                    record.shareholderFullName = full_company_name
                    record.shareholderShortName = abbr_company_name
                else:
                    record.shareholderShortName = record.shareholderFullName
        return rs

    def _extract_from_table_dict(self, table_dict):
        # print(table_dict)
        rs = []
        if table_dict is None or len(table_dict) <= 0:
            return rs
        row_length = len(table_dict)
        field_col_dict = {}
        skip_row_set = set()
        # 1. 假定第一行是表头部分则尝试进行规则匹配这一列是哪个类型的字段
        # 必须满足 is_match_pattern is True and is_match_col_skip_pattern is False
        head_row = table_dict[0]
        col_length = len(head_row)
        danwei = {'sharePrice': '', 'shareNum': ''}
        for i in range(col_length):
            text = head_row[i]
            for (field_name, table_dict_field_pattern) in self.table_dict_field_pattern_dict.items():
                col_good, _danwei = table_dict_field_pattern.is_match_pattern(text)
                if col_good and not table_dict_field_pattern.is_match_col_skip_pattern(text):
                    if field_name not in field_col_dict:
                        field_col_dict[field_name] = i
                    if field_name in ["sharePrice","shareNum"]:
                        danwei[field_name] = _danwei if _danwei else ""
                        if _danwei is not None:
                            print(field_name, _danwei)
                    for j in range(1, row_length):
                        try:
                            text = table_dict[j][i]
                            if table_dict_field_pattern.is_match_row_skip_pattern(text):
                                skip_row_set.add(j)
                        except KeyError:
                            pass
        if len(field_col_dict) <= 0:
            return rs
        # 2. 遍历每个有效行，获取 record
        for row_index in range(1, row_length):
            if row_index in skip_row_set:
                continue
            record = ZengJianChiRecord(None, None, None, None, None, None, None)
            for (field_name, col_index) in field_col_dict.items():
                try:
                    text = table_dict[row_index][col_index]
                    if field_name == 'shareholderFullName':
                        record.shareholderFullName = self.table_dict_field_pattern_dict.get(field_name).convert(text)
                    elif field_name == 'finishDate':
                        record.finishDate = self.table_dict_field_pattern_dict.get(field_name).convert(text)
                    elif field_name == 'sharePrice':
                        record.sharePrice = self.table_dict_field_pattern_dict.get(field_name).convert(normalize(text+danwei["sharePrice"]+"元"))
                    elif field_name == 'shareNum':
                        record.shareNum = self.table_dict_field_pattern_dict.get(field_name).convert(normalize(text+danwei["shareNum"]+"股"))
                    elif field_name == 'shareNumAfterChg':
                        record.shareNumAfterChg = self.table_dict_field_pattern_dict.get(field_name).convert(text)
                    elif field_name == 'sharePcntAfterChg':
                        record.sharePcntAfterChg = self.table_dict_field_pattern_dict.get(field_name).convert(text)
                    else:
                        pass
                except KeyError:
                    pass
            rs.append(record)
        return rs


    def _extract_from_paragraphs(self, paragraphs):
        self.clearComAbbrDict()
        change_records = []
        change_after_records = []
        record_list = []
        for para in paragraphs:
            change_records_para, change_after_records_para = self.__extract_from_paragraph(para)
            change_records += change_records_para
            change_after_records += change_after_records_para
        self.__mergeRecord(change_records, change_after_records)
        for record in change_records:
            record_list.append(record)
        return record_list


    def __extract_from_paragraph(self, paragraph):
        # lalal
        tag_res = self.ner_tagger.ner(paragraph, self.com_abbr_ner_dict)
        tagged_str = tag_res.get_tagged_str()
        if self.___extract_company_name(tagged_str) > 0:
            tag_res = self.ner_tagger.ner(paragraph, self.com_abbr_ner_dict)
            tagged_str = tag_res.get_tagged_str()

        # extract
        change_records = self.___extract_change(tagged_str)
        change_after_records = self.___extract_change_after(tagged_str)
        return change_records, change_after_records

    def ___extract_company_name(self, paragraph):
        # print(paragraph)
        targets = re.finditer(r"<org>(?P<com>.{1,28}?)</org>[(（].{0,5}?简称:?[\"“](?P<com_abbr>.{2,6}?)[\"”][)）]", paragraph)
        size_before = len(self.com_abbr_ner_dict)
        for target in targets:
            com_abbr = target.group("com_abbr")
            com_name = target.group("com")
            if com_abbr != None and com_name != None:
                self.com_abbr_dict[com_abbr] = com_name
                self.com_full_dict[com_name] = com_abbr
                self.com_abbr_ner_dict[com_abbr] = "Ni"
        return len(self.com_abbr_ner_dict) - size_before


    def ___extract_change(self, paragraph):
        records = []
        targets = re.finditer(r"(出售|减持|增持|买入)了?[^，。,:;!?？]*?(股票|股份).{0,30}?<num>(?P<share_num>.{1,20}?)</num>股", paragraph)
        for target in targets:
            share_num = target.group("share_num")
            start_pos = target.start()
            end_pos = target.end()
            #查找公司
            pat_com = re.compile(r"<org>(.*?)</org>")
            m_com = pat_com.findall(paragraph,0,end_pos)
            shareholder = ""
            if m_com != None and len(m_com) > 0:
                shareholder = m_com[-1]
            else :
                pat_person = re.compile(r"<person>(.*?)</person>")
                m_person = pat_person.findall(paragraph,0,end_pos)
                if m_person != None and len(m_person) > 0 :
                    shareholder = m_person[-1]
            #查找日期
            pat_date = re.compile(r"<date>(.*?)</date>")
            m_date = pat_date.findall(paragraph,0,end_pos)
            change_date = ""
            if m_date != None and len(m_date)>0:
                change_date = m_date[-1]
            #查找变动价格
            pat_price = re.compile(r"(均价|平均(增持|减持|成交)?(价格|股价))(:|：)?<num>(?P<share_price>.*?)</num>")
            m_price = pat_price.search(paragraph,start_pos)
            share_price = ""
            if m_price != None:
                share_price = m_price.group("share_price")
            if shareholder == None or len(shareholder) == 0:
                continue
            full_name,short_name = self.getShareholder(shareholder)
            records.append(ZengJianChiRecord(full_name, short_name, change_date, share_price, share_num,"", ""))
        return records


    def ___extract_change_after(self, paragraph):
        records = []
        targets = re.finditer(r"(增持后|减持后|变动后).{0,30}?持有.{0,30}?<num>(?P<share_num_after>.*?)</num>(股|万股|百万股|亿股)", paragraph)
        for target in targets:
            share_num_after = target.group("share_num_after")
            start_pos = target.start()
            end_pos = target.end()
            #查找公司
            pat_com = re.compile(r"<org>(.*?)</org>")
            m_com = pat_com.findall(paragraph,0,end_pos)
            shareholder = ""
            if m_com != None and len(m_com) > 0:
                shareholder = m_com[-1]
            else :
                pat_person = re.compile(r"<person>(.*?)</person>")
                m_person = pat_person.findall(paragraph,0,end_pos)
                if m_person != None and len(m_person) > 0:
                    shareholder = m_person[-1]
            #查找变动后持股比例
            pat_percent_after = re.compile(r"<percent>(?P<share_percent>.*?)</percent>")
            m_percent_after = pat_percent_after.search(paragraph,start_pos)
            share_percent_after = ""
            if m_percent_after != None:
                share_percent_after = m_percent_after.group("share_percent")
            if shareholder == None or len(shareholder) == 0:
                continue
            full_name,short_name = self.getShareholder(shareholder)
            records.append(ZengJianChiRecord(full_name,short_name, "", "", "", share_num_after, share_percent_after))
        return records

    def __mergeRecord(self, changeRecords, changeAfterRecords):
        if len(changeRecords) == 0 or len(changeAfterRecords) == 0:
            return
        last_record = None
        for record in changeRecords:
            if last_record != None and record.shareholderFullName != last_record.shareholderFullName:
                self.___mergeChangeAfterInfo(last_record,changeAfterRecords)
            last_record = record
        self.___mergeChangeAfterInfo(last_record,changeAfterRecords)

    def ___mergeChangeAfterInfo(self, changeRecord, changeAfterRecords):
        for record in changeAfterRecords:
            if record.shareholderFullName == changeRecord.shareholderFullName:
                changeRecord.shareNumAfterChg = record.shareNumAfterChg
                changeRecord.sharePcntAfterChg = record.sharePcntAfterChg

    def clearComAbbrDict(self):
        self.com_abbr_dict = {}
        self.com_full_dict = {}
        self.com_abbr_ner_dict = {}

    def getShareholder(self, shareholder):
        #归一化公司全称简称
        if shareholder in self.com_full_dict:
            return shareholder, self.com_full_dict.get(shareholder, "")
        if shareholder in self.com_abbr_dict:
            return self.com_abbr_dict.get(shareholder, ""),shareholder
        #股东为自然人时不需要简称
        return shareholder, ""




class TableDictFieldPattern(object):
    def __init__(self, field_name, convert_method, pattern, col_skip_pattern, row_skip_pattern):
        self.field_name = field_name
        self.convert_method = convert_method
        self.pattern = None
        if pattern is not None and len(pattern) > 0:
            self.pattern = re.compile(pattern)
        self.col_skip_pattern = None
        if col_skip_pattern is not None and len(col_skip_pattern) > 0:
            self.col_skip_pattern = re.compile(col_skip_pattern)
        self.row_skip_pattern = None
        if row_skip_pattern is not None and len(row_skip_pattern) > 0:
            self.row_skip_pattern = re.compile(row_skip_pattern)
        self.danwei_pattern = re.compile(r"\(((?P<danwei>[万|千]?)[美元|股|元|元\/股].{1,3}?)|(?P<danwei2>\%)\)")

    def is_match_pattern(self, text):
        if self.pattern is None:
            return False
        match = self.pattern.search(text)
        danwei = self.danwei_pattern.search(text)
        return ((True, (danwei.group("danwei") or danwei.group("danwei2"))) if danwei else (True, '')) if match else (
        False, None)  # 没找到="",没找到2=None

    def is_match_col_skip_pattern(self, text):
        if self.col_skip_pattern is None:
            return False
        match = self.col_skip_pattern.search(text)
        return True if match else False

    def is_match_row_skip_pattern(self, text):
        if self.row_skip_pattern is None:
            return False
        match = self.row_skip_pattern.search(text)
        return True if match else False

    def get_field_name(self):
        return self.field_name

    def convert(self, text):
        if self.convert_method is None:
            return self.default_convert(text)
        elif self.convert_method == 'getStringFromText':
            return self.getStringFromText(text)
        elif self.convert_method == 'getDateFromText':
            return self.getDateFromText(text)
        elif self.convert_method == 'getLongFromText':
            return self.getLongFromText(text)
        elif self.convert_method == 'getDecimalFromText':
            return self.getDecimalFromText(text)
        elif self.convert_method == 'getDecimalRangeFromTableText':
            return self.getDecimalRangeFromTableText(text)
        else:
            return self.default_convert(text)

    @staticmethod
    def default_convert(text):
        return text

    @staticmethod
    def getStringFromText(text):
        return text

    @staticmethod
    def getDateFromText(text):
        strList = text.split("至")
        if len(strList) < 2 and ("月" in text or "年" in text or "/" in text or "." in text):
            strList = re.split("-|—|~", text)
        return strList[-1]

    @staticmethod
    def getLongFromText(text):
        return remove_comma_in_number(text)

    @staticmethod
    def getDecimalFromText(text):
        return text

    @staticmethod
    def getDecimalRangeFromTableText(text):
        return text

