'''
classifier for GTSRB dataset
'''
import tensorflow as tf
from utils import pre_process_image
from utils import OHE_labels
import numpy as np
import pickle

# parameters
img_size = 128
N_classes = 43
num_channels = 3

# input variables
features = tf.placeholder(tf.float32, shape=[None, img_size, img_size, num_channels], name='features')
labels_true = tf.placeholder(tf.float32,shape=[None,N_classes], name='y_true')
labels_true_cls = tf.argmax(labels_true, dimension=1)
keep_prob = tf.placeholder(tf.float32)


# functions
def get_weights(name, shape):
    return tf.get_variable(name=name, shape=shape, initializer=tf.truncated_normal_initializer(stddev=0.05))
    # return tf.Variable(tf.truncated_normal(shape, stddev=0.05))
def get_biases(name, length):
    return tf.get_variable(name=name, shape=length, initializer=tf.constant_initializer(value=0.05))
    # return tf.Variable(tf.constant(0.05, shape=[length]))

def conv_layer(name, input, num_inp_channels, filter_size, num_filters, use_pooling):
    shape = [filter_size, filter_size, num_inp_channels,num_filters]
    weights = get_weights(name+'weights', shape)
    biases = get_biases(name+'bias', num_filters)
    layer = tf.nn.conv2d(input = input, filter = weights, strides = [1,1,1,1], padding = 'SAME')
    layer += biases
    if use_pooling:
        layer = tf.nn.max_pool(value=layer, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
    layer = tf.nn.relu(layer)
    return layer, weights

def flatten_layer(layer):
    # Get the shape of the input layer.
    layer_shape = layer.get_shape()
    num_features = layer_shape[1:4].num_elements()
    layer_flat = tf.reshape(layer, [-1, num_features])
    return layer_flat, num_features

def fc_layer(name,
             input,          # The previous layer.
             num_inputs,     # Num. inputs from prev. layer.
             num_outputs,    # Num. outputs.
             use_relu=True): # Use Rectified Linear Unit (ReLU)?
    weights = get_weights(name + 'weights', shape=[num_inputs, num_outputs])
    biases = get_biases(name + 'bias', length=num_outputs)
    layer = tf.matmul(input, weights) + biases
    if use_relu:
        layer = tf.nn.relu(layer)
    return layer,weights

def dropout_layer(layer, keep_prob):
    layer_drop = tf.nn.dropout(layer, keep_prob)
    return layer_drop

# Architecture of the Model

## Convlayer 0
filter_size0 = 1
num_filters0 = 3

## Convlayer 1
filter_size1 = 5
num_filters1 = 32
## Convlayer 2
filter_size2 = 5
num_filters2 = 32

## Convlayer 3
filter_size3 = 5
num_filters3 = 64
## Convlayer 4
filter_size4 = 5
num_filters4 = 64

## Convlayer 5
filter_size5 = 5
num_filters5 = 128
## Convlayer 6
filter_size6 = 5
num_filters6 = 128

## FC_size
fc_size1 = 1024
## FC_size
fc_size2 = 1024

def GTSRB_Model(
        features,
        keep_prob,
        reuse = False
):
    with tf.variable_scope('GTSRB') as scope:

        # image is 256 x 256 x (input_c_dim + output_c_dim)
        if reuse:
            tf.get_variable_scope().reuse_variables()
        else:
            assert tf.get_variable_scope().reuse == False
        layer_conv0, weights_conv0 =         conv_layer(name = 'conv0_', input=features,
                           num_inp_channels=num_channels,
                           filter_size=filter_size0,
                           num_filters=num_filters0,
                           use_pooling=False)

        layer_conv1, weights_conv1 =         conv_layer(name = 'conv1_', input=layer_conv0,
                           num_inp_channels=num_filters0,
                           filter_size=filter_size1,
                           num_filters=num_filters1,
                           use_pooling=False)
        layer_conv2, weights_conv2 =         conv_layer(name = 'conv2_', input=layer_conv1,
                           num_inp_channels=num_filters1,
                           filter_size=filter_size2,
                           num_filters=num_filters2,
                           use_pooling=True)
        layer_conv2_drop = dropout_layer(layer_conv2, keep_prob)

        layer_conv3, weights_conv3 =         conv_layer(name = 'conv3_', input=layer_conv2_drop,
                           num_inp_channels=num_filters2,
                           filter_size=filter_size3,
                           num_filters=num_filters3,
                           use_pooling=False)
        layer_conv4, weights_conv4=         conv_layer(name = 'conv4_', input=layer_conv3,
                           num_inp_channels=num_filters3,
                           filter_size=filter_size4,
                           num_filters=num_filters4,
                           use_pooling=True)
        layer_conv4_drop = dropout_layer(layer_conv4, keep_prob)

        layer_conv5, weights_conv5 =         conv_layer(name = 'conv5_', input=layer_conv4_drop,
                           num_inp_channels=num_filters4,
                           filter_size=filter_size5,
                           num_filters=num_filters5,
                           use_pooling=False)
        layer_conv6, weights_conv6 =         conv_layer(name = 'conv6_', input=layer_conv5,
                           num_inp_channels=num_filters5,
                           filter_size=filter_size6,
                           num_filters=num_filters6,
                           use_pooling=True)
        layer_conv6_drop = dropout_layer(layer_conv6, keep_prob)


        layer_flat2, num_fc_layers2 = flatten_layer(layer_conv2_drop)
        layer_flat4, num_fc_layers4 = flatten_layer(layer_conv4_drop)
        layer_flat6, num_fc_layers6 = flatten_layer(layer_conv6_drop)

        layer_flat = tf.concat([layer_flat2, layer_flat4, layer_flat6], 1)
        num_fc_layers = num_fc_layers2+num_fc_layers4+num_fc_layers6

        fc_layer1,weights_fc1 = fc_layer('fc_1', layer_flat,          # The previous layer.
                     num_fc_layers,     # Num. inputs from prev. layer.
                     fc_size1,    # Num. outputs.
                     use_relu=True)
        fc_layer1_drop = dropout_layer(fc_layer1, keep_prob)

        fc_layer2,weights_fc2 = fc_layer('fc_2', fc_layer1_drop,          # The previous layer.
                     fc_size1,     # Num. inputs from prev. layer.
                     fc_size2,    # Num. outputs.
                     use_relu=True)
        fc_layer2_drop = dropout_layer(fc_layer2, keep_prob)

        fc_layer3,weights_fc3 = fc_layer('fc_3', fc_layer2_drop,          # The previous layer.
                     fc_size2,     # Num. inputs from prev. layer.
                     N_classes,    # Num. outputs.
                     use_relu=False)

        tf.add_to_collection('reg', weights_conv0)
        tf.add_to_collection('reg', weights_conv1)
        tf.add_to_collection('reg', weights_conv2)
        tf.add_to_collection('reg', weights_conv3)
        tf.add_to_collection('reg', weights_conv4)
        tf.add_to_collection('reg', weights_conv5)
        tf.add_to_collection('reg', weights_conv6)
        tf.add_to_collection('reg', weights_fc1)
        tf.add_to_collection('reg', weights_fc2)
        tf.add_to_collection('reg', weights_fc3)


        labels_pred = tf.nn.softmax(fc_layer3)
        labels_pred_cls = tf.argmax(labels_pred, dimension=1)

        return fc_layer3, labels_pred, labels_pred_cls

'''
input:
image_GS_test: shape (1, 128, 128, 3)
label_test: one hot code, shape (1, 43)
y_test: label id, shape (1,)
keep_prob_test: default = 1.0
'''
def GTSRB_Classifier(path, image_GS_test, labels_test):
    features = tf.placeholder(tf.float32, shape=[None, img_size, img_size, num_channels], name='features')
    labels_true = tf.placeholder(tf.float32,shape=[None,N_classes], name='y_true')
    labels_true_cls = tf.argmax(labels_true, dimension=1)
    fc_layer3, labels_pred, labels_pred_cls = GTSRB_Model(features=features, keep_prob=1.0)
    correct_prediction = tf.equal(labels_pred_cls, labels_true_cls)
    accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
    totalacc = 0.0
    with tf.Session() as sess:
      saver = tf.train.Saver()
      saver.restore(sess=sess, save_path=path)
      for i in range(0, 100):
        if(i == 99):
          feed_dict_test = {features: image_GS_test[i*126:-1], labels_true: labels_test[i*126:-1], keep_prob:1.0}
        else:
          feed_dict_test = {features: image_GS_test[i*126:(i+1)*126], labels_true: labels_test[i*126:(i+1)*126], keep_prob:1.0}
        acc = sess.run(accuracy,feed_dict=feed_dict_test)
        print(acc)
        totalacc = totalacc + acc
      print("Accuracy on test set: {0:>6.1%}".format(totalacc/100))

if __name__ == "__main__":
  test_data_dir = '/media/dsgDisk/dsgPrivate/liuaishan/GTSRB/data/test.p'
  weights_dir = '/media/dsgDisk/dsgPrivate/liuaishan/GTSRB/model/test/GTSRB_best_test'
  with open(test_data_dir, 'rb') as f:
    dataset = pickle.load(f)
  image_GS_test = np.asarray([pre_process_image(item) for item in dataset['data']]).astype(np.float32)
  labels_test = OHE_labels(dataset['labels'], N_classes).astype(np.float32)
  GTSRB_Classifier(weights_dir, image_GS_test, labels_test)

