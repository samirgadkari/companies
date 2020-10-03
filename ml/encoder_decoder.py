from utils.file import get_filenames
from utils.environ import generated_data_dir, valid_test_data_dir
import tensorflow as tf
import tensorflow_addons as tfa
import tensorflow_datasets as tfds
from tensorflow import keras


def train_dataset(paths):
    filepaths = get_filenames(paths)
    dataset = tf.data.TextLineDataset(filepaths)
    return dataset


def valid_test_datasets(paths, valid_size=0.8):

    def get_datasets(paths, filetype):

        paths_for_type = paths.filter(lambda x: x.endswith(filetype))
        filepaths = get_filenames(paths_for_type)

        dataset = tf.data.TextLineDataset(filepaths)
        max_num_file_tokens = \
            np.max(tf.strings.split(dataset).map(lambda x: len(x)))

        dataset_len = len(dataset)
        print(f'len(dataset): {len(dataset)}')

        valid_dataset_len = valid_size * dataset_len
        valid_dataset = dataset.take(valid_dataset_len)
        test_dataset = dataset.skip(valid_dataset_len) \
                            .take(dataset_len - valid_dataset_len)
        return valid_dataset, test_dataset, max_num_file_tokens

    result = {}
    valid_dataset, test_dataset, max_num_file_tokens = \
        get_datasets(paths, 'html')
    result['html'] = {'valid': valid_dataset,
                      'test': test_dataset}
    result['json'] = {'valid': valid_dataset,
                      'test': test_dataset}
    return result, max_num_file_tokens


train_dataset = train_dataset(os.path.join(generated_data_dir(), '*'))
valid_test_datasets, max_num_file_tokens = \
    train_test_datasets(os.path.join(valid_test_data_dir(), '*'))




K = keras.backend

datasets, info = tfds.load('imdb_reviews', as_supervised=True, with_info=True)
train_size = info.splits['train'].num_examples


def preprocess(X_batch, y_batch):
    X_batch = tf.strings.substr(X_batch, 0, 300)
    X_batch = tf.strings.regex_replace(X_batch, b'<br\\s*/?>', b' ')
    X_batch = tf.strings.regex_replace(X_batch, b'[^a-zA-Z\']', b' ')
    X_batch = tf.strings.split(X_batch)
    return X_batch.to_tensor(default_value=b'<pad>'), y_batch


def encode_words(X_batch, y_batch):
    return table.lookup(X_batch), y_batch


train_set = datasets['train'].batch(32).map(preprocess)
train_set = train_set.map(encode_words).prefetch(1)


encoder_inputs = keras.layers.Input(shape=[None], dtype=np.int32)
decoder_inputs = keras.layers.Input(shape=[None], dtype=np.int32)
sequence_lengths = keras.layers.Input(shape=[], dtype=np.int32)

embeddings = keras.layers.Embedding(vocab_size, embed_size)
encoder_embeddings = embeddings(encoder_inputs)
decoder_embeddings = embeddings(decoder_inputs)

encoder = keras.layers.LSTM(512, return_state=True)
encoder_outputs, state_h, state_c = encoder(encoder_embeddings)
encoder_state = [state_h, state_c]

sampler = tfa.seq2seq.sampler.TrainingSampler()

decoder_cell = keras.layers.LSTM(512)
output_layer = keras.layers.Dense(vocab_size)
decoder = tfa.seq2seq.basic_decoder.BasicDecoder(decoder_cell, sampler,
                                                 output_layer=output_layer)
final_outputs, final_state, final_sequence_lengths = \
    decoder(decoder_embeddings, initial_state=encoder_state,
            sequence_length=sequence_lengths)
Y_proba = tf.nn.softmax(final_outputs.rnn_output)

model = keras.Model(inputs=[encoder_inputs, decoder_inputs, sequence_lengths],
                    outputs=[Y_proba])
