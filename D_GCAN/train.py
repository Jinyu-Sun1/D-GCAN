# -*- coding: utf-8 -*-
"""
Created on Wed Apr 27 20:09:31 2022

@author:Jinyu-Sun
"""

import timeit
import sys
import numpy as np
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import pickle
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.metrics import confusion_matrix
import preprocess as pp
import pandas as pd
import matplotlib.pyplot as plt
from D_GCAN import MolecularGraphNeuralNetwork,Trainer,Tester
def train (test_name,radius = 1,
    dim = 52 ,
    layer_hidden = 4,
    layer_output = 10,
    dropout = 0.45,
    batch_train = 8,
    batch_test = 8,
    lr =3e-4,
    lr_decay = 0.85,
    decay_interval = 25 ,
    iteration = 140,
    N = 5000    ,dataset_train='../dataset/data_train.txt'):

    dataset_test = test_name

    (radius, dim, layer_hidden, layer_output,
     batch_train, batch_test, decay_interval,
     iteration, dropout) = map(int, [radius, dim, layer_hidden, layer_output,
                                     batch_train, batch_test,
                                     decay_interval, iteration, dropout])
                                     
    lr, lr_decay = map(float, [lr, lr_decay])
    if torch.cuda.is_available():
        device = torch.device('cuda')
        print('The code uses a GPU!')
    else:
        device = torch.device('cpu')
        print('The code uses a CPU...')

    lr, lr_decay = map(float, [lr, lr_decay])

    print('-' * 100)
    print('Just a moment......')
    print('-' * 100)
    path = ''
    dataname = ''
    
    dataset_train=   pp.create_dataset(dataset_train,path,dataname)
    dataset_train,dataset_dev = pp.split_dataset(dataset_train,0.9)
    dataset_test= pp.create_dataset(dataset_test,path,dataname)
    np.random.seed(0)
    np.random.shuffle(dataset_train)
    np.random.shuffle(dataset_test)

    print('The preprocess has finished!')
    print('# of training data samples:', len(dataset_train))
    # print('# of development data samples:', len(dataset_dev))
    print('# of test data samples:', len(dataset_test))
    print('-' * 100)

    print('Creating a model.')
    torch.manual_seed(0)
    model = MolecularGraphNeuralNetwork(
        N, dim, layer_hidden, layer_output, dropout).to(device)
    trainer = Trainer(model,lr,batch_train)
    tester = Tester(model,batch_test)
    print('# of model parameters:',
          sum([np.prod(p.size()) for p in model.parameters()]))
    print('-' * 100)
    file_result = path + 'AUC' + '.txt'
    #    file_result = '../output/result--' + setting + '.txt'
    result = 'Epoch\tTime(sec)\tLoss_train\tLoss_test\tAUC_train\tAUC_test'
    file_test_result = path + 'test_prediction' + '.txt'
    file_predictions = path + 'train_prediction' + '.txt'
    file_model = '../D_GCAN/model/model' + '.h5'
    with open(file_result, 'w') as f:
        f.write(result + '\n')

    print('Start training.')
    print('The result is saved in the output directory every epoch!')

    np.random.seed(0)

    start = timeit.default_timer()

    for epoch in range(iteration):

        epoch += 1
        if epoch % decay_interval == 0:
            trainer.optimizer.param_groups[0]['lr'] *= lr_decay
        # [‘amsgrad’, ‘params’, ‘lr’, ‘betas’, ‘weight_decay’, ‘eps’]
        prediction_train, loss_train, train_res = trainer.train(dataset_train)
        prediction_test, loss_test, test_res = tester.test_classifier(dataset_test)

        time = timeit.default_timer() - start

        if epoch == 1:
            minutes = time * iteration / 60
            hours = int(minutes / 60)
            minutes = int(minutes - 60 * hours)
            print('The training will finish in about',
                  hours, 'hours', minutes, 'minutes.')
            print('-' * 100)
            print(result)

        result = '\t'.join(map(str, [epoch, time, loss_train, loss_test, prediction_train, prediction_test]))
        tester.save_result(result, file_result)
        tester.save_model(model, file_model)
        print(result)

    prediction_test, loss_test, test_res = tester.test_classifier(dataset_test)
    res_test = test_res.T

    cnf_matrix = confusion_matrix(res_test[:, 0], res_test[:, 1])
    cnf_matrix

    tn = cnf_matrix[0, 0]
    tp = cnf_matrix[1, 1]
    fn = cnf_matrix[1, 0]
    fp = cnf_matrix[0, 1]

    bacc = ((tp / (tp + fn)) + (tn / (tn + fp))) / 2  # balance accurance
    pre = tp / (tp + fp)  # precision/q+
    rec = tp / (tp + fn)  # recall/se
    sp = tn / (tn + fp)
    q_ = tn / (tn + fn)
    f1 = 2 * pre * rec / (pre + rec)  # f1score
    mcc = ((tp * tn) - (fp * fn)) / math.sqrt(
        (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))  # Matthews correlation coefficient
    acc = (tp + tn) / (tp + fp + fn + tn)  # accurancy
    fpr, tpr, thresholds = roc_curve(res_test[:, 0], res_test[:, 1])
    print('bacc:', bacc)
    print('pre:', pre)
    print('rec:', rec)
    print('f1:', f1)
    print('mcc:', mcc)
    print('sp:', sp)
    print('q_:', q_)
    print('acc:', acc)
    print('auc:', prediction_test)
       
    
    
    res_train = train_res.T
    cn_matrix = confusion_matrix(res_train[:, 0], res_train[:, 1])
    cn_matrix

    tn1 = cn_matrix[0, 0]
    tp1 = cn_matrix[1, 1]
    fn1 = cn_matrix[1, 0]
    fp1 = cn_matrix[0, 1]

    bacc_train = ((tp1 / (tp1 + fn1)) + (tn1 / (tn1 + fp1))) / 2  # balance accurance
    pre_train = tp1 / (tp1 + fp1)  # precision/q+
    rec_train = tp1 / (tp1 + fn1)  # recall/se
    sp_train = tn1 / (tn1 + fp1)
    q__train = tn1 / (tn1 + fn1)
    f1_train = 2 * pre_train * rec_train / (pre_train + rec_train)  # f1score
    mcc_train = ((tp1 * tn1) - (fp1 * fn1)) / math.sqrt(
        (tp1 + fp1) * (tp1 + fn1) * (tn1 + fp1) * (tn1 + fn1))  # Matthews correlation coefficient
    acc_train = (tp1 + tn1) / (tp1 + fp1 + fn1 + tn1)  # accurancy
    fpr_train, tpr_train, thresholds_train = roc_curve(res_train[:, 0], res_train[:, 1])
    print('bacc_train:', bacc_train)
    print('pre_train:', pre_train)
    print('rec_train:', rec_train)
    print('f1_train:', f1_train)
    print('mcc_train:', mcc_train)
    print('sp_train:', sp_train)
    print('q__train:', q__train)
    print('acc_train:', acc_train)
    return res_test
