#coding=utf-8
"""
@version=1.0
@author:zsh
@file:tableParser.py
@time:2018/11/6 09:23
"""
import codecs
import re
import bs4
from bs4 import BeautifulSoup

from parse import text_utils
from parse.text_utils import *

re_replace_blank= re.compile('\s+')
CommaCharInNumberSet1 = set([',','.','。','，','!','?',':','：'])

class Parser:
    def __init__(self):
        pass

    @classmethod
    def parse_table(self,html_file_path):
        rs_list = []
        with codecs.open(html_file_path, encoding='utf-8', mode='r') as fp:
            soup = BeautifulSoup(fp.read(), "html.parser")
            for table in soup.find_all('table'):
                table_dict, is_head_two_rowspan = self._parse_table_to_2d_dict(table)
                row_length = len(table_dict)
                if table_dict is not None:
                    if is_head_two_rowspan and row_length > 2:     # 把前兩排合并
                        try:
                            new_table_dict = {}
                            head_row = {}
                            col_length = len(table_dict[0])
                            for col_idx in range(col_length):
                                head_row[col_idx] = table_dict[0][col_idx] + table_dict[1][col_idx]
                            new_table_dict[0] = head_row
                            for row_idx in range(2, row_length):
                                new_table_dict[row_idx - 1] = table_dict[row_idx]
                            rs_list.append(new_table_dict)
                        except KeyError:
                            rs_list.append(table_dict)
                    else:
                        rs_list.append(table_dict)
        return rs_list

    @staticmethod
    def _parse_table_to_2d_dict(table):
        rs_dict = {}
        row_index = 0
        is_head_two_rowspan, is_head = False, True
        for tr in table.find_all('tr'):
            col_index, cur_col_index = 0, 0
            for td in tr.find_all('td'):
                rowspan = td.get('rowspan')
                rowspan = int(rowspan) if (rowspan is not None and int(rowspan) > 1) else 1
                colspan = td.get('colspan')
                colspan = int(colspan) if (colspan is not None and int(colspan) > 1) else 1
                if is_head:
                    if rowspan > 1 or colspan > 1:
                        is_head_two_rowspan = True
                    is_head = False
                for r in range(rowspan):
                    if (row_index + r) not in rs_dict:
                        rs_dict[row_index + r] = {}
                    for c in range(colspan):
                        cur_col_index = col_index
                        while cur_col_index in rs_dict[row_index + r]:
                            cur_col_index += 1
                        rs_dict[row_index + r][cur_col_index] = text_utils.clean_text(text_utils.normalize(td.text))
                        cur_col_index += 1
                col_index = cur_col_index
            row_index += 1
        return rs_dict, is_head_two_rowspan

    @classmethod
    def parse_text(self, html_file_path)
        with codecs.open(html_file_path, mode='r', encoding="UTF-8") as fr:
            soup = BeautifulSoup(fr.read(), 'html.parser')
            text = ""
            # print(html_file_path)
            for child in soup.descendants:
                sentence = ""
                if child.name == 'tr' or child.name == 'td':
                    if not text[-1] in CommaCharInNumberSet1:
                        sentence += ','
                if isinstance(child, bs4.element.Tag) and child.attrs.get('title'):
                    if 'title' in child.attrs:
                        sentence = clean_text(normalize(child['title']))
                        if not sentence.endswith(':'):
                            sentence += ':'
                elif isinstance(child, bs4.NavigableString) and len(child.string) > 2:
                    sentence = clean_text(normalize(child.string))
                text += sentence
            return text

    @classmethod
    def parse_content(self, html_file_path):
        """
        解析 HTML 中的段落文本
        按顺序返回多个 paragraph 构成一个数组，
        每个 paragraph 是一个 content 行构成的数组
        :param html_file_path:
        :return:
        """
        rs = []
        with codecs.open(html_file_path, encoding='utf-8', mode='r') as fp:
            soup = BeautifulSoup(fp.read(), "html.parser")
            paragraphs = []
            for div in soup.find_all('div'):
                div_type = div.get('type')
                if div_type is not None and div_type == 'paragraph':
                    paragraphs.append(div)
            for paragraph_div in paragraphs:
                has_sub_paragraph = False
                for div in paragraph_div.find_all('div'):
                    div_type = div.get('type')
                    if div_type is not None and div_type == 'paragraph':
                        has_sub_paragraph = True
                if has_sub_paragraph:
                    continue
                rs.append([])
                for content_div in paragraph_div.find_all('div'):
                    div_type = content_div.get('type')
                    if div_type is not None and div_type == 'content':
                        table = content_div.find_all('table')
                        if table:
                            tableText=""
                            tr = soup.find_all('tr')
                            for r in tr:
                                td = r.find_all('td')
                                for d in td:
                                    tableText+= (text_utils.clean_text(text_utils.normalize(d.text))) + ','

                            rs[-1].append((tableText))
                        else:
                            rs[-1].append(text_utils.clean_text(text_utils.normalize(content_div.text)))
        paragraphs = []
        for content_list in rs:
            if len(content_list) > 0:
                paragraphs.append(''.join(content_list))
        return paragraphs

