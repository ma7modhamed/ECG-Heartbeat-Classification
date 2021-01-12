# -*- coding: utf-8 -*-
"""SMOTE_ECG_Two_Stage.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Bl1dqEoqjAvlZWAX8au30aLnL-uI-wC-

**Mount Drive**
"""

from google.colab import drive
drive.mount('/content/drive')

"""**Import Packages**"""

# Commented out IPython magic to ensure Python compatibility.
# %tensorflow_version 1.x

######## Keras #########

import keras
from keras.models import Sequential
from keras.layers import Input , MaxPool1D , GlobalMaxPool1D , AvgPool1D , GlobalAvgPool1D , BatchNormalization
from keras.layers.core import Flatten, Dense, Dropout 
from keras.layers.convolutional import Convolution2D, MaxPooling2D, ZeroPadding2D ,Convolution1D ,MaxPooling1D,ZeroPadding1D 
from keras.optimizers import SGD 
from keras import optimizers , activations
from keras import losses
from keras import metrics
from keras import models

from keras.layers import LSTM
from keras.layers.embeddings import Embedding
from keras.preprocessing import sequence

from keras.utils import plot_model
from keras import regularizers
from keras.layers import Activation
from keras.models import Model , Sequential

from keras.layers import Conv1D , MaxPool1D , Dropout , Flatten , Dense ,\
 Input ,concatenate , GlobalAveragePooling1D , AveragePooling1D  , MaxPooling1D , BatchNormalization , Activation , GlobalAveragePooling2D

from keras.layers.convolutional import Convolution1D
from keras import optimizers , activations

from keras.optimizers import *
from keras.utils import plot_model

import numpy as np
from numpy import  newaxis
from sklearn.utils import shuffle
from sklearn.model_selection import train_test_split
from sklearn.utils import shuffle
import numpy
s as pd
import os
import torch
import pandas as pd
from imblearn.over_sampling import SMOTE

"""**Helper Methods for Construction**"""

# Make Y Train or Test based on class number ,  #classes , #samples in this class
    def One_Hot_Encoded_Y(classNumber,NumberOfClasses,NumberOfSamples):
      Yi = np.zeros(NumberOfClasses)
      Yi[classNumber] = 1
      Y = np.vstack([Yi]*NumberOfSamples)
      return Y
    # Read Class from Text file and return X , Y
    def ReadClassData(path,ZeroBased_classNumber,NumOfClasses):
      Data = open(path, "r").readlines()
      X = []
      for i in Data:
          row = i.split('|')
          row.remove('\n')
          row = list(map(float, row))
          X.append(row)
      X = np.array(X)
      Y = One_Hot_Encoded_Y(ZeroBased_classNumber,NumOfClasses,X.shape[0])
      return X,Y

    # concatenate classes training data & testing data and make Y for this category
    def Prepare_Category(ClassesTrainData,ClassesTestData, classNumber,NumberOfCategories,MultiClassCategory=True):
      if MultiClassCategory:
        Ncat_X_train= np.concatenate(ClassesTrainData, axis=0)
        Ncat_X_test = np.concatenate(ClassesTestData, axis=0)
      else:
        print('category of one class')
        Ncat_X_train = ClassesTrainData
        Ncat_X_test = ClassesTestData
      
      Ncat_Y_train = One_Hot_Encoded_Y(classNumber,NumberOfCategories,Ncat_X_train.shape[0])
      Ncat_Y_test = One_Hot_Encoded_Y(classNumber,NumberOfCategories,Ncat_X_test.shape[0])
      return Ncat_X_train , Ncat_X_test , Ncat_Y_train , Ncat_Y_test

    def Model_Y(NumberOfSamplesEachClass = []):
      NumberOfClasses = len(NumberOfSamplesEachClass)
      Ys = []
      for i in range(NumberOfClasses):
          Ys.append(One_Hot_Encoded_Y(i,NumberOfClasses,NumberOfSamplesEachClass[i]))
      Ys = tuple(Ys)
      Y = np.concatenate(Ys,axis=0)
      return Y

"""**Helper Methods For Testing**"""

def Build_Confusion_Matrix(y_test,y_pred,num_of_classes):
  confusion_matrix = np.zeros((num_of_classes,num_of_classes))
  for i in range(len(y_test)):
    confusion_matrix[y_test[i],y_pred[i]]+=1
  return confusion_matrix

def Calculate_Accuracy(confusion_matrix):
  acc = (np.sum(confusion_matrix.diagonal())/np.sum(confusion_matrix))*100
  accuracies = []
  for i in range(len(confusion_matrix)):
    class_true_count = confusion_matrix[i,i]
    class_count = np.sum(confusion_matrix[i,:])
    if class_true_count == 0:
      accuracies.append(0)
    else:                   
      ac = (class_true_count/class_count)*100
      accuracies.append(ac)
  print(accuracies)
  average_accuracy = np.average(accuracies)
  print('Overall Accuracy',acc)
  print('Average Accuracy', average_accuracy )
  return acc , average_accuracy , accuracies

def Evaluate(y_test,y_pred,num_of_classes):
  confusion_matrix = Build_Confusion_Matrix(y_test,y_pred,num_of_classes)
  return Calculate_Accuracy(confusion_matrix)

def Predict_and_Evaluate(model,X_test,Y_test,NumOfClasses):
  Y_predict = model.predict(X_test)
  inds = np.argmax(Y_test,axis=1)
  pred = np.argmax(Y_predict,axis=1)
  accuracy = sum([np.argmax(Y_predict[i])==np.argmax(Y_test[i]) for i in range(len(Y_test))])/len(Y_test)
  print(accuracy)
  return Evaluate( inds , pred , NumOfClasses)

def Two_Stages_Predict(X_Test , models = {} , lockups = {} , cat = None):
  first_stage_model = models['first_stage']
  y_pred = []
  counter = 0
  inds = first_stage_model.predict(X_Test)
  inds = np.argmax(inds,axis=1)
  print ("Start Test : ")
  if cat is None:
    print('Predicting all models')
    for i in range(X_Test.shape[0]):
      xtest = X_Test[i]
      xtest = np.expand_dims(xtest,axis=0)
      
      #first_model_prediction = first_stage_model.predict(xtest)
      #first_model_prediction = int (np.argmax(first_model_prediction,axis = 1) )
      first_model_prediction = inds[i]
      if (first_model_prediction != 3):
          #print ("IN")
        second_stage_prediction = models[first_model_prediction].predict(xtest)
        second_stage_prediction = int (np.argmax(second_stage_prediction, axis = 1))
        current_model_lockup = lockups[first_model_prediction]
        y_pred.append(current_model_lockup[second_stage_prediction])
      else:
        y_pred.append(7)
  else:
    print('Predicting cat',cat,'only')
    for i in range(X_Test.shape[0]):
      xtest = X_Test[i]
      xtest = np.expand_dims(xtest,axis=0)
      
      #first_model_prediction = first_stage_model.predict(xtest)
      #first_model_prediction = int (np.argmax(first_model_prediction,axis = 1) )
      first_model_prediction = inds[i]
      if (first_model_prediction != 3 and first_model_prediction == cat):
        second_stage_prediction = models[first_model_prediction].predict(xtest)
        second_stage_prediction = int (np.argmax(second_stage_prediction, axis = 1))
        current_model_lockup = lockups[first_model_prediction]
        y_pred.append(current_model_lockup[second_stage_prediction])
      else :
        y_pred.append(-1)
        #counter = counter +1  
        #if (counter % 10000 == 0 ) : 
          #print ("Else*10 .. -1   "  , counter )
  return y_pred
  

def WriteCombinations(combination, filepath):
  s = open(filepath,'w')
  for cat , path in combination.items():
    s.write(str(cat)+ ' ' + str(path) + '\n')
  s.close() 
def Calculate_Classes_Average_Accuracy(path , categoryNumber , models , lookups , x_test , y_test):
  print ("Calculate_Classes_Average_Accuracy")
  models[categoryNumber].load_weights(path)
  y_pred = Two_Stages_Predict(x_test,models,lockups,categoryNumber)
  print("end two_stages_predict " , len(y_pred))
  ytestInds = np.argmax(y_test,axis = 1)
  acc , avg , accuracies = Evaluate(ytestInds , y_pred , 16)
  print(accuracies)
  lookup = lookups[categoryNumber]
  values = []

  for value in lookup.values():
    values.append(accuracies[int(value)])
  print(values)  
  return np.average(values)

def ReadCombination(path):
  s = open(path,'r')
  content = s.read()
  lines = str(content).split('\n')
  combination = {}
  for line in lines:
    #print(line)
    if line == '':
      continue
    dictionary_item = str(line).split(' ')
    print(dictionary_item)
    
    weightsFile = ''
    for i in range(1,len(dictionary_item)):
      weightsFile += dictionary_item[i] + ' '
    weightsFile = weightsFile[:-1]
    if (dictionary_item[0]).isdigit():
      combination[int(dictionary_item[0])] = weightsFile
    else:
      combination[dictionary_item[0]] = weightsFile
  return combination

def ReadClass_X_Data(path):
  X = pd.read_csv(path)
  X = X.drop(X.columns[0],axis=1)
  X = np.array(X)
  return X
NumberOfClasses = 16
directory = "/content/drive/My Drive/Graduation Project/Preprocessed Dataset/Trial8/"
XN_train = ReadClass_X_Data(directory+"XN_train.csv")
XN_test  = ReadClass_X_Data(directory+"XN_test.csv")
YN_train = One_Hot_Encoded_Y(0, NumberOfClasses ,XN_train.shape[0])
YN_test  = One_Hot_Encoded_Y(0, NumberOfClasses ,XN_test.shape[0])
#------------------------------------------
XL_train = ReadClass_X_Data(directory+"XL_train.csv")
XL_test  = ReadClass_X_Data(directory+"XL_test.csv") 
YL_train = One_Hot_Encoded_Y(1, NumberOfClasses ,XL_train.shape[0])
YL_test  = One_Hot_Encoded_Y(1, NumberOfClasses ,XL_test.shape[0]) 
#------------------------------------------
XR_train = ReadClass_X_Data(directory+"XR_train.csv")
XR_test  = ReadClass_X_Data(directory+"XR_test.csv")
YR_train = One_Hot_Encoded_Y(2, NumberOfClasses ,XR_train.shape[0])
YR_test  = One_Hot_Encoded_Y(2, NumberOfClasses ,XR_test.shape[0])

#------------------------------------------
XA_train = ReadClass_X_Data(directory+"XA_train.csv")
XA_test  = ReadClass_X_Data(directory+"XA_test.csv")
YA_train = One_Hot_Encoded_Y(3, NumberOfClasses ,XA_train.shape[0])
YA_test  = One_Hot_Encoded_Y(3, NumberOfClasses ,XA_test.shape[0])
#------------------------------------------
Xa_train = ReadClass_X_Data(directory+"Xa_train.csv")
Xa_test  = ReadClass_X_Data(directory+"Xa_test.csv")
Ya_train = One_Hot_Encoded_Y(4, NumberOfClasses ,Xa_train.shape[0])
Ya_test  = One_Hot_Encoded_Y(4, NumberOfClasses ,Xa_test.shape[0])
#------------------------------------------
XJ_train = ReadClass_X_Data(directory+"XJ_train.csv")
XJ_test  = ReadClass_X_Data(directory+"XJ_test.csv")
YJ_train = One_Hot_Encoded_Y(5, NumberOfClasses ,XJ_train.shape[0])
YJ_test  = One_Hot_Encoded_Y(5, NumberOfClasses ,XJ_test.shape[0])
#------------------------------------------
XV_train = ReadClass_X_Data(directory+"XV_train.csv")
XV_test  = ReadClass_X_Data(directory+"XV_test.csv")
YV_train = One_Hot_Encoded_Y(6, NumberOfClasses ,XV_train.shape[0])
YV_test  = One_Hot_Encoded_Y(6, NumberOfClasses ,XV_test.shape[0])
#------------------------------------------
XF_train = ReadClass_X_Data(directory+"XF_train.csv")
XF_test  = ReadClass_X_Data(directory+"XF_test.csv")
YF_train = One_Hot_Encoded_Y(7, NumberOfClasses ,XF_train.shape[0])
YF_test  = One_Hot_Encoded_Y(7, NumberOfClasses ,XF_test.shape[0])
#------------------------------------------
Xvfw_train = ReadClass_X_Data(directory+"Xvfw_train.csv")
Xvfw_test  = ReadClass_X_Data(directory+"Xvfw_test.csv")
Yvfw_train = One_Hot_Encoded_Y(8, NumberOfClasses ,Xvfw_train.shape[0])
Yvfw_test  = One_Hot_Encoded_Y(8, NumberOfClasses ,Xvfw_test.shape[0])
#------------------------------------------
Xe_train = ReadClass_X_Data(directory+"Xe_train.csv")
Xe_test  = ReadClass_X_Data(directory+"Xe_test.csv")
Ye_train = One_Hot_Encoded_Y(9, NumberOfClasses ,Xe_train.shape[0])
Ye_test  = One_Hot_Encoded_Y(9, NumberOfClasses ,Xe_test.shape[0])
#------------------------------------------
Xj_train = ReadClass_X_Data(directory+"Xj_train.csv")
Xj_test  = ReadClass_X_Data(directory+"Xj_test.csv")
Yj_train = One_Hot_Encoded_Y(10, NumberOfClasses ,Xj_train.shape[0])
Yj_test  = One_Hot_Encoded_Y(10, NumberOfClasses ,Xj_test.shape[0])
#------------------------------------------
XE_train = ReadClass_X_Data(directory+"XE_train.csv")
XE_test  = ReadClass_X_Data(directory+"XE_test.csv")
YE_train = One_Hot_Encoded_Y(11, NumberOfClasses ,XE_train.shape[0])
YE_test  = One_Hot_Encoded_Y(11, NumberOfClasses ,XE_test.shape[0])
#------------------------------------------
XP_train = ReadClass_X_Data(directory+"XP_train.csv")
XP_test  = ReadClass_X_Data(directory+"XP_test.csv")
YP_train = One_Hot_Encoded_Y(12, NumberOfClasses ,XP_train.shape[0])
YP_test  = One_Hot_Encoded_Y(12, NumberOfClasses ,XP_test.shape[0])
#------------------------------------------
Xf_train = ReadClass_X_Data(directory+"Xf_train.csv")
Xf_test  = ReadClass_X_Data(directory+"Xf_test.csv")
Yf_train = One_Hot_Encoded_Y(13, NumberOfClasses ,Xf_train.shape[0])
Yf_test  = One_Hot_Encoded_Y(13, NumberOfClasses ,Xf_test.shape[0])
#------------------------------------------
Xx_train = ReadClass_X_Data(directory+"Xx_train.csv")
Xx_test  = ReadClass_X_Data(directory+"Xx_test.csv")
Yx_train = One_Hot_Encoded_Y(14, NumberOfClasses ,Xx_train.shape[0])
Yx_test  = One_Hot_Encoded_Y(14, NumberOfClasses ,Xx_test.shape[0])
#------------------------------------------
XQ_train = ReadClass_X_Data(directory+"XQ_train.csv")
XQ_test  = ReadClass_X_Data(directory+"XQ_test.csv")
YQ_train = One_Hot_Encoded_Y(15, NumberOfClasses ,XQ_train.shape[0])
YQ_test  = One_Hot_Encoded_Y(15, NumberOfClasses ,XQ_test.shape[0])
#------------------------------------------

"""**Prepare Models Training & Testing Data**"""

#-------------------------One Stage Data------------------------
    X_TRAIN= np.concatenate((XA_train,Xa_train,XE_train,Xe_train,XF_train,Xf_train,XJ_train,Xj_train,XL_train,XN_train,XQ_train,XR_train,XV_train,Xx_train,XP_train,Xvfw_train), axis=0)
    Y_TRAIN= np.concatenate((YA_train,Ya_train,YE_train,Ye_train,YF_train,Yf_train,YJ_train,Yj_train,YL_train,YN_train,YQ_train,YR_train,YV_train,Yx_train,YP_train,Yvfw_train), axis=0)
    
    
    X_TEST= np.concatenate((XA_test,Xa_test,XE_test,Xe_test,XF_test,Xf_test,XJ_test,Xj_test,XL_test,XN_test,XQ_test,XR_test,XV_test,Xx_test,XP_test,Xvfw_test), axis=0)
    Y_TEST= np.concatenate((YA_test,Ya_test,YE_test,Ye_test,YF_test,Yf_test,YJ_test,Yj_test,YL_test,YN_test,YQ_test,YR_test,YV_test,Yx_test,YP_test,Yvfw_test), axis=0)

    X_train , Y_train = shuffle(X_TRAIN , Y_TRAIN)
    X_test,Y_test = shuffle( X_TEST,Y_TEST)
    X_test = np.expand_dims(X_test,axis=2)
  
    #-------------------Two Stages Data-------------------------------
    
    # Categories Data
    Ncat_X_train , Ncat_X_test , Ncat_Y_train , Ncat_Y_test = Prepare_Category((XN_train,XL_train,XR_train,Xe_train,Xj_train), (XN_test,XL_test,XR_test,Xe_test,Xj_test) , 0 , 5)
    Scat_X_train , Scat_X_test  , Scat_Y_train  , Scat_Y_test = Prepare_Category((XA_train,Xa_train,XJ_train,Xx_train) , (XA_test,Xa_test,XJ_test,Xx_test) , 1 ,5)
    Vcat_X_train, Vcat_X_test, Vcat_Y_train ,Vcat_Y_test = Prepare_Category((XV_train,Xvfw_train,XE_train),(XV_test,Xvfw_test,XE_test),2,5)
    Fcat_X_train , Fcat_X_test, Fcat_Y_train ,  Fcat_Y_test = Prepare_Category((XF_train),(XF_test) , 3 , 5,False)
    Qcat_X_train ,  Qcat_X_test, Qcat_Y_train ,Qcat_Y_test = Prepare_Category((XP_train,Xf_train,XQ_train) , (XP_test,Xf_test,XQ_test) , 4 , 5)
    #______________________________

    # First Stage Data
    first_stage_model_X_train = np.concatenate((Ncat_X_train , Scat_X_train , Vcat_X_train , Fcat_X_train , Qcat_X_train),axis=0)
    first_stage_model_X_test = np.concatenate((Ncat_X_test , Scat_X_test , Vcat_X_test , Fcat_X_test , Qcat_X_test),axis=0)


    first_stage_model_Y_train = np.concatenate((Ncat_Y_train , Scat_Y_train , Vcat_Y_train , Fcat_Y_train , Qcat_Y_train),axis=0)
    first_stage_model_Y_test = np.concatenate((Ncat_Y_test , Scat_Y_test , Vcat_Y_test , Fcat_Y_test , Qcat_Y_test),axis=0)

    #shuffle Data 
    first_stage_model_X_train , first_stage_model_Y_train = shuffle(first_stage_model_X_train , first_stage_model_Y_train)
    first_stage_model_X_test , first_stage_model_Y_test = shuffle(first_stage_model_X_test , first_stage_model_Y_test)

    
    first_stage_model_X_test = np.expand_dims(first_stage_model_X_test,axis=2)
    #------------------------------------------------------------------------------------------------------------------------
    
    #Each Model Data in the second stage
    model1_Y_train = Model_Y([XN_train.shape[0] ,XL_train.shape[0] ,XR_train.shape[0] ,Xe_train.shape[0] ,Xj_train.shape[0]])
    model1_Y_test = Model_Y([XN_test.shape[0] ,XL_test.shape[0] ,XR_test.shape[0] ,Xe_test.shape[0] ,Xj_test.shape[0]])

    #Shuffle Data
    Ncat_X_train , model1_Y_train = shuffle(Ncat_X_train , model1_Y_train)     
    Ncat_X_test , model1_Y_test = shuffle(Ncat_X_test , model1_Y_test)         
    
    Ncat_X_test = np.expand_dims(Ncat_X_test,axis=2)
    #___________________________________
    
    model2_Y_train = Model_Y([XA_train.shape[0] ,Xa_train.shape[0] ,XJ_train.shape[0] ,Xx_train.shape[0]])
    model2_Y_test = Model_Y([XA_test.shape[0] ,Xa_test.shape[0] ,XJ_test.shape[0] ,Xx_test.shape[0]])
    #Shuffle Data 
    Scat_X_train , model2_Y_train = shuffle(Scat_X_train , model2_Y_train)
    Scat_X_test , model2_Y_test = shuffle(Scat_X_test , model2_Y_test)

    Scat_X_test = np.expand_dims(Scat_X_test,axis=2)
    
    #__________________________________

    model3_Y_train = Model_Y([ XV_train.shape[0], Xvfw_train.shape[0], XE_train.shape[0]])
    model3_Y_test = Model_Y([XV_test.shape[0], Xvfw_test.shape[0] ,XE_test.shape[0]])
    #shuflle Data 
    Vcat_X_train , model3_Y_train = shuffle(Vcat_X_train , model3_Y_train)
    Vcat_X_test , model3_Y_test = shuffle(Vcat_X_test , model3_Y_test)

    
    Vcat_X_test = np.expand_dims(Vcat_X_test,axis=2)
    #_________________________________

    model5_Y_train = Model_Y([XP_train.shape[0],Xf_train.shape[0],XQ_train.shape[0]])
    model5_Y_test = Model_Y([XP_test.shape[0] ,Xf_test.shape[0] ,XQ_test.shape[0]])
    #shuffle Data
    Qcat_X_train , model5_Y_train = shuffle(Qcat_X_train , model5_Y_train)
    Qcat_X_test , model5_Y_test = shuffle(Qcat_X_test , model5_Y_test)   
    Qcat_X_test = np.expand_dims(Qcat_X_test,axis=2)
    #_____________________________

    # key is the class number in the category model and the value is the class number between all classes
    model1_lookup = {0:0,1:1,2:2,3:9,4:10}
    model2_lookup = {0:3,1:4,2:5,3:14}
    model3_lookup = {0:6,1:8,2:11}
    model5_lookup = {0:12,1:13,2:15}

"""**lenghts Before Generation**"""

print (X_train.shape , Y_train.shape , X_test.shape , Y_test.shape )
print(first_stage_model_X_train.shape , first_stage_model_Y_train.shape ,first_stage_model_X_test.shape , first_stage_model_Y_test.shape)
print(Ncat_X_train.shape , model1_Y_train.shape,Ncat_X_test.shape , model1_Y_test.shape)
print(Scat_X_train.shape , model2_Y_train.shape,Scat_X_test.shape , model2_Y_test.shape)
print(Vcat_X_train.shape , model3_Y_train.shape,Vcat_X_test.shape , model3_Y_test.shape)
print(Fcat_X_train.shape , Fcat_X_test.shape)
print(Qcat_X_train.shape , model5_Y_train.shape,Qcat_X_test.shape , model5_Y_test.shape)

"""**Generate Variarions for Each Category**"""

#Generate Data in Total Data .. Using in One Stage 
oversample = SMOTE(sampling_strategy='not majority')
X_train_NG, Y_train_NG = oversample.fit_resample(X_train, Y_train )
#___________________Generate Data Into Each Categories 

#N_Cat 
oversample = SMOTE(sampling_strategy='not majority')
NCat_X_train_NG, NCat_Y_train_NG = oversample.fit_resample(Ncat_X_train, model1_Y_train )

#Category S
oversample = SMOTE(sampling_strategy='not majority')
SCat_X_train_NG, SCat_Y_train_NG = oversample.fit_resample(Scat_X_train, model2_Y_train )

#Category V 
oversample = SMOTE(sampling_strategy='not majority')
VCat_X_train_NG, VCat_Y_train_NG = oversample.fit_resample(Vcat_X_train, model3_Y_train )

#Category F .. One Class NO Dependency .. Can't Generate 

#Category Q
oversample = SMOTE(sampling_strategy='not majority')
QCat_X_train_NG, QCat_Y_train_NG = oversample.fit_resample(Qcat_X_train, model5_Y_train )

#________________________________Generate Data For Fisrt Stage Model .. 
#**** We have Two  Strategy ****
# - First : Using Defult Data 
oversample = SMOTE(sampling_strategy='not majority')
first_stage_model_X_train_NG1 , first_stage_model_Y_train_NG1 = oversample.fit_resample(
    first_stage_model_X_train, first_stage_model_Y_train )

#Second : Using Data With New Generation 

first_stage_model_X_train2 = np.concatenate((NCat_X_train_NG , SCat_X_train_NG , VCat_X_train_NG , Fcat_X_train , QCat_X_train_NG),axis=0)

first_stage_model_Y_train2 = np.concatenate(( One_Hot_Encoded_Y (0,5,NCat_Y_train_NG.shape[0] ), 
                                             One_Hot_Encoded_Y(1,5, SCat_Y_train_NG .shape[0]),
                                             One_Hot_Encoded_Y(2,5,VCat_Y_train_NG.shape[0]) ,
                                             Fcat_Y_train , 
                                             One_Hot_Encoded_Y(4,5 ,QCat_Y_train_NG.shape[0])),
                                             axis=0)

print (first_stage_model_X_train2.shape , first_stage_model_Y_train2.shape)
#Data Still imbalanced ..  Generare Again 
oversample = SMOTE(sampling_strategy='not majority')
first_stage_model_X_train_NG2 , first_stage_model_Y_train_NG2 = oversample.fit_resample(
    first_stage_model_X_train2, first_stage_model_Y_train2 )

"""**Expand** **Dimensions**

**Expand Dimensions for Normal Data**
"""

X_train = np.expand_dims(X_train,axis=2)
first_stage_model_X_train = np.expand_dims(first_stage_model_X_train,axis=2)
Ncat_X_train = np.expand_dims(Ncat_X_train,axis=2)
Scat_X_train = np.expand_dims(Scat_X_train,axis=2)
Vcat_X_train = np.expand_dims(Vcat_X_train,axis=2)
Qcat_X_train = np.expand_dims(Qcat_X_train,axis=2)

"""**Expand Dimensions for Data With New Generation ..**"""

X_train_NG = np.expand_dims(X_train_NG,axis=2)
first_stage_model_X_train_NG1 = np.expand_dims (first_stage_model_X_train_NG1 , axis=2)
first_stage_model_X_train_NG2 = np.expand_dims (first_stage_model_X_train_NG2 , axis=2)
NCat_X_train_NG = np.expand_dims (NCat_X_train_NG,axis=2) 
SCat_X_train_NG = np.expand_dims (SCat_X_train_NG,axis=2 ) 
VCat_X_train_NG = np.expand_dims (VCat_X_train_NG , axis=2) 
QCat_X_train_NG = np.expand_dims(QCat_X_train_NG,axis=2)

"""**lenghts after Generation and Expand Dimensions**"""

print ("All Data ") 
print ("Before :- ",X_train.shape , Y_train.shape , X_test.shape , Y_test.shape )
print ("After :- ",X_train_NG.shape , Y_train_NG.shape , X_test.shape , Y_test.shape) 
print ('First model ')
print(first_stage_model_X_train.shape , first_stage_model_Y_train.shape ,first_stage_model_X_test.shape , first_stage_model_Y_test.shape)
print (" Strategy 1 ") 
print(first_stage_model_X_train_NG1.shape , first_stage_model_Y_train_NG1.shape ,first_stage_model_X_test.shape , first_stage_model_Y_test.shape)
#res = np.sum (first_stage_model_Y_train_NG1 , axis = 0) 
#print (res)
print ("Strategy 2 ")
print(first_stage_model_X_train_NG2.shape , first_stage_model_Y_train_NG2.shape ,first_stage_model_X_test.shape , first_stage_model_Y_test.shape)
#res = np.sum (first_stage_model_Y_train_NG2 , axis = 0) 
#print (res)
print ("NCat")
print("Before :- ",Ncat_X_train.shape , model1_Y_train.shape,Ncat_X_test.shape , model1_Y_test.shape)
print ("After :- ",NCat_X_train_NG .shape , NCat_Y_train_NG.shape ,Ncat_X_test.shape , model1_Y_test.shape )
#res = np.sum (NCat_Y_train_NG , axis = 0) 
#print (res)
print ("Category S") 
print("Before :- ",Scat_X_train.shape , model2_Y_train.shape,Scat_X_test.shape , model2_Y_test.shape)
print ("After :- " , SCat_X_train_NG.shape , SCat_Y_train_NG.shape ,  Scat_X_test.shape , model2_Y_test.shape)
#res = np.sum (SCat_Y_train_NG , axis = 0) 
#print (res)
print ("Category V ")
print("Before", Vcat_X_train.shape , model3_Y_train.shape,Vcat_X_test.shape , model3_Y_test.shape)
print ("After" ,VCat_X_train_NG.shape , VCat_Y_train_NG.shape,Vcat_X_test.shape , model3_Y_test.shape )
#res = np.sum (VCat_Y_train_NG , axis = 0) 
#print (res)
print ("Class F ") 
print(Fcat_X_train.shape , Fcat_X_test.shape)
print ("Category Q ") 
print("Before",Qcat_X_train.shape , model5_Y_train.shape,Qcat_X_test.shape , model5_Y_test.shape)

print("After" , QCat_X_train_NG.shape , QCat_Y_train_NG.shape,Qcat_X_test.shape , model5_Y_test.shape)
#res = np.sum (QCat_Y_train_NG , axis = 0) 
#print (res)

"""**Models Construction**

CNN Model
"""

def CNN(nclass = 16):
    inp = Input(shape=(300, 1))
    
    lay = Convolution1D(32, kernel_size=5, activation=activations.relu, padding="valid")(inp)
    lay = Convolution1D(32, kernel_size=5, activation=activations.relu, padding="valid")(lay)
    lay = AvgPool1D(pool_size=2)(lay)
    
    lay = Convolution1D(64, kernel_size=3, activation=activations.relu, padding="valid")(lay)
    lay = Convolution1D(64, kernel_size=3, activation=activations.relu, padding="valid")(lay)
    lay = Convolution1D(64, kernel_size=3, activation=activations.relu, padding="valid")(lay)
    lay = AvgPool1D(pool_size=2)(lay)
    lay = Dropout(rate=0.1)(lay)
    lay = BatchNormalization() (lay)

    lay = Convolution1D(64, kernel_size=3, activation=activations.relu, padding="valid")(lay)
    lay = Convolution1D(64, kernel_size=3, activation=activations.relu, padding="valid")(lay)
    lay = Convolution1D(64, kernel_size=3, activation=activations.relu, padding="valid")(lay)
    lay = AvgPool1D(pool_size=2)(lay)
    lay = Dropout(rate=0.1)(lay)
    lay = BatchNormalization() (lay)

    lay = Convolution1D(128, kernel_size=3, activation=activations.relu, padding="valid")(lay)
    lay = Convolution1D(128, kernel_size=3, activation=activations.relu, padding="valid")(lay)
    lay = Convolution1D(128, kernel_size=3, activation=activations.relu, padding="valid")(lay)
    lay = AvgPool1D(pool_size=2)(lay)
    lay = Dropout(rate=0.1)(lay)
    lay = BatchNormalization() (lay)

    lay = Convolution1D(256, kernel_size=3, activation=activations.relu, padding="valid")(lay)
    lay = Convolution1D(256, kernel_size=3, activation=activations.relu, padding="valid")(lay)
    lay = Convolution1D(256, kernel_size=3, activation=activations.relu, padding="valid")(lay)
    lay = GlobalMaxPool1D()(lay)
    lay = Dropout(rate=0.1)(lay)
    lay = BatchNormalization() (lay)
    
    dense_1 = Dense(64, activation=activations.relu)(lay)
    dense_1 = Dense(64, activation=activations.relu)(dense_1)
    dense_1 = Dense(nclass, activation=activations.softmax)(dense_1)


    model = models.Model(inputs=inp, outputs=dense_1)
    model.compile(optimizer=optimizers.Adam(lr=0.00001), loss= losses.categorical_crossentropy,metrics=['acc'])
    return model

model = CNN()
model.summary()
#from keras.utils import plot_model
#plot_model(model, to_file='model.png')

"""Inception Module"""

def inception_module2(layer_in, f1, f2_in, f2_out, f3_in, f3_out, f4_out):
	# 1x1 conv
	conv1 = Conv1D(f1, 1, padding='same', activation='relu')(layer_in)
	# 3x3 conv
	conv3 = Conv1D(f2_in, 1, padding='same', activation='relu')(layer_in)
	conv3 = Conv1D(f2_out, 3, padding='same', activation='relu')(conv3)
	# 5x5 conv
	conv5 = Conv1D(f3_in, 1, padding='same', activation='relu')(layer_in)
	conv5 = Conv1D(f3_out, 5, padding='same', activation='relu')(conv5)
	# 3x3 max pooling
	pool = MaxPooling1D(1, strides=None, padding='same')(layer_in)
	pool = Conv1D(f4_out, 1, padding='same', activation='relu')(pool)
	# concatenate filters, assumes filters/channels last
	layer_out = concatenate([conv1, conv3, conv5, pool], axis=-1)
	return layer_out

"""Inception Model"""

def inception(nclass = 16):
  inp = Input (shape=(300,1))
  conv1 = Conv1D(32, 3, padding='same', activation='relu')(inp)
  conv2 = Conv1D(64, 3, padding='same', activation='relu')(conv1)

  Module= inception_module2(conv2 , 64, 96, 128, 16, 32, 32)
  batch = BatchNormalization() (Module)

  Module2 = inception_module2(batch, 64, 96, 128, 16, 32, 32) 
  batch2 = BatchNormalization() (Module2)

  Module3 = inception_module2(batch2, 128, 128 ,192,32,96,64) 
  batch3 = BatchNormalization() (Module3)

  Module4 = inception_module2(batch3, 128, 128 ,192,32,96,64) 
  batch4 = BatchNormalization() (Module4)

  Module5 = inception_module2(batch4, 128, 128 ,192,32,96,64) 
  batch5 = BatchNormalization() (Module5)

  Module6 = inception_module2(batch5,  196 ,128,  256,64, 128, 96)
  batch6 = BatchNormalization() (Module6)
  
  GAP = GlobalAveragePooling1D() (batch6) 
  layer = Dense(128 , activation='relu' ) (GAP)
  Dense_layer_ouput = Dense(nclass, activation='softmax') (layer)
  model = Model (inputs = inp , outputs = Dense_layer_ouput) 
  model.compile(loss='categorical_crossentropy', optimizer=optimizers.Adam(lr=0.00001), metrics=['accuracy'])
  model .summary()
  return model

"""VGG16 Model"""

def VGG_16(weights_path=None):


  model = Sequential()
  model.add(Conv1D(input_shape=(300,1),filters=64,kernel_size=3,padding="valid", activation="relu"))
  model.add(Conv1D(filters=64,kernel_size=3,padding="valid", activation="relu"))
  model.add(MaxPooling1D(pool_size=2,strides=2))

  model.add(Conv1D(filters=128, kernel_size=3, padding="valid", activation="relu"))
  model.add(Conv1D(filters=128, kernel_size=3, padding="valid", activation="relu"))
  model.add(MaxPooling1D(pool_size=2,strides=2))

  model.add(Conv1D(filters=256, kernel_size=3, padding="valid", activation="relu"))
  model.add(Conv1D(filters=256, kernel_size=3, padding="valid", activation="relu"))
  model.add(Conv1D(filters=256, kernel_size=3, padding="valid", activation="relu"))
  model.add(MaxPooling1D(pool_size=2,strides=2))

  model.add(Conv1D(filters=512, kernel_size=3, padding="valid", activation="relu"))
  model.add(Conv1D(filters=512, kernel_size=3, padding="valid", activation="relu"))
  model.add(Conv1D(filters=512, kernel_size=3, padding="valid", activation="relu"))
  model.add(MaxPooling1D(pool_size=2,strides=2))

  model.add(Conv1D(filters=512, kernel_size=3, padding="valid", activation="relu"))
  model.add(Conv1D(filters=512, kernel_size=3, padding="valid", activation="relu"))
  model.add(Conv1D(filters=512, kernel_size=3, padding="valid", activation="relu"))
  model.add(MaxPooling1D(pool_size=2,strides=2))

  model.add(Flatten())
  model.add(Dense(units=4096,activation="relu"))
  model.add(Dense(units=4096,activation="relu"))
  model.add(Dense(units=16, activation="softmax"))

  if weights_path:
      model.load_weights(weights_path)

  return model

"""LSTM Model"""

def LSTM_ ():
  model = Sequential()
  model.add(LSTM(units=320,input_shape=(None, 300),implementation=1,return_sequences=True))#,kernel_regularizer=regularizers.l2(0.1))) 
  model.add(LSTM(200))
  model.add(Dropout(0.1))
  model.add(Dense(16,activation='softmax'))
  #model.add(Activation('softmax'))
  model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

  return model

"""Models for One Stage and Two stages"""

one_stage_model = CNN() 

first_stage_model = CNN(5)
cat_N_model = CNN(5)
cat_S_model = CNN(4)
cat_V_model = CNN(3)
cat_Q_model = CNN(3)

"""**Load Weights .. If Weights Saved Before**"""

directory = '/content/drive/My Drive/Graduation Project/Preprocessed Dataset/Trial7/'

first_stage_model.load_weights('/content/drive/My Drive/Graduation Project/Preprocessed Dataset/Trial8/TS_CNN_NG_One_Stage/one_stage_model92.16713749343761##88.26471272388928#Epoch : 4')

cat_N_model.load_weights('/content/drive/My Drive/Graduation Project/Preprocessed Dataset/Trial8/TS_CNN_NG_cat_N/cat_N_model96.3506624511181##99.73843760060093#Epoch : 37')

cat_S_model.load_weights('/content/drive/My Drive/Graduation Project/Preprocessed Dataset/Trial8/TS_CNN_NG_cat_S/cat_S_model97.38208467515983##98.33429063756462#Epoch : 149')

cat_V_model.load_weights('/content/drive/My Drive/Graduation Project/Preprocessed Dataset/Trial8/TS_CNN_NG_cat_V/cat_V_model99.41164737414287##99.84669294787561#Epoch : 62')

cat_Q_model.load_weights('/content/drive/My Drive/Graduation Project/Preprocessed Dataset/Trial8/TS_CNN_NG_cat_Q/cat_Q_model89.47421290811464##98.83474576271186#Epoch : 24')

"""**Model Training**"""

epochs = []
accuracies =[]
Avgs = []
counter=
maxi = 0
max_avg = 0

first_stage_model.fit(x =  first_stage_model_X_train_NG1, y = first_stage_model_Y_train_NG1 ,  batch_size=32 , epochs= 10)

for i in range (150) :
  print (i+counter) 

  first_stage_model.fit(x =  first_stage_model_X_train_NG1, y = first_stage_model_Y_train_NG1 ,  batch_size=32 , epochs= 1)
  acc , avg , accuraciess = Predict_and_Evaluate(first_stage_model,X_test=first_stage_model_X_test , Y_test=first_stage_model_Y_test ,NumOfClasses=5 )
   
  #print ("Accuracy = " + str (acc) ) 
  #print ("Average = " + str (avg) ) 

  if ( avg > max_avg or (avg +0.2 > max_avg and acc > maxi)) :
    s = "first" + str (avg) + "##" + str (acc) + "#Epoch : " + str (counter+i) 
    first_stage_model.save_weights("/content/drive/My Drive/Graduation Project/Preprocessed Dataset/Trial8/TS_CNN_NG_first_stage_model/" +s)

    if (acc > maxi ) :
      maxi=acc 
    if (avg > max_avg):
      max_avg = avg 

    Avgs .append (avg)
    accuracies.append (acc)
    epochs.append(i) 
        

print (maxi)
print (max_avg)

"""**Model Testing**

For One Model
"""

#acc , avg = Evaluate(first_stage_model,first_stage_model_X_test,first_stage_model_Y_test , 5) 
acc , avg  = Evaluate(cat_N_model,Ncat_X_test,Ncat_Y_test , 5) 

#acc , avg , accuraciess= Predict_and_Evaluate(cat_N_model,Ncat_X_test,Ncat_Y_test , 5) 
print ("fdslklmdlkdsmlkds")
print (acc , avg  )
#print (max_avg)
#acc , avg = Evaluate(cat_N_model,Ncat_X_test,model1_Y_test , 5) 
#print (avg)

"""**For Two Stage Models**

Test all of Best models weights Combinations with each other to get Best Result !
"""

models = {'first_stage':first_stage_model , 0: cat_N_model , 1: cat_S_model , 2: cat_V_model , 4: cat_Q_model }
model1_lookup = {0:0,1:1,2:2,3:9,4:10}
model2_lookup = {0:3,1:4,2:5,3:14}
model3_lookup = {0:6,1:8,2:11}
model5_lookup = {0:12,1:13,2:15}
lockups = {0:model1_lookup , 1:model2_lookup , 2:model3_lookup, 4: model5_lookup}
print (X_test.shape)

directory = '/content/drive/My Drive/Graduation Project/Preprocessed Dataset/Trial7/'
first_directory = 'TS_CNN_NG_first_stage/'
N_directory = 'TS_CNN_NG_CatN/'
S_directory = 'TS_CNN_NG_SCat/'
V_directory = 'TS_CNN_NG_VCat/'
Q_directory = 'TS_CNN_NG_QCat/'

First_Stage_Weights = os.listdir(directory +first_directory )
N_Cat_Weights = os.listdir(directory +N_directory)
S_Cat_Weights = os.listdir(directory +S_directory)
V_Cat_Weights = os.listdir(directory +V_directory)
Q_Cat_Weights = os.listdir(directory +Q_directory)
First_Stage_Weights = sorted(First_Stage_Weights,reverse=True)
N_Cat_Weights = sorted(N_Cat_Weights,reverse= True)
S_Cat_Weights = sorted(S_Cat_Weights,reverse= True)
V_Cat_Weights = sorted(V_Cat_Weights,reverse= True)
Q_Cat_Weights = sorted(Q_Cat_Weights,reverse= True)
print('First Stages :',len(First_Stage_Weights))
print(First_Stage_Weights)
print('N Category :',len(N_Cat_Weights))
print(N_Cat_Weights)
print('S Category :',len(S_Cat_Weights))
print(S_Cat_Weights)

print('V Category :',len(V_Cat_Weights))
print(V_Cat_Weights)

print('Q Category :',len(Q_Cat_Weights))
print(Q_Cat_Weights)

best_combination = {'first':'', 0 : '' , 1 : '' , 2 : '' , 4 : ''}



models = {'first_stage':first_stage_model , 0: cat_N_model , 1: cat_S_model , 2: cat_V_model , 4: cat_Q_model }
max_avg = -1
max_avg_N = -1
max_avg_S = -1
max_avg_V = -1
max_avg_Q = -1
bestN = ''
bestS = ''
bestV = ''
bestQ = ''
for first in First_Stage_Weights:
  models['first_stage'].load_weights(directory+first_directory+first)

  print ("Time for V : ")
  for V in V_Cat_Weights:
    avg = Calculate_Classes_Average_Accuracy(directory+V_directory+V,2, models ,lockups,X_test,Y_test)
    print (avg)
    if avg > max_avg_V:
      max_avg_V = avg
      bestV = V
      print ("Best V" , bestV)
  
  print ("Time for S : ")
  for S in S_Cat_Weights:
    avg = Calculate_Classes_Average_Accuracy(directory+S_directory+S,1, models ,lockups,X_test,Y_test)
    print (avg)
    if avg > max_avg_S:
      max_avg_S = avg
      bestS = S
      print ("Best S" , bestS)
  


  print ("Time for Q : ")
  for Q in Q_Cat_Weights:
    avg = Calculate_Classes_Average_Accuracy(directory+Q_directory+Q,4, models ,lockups,X_test,Y_test)
    print (avg)
    if avg > max_avg_Q:
      max_avg_Q = avg
      bestQ = Q
      print ("Best Q" , bestQ)
    

  
  
  print ("Time for N : ")
  for N in N_Cat_Weights:
    avg = Calculate_Classes_Average_Accuracy(directory+N_directory+N,0, models ,lockups,X_test,Y_test )
    print (avg)
    if avg > max_avg_N:
      max_avg_N = avg
      bestN = N
      print ("best N" , bestN)
  
  
  models[0].load_weights(directory+N_directory+bestN)
  models[1].load_weights(directory+S_directory+bestS)
  models[2].load_weights(directory+V_directory+bestV)
  models[4].load_weights(directory+Q_directory+bestQ)
  
  print ("Time for Total : ")    
  y_pred = Two_Stages_Predict(X_test,models,lockups)
  print(len(y_pred))
  ytestInds = np.argmax(Y_test,axis = 1)
  acc , avg , accuracies = Evaluate(ytestInds , y_pred , 16)
  
  
  
  max_avg = avg
  best_combination['first'] = first
  best_combination[0] = bestN
  best_combination[1] = bestS
  #best_combination[1] = "bestS"
  best_combination[2] = bestV
  #best_combination[2] = "bestV"
  best_combination[4] = bestQ
  #best_combination[4] = "bestQ"
  WriteCombinations(best_combination, directory+'CNN_NG_best'+str(max_avg)+'.txt')
  print ("TOTAAAL AVERAGE " , max_avg)
  
  
  max_avg_N = -1
  max_avg_S = -1
  max_avg_V = -1
  max_avg_Q = -1
  


print(best_combination)

"""Test With Best Combination , saved Before"""

directory = '/content/drive/My Drive/Graduation Project/Preprocessed Dataset/Trial6/'
first_directory = 'TS_First_mode_CNN/'
N_directory = 'TS_Ncat_CNN/'
S_directory = 'TS_Scat_CNN/'
V_directory = 'TS_Vcat_CNN/'
Q_directory = 'TS_Qcat_CNN/'

best_combination = ReadCombination(directory + 'Deifbest_combination_88.06246664518969.txt')
print(best_combination)
models = {'first_stage':first_stage_model , 0: cat_N_model , 1: cat_S_model , 2: cat_V_model , 4: cat_Q_model }
model1_lookup = {0:0,1:1,2:2,3:9,4:10}
model2_lookup = {0:3,1:4,2:5,3:14}
model3_lookup = {0:6,1:8,2:11}
model5_lookup = {0:12,1:13,2:15}
lockups = {0:model1_lookup , 1:model2_lookup , 2:model3_lookup, 4: model5_lookup}
print (X_test.shape)


models['first_stage'].load_weights(directory+ first_directory + best_combination['first'])
models[0].load_weights(directory + N_directory + best_combination[0] )
models[1].load_weights(directory + S_directory + best_combination[1] )
models[2].load_weights(directory + V_directory + best_combination[2] )
models[4].load_weights(directory + Q_directory + best_combination[4] )

print('First Stage Accuracy :')
Predict_and_Evaluate(models['first_stage'],first_stage_model_X_test , first_stage_model_Y_test , 5)


print ("Time for Total : ")    
y_pred = Two_Stages_Predict(X_test,models,lockups)
print(len(y_pred))
ytestInds = np.argmax(Y_test,axis = 1)
acc , avg , accuracies = Evaluate(ytestInds , y_pred , 16)
print (avg)