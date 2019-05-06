import itertools
import os
import pickle
from collections import OrderedDict

import numpy as np
import tensorflow as tf

from lib.data_utils import load_word2vec, BatchManager, prepare_dataset
from lib.loader_utils import load_sentences, update_tag_scheme
from lib.map_utils import augment_with_pretrained, char_mapping, tag_mapping

from lib.utils import print_config, save_config, load_config

from model.model import Model
from model.model_utils import save_model
from model.model_utils import create_model
from work.evaluate import return_f1

from logging import getLogger


logger = getLogger(__name__)
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = "2"  # 使用第二块GPU（从0开始）
from tqdm import tqdm
from parse.getTextFromHtml import getContentFromEveryDiv



def train(FLAGS):
    # load data sets
    train_sentences = load_sentences(FLAGS.resource.train_file, FLAGS.trainer.zeros)
    test_sentences = load_sentences(FLAGS.resource.test_file, FLAGS.trainer.zeros)
    update_tag_scheme(train_sentences, FLAGS.model.tag_schema)    # Use selected tagging scheme (IOB / IOBES)
    update_tag_scheme(test_sentences, FLAGS.model.tag_schema)

    # create maps if not exist
    if not os.path.isfile(FLAGS.resource.map_file):
        if FLAGS.trainer.pre_emb: # create dictionary for word
            dico_chars_train = char_mapping(train_sentences, FLAGS.trainer.lower)[0]
            _, char_to_id, id_to_char = augment_with_pretrained(
                dico_chars_train.copy(),
                FLAGS.resource.emb_file,
                list(itertools.chain.from_iterable(
                    [[w[0] for w in s] for s in test_sentences])
                )
            )
        else:
            _, char_to_id, id_to_char = char_mapping(train_sentences, FLAGS.trainer.lower)
        _, tag_to_id, id_to_tag = tag_mapping(train_sentences)# Create a dictionary and a mapping for tags
        with open(FLAGS.resource.map_file, "wb") as f:
            pickle.dump([char_to_id, id_to_char, tag_to_id, id_to_tag], f)
    else:
        with open(FLAGS.resource.map_file, "rb") as f:
            char_to_id, id_to_char, tag_to_id, id_to_tag = pickle.load(f)

    # prepare data, get a collection of list containing index
    train_data = prepare_dataset(
        train_sentences, char_to_id, tag_to_id, FLAGS.trainer.lower
    )
    test_data = prepare_dataset(
        test_sentences, char_to_id, tag_to_id, FLAGS.trainer.lower
    )
    train_manager = BatchManager(train_data, FLAGS.trainer.batch_size)
    test_manager = BatchManager(test_data, 100)

    # make path for store log and model if not exist
    if os.path.isfile(FLAGS.resource.config_file2):
        config = load_config(FLAGS.resource.config_file2)
    else:
        config = _config_model(FLAGS, char_to_id, tag_to_id)
        save_config(config, FLAGS.resource.config_file2)
    print_config(config, logger)

    # limit GPU memory
    tf_config = tf.ConfigProto()
    tf_config.gpu_options.allow_growth = True
    steps_per_epoch = train_manager.len_data
    with tf.Session(config=tf_config) as sess:
        model = create_model(sess, Model, FLAGS.resource.ckpt_dir, load_word2vec, config, id_to_char)
        logger.info("Start raining")
        loss = []
        for i in range(FLAGS.trainer.max_epoch):
            for batch in train_manager.iter_batch(shuffle=True):
                step, batch_loss = model.run_step(sess, True, batch)
                loss.append(batch_loss)
                if step % FLAGS.trainer.steps_check == 0:
                    iteration = step // steps_per_epoch + 1
                    logger.info("iteration:{} step:{}/{}, "
                                "NER loss:{:>9.6f}".format(
                        iteration, step%steps_per_epoch, steps_per_epoch, np.mean(loss)))
                    loss = []

            best = return_f1(FLAGS, sess, model, "test", test_manager, id_to_tag)
            if best:
                save_model(sess, model, FLAGS.resource.ckpt_dir)

# config for the model
def _config_model(FLAGS, char_to_id, tag_to_id):
    config = OrderedDict()
    config["model_type"] = FLAGS.resource.model_type
    config["emb_file"] = FLAGS.resource.emb_file

    config["num_chars"] = len(char_to_id)
    config["num_tags"] = len(tag_to_id)
    config["char_dim"] = FLAGS.model.char_dim
    config["seg_dim"] = FLAGS.model.seg_dim
    config["lstm_dim"] = FLAGS.model.lstm_dim
    config["tag_schema"] = FLAGS.model.tag_schema

    config["batch_size"] = FLAGS.trainer.batch_size
    config["clip"] = FLAGS.trainer.clip
    config["dropout_keep"] = 1.0 - FLAGS.trainer.dropout
    config["optimizer"] = FLAGS.trainer.optimizer
    config["lr"] = FLAGS.trainer.lr
    config["pre_emb"] = FLAGS.trainer.pre_emb
    config["zeros"] = FLAGS.trainer.zeros
    config["lower"] = FLAGS.trainer.lower
    return config