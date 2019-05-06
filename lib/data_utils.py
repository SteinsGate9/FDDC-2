# encoding = utf8
import re
import math
import codecs
import random

import numpy as np
import jieba
jieba.initialize()

from logging import getLogger
logger = getLogger(__name__)
from main import FLAGS
# def insert_singletons(words, singletons, p=0.5):
#     """
#     Replace singletons by the unknown word with a probability p.
#     """
#     new_words = []
#     for word in words:
#         if word in singletons and np.random.uniform() < p:
#             new_words.append(0)
#         else:
#             new_words.append(word)
#     return new_words



# def create_input(data):
#     """
#     Take sentence data and return an input for
#     the training or the evaluation function.
#     """
#     inputs = list()
#     inputs.append(data['chars'])
#     inputs.append(data["segs"])
#     inputs.append(data['tags'])
#     return inputs





# def cut_to_sentence(text):
#     """
#     Cut text to sentences
#     """
#     sentence = []
#     sentences = []
#     len_p = len(text)
#     pre_cut = False
#     for idx, word in enumerate(text):
#         sentence.append(word)
#         cut = False
#         if pre_cut:
#             cut=True
#             pre_cut=False
#         if word in u"。;!?\n":
#             cut = True
#             if len_p > idx+1:
#                 if text[idx+1] in ".。”\"\'“”‘’?!":
#                     cut = False
#                     pre_cut=True
#
#         if cut:
#             sentences.append(sentence)
#             sentence = []
#     if sentence:
#         sentences.append("".join(list(sentence)))
#     return sentences




def load_word2vec(emb_path, id_to_word, word_dim, old_weights):
    """
    Load word embedding from pre-trained file
    embedding size must match
    """
    new_weights = old_weights
    print('Loading pretrained embeddings from {}...'.format(emb_path))
    pre_trained = {}
    emb_invalid = 0
    for i, line in enumerate(codecs.open(emb_path, 'r', 'utf-8')):
        line = line.rstrip().split()
        if len(line) == word_dim + 1:
            pre_trained[line[0]] = np.array(
                [float(x) for x in line[1:]]
            ).astype(np.float32)
        else:
            emb_invalid += 1
    if emb_invalid > 0:
        print('WARNING: %i invalid lines' % emb_invalid)
    c_found = 0
    c_lower = 0
    c_zeros = 0
    n_words = len(id_to_word)
    # Lookup table initialization
    for i in range(n_words):
        word = id_to_word[i]
        if word in pre_trained:
            new_weights[i] = pre_trained[word]
            c_found += 1
        elif word.lower() in pre_trained:
            new_weights[i] = pre_trained[word.lower()]
            c_lower += 1
        elif re.sub('\d', '0', word.lower()) in pre_trained:
            new_weights[i] = pre_trained[
                re.sub('\d', '0', word.lower())
            ]
            c_zeros += 1
    print('Loaded %i pretrained embeddings.' % len(pre_trained))
    print('%i / %i (%.4f%%) words have been initialized with '
          'pretrained embeddings.' % (
        c_found + c_lower + c_zeros, n_words,
        100. * (c_found + c_lower + c_zeros) / n_words)
    )
    print('%i found directly, %i after lowercasing, '
          '%i after lowercasing + zero.' % (
        c_found, c_lower, c_zeros
    ))
    return new_weights

def input_from_line(line, char_to_id):
    """
    Take sentence data and return an input for
    the training or the evaluation function.
    """
    line = _full_to_half(line)
    line = _replace_html(line)
    inputs = list()
    inputs.append([line])
    line.replace(" ", "$")
    inputs.append([[char_to_id[char] if char in char_to_id else char_to_id["<UNK>"]
                   for char in line]])
    inputs.append([_get_seg_features(line)])
    inputs.append([[]])
    return inputs

def _replace_html(s):
    s = s.replace('&quot;','"')
    s = s.replace('&amp;','&')
    s = s.replace('&lt;','<')
    s = s.replace('&gt;','>')
    s = s.replace('&nbsp;',' ')
    s = s.replace("&ldquo;", "“")
    s = s.replace("&rdquo;", "”")
    s = s.replace("&mdash;","")
    s = s.replace("\xa0", " ")
    return(s)

def _full_to_half(s):
    """
    Convert full-width character to half-width one
    """
    n = []
    for char in s:
        num = ord(char)
        if num == 0x3000:
            num = 32
        elif 0xFF01 <= num <= 0xFF5E:
            num -= 0xfee0
        char = chr(num)
        n.append(char)
    return ''.join(n)

def _get_seg_features(string):
    """
    Segment text with jieba
    features are represented in bies format
    s donates single word
    """
    seg_feature = []
    for word in jieba.cut(string):
        if len(word) == 1:
            seg_feature.append(0)
        else:
            tmp = [2] * len(word)
            tmp[0] = 1
            tmp[-1] = 3
            seg_feature.extend(tmp)
    return seg_feature

class BatchManager(object):

    def __init__(self, data,  batch_size):
        self.batch_data = self._sort_and_pad(data, batch_size)
        self.len_data = len(self.batch_data) # how many batches

    def _sort_and_pad(self, data, batch_size):
        num_batch = int(math.ceil(len(data) /batch_size))
        sorted_data = sorted(data, key=lambda x: len(x[0]))
        batch_data = list()
        for i in range(num_batch):
            batch_data.append(self._pad_data(sorted_data[i*batch_size : (i+1)*batch_size]))  #[[[s]],[[c]],[[]],[[]]], ]
        return batch_data

    @staticmethod
    def _pad_data(data):
        strings = []
        chars = []
        segs = []
        targets = []
        max_length = max([len(sentence[0]) for sentence in data])
        for line in data:
            string, char, seg, target = line
            padding = [0] * (max_length - len(string))
            strings.append(string + padding)
            chars.append(char + padding)
            segs.append(seg + padding)
            targets.append(target + padding)
        return [strings, chars, segs, targets]

    def iter_batch(self, shuffle=False):
        if shuffle:
            random.shuffle(self.batch_data)
        for idx in range(self.len_data):
            yield self.batch_data[idx]  # [[s]x5],[[c]],[[]],[[]]]

def prepare_dataset(sentences, char_to_id, tag_to_id, lower=False):
    """
    Prepare the dataset. Return a list of lists of dictionaries containing:
        - word indexes
        - word char indexes
        - tag indexes
    """
    none_index = tag_to_id["O"]
    def f(x):
        return x.lower() if lower else x
    data = []
    for s in sentences:#[[(c,t)],word[]]   ]
        string = [w[0] for w in s] # string for sentence [c]
        chars = [char_to_id[f(w) if f(w) in char_to_id else '<UNK>']
                 for w in string] # id for sentence  [id]
        segs = _get_seg_features("".join(string)) # [segid]
        if FLAGS.opts.train:
            tags = [tag_to_id[w[-1]] for w in s]  # [tags]
        else:
            tags = [none_index for _ in chars]
        data.append([string, chars, segs, tags])
    # logger.info("Prepared Datesets.")
    return data

