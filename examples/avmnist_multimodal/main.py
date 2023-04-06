import torch

import argparse
import os
from trainer import Trainer
from config import get_cfg_defaults
from kale.loaddata.avmnist_datasets import AVMNISTDataset
from kale.utils.seed import set_seed
from kale.utils.logger import construct_logger
from kale.utils.download import download_file_gdrive

from model import get_model


def arg_parse():
    """Parsing arguments"""
    parser = argparse.ArgumentParser(description="PyTorch AVMNIST Training")
    parser.add_argument("--cfg", required=True, help="path to config file", type=str)
    parser.add_argument("--output", default="default", help="folder to save output", type=str)
    args = parser.parse_args()
    return args

def main():
    """The main for this avmnist example, showing the workflow"""
    args = arg_parse()
    # ---- setup device ----
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("==> Using device " + device)

    # ---- setup configs ----
    cfg = get_cfg_defaults()
    cfg.merge_from_file(args.cfg)
    cfg.freeze()
    set_seed(cfg.SOLVER.SEED)

    # ---- setup logger and output ----
    output_dir = os.path.join(cfg.OUTPUT_DIR, cfg.DATASET.NAME, args.output)
    os.makedirs(output_dir, exist_ok=True)
    logger = construct_logger("avmnist", output_dir)
    logger.info("Using " + device)
    logger.info("\n" + cfg.dump())

    download_file_gdrive(cfg.DATASET.GDRIVE_ID,cfg.DATASET.ROOT, cfg.DATASET.NAME, cfg.DATASET.FILE_FORAMT)

    dataset = AVMNISTDataset(data_dir=cfg.DATASET.ROOT,batch_size=cfg.DATASET.BATCH_SIZE)
    traindata = dataset.get_train_loader()
    validdata = dataset.get_valid_loader()
    testdata = dataset.get_test_loader()
    print("Data Loaded Successfully")

    model = get_model(cfg,device)

    trainer = Trainer(device,model,traindata,validdata,testdata, cfg.SOLVER.MAX_EPOCHS, optimtype= torch.optim.SGD, lr=cfg.SOLVER.BASE_LR, weight_decay=cfg.SOLVER.WEIGHT_DECAY)

    trainer.train()

    print("Testing:")
    trainer.single_test()


if __name__ == '__main__':
    main()
