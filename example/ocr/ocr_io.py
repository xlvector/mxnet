# pylint: disable=C0111,too-many-arguments,too-many-instance-attributes,too-many-locals,redefined-outer-name,fixme
# pylint: disable=superfluous-parens, no-member, invalid-name
import sys
sys.path.insert(0, "../../python")
import numpy as np
import mxnet as mx
from io import BytesIO
from captcha.image import ImageCaptcha
import cv2, random

class SimpleBatch(object):
    def __init__(self, data_names, data, label_names, label):
        self.data = data
        self.label = label
        self.data_names = data_names
        self.label_names = label_names

        self.pad = 0
        self.index = None # TODO: what is index?

    @property
    def provide_data(self):
        return [(n, x.shape) for n, x in zip(self.data_names, self.data)]

    @property
    def provide_label(self):
        return [(n, x.shape) for n, x in zip(self.label_names, self.label)]

def gen_rand():
    num = random.randint(0, 9999)
    buf = str(num)
    while len(buf) < 4:
        buf = "0" + buf
    return buf

def get_label(buf):
    ret = np.zeros(4, dtype=np.int)
    for i in range(4):
        ret[i] = int(buf[i])
    return ret

class OCRIter(mx.io.DataIter):
    def __init__(self, count, batch_size, init_states,
                 data_name='data', label_name='label'):
        super(OCRIter, self).__init__()
        self.captcha = ImageCaptcha(fonts=['./data/OpenSans-Regular.ttf'])
        self.batch_size = batch_size
        self.count = count
        self.init_states = init_states
        self.init_state_arrays = [mx.nd.zeros(x[1]) for x in init_states]
        self.provide_data = [('data', (batch_size, 30 * 80))] + init_states
        self.provide_label = [('softmax_label', (self.batch_size, 4))]

    def __iter__(self):
        init_state_names = [x[0] for x in self.init_states]
        for k in range(self.count):
            data = []
            label = []
            for i in range(self.batch_size):
                num = gen_rand()
                img = self.captcha.generate(num)
                img = np.fromstring(img.getvalue(), dtype='uint8')
                img = cv2.imdecode(img, cv2.IMREAD_GRAYSCALE)
                img = cv2.resize(img, (80, 30))
                img = img.transpose(1, 0)
                img = img.reshape((80 * 30))
                img = np.multiply(img, 1/255.0)
                data.append(img)
                label.append(get_label(num))

            data_all = [mx.nd.array(data)] + self.init_state_arrays
            label_all = [mx.nd.array(label)]
            data_names = ['data'] + init_state_names
            label_names = ['softmax_label']
            
            data_batch = SimpleBatch(data_names, data_all, label_names, label_all)
            yield data_batch

    def reset(self):
        pass
