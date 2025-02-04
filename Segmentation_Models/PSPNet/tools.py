import scipy.io as sio
import numpy as np
import tensorflow as tf
import os
import sys

IMG_MEAN = np.array((103.939, 116.779, 123.68), dtype=np.float32)
label_colours = [(128, 64, 128), (244, 35, 231), (69, 69, 69)
                 # 0 = road, 1 = sidewalk, 2 = building
    , (102, 102, 156), (190, 153, 153), (153, 153, 153)
                 # 3 = wall, 4 = fence, 5 = pole
    , (250, 170, 29), (219, 219, 0), (106, 142, 35)
                 # 6 = traffic light, 7 = traffic sign, 8 = vegetation
    , (152, 250, 152), (69, 129, 180), (219, 19, 60)
                 # 9 = terrain, 10 = sky, 11 = person
    , (255, 0, 0), (0, 0, 142), (0, 0, 69)
                 # 12 = rider, 13 = car, 14 = truck
    , (0, 60, 100), (0, 79, 100), (0, 0, 230)
                 # 15 = bus, 16 = train, 17 = motocycle
    , (119, 10, 32)]
# 18 = bicycle

osm_label_colours = [(0, 0, 0),        # 0 = unlabelled
                     (213, 131, 7),    # 0 = building
                     (0, 153, 0),      # 0 = wood
                     (0, 0, 204),      # 0 = water
                     (76, 0, 153),     # 0 = road
                     (255, 255, 102)]  # 0 = residential


matfn = './utils/color150.mat'


def read_labelcolours(matfn):
    mat = sio.loadmat(matfn)
    color_table = mat['colors']
    shape = color_table.shape
    color_list = [tuple(color_table[i]) for i in range(shape[0])]

    return color_list


def decode_labels(mask, img_shape, num_classes):
    """

    :param mask: the output of the net after argmax(1, width, height)
    :param img_shape: the shape of the img
    :param num_classes: number of classes
    :return:
    """
    if num_classes == 150:
        color_table = read_labelcolours(matfn)
    elif num_classes == 19:
        color_table = label_colours
    elif num_classes == 6:  # osm data!!
        color_table = label_colours  # TODO Replace with osm color map!!
        color_table = osm_label_colours

    color_mat = tf.constant(color_table, dtype=tf.float32)
    onehot_output = tf.one_hot(mask, depth=num_classes)
    onehot_output = tf.reshape(onehot_output, (-1, num_classes))
    pred = tf.matmul(onehot_output, color_mat)
    pred = tf.reshape(pred, (1, img_shape[0], img_shape[1], 3))
    # for this reshape (1, img_shape[0], img_shape[1], 3) pred[0] (not pred) is taken when saving the file

    return pred


def prepare_label(input_batch, new_size, num_classes, one_hot=True):
    with tf.name_scope('label_encode'):
        input_batch = tf.image.resize_nearest_neighbor(input_batch,
                                                       new_size)  # as labels are integer numbers, need to use NN interp.
        input_batch = tf.squeeze(input_batch, squeeze_dims=[3])  # reducing the channel dimension.
        if one_hot:
            input_batch = tf.one_hot(input_batch, depth=num_classes)

    return input_batch


def load_img(img_path):
    if os.path.isfile(img_path):
        print('successful load img: {0}'.format(img_path))
    else:
        print('not found file: {0}'.format(img_path))
        sys.exit(0)

    filename = img_path.split('/')[-1]
    ext = filename.split('.')[-1]

    if ext.lower() == 'png':
        img = tf.image.decode_png(tf.read_file(img_path), channels=3)
    elif ext.lower() == 'jpg':
        img = tf.image.decode_jpeg(tf.read_file(img_path), channels=3)
    else:
        print('cannot process {0} file.'.format(file_type))

    return img, filename


def preprocess(img, h, w):
    # Convert RGB to BGR
    img_r, img_g, img_b = tf.split(axis=2, num_or_size_splits=3, value=img)
    img = tf.cast(tf.concat(axis=2, values=[img_b, img_g, img_r]), dtype=tf.float32)
    # Extract mean.
    img -= IMG_MEAN

    pad_img = tf.image.pad_to_bounding_box(img, 0, 0, h, w)
    pad_img = tf.expand_dims(pad_img, dim=0)

    return pad_img
