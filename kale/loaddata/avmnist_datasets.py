import numpy as np
from torch.utils.data import DataLoader
import torch

class AVMNISTDataset:
    def __init__(self, data_dir,batch_size = 40, flatten_audio=False, flatten_image=False, unsqueeze_channel=True, normalize_image=True, normalize_audio=True):
        """Get dataloaders for AVMNIST.
    Args:
        data_dir (str): Directory of data.
        batch_size (int, optional): Batch size. Defaults to 40.
        flatten_audio (bool, optional): Whether to flatten audio data or not. Defaults to False.
        flatten_image (bool, optional): Whether to flatten image data or not. Defaults to False.
        unsqueeze_channel (bool, optional): Whether to unsqueeze any channels or not. Defaults to True.
        normalize_image (bool, optional): Whether to normalize the images before returning. Defaults to True.
        normalize_audio (bool, optional): Whether to normalize the audio before returning. Defaults to True.
    """
        self.data_dir = data_dir
        self.flatten_audio = flatten_audio
        self.flatten_image = flatten_image
        self.unsqueeze_channel = unsqueeze_channel
        self.normalize_image = normalize_image
        self.normalize_audio = normalize_audio
        self.batch_size = batch_size
        self.load_data()

    def load_data(self):
        trains = [np.load(self.data_dir+"/image/train_data.npy"), np.load(self.data_dir + "/audio/train_data.npy"), np.load(self.data_dir+"/train_labels.npy")]
        tests = [np.load(self.data_dir+"/image/test_data.npy"), np.load(self.data_dir + "/audio/test_data.npy"), np.load(self.data_dir+"/test_labels.npy")]
        train_valid_size = len(trains[0])
        test_size = len(tests[0])

        if self.flatten_audio:
            trains[1] = trains[0].reshape(train_valid_size, 112*112)
            tests[1] = tests[0].reshape(test_size, 112*112)

        if self.normalize_image:
            trains[0] = trains[0].astype('float64')
            trains[0] /= 255.0
            tests[0] = tests[0].astype('float64')
            tests[0] /= 255.0
        if self.normalize_audio:
            trains[1] = trains[1].astype('float64')
            trains[1] /= 255.0
            tests[1] = tests[1].astype('float64')
            tests[1] /= 255.0
        if not self.flatten_image:
            trains[0] = trains[0].reshape(train_valid_size, 28, 28)
            tests[0] = tests[0].reshape(test_size, 28, 28)
        if self.unsqueeze_channel:
            trains[0] = np.expand_dims(trains[0], 1)
            tests[0] = np.expand_dims(tests[0], 1)
            trains[1] = np.expand_dims(trains[1], 1)
            tests[1] = np.expand_dims(tests[1], 1)
        trains[2] = trains[2].astype(int)
        tests[2] = tests[2].astype(int)

        self.train_valid_data = [[trains[j][i] for j in range(3)] for i in range(train_valid_size)]
        self.test_data = [[tests[j][i] for j in range(3)] for i in range(test_size)]

        train_size = int(train_valid_size * 0.9)
        valid_size = train_valid_size - train_size

        self.train_data, self.valid_data = torch.utils.data.random_split(self.train_valid_data, [train_size, valid_size])

    def get_train_loader(self,shuffle=True):
        return DataLoader(self.train_data, shuffle=shuffle, batch_size=self.batch_size)

    def get_valid_loader(self, shuffle=False):
        return DataLoader(self.valid_data, shuffle=shuffle, batch_size=self.batch_size)

    def get_test_loader(self, shuffle=False):
        return DataLoader(self.test_data, shuffle=shuffle, batch_size=self.batch_size)
