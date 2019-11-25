import os

import torch

class Config():

    def __init__(self):

        ## Files and names
        self.BASE_DIR = os.path.abspath(os.path.join(__file__, os.path.pardir, os.path.pardir))
        SUBSET = 'united'
        self.DATA_DIR = os.path.join(self.BASE_DIR, 'data', SUBSET)
        self.MODEL_DIR = os.path.join(self.BASE_DIR, 'models')
        self.WORD2VEC_MODEL_DIR = os.path.join(self.MODEL_DIR, 'word2vec')
        self.WORD2VEC_MODEL_FILE = os.path.join(self.WORD2VEC_MODEL_DIR, SUBSET + '_word2vec.model')
        self.MODEL_NAME = SUBSET
        self.LOG_HEADER = 'Epoch,Iteration,G_loss,D_loss,D_rr_acc,D_rf_acc,D_fr_acc'

        ## Shapes  !!! L X S = W x H !!!
        self.SENTENCE_LENGTH = 8
        self.WV_SIZE = 512        ## Should be same as in data/config.py
        self.IMAGE_SIZE_WIDTH = 64
        self.IMAGE_SIZE_HEIGHT = 64
        self.N_CHANNELS = 3
        assert self.SENTENCE_LENGTH * self.WV_SIZE == self.IMAGE_SIZE_WIDTH * self.IMAGE_SIZE_HEIGHT, \
               "Incompatible shapes {} x {} != {} x {}".format(self.SENTENCE_LENGTH, self.WV_SIZE, \
                                                               self.IMAGE_SIZE_WIDTH, self.IMAGE_SIZE_HEIGHT)

        ## Stats (Change w.r.t stats file under data/)
        self.MEAN = [0.4731, 0.4638, 0.6420]
        self.STD = [0.1421, 0.3141, 0.2030]

        ## Batch sampler
        self.SHUFFLE_GROUPS = True
        # self.GROUP_N_LABELS_RANGES = [-1, 5, 7, 11, 1000]
        self.GROUP_N_LABELS_RANGES = [0, 10, 20]
        self.GROUP_WIDTH_RANGES = [-1, 500, 700, 1000, 100000]
        self.GROUP_HEIGHT_RANGES = [-1, 590, 100000]
        # self.GROUP_HEIGHT_RANGES = [-1, 100000]

        ## Augmentation options
        self.HORIZONTAL_FLIPPING = True
        self.RANDOM_ROTATION = False
        self.COLOR_JITTERING = False
        self.RANDOM_CHANNEL_SWAPPING = False
        self.RANDOM_GAMMA = False
        self.RANDOM_GRAYSCALE = False
        self.RANDOM_RESOLUTION = False

        ## Word vectors options
        self.LOAD_WORD_VECTORS = True
        self.WORD_VECTORS_SIMILAR_PAD = True
        self.WORD_VECTORS_SIMILAR_PAD_TOPN = 2
        self.WORD_VECTORS_SIMILAR_TAKE_SELF = True
        self.WORD_VECTORS_DISSIMILAR_TOPN = 10

        ## GAN options
        self.N_INPUT = self.SENTENCE_LENGTH * self.WV_SIZE
        self.NGF = 128
        self.NDF = 128
        self.GAN_LOSS = 'lsgan'   ## One of 'lsgan', 'vanilla', 'wgangp'
        self.LAMBDA_L1 = 100.0
        self.NORM_LAYER = torch.nn.BatchNorm2d
        self.USE_DROPOUT = True
        self.N_BLOCKS = 9
        self.PADDING_TYPE = 'reflect'
        self.TRAIN_D_TREND = 3    ## e.g. Train D for each 3 epoch, freeze at others
        self.TRAIN_G_TREND = 1    ## e.g. Train G for each 1 epoch, freeze at others

        ## Hyper-params
        self.BATCH_SIZE = 64
        self.N_EPOCHS = 100
        self.LR = 2e-4
        self.BETA = 0.5
        self.WEIGHT_DECAY = 1e-4

        ## Hardware
        self.DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.N_WORKERS = 4
        self.N_GPUS = 1

        ## Logging
        self.N_PRINT_BATCH = 50
        self.N_LOG_BATCH = 100
        self.N_SAVE_VISUALS_BATCH = 200
        self.N_SAVE_MODEL_EPOCHS = 1
        self.N_GRID_ROW = 6

        ## Misc
        self.FONTS = ['Lato-Medium.ttf', 'FreeMono.ttf', 'LiberationMono-Regular.ttf']
        self.WORDS2IMAGE_N_COLUMN = 1
