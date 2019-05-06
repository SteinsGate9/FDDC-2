import pickle
import os

import tensorflow as tf

from lib.data_utils import load_word2vec, input_from_line
from lib.loader_utils import load_sentences


from model.model import Model
from model.model_utils import create_model

from work.conlleval import return_report

from logging import getLogger
logger = getLogger(__name__)

def return_f1(FLAGS, sess, model, name, data, id_to_tag):
    """
    :return: f1
    """
    logger.info("evaluate:{}".format(name))
    ner_results = model.return_sentence_charrealpred(sess, data, id_to_tag)
    if ner_results is not None :
        eval_lines = _test_ner(ner_results, FLAGS.resource.result_dir)
        for line in eval_lines:
            logger.info(line)
        f1 = float(eval_lines[1].strip().split()[-1])

        if name == "dev": # f1
            best_test_f1 = model.best_dev_f1.eval()
            if f1 > best_test_f1:
                tf.assign(model.best_dev_f1, f1).eval()
                logger.info("new best dev f1 score:{:>.3f}".format(f1))
            return f1 > best_test_f1
        elif name == "test":
            best_test_f1 = model.best_test_f1.eval()
            if f1 > best_test_f1:
                tf.assign(model.best_test_f1, f1).eval()
                logger.info("new best test f1 score:{:>.3f}".format(f1))
            return f1 > best_test_f1

def _test_ner(results, path):
    """
    Run perl script to evaluate model
    """
    output_file = os.path.join(path, "ner_predict_utf8.txt")
    with open(output_file, "w",encoding='utf-8') as f:
        logger.info(results[0])
        to_write = []
        for block in results:
            for line in block:
                to_write.append(line + "\n")
            to_write.append("\n")
        f.writelines(to_write)
    eval_lines = return_report(output_file)
    return eval_lines

def return_line_entity(FLAGS):
    # evaluate
    logger.info("Evaluate Line")

    # load data
    config = load_config(FLAGS.resource.config_file)
    with open(FLAGS.resource.map_file, "rb") as f:
        char_to_id, id_to_char, tag_to_id, id_to_tag = pickle.load(f)

    # start
    tf_config = tf.ConfigProto()
    tf_config.gpu_options.allow_growth = True
    with tf.Session(config=tf_config) as sess:
        model = create_model(sess, Model, FLAGS.resource.ckpt_path, load_word2vec, config, id_to_char, False)
        while True:
            line = input("请输入测试句子:")
            result = model.return_sentence_pred_evaluate(sess, input_from_line(line, char_to_id), id_to_tag)
            print(result)

from lib.data_utils import prepare_dataset, BatchManager
from lib.loader_utils import iobes_iob
from model.model_utils import result_to_json
from main import FLAGS
def return_html_entity(html_id, sess, trans, model, id_to_tag, tag_to_id, char_to_id):
    # evaluate
    # logger.info("Evaluate HTML")
    txt_name = html_id[:-5]+'.txt'
    # load data sets
    mode = "file"
    if mode == "dir":
        files = {}
        for file in os.listdir(FLAGS.resource.eval_dir):
            files[file] = (load_sentences(os.path.join(FLAGS.resource.bio_dir+"/text_10_BIO_10_nofast_new", file), FLAGS.trainer.zeros))
            files[file] = BatchManager(prepare_dataset(files[file], char_to_id, tag_to_id, FLAGS.trainer.lower), FLAGS.trainer.batch_size)
    # elif mode == 'file':
    #     files = {}
    #     files["file"] = (load_sentences(os.path.join(FLAGS.resource.train_file), FLAGS.trainer.zeros))
    #     files["file"] = BatchManager(prepare_dataset(files["file"], char_to_id, tag_to_id, FLAGS.trainer.lower), FLAGS.trainer.batch_size)
    elif mode == 'file':
        files = {}
        files["file"] = (load_sentences(os.path.join(FLAGS.resource.bio_dir+"/text_10_BIO_10_nofast_new", txt_name), FLAGS.trainer.zeros))
        files["file"] = BatchManager(prepare_dataset(files["file"], char_to_id, tag_to_id, FLAGS.trainer.lower),
                                     FLAGS.trainer.batch_size)

    # start
    map = {}
    for file, data in (files.items()):
        map[file] = {}
        b = 0
        for batch in data.iter_batch():
            lengths, scores = model.run_step(sess, False, batch)
            batch_paths = model._decode(scores, lengths, trans)
            strings = batch[0]
            for i in range(len(strings)):
                string = strings[i][:lengths[i]]
                pred = [id_to_tag[int(x)] for x in batch_paths[i][:lengths[i]]]
                enti_list = result_to_json(string, pred)["entities"]
                map[file][b] = {"jiafang":"","yifang":"","xiangmu":"","hetong":""}
                for enti in enti_list:
                    map[file][b][enti["type"]] = enti["word"]
                b += 1
    # for file,res in map.items():
    #     print(file)
    #     for line,gg in res.items():
    #         print(gg)

    return map

if __name__ == "__main__":
    pass




