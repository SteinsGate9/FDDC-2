from tqdm import tqdm
import os
import pandas as pd

# def extract_hetong_from_html_dir(dz_ex, html_dir_path):
#     map = {"公告id": [], "增发对象": [], "增发数量": [], "增发金额": [], "锁定期": [], "认购方式": []}
#
#     for html_id in tqdm(os.listdir(html_dir_path)):
#         _extract_hetong(dz_ex, html_dir_path, html_id, map)
#
#     dataframe = pd.DataFrame(data=map, columns=["公告id", "增发对象", "增发数量", "增发金额", "锁定期", "认购方式"], dtype=None, copy=False)
#     if os.path.exists('data/dz_result.csv'):
#         os.remove('data/dz_result.csv')
#     dataframe.to_csv("data/dz_result.csv", encoding="utf_8_sig")
#
#
# def _extract_hetong(dz_ex, html_dir_path, html_id, map):
#     record_list = []
#     for record in dz_ex.extract(os.path.join(html_dir_path, html_id)):
#         if record is not None and \
#                         record.name is not None and \
#                         len(record.name) > 1:
#             record_list.append("%s\t%s" % (html_id[:-5], record.to_result()))
#
#     for record in record_list:
#         records = record.split('\t')
#         map['公告id'].append(records[0])
#         map['增发对象'].append(records[1])
#         map['增发数量'].append(records[2])
#         map['增发金额'].append(records[3])
#         map['锁定期'].append(records[4])
#         map['认购方式'].append(records[5])
#     return record_list

#-*- coding: utf-8 -*-

import codecs
import json
import re

from parse.parseFromHtml import Parser
from parse import text_utils
from parse.text_utils import normalize
from main import FLAGS
from work.evaluate import return_html_entity

class HeTongRecord(object):
    def __init__(self, name=None, jiafang=None, yifang=None, hetong=None, xiangmu=None, shangxian=None, xiaxian=None, lianheti=None, danwei=None):
        self.name = name  # string
        # 股东
        self.jiafang = jiafang #string
        # 数量
        self.yifang = yifang #string
        # 钱
        self.hetong = hetong #string
        # 月份
        self.xiangmu = xiangmu #string
        # 现金？
        self.shangxian = shangxian #string
        # 现金？
        self.xiaxian = xiaxian  # string
        # 现金？
        self.lianheti = lianheti  # string
        # 單位
        self.danwei = danwei if danwei is not None else {'num':'', 'money':''} #{'num':,'money':.}

    def __str__(self):
        return json.dumps(self.__dict__, ensure_ascii=False)

    def to_result(self):
        self._normalize()
        return "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (
            self.jiafang if self.jiafang is not None else '',
            self.yifang if self.yifang is not None else '',
            self.hetong if self.hetong is not None else '',
            self.xiangmu if self.xiangmu is not None else '',
            self.shangxian if self.shangxian is not None else '',
            self.xiaxian if self.xiaxian is not None else '',
            self.xiangmu if self.xiangmu is not None else '',
            self.lianheti if self.lianheti is not None else '')

    def _normalize(self):
        if self.shangxian is not None:
            self.shangxian = text_utils.normalize(self.shangxian)
        if self.xiaxian is not None:
            self.xiaxian = text_utils.normalize(self.xiaxian)


class HeTongExtractor(object):
    def __init__(self):
        self.html_parser = Parser()
        self.config = None

        self.name = {}
        self.month = None
        self.money = None

        with codecs.open(FLAGS.resource.config_file, encoding='utf-8', mode='r') as fp: #open config
            self.config = json.loads(fp.read())
        self.table_dict_field_pattern_dict = {}
        for table_dict_field in self.config['table_dict']['fields']:
            self.table_dict_field_pattern_dict[table_dict_field['fieldName']] = \
                TableDictFieldPattern(field_name=table_dict_field['fieldName'],
                                      convert_method=table_dict_field['convertMethod'],
                                      pattern=table_dict_field['pattern'],
                                      col_skip_pattern=table_dict_field['colSkipPattern'] if 'colSkipPattern' in table_dict_field else None,
                                      row_skip_pattern=table_dict_field['rowSkipPattern'] if 'rowSkipPattern' in table_dict_field else None )

    def extract(self, html_file_path):
        rs = []

        # 1. 解析other
        paragraphs = self.html_parser.parse_text(html_file_path)
        self._extract_shangxiaxian(paragraphs)
        # self._extract_time(paragraphs)
        # rs_paragraphs = self._extract_from_paragraphs(paragraphs)

        # 1. 解析everything
        map = return_html_entity(FLAGS)
        for file, res in map.items():
            for line, gg in res.items():
                rs.append(HeTongRecord(file, gg["jiafang"],gg["yifang"],gg["hetong"],gg["xiangmu"]))

        # 2. 解析table
        # for table_dict in self.html_parser.parse_table(html_file_path):
        #     rs.extend(self._extract_from_table_dict(table_dict))

        return rs

    def _extract_shangxiaxian(self,paragraphs):
        for para in paragraphs:
            targets = re.finditer(r"(中标|合同)总?(价|金额|额)(总计|合计|:|：)?为?(人民币)?(?P<num>.{1,15})(亿|万)?元", para)
            for target in targets:
                print(target)
                self.shangxian = target.group('num')
                self.xiaxian = target.group('num')
                return

#    def _extract_money(self, paragraphs):
#        for para in paragraphs:
#            targets = re.findall(r"(以)?现金(方式)?.{0,5}?认购", para)
#            if len(targets) > 0:
#                self.money = "现金"
#                break

#    def _extract_time(self, paragraphs):
#        for para in paragraphs:
#            targets = re.finditer(r"(本次)?(发行结束之日起|限售期为)[,，]?(?P<month>.{1,3}?)个月(内不得转让)?", para)
#            for target in targets:
#                print(target)
#                self.month = target.group('month')
#                if self.month == "3十6":
#                    self.month = '36'
#                if self.month == "十2":
#                    self.month = '12'
#                if self.month == "6十":
#                    self.month = '60'
#                return

    def _extract_from_table_dict(self, table_dict):
        # check none
        rs = []
        if table_dict is None or len(table_dict) <= 0:
            return rs

        # 1. 假定第一行是表头部分则尝试进行规则匹配这一列是哪个类型的字段
        # 必须满足 is_match_pattern is True and is_match_col_skip_pattern is False
        head_row = table_dict[0]
        col_length = len(head_row)
        row_length = len(table_dict)
        field_col_dict = {}
        skip_row_set = set()
        danwei = {'shuliang': '', 'jine': ''}  # {'num':,'money':.}
        print("    head",head_row)
        for i in range(col_length):
            text = head_row[i]
            for (field_name, table_dict_field_pattern) in self.table_dict_field_pattern_dict.items():
                col_good, _danwei = table_dict_field_pattern.is_match_pattern(text)
                if col_good and not table_dict_field_pattern.is_match_col_skip_pattern(text):
                    if field_name not in field_col_dict:
                        field_col_dict[field_name] = i
                    if field_name in ["jine","shuliang"]:
                        danwei[field_name] = _danwei if _danwei else ""
                    # 逐行扫描这个字段的取值，如果满足 row_skip_pattern 则丢弃整行 row
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
            record = DingZengRecord(None, None, None, None, None)
            for (field_name, col_index) in field_col_dict.items():
                try:
                    text = table_dict[row_index][col_index]
                    if field_name == 'duixiang':
                        record.name = self.table_dict_field_pattern_dict.get(field_name).convert(text)
                    elif field_name == 'shuliang':
                        record.shuliang = self.table_dict_field_pattern_dict.get(field_name).convert(normalize(text+danwei["shuliang"]+"股"))
                    elif field_name == 'jine':
                        record.jine = self.table_dict_field_pattern_dict.get(field_name).convert(normalize(text+danwei["jine"]+"元"))
                    elif field_name == 'rengoufangshi':
                        record.money = self.table_dict_field_pattern_dict.get(field_name).convert(text)
                        if not record.money:
                            record.money = self.money
                    elif field_name == 'suodingqi':
                        record.time = self.table_dict_field_pattern_dict.get(field_name).convert(text)
                        if not record.time:
                            record.time = self.month
                    else:
                        pass
                except KeyError:
                    pass

            rs.append(record)
        return rs


    def _extract_from_paragraphs(self, paragraphs):
         self.clearComAbbrDict()
         change_records = []
    #     change_after_records = []
         record_list = []
         for para in paragraphs:
             change_records_para, change_after_records_para = self.__extract_from_paragraph(para)
             change_records += change_records_para
    #         change_after_records += change_after_records_para
    #     self.__mergeRecord(change_records, change_after_records)
    #     for record in change_records:
    #         record_list.append(record)
    #     return record_list

    # def __extract_from_paragraph(self, paragraph):
    #     # lalal
    #     tag_res = self.ner_tagger.ner(paragraph, self.com_abbr_ner_dict)
    #     tagged_str = tag_res.get_tagged_str()
    #     if self.___extract_company_name(tagged_str) > 0:
    #         tag_res = self.ner_tagger.ner(paragraph, self.com_abbr_ner_dict)
    #         tagged_str = tag_res.get_tagged_str()
    #
    #     # extract
    #     change_records = self.___extract_change(tagged_str)
    #     change_after_records = self.___extract_change_after(tagged_str)
    #     return change_records, change_after_records

    # def ___extract_company_name(self, paragraph):
    #     targets = re.finditer(r"<org>(?P<com>.{1,28}?)</org>[(（].{0,5}?简称:?[\"“](?P<com_abbr>.{2,6}?)[\"”][)）]", paragraph)
    #     size_before = len(self.com_abbr_ner_dict)
    #     for target in targets:
    #         com_abbr = target.group("com_abbr")
    #         com_name = target.group("com")
    #         if com_abbr != None and com_name != None:
    #             self.com_abbr_dict[com_abbr] = com_name
    #             self.name[com_name] = com_abbr
    #             self.com_abbr_ner_dict[com_abbr] = "Ni"
    #     return len(self.com_abbr_ner_dict) - size_before
    #
    # def ___extract_time(self, paragraph):
    #     pass
    #
    # def ___extract_change(self, paragraph):
    #     records = []
    #     targets = re.finditer(r"(出售|减持|增持|买入)了?[^，。,:;!?？]*?(股票|股份).{0,30}?<num>(?P<share_num>.{1,20}?)</num>股", paragraph)
    #     for target in targets:
    #         share_num = target.group("share_num")
    #         start_pos = target.start()
    #         end_pos = target.end()
    #         #查找公司
    #         pat_com = re.compile(r"<org>(.*?)</org>")
    #         m_com = pat_com.findall(paragraph,0,end_pos)
    #         shareholder = ""
    #         if m_com != None and len(m_com) > 0:
    #             shareholder = m_com[-1]
    #         else :
    #             pat_person = re.compile(r"<person>(.*?)</person>")
    #             m_person = pat_person.findall(paragraph,0,end_pos)
    #             if m_person != None and len(m_person) > 0 :
    #                 shareholder = m_person[-1]
    #         #查找日期
    #         pat_date = re.compile(r"<date>(.*?)</date>")
    #         m_date = pat_date.findall(paragraph,0,end_pos)
    #         change_date = ""
    #         if m_date != None and len(m_date)>0:
    #             change_date = m_date[-1]
    #         #查找变动价格
    #         pat_price = re.compile(r"(均价|平均(增持|减持|成交)?(价格|股价))(:|：)?<num>(?P<share_price>.*?)</num>")
    #         m_price = pat_price.search(paragraph,start_pos)
    #         share_price = ""
    #         if m_price != None:
    #             share_price = m_price.group("share_price")
    #         if shareholder == None or len(shareholder) == 0:
    #             continue
    #         full_name,short_name = self.getShareholder(shareholder)
    #         records.append(DingZengRecord(full_name, change_date, share_price, share_num,"", ""))
    #     return records
    #
    # def ___extract_change_after(self, paragraph):
    #     records = []
    #     targets = re.finditer(r"(增持后|减持后|变动后).{0,30}?持有.{0,30}?<num>(?P<share_num_after>.*?)</num>(股|万股|百万股|亿股)", paragraph)
    #     for target in targets:
    #         share_num_after = target.group("share_num_after")
    #         start_pos = target.start()
    #         end_pos = target.end()
    #         #查找公司
    #         pat_com = re.compile(r"<org>(.*?)</org>")
    #         m_com = pat_com.findall(paragraph,0,end_pos)
    #         shareholder = ""
    #         if m_com != None and len(m_com) > 0:
    #             shareholder = m_com[-1]
    #         else :
    #             pat_person = re.compile(r"<person>(.*?)</person>")
    #             m_person = pat_person.findall(paragraph,0,end_pos)
    #             if m_person != None and len(m_person) > 0:
    #                 shareholder = m_person[-1]
    #         #查找变动后持股比例
    #         pat_percent_after = re.compile(r"<percent>(?P<share_percent>.*?)</percent>")
    #         m_percent_after = pat_percent_after.search(paragraph,start_pos)
    #         share_percent_after = ""
    #         if m_percent_after != None:
    #             share_percent_after = m_percent_after.group("share_percent")
    #         if shareholder == None or len(shareholder) == 0:
    #             continue
    #         full_name,short_name = self.getShareholder(shareholder)
    #         records.append(DingZengRecord(full_name,short_name, "", "", "", share_num_after, share_percent_after))
    #     return records
    #
    # def ___mergeChangeAfterInfo(self, changeRecord, changeAfterRecords):
    #     for record in changeAfterRecords:
    #         if record.name == changeRecord.name:
    #             changeRecord.shareP = record.shareNumAfterChg
    #             changeRecord.sharePcntAfterChg = record.sharePcntAfterChg
    #
    # def clearComAbbrDict(self):
    #     self.com_abbr_dict = {}
    #     self.name = {}
    #     self.com_abbr_ner_dict = {}
    #
    # def getShareholder(self, shareholder):
    #     #归一化公司全称简称
    #     if shareholder in self.name:
    #         return shareholder, self.name.get(shareholder, "")
    #     if shareholder in self.com_abbr_dict:
    #         return self.com_abbr_dict.get(shareholder, ""),shareholder
    #     #股东为自然人时不需要简称
    #     return shareholder, ""


class TableDictFieldPattern(object):
    def __init__(self, field_name, convert_method, pattern, col_skip_pattern, row_skip_pattern):
        self.field_name = field_name
        self.convert_method = convert_method
        self.pattern = re.compile(pattern) if pattern is not None and len(pattern)>0 else None
        self.col_skip_pattern = re.compile(col_skip_pattern) if col_skip_pattern is not None and len(col_skip_pattern)>0 else None
        self.row_skip_pattern = re.compile(row_skip_pattern) if row_skip_pattern is not None and len(row_skip_pattern)>0 else None
        self.danwei_pattern = re.compile(r"\(((?P<danwei>[万|千]?)[美元|股|元|元\/股].{1,3}?)|(?P<danwei2>\%)\)")

    def is_match_pattern(self, text):
        if self.pattern is None:
            return False
        match = self.pattern.search(text)
        danwei = self.danwei_pattern.search(text)
        return ((True,(danwei.group("danwei") or danwei.group("danwei2"))) if danwei else (True,'')) if match else (False,None) # 没找到="",没找到2=None

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
        return text

    @staticmethod
    def getDecimalFromText(text):
        return text

    @staticmethod
    def getDecimalRangeFromTableText(text):
        return text

if __name__ == '__main__':
    html_file_path = '/root/lab2/data/train_data/hetong/html/'
    HetongExtractor().extract(html_file_path)
