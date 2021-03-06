import tensorflow as tf


def inference(images, batch_size, n_classes):
    # with tf.name_scope('images'):
    #     tf.summary.image('images', images, batch_size)
    with tf.variable_scope('conv1'):
        weights = tf.get_variable('weights', shape=[3, 3, 3, 32], dtype=tf.float32, initializer=tf.truncated_normal_initializer(stddev=0.1, dtype=tf.float32))
        biases = tf.get_variable('biases', shape=[32], dtype=tf.float32, initializer=tf.constant_initializer(0.1))
        conv = tf.nn.conv2d(images, weights, strides=[1, 1, 1, 1], padding='SAME')
        pre_activation = tf.nn.bias_add(conv, biases)
        conv1 = tf.nn.relu(pre_activation, name='conv1')
    with tf.variable_scope('pooling1_lrn'):
        pool1 = tf.nn.max_pool(conv1, ksize=[1, 3, 3, 1], strides=[1, 2, 2, 1], padding='SAME', name='pooling1')
        norm1 = tf.nn.lrn(pool1, depth_radius=4, bias=1.0, alpha=0.001 / 9.0, beta=0.75, name='norm1')

    with tf.variable_scope('conv2'):
        weights = tf.get_variable('weights', shape=[3, 3, 32, 64], dtype=tf.float32, initializer=tf.truncated_normal_initializer(stddev=0.1, dtype=tf.float32))
        biases = tf.get_variable('biases', shape=[64], dtype=tf.float32, initializer=tf.constant_initializer(0.1))
        conv = tf.nn.conv2d(norm1, weights, strides=[1, 1, 1, 1], padding='SAME')
        pre_activation = tf.nn.bias_add(conv, biases)
        conv2 = tf.nn.relu(pre_activation, name='conv2')
    with tf.variable_scope('pooling2_lrn'):
        pool2 = tf.nn.max_pool(conv2, ksize=[1, 3, 3, 1], strides=[1, 2, 2, 1], padding='SAME', name='pooling2')
        norm2 = tf.nn.lrn(pool2, depth_radius=4, bias=1.0, alpha=0.001 / 9.0, beta=0.75, name='norm2')

    with tf.variable_scope('conv3'):
        weights = tf.get_variable('weights', shape=[3, 3, 64, 128], dtype=tf.float32, initializer=tf.truncated_normal_initializer(stddev=0.1, dtype=tf.float32))
        biases = tf.get_variable('biases', shape=[128], dtype=tf.float32, initializer=tf.constant_initializer(0.1))
        conv = tf.nn.conv2d(norm2, weights, strides=[1, 1, 1, 1], padding='SAME')
        pre_activation = tf.nn.bias_add(conv, biases)
        conv3 = tf.nn.relu(pre_activation, name='conv3')
    with tf.variable_scope('pooling3_lrn'):
        norm3 = tf.nn.lrn(conv3, depth_radius=4, bias=1.0, alpha=0.001 / 9.0, beta=0.75, name='norm3')
        pool3 = tf.nn.max_pool(norm3, ksize=[1, 3, 3, 1], strides=[1, 2, 2, 1], padding='SAME', name='pooling3')

    with tf.variable_scope('local3'):
        reshape = tf.reshape(pool3, shape=[batch_size, -1])
        dim = reshape.get_shape()[1].value
        weights = tf.get_variable('weights',
                                  shape=[dim, 4096],
                                  dtype=tf.float32,
                                  initializer=tf.truncated_normal_initializer(stddev=0.005, dtype=tf.float32))
        biases = tf.get_variable('biases',
                                 shape=[4096],
                                 dtype=tf.float32,
                                 initializer=tf.constant_initializer(0.1))
        local3 = tf.nn.relu(tf.matmul(reshape, weights) + biases, name='local3')

    with tf.variable_scope('local4'):
        weights = tf.get_variable('weights',
                                  shape=[4096, 192],
                                  dtype=tf.float32,
                                  initializer=tf.truncated_normal_initializer(stddev=0.005, dtype=tf.float32))
        biases = tf.get_variable('biases',
                                 shape=[192],
                                 dtype=tf.float32,
                                 initializer=tf.constant_initializer(0.1))
        local4 = tf.nn.relu(tf.matmul(local3, weights) + biases, name='local4')

    with tf.variable_scope('dropout'):
        h_fc1_drop = tf.nn.dropout(local4, keep_prob=0.9)

    with tf.variable_scope('output'):
        weights = tf.get_variable('softmax_linear',
                                  shape=[192, n_classes],
                                  dtype=tf.float32,
                                  initializer=tf.truncated_normal_initializer(stddev=0.005, dtype=tf.float32))
        biases = tf.get_variable('biases',
                                 shape=[n_classes],
                                 dtype=tf.float32,
                                 initializer=tf.constant_initializer(0.1))
        logits = tf.add(tf.matmul(h_fc1_drop, weights), biases, name='softmax_linear')

    return logits


def losses(logits, labels):
    with tf.variable_scope('loss') as scope:
        cross_entropy = tf.nn.sparse_softmax_cross_entropy_with_logits(logits=logits, labels=labels, name='cross_entropy')
        loss = tf.reduce_mean(cross_entropy, name='loss')
        tf.summary.scalar(scope.name, loss)
    return loss


def trainning(loss, learning_rate):
    with tf.name_scope('optimizer'):
        optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate)
        global_step = tf.Variable(0, name='global_step', trainable=False)
        train_op = optimizer.minimize(loss, global_step=global_step)
    return train_op


def evaluation(logits, labels):
    with tf.variable_scope('accuracy') as scope:
        correct = tf.nn.in_top_k(logits, labels, 1)
        correct = tf.cast(correct, tf.float16)
        accuracy = tf.reduce_mean(correct, name='accuracy')
        tf.summary.scalar(scope.name, accuracy)
    return accuracy
