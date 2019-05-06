#-*- coding: utf-8 -*-
import os,sys
def add_path():
    _PATH_ = os.path.dirname(__file__)
    if _PATH_ not in sys.path:
        sys.path.append(_PATH_)
add_path()
from args import get_everything
FLAGS = get_everything()

if __name__ == "__main__":
    from work.train import train
    from lib.utils import clean
    from work.zengjianchiExtractor import ZengJianChiExtractor
    from work.dingzengExtractor import DingZengExtractor
    from work.hetongExtractor import HeTongExtractor

    if FLAGS.opts.train:
        if FLAGS.opts.clean:
            clean(FLAGS)
        train(FLAGS)
    else:
        # pass
        # ZengJianChiExtractor(FLAGS.resource.ner_model_dir_path, FLAGS.resource.black_file).extract_from_html_dir(r"F:\dasanxia\FDDC-master\DATA\html")
        # DingZengExtractor().extract_from_html_dir(r"F:\dasanxia\FDDC-master\DATA\h\html")
        HeTongExtractor().extract_from_html_dir("../utils/new_hetong")


    from parse.getTextFromHtml import getContentFromEveryDiv
    from parse.parseFromHtml import Parser
    from work.dingzengExtractor import DingZengExtractor
    from tqdm import tqdm


    # hetong heads
    # gg = []
    # for filename in tqdm(os.listdir(r"../utils/new_hetong")):
    #     # getContentFromEveryDiv(os.path.join(FLAGS.resource.html_dir, filename))
    #     for table in Parser.parse_table(os.path.join(r"../utils/new_hetong", filename)):
    #         print(filename)
    #         if len(table)>0:
    #             gg.append(table[0])
    #             print("    ",table[0])
    #         # DingZengExtractor().extract(os.path.join(FLAGS.resource.html_dir, "230115.html"))
    # import json
    # with open('hetong_heads.json', 'w') as f:
    #     json.dump(gg, f)

    # hetong train
    # gg = []
    # for filename in tqdm(os.listdir(r"../utils/new_hetong")):
    #     gg.append(filename[:filename.find('.')])
    # shit = []
    # with open("hetong.train", 'r', encoding="UTF-8") as fr:
    #     for line in fr.readlines():
    #         a = line.split('\t')
    #         if a[0] not in gg:
    #             continue
    #         shit.append(line)
    # with open("hetong2.train","w",encoding="UTF-8") as fw:
    #     fw.writelines(shit)
    # print(len(shit))

    # dingzeng heads
    # gg = []
    # for filename in tqdm(os.listdir(r"../utils/new_dingzeng")):
    #     # getContentFromEveryDiv(os.path.join(FLAGS.resource.html_dir, filename))
    #     for table in Parser.parse_table(os.path.join(r"../utils/new_dingzeng", filename)):
    #         if len(table)>0:
    #             try:
    #                 gg.append(table[0])
    #                 print(table[0])
    #             except:
    #                 pass
    #
    #     # DingZengExtractor().extract(os.path.join(FLAGS.resource.html_dir, "230115.html"))
    # import json
    # with open('dingzeng_heads.json', 'w') as f:
    #     json.dump(gg, f)

    # ZENGJIANCHI head
    # gg = []
    # for filename in tqdm(os.listdir("../utils/new_zengjianchi")):
    #     # getContentFromEveryDiv(os.path.join(FLAGS.resource.html_dir, filename))
    #     for table in Parser.parse_table(os.path.join("../utils/new_zengjianchi", filename)):
    #         if len(table)>0:
    #             gg.append(table[0])
    #             print(table[0])
    #     # DingZengExtractor().extract(os.path.join(FLAGS.resource.html_dir, "230115.html"))
    # import json
    # with open('zengjianchi_heads.json', 'w') as f:
    #     json.dump(gg, f)

    # print hetong heads
    # import json
    # with open('dingzeng_heads.json', 'r', encoding='utf-8') as f:
    #     l = json.load(f)
    # for i in l:
    #     print(i)

    # print hetong heads
    # with open(FLAGS.resource.map_file, "rb") as f:
    #     char_to_id, id_to_char, tag_to_id, id_to_tag = pickle.load(f)
    # print(tag_to_id)



