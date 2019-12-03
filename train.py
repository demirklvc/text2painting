import argparse
import glob
import os
import sys
import time
from multiprocessing import cpu_count

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image, ImageFilter

import torch
import torch.nn as nn
from gensim.models import Word2Vec
from lib.config import Config
from lib.dataset import AlignCollate, ImageBatchSampler, TextArtDataLoader
from lib.model import GANModel
from torch.utils.data import DataLoader


CONFIG = Config()



if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, help='Model file to load')
    parser.add_argument('--reset_lr', action='store_true', help='Reset learning rate')
    args = parser.parse_args()
    model_file = args.model
    reset_lr = args.reset_lr

    ## Data loaders
    print("Data loaders initializing..")
    train_dataset = TextArtDataLoader(CONFIG, mode='train')
    # val_dataset = TextArtDataLoader(CONFIG, mode='val')
    train_align_collate = AlignCollate(CONFIG, 'train')
    # val_align_collate = AlignCollate(CONFIG, 'val')
    train_batch_sampler = ImageBatchSampler(CONFIG, mode='train')
    # val_batch_sampler = ImageBatchSampler(CONFIG, mode='val')
    train_loader = DataLoader(train_dataset,
                              batch_size=CONFIG.BATCH_SIZE,
                              shuffle=False,
                              num_workers=CONFIG.N_WORKERS,
                              pin_memory=True,
                              collate_fn=train_align_collate,
                              sampler=train_batch_sampler,
                             )
    # val_loader = DataLoader(val_dataset,
    #                         batch_size=CONFIG.BATCH_SIZE,
    #                         shuffle=False,
    #                         num_workers=CONFIG.N_WORKERS,
    #                         pin_memory=True,
    #                         collate_fn=val_align_collate,
    #                         sampler=val_batch_sampler
    #                         )
    print("\tTrain size:", len(train_dataset))
    # print("\tValidation size:", len(val_dataset))
    n_train_batch = len(train_dataset) // CONFIG.BATCH_SIZE
    # n_val_batch = len(val_dataset) // CONFIG.BATCH_SIZE
    time.sleep(0.5)

    ## Init model with G and D
    print("\nModel initializing..")
    model = GANModel(CONFIG, model_file=model_file, mode='train', reset_lr=reset_lr)
    time.sleep(1.0)

    print("\nTraining starting..")
    for epoch in range(model.epoch, model.epoch + CONFIG.N_EPOCHS):
        print("Epoch {}/{}:".format(epoch, model.epoch + CONFIG.N_EPOCHS - 1))

        for phase in ['train']:

            phase_start = time.time()
            print("\t{} phase:".format(phase.title()))

            total_loss_g = 0.0
            total_loss_d = 0.0
            total_loss_g_refiner = 0.0
            total_loss_gp_fr = 0.0
            total_loss_gp_rf = 0.0
            total_acc_rr = 0.0
            total_acc_rf = 0.0
            total_acc_fr = 0.0
            total_acc_refined_fr = 0.0
            classic = True if epoch % 2 == 1 else False   ## Backward D rule

            if phase == 'train':

                ## Set network to train
                train_D = True if (epoch - 1) % CONFIG.TRAIN_D_TREND == 0 else False
                train_G = True if (epoch - 1) % CONFIG.TRAIN_G_TREND == 0 else False
                print("\tUpdate D: {}, Update G: {}".format(str(train_D), str(train_G)))
                data_loader = train_loader
                n_batch = n_train_batch
                model.G.train()
                model.D.train()
                model.G_refiner.train()

            else:
                data_loader = val_loader
                n_batch = n_val_batch
                model.G.eval()
                model.D.eval()
                model.G_refiner.eval()
                train_D = False
                train_G = False

            for i, data in enumerate(data_loader):
                iteration = (epoch - 1) * n_batch + i

                ## Get data
                real_images, real_wvs, fake_wvs = data
                batch_size = real_images.size()[0]

                ## Fit batch
                model.fit(data, phase=phase, train_D=train_D, train_G=train_G, classic=classic)

                ## Update total loss
                loss_g, loss_d, loss_g_refiner, loss_gp_fr, loss_gp_rf = model.get_losses()
                total_loss_g += loss_g
                total_loss_d += loss_d
                total_loss_g_refiner += loss_g_refiner
                if loss_gp_fr:
                    total_loss_gp_fr += loss_gp_fr
                if loss_gp_rf:
                    total_loss_gp_rf += loss_gp_rf

                ## Get D accuracy
                acc_rr, acc_rf, acc_fr, acc_refined_fr = model.get_D_accuracy()
                total_acc_rr += acc_rr
                total_acc_rf += acc_rf
                total_acc_fr += acc_fr
                total_acc_refined_fr += acc_refined_fr

                ## Save logs
                if iteration % CONFIG.N_LOG_BATCH == 0:
                    log_tuple = phase, epoch, iteration, loss_g, loss_d, loss_g_refiner, acc_rr, acc_rf, acc_fr, acc_refined_fr
                    model.save_logs(log_tuple)

                # Print logs
                if i % CONFIG.N_PRINT_BATCH == 0:
                    print("\t\tBatch {: 4}/{: 4}:".format(i, n_batch), end=' ')
                    print("G loss: {:.4f} | D loss: {:.4f} | G refiner loss: {:.4f}".format(loss_g, loss_d, loss_g_refiner), end=' ')
                    if CONFIG.GAN_LOSS == 'wgangp':
                        print("| GP loss fake-real: {:.4f}".format(loss_gp_fr), end=' ')
                        print("| GP loss real-fake: {:.4f}".format(loss_gp_rf), end=' ')
                    print("| Accuracy D real-real: {:.4f} | real-fake: {:.4f} | fake-real {:.4f} | fake refined-real {:.4f}".format(acc_rr, acc_rf, acc_fr, acc_refined_fr))

                ## Save visual outputs
                try:
                    if iteration % CONFIG.N_SAVE_VISUALS_BATCH == 0 and phase == 'train':
                        output_filename = "{}_{:04}_{:08}.png".format(model.model_name, epoch, iteration)
                        grid_img_pil = model.generate_grid(real_wvs, real_images, train_dataset.word2vec_model)
                        model.save_img_output(grid_img_pil, output_filename)
                        # model.save_grad_output(output_filename)
                except Exception as e:
                    print('Grid image generation failed.', e, 'Passing.')

            total_loss_g /= (i + 1)
            total_loss_d /= (i + 1)
            total_loss_g_refiner /= (i + 1)
            total_loss_gp_fr /= (i + 1)
            total_loss_gp_rf /= (i + 1)
            total_acc_rr /= (i + 1)
            total_acc_rf /= (i + 1)
            total_acc_fr /= (i + 1)
            total_acc_refined_fr /= (i + 1)
            if CONFIG.GAN_LOSS == 'wgangp':
                print("\t\t{p} G loss: {:.4f} | {p} D loss: {:.4f} | {p} G_refiner loss: {:.4f}".format(total_loss_g, total_loss_d, total_loss_g_refiner, p=phase.title()), end=' ')
                print("| GP loss fake-real: {:.4f}".format(total_loss_gp_fr), end=' ')
                print("| GP loss real-fake: {:.4f}".format(total_loss_gp_rf))
            else:
                print("\t\t{p} G loss: {:.4f} | {p} D loss: {:.4f} | {p} G refiner loss: {:.4f}".format(total_loss_g, total_loss_d, total_loss_g_refiner, p=phase.title()))
            print("\t\tAccuracy D real-real: {:.4f} | real-fake {:.4f} | fake-real {:.4f} | fake refined-real {:.4f}".format(total_acc_rr, total_acc_rf, total_acc_fr, total_acc_refined_fr))
            print("\t{} time: {:.2f} seconds".format(phase.title(), time.time() - phase_start))

        ## Update lr
        model.update_lr()

        ## Save model
        if epoch % CONFIG.N_SAVE_MODEL_EPOCHS == 0:
            model.save_model_dict(epoch, iteration, total_loss_g, total_loss_d, total_loss_g_refiner)
