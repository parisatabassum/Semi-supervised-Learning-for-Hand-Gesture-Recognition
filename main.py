# -*- coding: utf-8 -*-
"""Main.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/15_Q0jMgkwwD_6sGiOOdptWHly9mSUF5V
"""

#history save
#model save
#train test validation split

# Commented out IPython magic to ensure Python compatibility.
import numpy as np
import os
from keras.preprocessing.image import image, img_to_array
import matplotlib.image as mpimg
import pandas as pd
import tensorflow as tf
import cv2
import glob
from keras.preprocessing.image import image, img_to_array
import tensorflow_datasets as tfds
from tensorflow import keras
from tensorflow.keras import layers
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix,accuracy_score, roc_curve, auc
import matplotlib.pyplot as plt
# %matplotlib inline
import seaborn as sns
import itertools
import sklearn.metrics as metrics

device_name = tf.test.gpu_device_name()
if device_name != '/device:GPU:0':
  raise SystemError('GPU device not found')
print('Found GPU at: {}'.format(device_name))

#access google drive
from google.colab import drive
drive.mount('/content/drive')

AUTOTUNE = tf.data.AUTOTUNE
shuffle_buffer = 5000
temperature = 0.1
queue_size = 10000
contrastive_augmenter = {
    "brightness": 0.5,
    "name": "contrastive_augmenter",
    "scale": (0.2, 1.0),
}
classification_augmenter = {
    "brightness": 0.2,
    "name": "classification_augmenter",
    "scale": (0.5, 1.0),
}
input_shape = (96, 96, 3)
width = 128
num_epochs = 200
steps_per_epoch = 200

lookup = dict()
reverselookup = dict()
count = 0
for j in os.listdir('/content/drive/MyDrive/leapGestRecog/00'):
    if not j.startswith('.'): # If running this code locally, this is to
                              # ensure you aren't reading in hidden folders
        lookup[j] = count
        reverselookup[count] = j
        count = count + 1
lookup

x_data1 = []
x_data = []
y_data = []
datacount = 0
for i in range(0, 1):
################### ARUNAVO BHAIA NOTE#####################################
################### for i in range(0, 10) FOR FULL DATASET##############################
    for j in os.listdir('/content/drive/MyDrive/leapGestRecog/0' + str(i) + '/'):
        if not j.startswith('.'): # Again avoid hidden folders
            count = 0 # To tally images of a given gesture
            for k in os.listdir('/content/drive/MyDrive/leapGestRecog/0' +
                                str(i) + '/' + j + '/'):
                                # Loop over the images
                img = image.load_img(('/content/drive/MyDrive/leapGestRecog/0' +
                                 str(i) + '/' + j + '/' + k),
                color_mode='rgb',
                target_size=(96, 96)
                )
                x_data1.append(img)
                count = count + 1
            y_values = np.full((count, 1), lookup[j])
            y_data.append(y_values)
            datacount = datacount + count

datacount

y_data = np.array(y_data)
y_data = y_data.reshape(datacount,)
for index1 in x_data1:
  k1=tf.keras.preprocessing.image.img_to_array(index1)
  x_data.append(tf.convert_to_tensor(k1, dtype=tf.uint8, name=None))

X_train, X_test, y_train, y_test = train_test_split(x_data, y_data, test_size=0.3, random_state=42, stratify=y_data)

X_trainn, test_dataset_image, y_trainn, test_dataset_label = train_test_split(X_train, y_train, test_size=0.3, random_state=42, stratify=y_train)

unlabeled_train_dataset_image, labeled_train_dataset_image, unlabeled_train_dataset_label, labeled_train_dataset_label = train_test_split(X_trainn, y_trainn, test_size=0.1, random_state=42, stratify=y_trainn)

unlabeled_train_dataset_label = tf.convert_to_tensor(unlabeled_train_dataset_label)
labeled_train_dataset_label = tf.convert_to_tensor(labeled_train_dataset_label)
test_dataset_label = tf.convert_to_tensor(test_dataset_label)
y_test=tf.convert_to_tensor(y_test)

y_test

labeled_train_dataset_label

unlabeled_train_dataset_label

test_dataset_label

labelled_train_images = 98
unlabelled_images = 882

unlabeled_batch_size = unlabelled_images // steps_per_epoch
labeled_batch_size = labelled_train_images // steps_per_epoch
batch_size = unlabeled_batch_size + labeled_batch_size

batch_size

dataset1 = tf.data.Dataset.from_tensors(unlabeled_train_dataset_image)
dataset2 = tf.data.Dataset.from_tensors(unlabeled_train_dataset_label)
unlabeled_train_dataset = tf.data.Dataset.zip(
(dataset1, dataset2)
).prefetch(buffer_size=AUTOTUNE)

dataset3 = tf.data.Dataset.from_tensors(labeled_train_dataset_image)
dataset4 = tf.data.Dataset.from_tensors(labeled_train_dataset_label)
labeled_train_dataset = tf.data.Dataset.zip(
(dataset3, dataset4)
).prefetch(buffer_size=AUTOTUNE)




train_dataset = tf.data.Dataset.zip(
(unlabeled_train_dataset, labeled_train_dataset)
).prefetch(buffer_size=AUTOTUNE)

dataset5 = tf.data.Dataset.from_tensors(test_dataset_image)
dataset6 = tf.data.Dataset.from_tensors(test_dataset_label)
test_dataset = tf.data.Dataset.zip(
(dataset5, dataset6)
).prefetch(buffer_size=AUTOTUNE)

dataset7 = tf.data.Dataset.from_tensors(X_test)
dataset8 = tf.data.Dataset.from_tensors(y_test)
final_testing = tf.data.Dataset.zip(
(dataset7, dataset8)
).prefetch(buffer_size=AUTOTUNE)

final_testing

train_dataset

test_dataset

class RandomResizedCrop(layers.Layer):
    def __init__(self, scale, ratio):
        super(RandomResizedCrop, self).__init__()
        self.scale = scale
        self.log_ratio = (tf.math.log(ratio[0]), tf.math.log(ratio[1]))

    def call(self, images):
        batch_size = tf.shape(images)[0]
        height = tf.shape(images)[1]
        width = tf.shape(images)[2]

        random_scales = tf.random.uniform((batch_size,), self.scale[0], self.scale[1])
        random_ratios = tf.exp(
            tf.random.uniform((batch_size,), self.log_ratio[0], self.log_ratio[1])
        )

        new_heights = tf.clip_by_value(tf.sqrt(random_scales / random_ratios), 0, 1)
        new_widths = tf.clip_by_value(tf.sqrt(random_scales * random_ratios), 0, 1)
        height_offsets = tf.random.uniform((batch_size,), 0, 1 - new_heights)
        width_offsets = tf.random.uniform((batch_size,), 0, 1 - new_widths)

        bounding_boxes = tf.stack(
            [
                height_offsets,
                width_offsets,
                height_offsets + new_heights,
                width_offsets + new_widths,
            ],
            axis=1,
        )
        images = tf.image.crop_and_resize(
            images, bounding_boxes, tf.range(batch_size), (height, width)
        )
        return images

class RandomBrightness(layers.Layer):
    def __init__(self, brightness):
        super(RandomBrightness, self).__init__()
        self.brightness = brightness

    def blend(self, images_1, images_2, ratios):
        return tf.clip_by_value(ratios * images_1 + (1.0 - ratios) * images_2, 0, 1)

    def random_brightness(self, images):
        # random interpolation/extrapolation between the image and darkness
        return self.blend(
            images,
            0,
            tf.random.uniform(
                (tf.shape(images)[0], 1, 1, 1), 1 - self.brightness, 1 + self.brightness
            ),
        )

    def call(self, images):
        images = self.random_brightness(images)
        return images

def augmenter(brightness, name, scale):
    return keras.Sequential(
        [
            layers.Input(shape=input_shape),
            layers.Rescaling(1 / 255),
            layers.RandomFlip("horizontal"),
            RandomResizedCrop(scale=scale, ratio=(3 / 4, 4 / 3)),
            RandomBrightness(brightness=brightness),
        ],
        name=name,
    )

def encoder():
    return keras.Sequential(
        [
            layers.Input(shape=input_shape),
            layers.Conv2D(width, kernel_size=3, strides=2, activation="relu"),
            layers.Conv2D(width, kernel_size=3, strides=2, activation="relu"),
            layers.Conv2D(width, kernel_size=3, strides=2, activation="relu"),
            layers.Conv2D(width, kernel_size=3, strides=2, activation="relu"),
            layers.Flatten(),
            layers.Dense(width, activation="relu"),
        ],
        name="encoder",
    )

class NNCLR(keras.Model):
    def __init__(
        self,
        temperature,
        queue_size,
    ):
        super(NNCLR, self).__init__()
        self.probe_accuracy = keras.metrics.SparseCategoricalAccuracy()
        self.correlation_accuracy = keras.metrics.SparseCategoricalAccuracy()
        self.contrastive_accuracy = keras.metrics.SparseCategoricalAccuracy()
        self.probe_loss = keras.losses.SparseCategoricalCrossentropy(from_logits=True)

        self.contrastive_augmenter = augmenter(**contrastive_augmenter)
        self.classification_augmenter = augmenter(**classification_augmenter)
        self.encoder = encoder()
        self.projection_head = keras.Sequential(
            [
                layers.Input(shape=(width,)),
                layers.Dense(width, activation="relu"),
                layers.Dense(width),
            ],
            name="projection_head",
        )
        self.linear_probe = keras.Sequential(
            [layers.Input(shape=(width,)), layers.Dense(10)], name="linear_probe"
        )
        self.temperature = temperature

        feature_dimensions = self.encoder.output_shape[1]
        self.feature_queue = tf.Variable(
            tf.math.l2_normalize(
                tf.random.normal(shape=(queue_size, feature_dimensions)), axis=1
            ),
            trainable=False,
        )

    def compile(self, contrastive_optimizer, probe_optimizer, **kwargs):
        super(NNCLR, self).compile(**kwargs)
        self.contrastive_optimizer = contrastive_optimizer
        self.probe_optimizer = probe_optimizer

    def nearest_neighbour(self, projections):
        support_similarities = tf.matmul(
            projections, self.feature_queue, transpose_b=True
        )
        nn_projections = tf.gather(
            self.feature_queue, tf.argmax(support_similarities, axis=1), axis=0
        )
        return projections + tf.stop_gradient(nn_projections - projections)

    def update_contrastive_accuracy(self, features_1, features_2):
        features_1 = tf.math.l2_normalize(features_1, axis=1)
        features_2 = tf.math.l2_normalize(features_2, axis=1)
        similarities = tf.matmul(features_1, features_2, transpose_b=True)

        batch_size = tf.shape(features_1)[0]
        contrastive_labels = tf.range(batch_size)
        self.contrastive_accuracy.update_state(
            tf.concat([contrastive_labels, contrastive_labels], axis=0),
            tf.concat([similarities, tf.transpose(similarities)], axis=0),
        )

    def update_correlation_accuracy(self, features_1, features_2):
        features_1 = (
            features_1 - tf.reduce_mean(features_1, axis=0)
        ) / tf.math.reduce_std(features_1, axis=0)
        features_2 = (
            features_2 - tf.reduce_mean(features_2, axis=0)
        ) / tf.math.reduce_std(features_2, axis=0)

        batch_size = tf.shape(features_1, out_type=tf.float32)[0]
        cross_correlation = (
            tf.matmul(features_1, features_2, transpose_a=True) / batch_size
        )

        feature_dim = tf.shape(features_1)[1]
        correlation_labels = tf.range(feature_dim)
        self.correlation_accuracy.update_state(
            tf.concat([correlation_labels, correlation_labels], axis=0),
            tf.concat([cross_correlation, tf.transpose(cross_correlation)], axis=0),
        )

    def contrastive_loss(self, projections_1, projections_2):
        projections_1 = tf.math.l2_normalize(projections_1, axis=1)
        projections_2 = tf.math.l2_normalize(projections_2, axis=1)

        similarities_1_2_1 = (
            tf.matmul(
                self.nearest_neighbour(projections_1), projections_2, transpose_b=True
            )
            / self.temperature
        )
        similarities_1_2_2 = (
            tf.matmul(
                projections_2, self.nearest_neighbour(projections_1), transpose_b=True
            )
            / self.temperature
        )

        similarities_2_1_1 = (
            tf.matmul(
                self.nearest_neighbour(projections_2), projections_1, transpose_b=True
            )
            / self.temperature
        )
        similarities_2_1_2 = (
            tf.matmul(
                projections_1, self.nearest_neighbour(projections_2), transpose_b=True
            )
            / self.temperature
        )

        batch_size = tf.shape(projections_1)[0]
        contrastive_labels = tf.range(batch_size)
        loss = keras.losses.sparse_categorical_crossentropy(
        #loss = keras.losses.categorical_crossentropy(
            tf.concat(
                [
                    contrastive_labels,
                    contrastive_labels,
                    contrastive_labels,
                    contrastive_labels,
                ],
                axis=0,
            ),
            tf.concat(
                [
                    similarities_1_2_1,
                    similarities_1_2_2,
                    similarities_2_1_1,
                    similarities_2_1_2,
                ],
                axis=0,
            ),
            from_logits=True,
        )

        self.feature_queue.assign(
            tf.concat([projections_1, self.feature_queue[:-batch_size]], axis=0)
        )
        return loss

    def train_step(self, data):
        (unlabeled_images, _), (labeled_images, labels) = data
        images = tf.concat((unlabeled_images, labeled_images), axis=0)
        augmented_images_1 = self.contrastive_augmenter(images)
        augmented_images_2 = self.contrastive_augmenter(images)

        with tf.GradientTape() as tape:
            features_1 = self.encoder(augmented_images_1)
            features_2 = self.encoder(augmented_images_2)
            projections_1 = self.projection_head(features_1)
            projections_2 = self.projection_head(features_2)
            contrastive_loss = self.contrastive_loss(projections_1, projections_2)
        gradients = tape.gradient(
            contrastive_loss,
            self.encoder.trainable_weights + self.projection_head.trainable_weights,
        )
        self.contrastive_optimizer.apply_gradients(
            zip(
                gradients,
                self.encoder.trainable_weights + self.projection_head.trainable_weights,
            )
        )
        self.update_contrastive_accuracy(features_1, features_2)
        self.update_correlation_accuracy(features_1, features_2)
        preprocessed_images = self.classification_augmenter(labeled_images)

        with tf.GradientTape() as tape:
            features = self.encoder(preprocessed_images)
            class_logits = self.linear_probe(features)
            probe_loss = self.probe_loss(labels, class_logits)
        gradients = tape.gradient(probe_loss, self.linear_probe.trainable_weights)
        self.probe_optimizer.apply_gradients(
            zip(gradients, self.linear_probe.trainable_weights)
        )
        self.probe_accuracy.update_state(labels, class_logits)

        return {
            "c_loss": contrastive_loss,
            "c_acc": self.contrastive_accuracy.result(),
            "r_acc": self.correlation_accuracy.result(),
            "p_loss": probe_loss,
            "p_acc": self.probe_accuracy.result(),
        }

    def test_step(self, data):
        labeled_images, labels = data

        preprocessed_images = self.classification_augmenter(
            labeled_images, training=False
        )
        features = self.encoder(preprocessed_images, training=False)
        class_logits = self.linear_probe(features, training=False)
        probe_loss = self.probe_loss(labels, class_logits)

        self.probe_accuracy.update_state(labels, class_logits)
        return {"p_loss": probe_loss, "p_acc": self.probe_accuracy.result()}

model = NNCLR(temperature=temperature, queue_size=queue_size)
model.compile(
    contrastive_optimizer=keras.optimizers.Adam(),
    probe_optimizer=keras.optimizers.Adam(),
)

pip install codecarbon

from codecarbon import EmissionsTracker

with tf.device('/device:GPU:0'):
  tracker = EmissionsTracker()
  tracker.start()
  pretrain_history = model.fit(
      train_dataset, epochs=num_epochs, validation_data=test_dataset
      )
  emissions = tracker.stop()

finetuning_model = keras.Sequential(
    [
        layers.Input(shape=input_shape),
        augmenter(**classification_augmenter),
        model.encoder,
        layers.Dense(10),
    ],
    name="finetuning_model",
)
finetuning_model.compile(
    optimizer=keras.optimizers.Adam(),
    loss=keras.losses.SparseCategoricalCrossentropy(from_logits=True),
    metrics=[keras.metrics.SparseCategoricalAccuracy(name="acc")],
)

with tf.device('/device:GPU:0'):
  tracker = EmissionsTracker()
  tracker.start()
  finetuning_history = finetuning_model.fit(
      labeled_train_dataset, epochs=num_epochs, validation_data=test_dataset
      )
  emissions = tracker.stop()

# Look at confusion matrix
#import itertools
plt.rcParams['figure.figsize'] = (5, 5)
def plot_confusion_matrix(cm, classes,
                          normalize=False,
                          #title='Validation Confusion matrix',
                          cmap=plt.cm.Blues):
    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    #plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)

    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, cm[i, j],
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")

    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    #plt.savefig('confusion_matricesfor61classbangengtype.png', dpi=100)

y_pred = finetuning_model.predict(final_testing)
y_pred

predicted_categories = tf.argmax(y_pred, axis=1)
predicted_categories

true_categories=y_test
true_categories

confusion_matrix(true_categories, predicted_categories)

plot_confusion_matrix(confusion_matrix(true_categories, predicted_categories) ,classes = range(10))

score  = model.evaluate(final_testing, steps=len(final_testing), verbose=1)
print('Test loss:', score[0])
print('Test accuracy:', score[1])

score1  = finetuning_model.evaluate(final_testing, steps=len(final_testing), verbose=1)
print('Test loss:', score1[0])
print('Test accuracy:', score1[1])

report = metrics.classification_report(true_categories, predicted_categories)
print(report)

history = pretrain_history
print(history.history.keys())

plt.plot(history.history['c_acc'])
plt.plot(history.history['val_p_acc'])
#plt.title('model accuracy')
plt.ylabel('accuracy')
plt.xlabel('epoch')
plt.legend(['train', 'val'], loc='upper left')
plt.show()

plt.plot(history.history['r_acc'])
plt.plot(history.history['val_p_acc'])
#plt.title('model accuracy')
plt.ylabel('accuracy')
plt.xlabel('epoch')
plt.legend(['train', 'val'], loc='upper left')
plt.show()

plt.plot(history.history['p_acc'])
plt.plot(history.history['val_p_acc'])
#plt.title('model accuracy')
plt.ylabel('accuracy')
plt.xlabel('epoch')
plt.legend(['train', 'val'], loc='upper left')
plt.show()

plt.plot(history.history['c_loss'])
plt.plot(history.history['val_p_loss'])
plt.rcParams["figure.figsize"] = (20,10)
#plt.title('model loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'val'], loc='upper left')
plt.show()

plt.plot(history.history['p_loss'])
plt.plot(history.history['val_p_loss'])
#plt.title('model loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'val'], loc='upper left')
plt.show()

history1 = finetuning_history
print(history1.history.keys())

plt.plot(history1.history['acc'])
plt.plot(history1.history['val_acc'])
#plt.title('model accuracy')
plt.ylabel('accuracy')
plt.xlabel('epoch')
plt.legend(['train', 'val'], loc='upper left')
plt.show()

plt.plot(history1.history['loss'])
plt.plot(history1.history['val_loss'])
#plt.title('model accuracy')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'val'], loc='upper left')
plt.show()

def plt_metric(history, metric, title, has_valid=True):
    """Plots the given 'metric' from 'history'.

    Arguments:
        history: history attribute of History object returned from Model.fit.
        metric: Metric to plot, a string value present as key in 'history'.
        title: A string to be used as title of plot.
        has_valid: Boolean, true if valid data was passed to Model.fit else false.

    Returns:
        None.
    """
    plt.plot(history[metric])
    if has_valid:
        plt.plot(history["val_p_acc"])
        plt.legend(["train", "val"], loc="upper left")
    plt.title(title)
    plt.ylabel(metric)
    plt.xlabel("epoch")
    plt.show()


# Plot the accuracy
plt_metric(history=history.history, metric="c_acc", title="Model accuracy")

# Plot the constrastive loss
plt_metric(history=history.history, metric="c_loss", title="Constrastive Loss")

x_data1 = []
x_data = []
y_data = []
datacount = 0
for i in range(9,10): # (7,10 for main code)
    for j in os.listdir('/content/drive/MyDrive/leapGestRecog/0' + str(i) + '/'):
        if not j.startswith('.'): # Again avoid hidden folders
            count = 0 # To tally images of a given gesture
            for k in os.listdir('/content/drive/MyDrive/leapGestRecog/0' +
                                str(i) + '/' + j + '/'):
                                # Loop over the images
                img = image.load_img(('/content/drive/MyDrive/leapGestRecog/0' +
                                 str(i) + '/' + j + '/' + k),
                color_mode='rgb',
                target_size=(96, 96)
                )
                x_data1.append(img)
                count = count + 1
            y_values = np.full((count, 1), lookup[j])
            y_data.append(y_values)
            datacount = datacount + count

datacount

y_data = np.array(y_data)
y_data = y_data.reshape(datacount,)
y_test2=tf.convert_to_tensor(y_data)
for index1 in x_data1:
  k1=tf.keras.preprocessing.image.img_to_array(index1)
  x_data.append(tf.convert_to_tensor(k1, dtype=tf.uint8, name=None))

y_test2

test_leb = y_test2

dataset9 = tf.data.Dataset.from_tensors(x_data)
dataset10 = tf.data.Dataset.from_tensors(y_test2)
final_testing2 = tf.data.Dataset.zip(
(dataset9, dataset10)
).prefetch(buffer_size=AUTOTUNE)

final_testing2

y_pred2 = finetuning_model.predict(final_testing2)
y_pred2

predicted_categories2 = tf.argmax(y_pred2, axis=1)
predicted_categories2

true_categories2=y_test2
true_categories2

plot_confusion_matrix(confusion_matrix(true_categories2, predicted_categories2) ,classes = range(10))

score3  = finetuning_model.evaluate(final_testing2, steps=len(final_testing2), verbose=1)
print('Test loss:', score3[0])
print('Test accuracy:', score3[1])

report2 = metrics.classification_report(true_categories2, predicted_categories2)
print(report2)