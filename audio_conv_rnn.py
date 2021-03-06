# -*- coding: utf-8 -*-
'''AudioConvRNN model for Keras.

'''
from keras import backend as K
from keras.layers import Input, Dense
from keras.models import Model
from keras.layers import Dense, Dropout, Reshape, Permute
from keras.layers.convolutional import Convolution2D
from keras.layers.convolutional import MaxPooling2D, ZeroPadding2D
from keras.layers.normalization import BatchNormalization
from keras.layers.advanced_activations import ELU
from keras.layers.recurrent import GRU
from keras.utils.data_utils import get_file

TH_WEIGHTS_PATH = 'https://github.com/keunwoochoi/music-auto_tagging-keras/blob/master/data/rnn_weights_theano.hdf5'
TF_WEIGHTS_PATH = 'https://github.com/keunwoochoi/music-auto_tagging-keras/blob/master/data/rnn_weights_tensorflow.hdf5'


def AudioConvRNN(weights='msd', input_tensor=None):
    '''Instantiate the AudioConvRNN architecture,
    optionally loading weights pre-trained
    on Million Song Dataset. 

    To use pre-trained weights, you should set
    `image_dim_ordering="th"` in your Keras config
    at ~/.keras/keras.json.

    The model and the weights are compatible with both
    TensorFlow and Theano. The dimension ordering
    convention used by the model is the one
    specified in your Keras config file.

    # Arguments
        weights: one of `None` (random initialization)
            or "imagenet" (pre-training on ImageNet).
        input_tensor: optional Keras tensor (i.e. output of `layers.Input()`)
            to use as image input for the model.


    # Returns
        A Keras model instance.
    '''
    if weights not in {'msd', None}:
        raise ValueError('The `weights` argument should be either '
                         '`None` (random initialization) or `msd` '
                         '(pre-training on Million Song Dataset).')
    
    # Determine proper input shape
    if K.image_dim_ordering() == 'th':
        input_shape = (1, 96, 1366)
    else:
        input_shape = (96, 1366, 1)

    if input_tensor is None:
        melgram_input = Input(shape=input_shape)
    else:
        if not K.is_keras_tensor(input_tensor):
            melgram_input = Input(tensor=input_tensor, shape=input_shape)
        else:
            melgram_input = input_tensor
    
    # Determine input axis
    if K.image_dim_ordering() == 'th':
        channel_axis = 1
        freq_axis = 2
        time_axis = 3
    else:
        channel_axis = 3
        freq_axis = 1
        time_axis = 2
    
    # Input block
    x = ZeroPadding2D(padding=(0, 37))(melgram_input)
    x = BatchNormalization(axis=time_axis, name='bn_0_freq')(x)
    
    # Conv block 1
    x = Convolution2D(64, 3, 3, border_mode='same', name='conv1')(x)
    x = BatchNormalization(axis=channel_axis, mode=2, name='bn1')(x)
    x = ELU()(x)
    x = MaxPooling2D((2, 2), strides=(2, 2), name='pool1')(x)
    x = Dropout(0.5, name='dropout1')(x)
    
    # Conv block 2
    x = Convolution2D(128, 3, 3, border_mode='same', name='conv2')(x)
    x = BatchNormalization(axis=channel_axis, mode=2, name='bn2')(x)
    x = ELU()(x)
    x = MaxPooling2D((3, 3), strides=(3, 3), name='pool2')(x)
    x = Dropout(0.5, name='dropout2')(x)
    
    # Conv block 3
    x = Convolution2D(128, 3, 3, border_mode='same', name='conv3')(x)
    x = BatchNormalization(axis=channel_axis, mode=2, name='bn3')(x)
    x = ELU()(x)
    x = MaxPooling2D((4, 4), strides=(4, 4), name='pool3')(x)
    x = Dropout(0.5, name='dropout3')(x)
    
    # Conv block 4
    x = Convolution2D(128, 3, 3, border_mode='same', name='conv4')(x)
    x = BatchNormalization(axis=channel_axis, mode=2, name='bn4')(x)
    x = ELU()(x)
    x = MaxPooling2D((4, 4), strides=(4, 4), name='pool4')(x)
    x = Dropout(0.5, name='dropout4')(x)
    
    # reshaping
    if K.image_dim_ordering() == 'th':
        x = Permute((3, 1, 2))(x)
    x = Reshape((15, 128))(x)
    
    # GRU block 1, 2, output
    x = GRU(32, return_sequences=True, name='gru1')(x)
    x = GRU(32, return_sequences=False, name='gru2')(x)
    x = Dropout(0.3)(x)
    x = Dense(50, activation='sigmoid', name='output')(x)

    # Create model
    model = Model(melgram_input, x)
    if weights is None:
        return model
    else: 
        # Load input
        if K.image_dim_ordering == 'tf':
            raise RuntimeError("Please set image_dim_ordering == 'th'." + \
                "You can set it at ~/.keras/keras.json")
        if K._BACKEND == 'theano':        
            weights_path = get_file('rnn_weights_theano.h5',
                                    TH_WEIGHTS_PATH,
                                    cache_subdir='models')                
        else:
            weights_path = get_file('rnn_weights_tensorflow.h5',
                                    TF_WEIGHTS_PATH,
                                    cache_subdir='models')
        
        model.load_weights(weights_path)
        return model
