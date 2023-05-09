import numpy as np
import tensorflow as tf
from tensorflow.python import keras

class F1Score(keras.metrics.Metric):
    # num_classes parameter were added for api compatibility with tensorflow_addons.metrics.F1Score() previously used
    def __init__(self, name='f1_score', average=None, num_classes=9, **kwargs):
        # added for corner case issue: 
        # if we're loading an old keras model that was 
        # compiled with tensorflow_addons.metrics.F1Score() custom metric (which is internally called "Addons>F1Score"), 
        # then 'threshold' key will be passed to this F1Score class as one of its configuration attributes, 
        # so we want to remove that, as super.__init()__ doesn't recognize it
        if 'threshold' in kwargs.keys(): 
            kwargs.pop('threshold')
        super(F1Score, self).__init__(name=name, **kwargs)
        self.num_classes = num_classes # unused
        self.average = average
        self.tp = None
        self.fp = None
        self.fn = None
        self.f1 = None
    
    def update_state(self, y_true, y_pred, sample_weight=None):
        self.tp = tf.reduce_sum(tf.round(tf.clip_by_value(y_true * y_pred, 0, 1)), axis=0)
        self.fp = tf.reduce_sum(tf.round(tf.clip_by_value((1 - y_true) * y_pred, 0, 1)), axis=0)
        self.fn = tf.reduce_sum(tf.round(tf.clip_by_value(y_true * (1 - y_pred), 0, 1)), axis=0)
        precision = self.tp / (self.tp + self.fp + 1e-7)
        recall = self.tp / (self.tp + self.fn + 1e-7)
        self.f1 = 2 * precision * recall / (precision + recall + 1e-7)
    
    def result(self):
        f1_score = self.f1
        if self.average == 'macro':
            f1_score = tf.reduce_mean(f1_score, axis=0)
        elif self.average == 'micro':
            self.tp = tf.math.reduce_sum(self.tp)
            self.fn = tf.math.reduce_sum(self.fn)
            self.fp = tf.math.reduce_sum(self.fp)
            f1_score = 2 * self.tp / (2 * self.tp + self.fp + self.fn + 1e-7)
        elif self.average == 'weighted':
            weights = tf.reduce_sum(self.tp + self.fn, axis=0)
            weights = tf.where(tf.math.greater(weights, 0), weights, tf.ones_like(weights))
            weights = weights / tf.reduce_sum(weights)
            f1_score = tf.reduce_sum(f1_score * weights)
        
        return f1_score