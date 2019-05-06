import argparse
import torch
import os
from moke_config import ConfigBase
from moke_config import create_config
from logging import StreamHandler, basicConfig, DEBUG, getLogger, Formatter

# src
class Config(ConfigBase):
    def __init__(self):
        self.opts = OptionsConfig()
        self.resource = ResourceConfig()
        self.model = ModelConfig()
        self.trainer = TrainerConfig()


class OptionsConfig(ConfigBase):
    def __init__(self):
        self.device = None
        self.clean = None
        self.train = None


class ResourceConfig(ConfigBase):
    def __init__(self):
        self.script = "conlleval"
        self.model_type = "idcnn"
        self.task = "hetong"

        self.ckpt_dir = os.path.join(self._model_dir, "ckpt_10_new_nofast")
        self.map_file = os.path.join(self._model_dir, "maps_10_new_nofast.pkl")
        self.config_file2 = os.path.join(self._model_dir, "config_file_10_new_nofast")

        self.vocab_file = os.path.join(self._model_dir, "vocab.json")
        self.config_file = os.path.join(self._model_dir, "config_file.json")
        self.emb_file = os.path.join(self._model_dir, "vec.txt")
        self.black_file = os.path.join(self._model_dir, "ner_com_blacklist.txt")
        self.ner_model_dir_path = r'F:\dasanxia\fddc-extraction-release-master\model\ltp_data_v3.4.0'

        self.result_dir = os.path.join(self._result_dir,"result")

        self.summary_dir = os.path.join(self._log_dir, "summary")
        self.log_file = os.path.join(self._log_dir, "train.log")
        self.main_log_file = os.path.join(self._log_dir, "main.log")

        self.train_dir = os.path.join(os.path.join(self._data_dir, self.task), "train")
        self.html_dir = os.path.join(os.path.join(self._data_dir, self.task), "html")
        self.text_dir = os.path.join(os.path.join(self._data_dir, self.task), "text")
        self.fasttext_dir = os.path.join(os.path.join(self._data_dir, self.task), "fasttext")
        self.textafter_dir = os.path.join(os.path.join(self._data_dir, self.task), "textafter")
        self.bio_dir = os.path.join(os.path.join(self._data_dir, self.task), "bio")
        self.eval_dir = os.path.join(self.bio_dir,"eval")
        self.original_dir = os.path.join(self.bio_dir, "original")
        self.train_file =  os.path.join(self.bio_dir,"BIO_new_10/example.train")
        self.test_file = os.path.join(self.bio_dir,"BIO_new_10/example.test")

        self.create_dirs()

    def create_dirs(self):
        dirs = [self.ckpt_dir, self._model_dir, self._result_dir, self._log_dir, self.result_dir,
                self.summary_dir, self.html_dir, self.text_dir, self.bio_dir, self.train_dir, self.eval_dir, self.original_dir, self.fasttext_dir, self.textafter_dir]
        for d in dirs:
            if not os.path.exists(d):
                os.makedirs(d)

    @property
    def _project_dir(self):
        return os.path.dirname(os.path.abspath(__file__))

    @property
    def _pro_project_dir(self):
        return os.path.dirname(os.path.dirname(self._project_dir))

    @property
    def _data_dir(self):
        return os.path.join(self._pro_project_dir, "DATA")

    @property
    def _model_dir(self):
        return os.path.join(self._data_dir, self.task+"/data/model_data")

    @property
    def _result_dir(self):
        return os.path.join(self._data_dir, self.task+"/data/result_data")

    @property
    def _log_dir(self):
        return os.path.join(self._data_dir, self.task+"/data/log_data")


class TrainerConfig(ConfigBase):
    def __init__(self):
        self.clip = 5
        self.dropout = 0.5
        self.batch_size = 5
        self.lr = 0.001
        self.optimizer = "adam"
        self.pre_emb = True
        self.zeros = False
        self.lower = True
        self.max_epoch = 80
        self.steps_check = 50


class ModelConfig(ConfigBase):
    def __init__(self):
        # configurations for the model
        self.seg_dim = 20
        self.char_dim = 100
        self.lstm_dim = 100
        self.tag_schema = 'iobes' # or iob


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", help="what to do", default=False, dest='train')
    parser.add_argument("--clean", help="specify config yaml", default=False, dest='clean')
    parser.add_argument("--no_cuda", help="no cuda", action="store_false", default=True, dest='cuda')
    return parser.parse_args()

def setup_logger(log_filename):
    format_str = '%(asctime)s@%(name)s %(levelname)s # %(message)s'
    basicConfig(filename=log_filename, level=DEBUG, format=format_str)
    stream_handler = StreamHandler()
    stream_handler.setFormatter(Formatter(format_str))
    getLogger().addHandler(stream_handler)

def get_everything():
    # get args
    args = create_parser()
    device = torch.device('cuda' if torch.cuda.is_available() and args.cuda else 'cpu')

    # get config
    config = create_config(Config)

    # update config
    config.opts.device = device
    config.opts.train = args.train
    config.opts.clean = args.clean

    # get logger
    setup_logger(config.resource.main_log_file)
    return config

