import os
import random
from pathlib import Path

import numpy as np
import pytest
import torch
from torchvision import transforms
from yacs.config import CfgNode

from kale.loaddata.few_shot import NWayKShotDataset
from kale.utils.download import download_file_by_url

url = "https://github.com/pykale/data/raw/main/images/omniglot/omniglot_demo.zip"
modes = ["train", "val", "test"]


@pytest.fixture(scope="module")
def testing_cfg(download_path):
    cfg = CfgNode()
    cfg.DATASET = CfgNode()
    cfg.DATASET.ROOT = os.path.join(download_path, "omniglot_demo")
    yield cfg


@pytest.mark.parametrize("mode", modes)
def test_n_way_k_shot(mode, testing_cfg):
    cfg = testing_cfg
    output_dir = str(Path(cfg.DATASET.ROOT).parent.absolute())
    download_file_by_url(url=url, output_directory=output_dir, output_file_name="omniglot_demo.zip", file_format="zip")
    transform = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor()])
    k_shot = random.randint(1, 10)
    query_samples = random.randint(1, 10)
    n_way = random.randint(1, 10)
    dataset = NWayKShotDataset(
        path=cfg.DATASET.ROOT, mode=mode, k_shot=k_shot, query_samples=query_samples, transform=transform
    )

    assert len(dataset) == len(dataset.classes) > 0
    assert isinstance(dataset._get_idx(0), np.ndarray)
    assert isinstance(dataset._sample_data(dataset._get_idx(0)), list)
    assert isinstance(dataset._sample_data(dataset._get_idx(0))[0], torch.Tensor)
    assert isinstance(dataset.__getitem__(0), tuple)
    assert isinstance(dataset.__getitem__(0)[0], torch.Tensor)
    assert isinstance(dataset.__getitem__(0)[1], int)

    dataloader = torch.utils.data.DataLoader(dataset, batch_size=n_way, shuffle=True, drop_last=True)
    for batch in dataloader:
        assert len(dataloader) > 0
        assert isinstance(batch, list)
        assert isinstance(batch[0], torch.Tensor)
        assert isinstance(batch[1], torch.Tensor)
        assert batch[0].shape == (n_way, k_shot + query_samples, 3, 224, 224)
        assert batch[1].shape == (n_way,)
        break
