# =============================================================================
# Author: Wenrui Fan, wenrui.fan@sheffield.ac.uk
# =============================================================================

"""ProtoNet trainer (pipelines)

This module contains the ProtoNet trainer class and its related functions. It is used to train the ProtoNet model in N-way-k-shot problems.

This module uses `PyTorch Lightning <https://github.com/Lightning-AI/lightning>` to standardize the flow.

This is a modified version of original prototypical networks for few-shot learning projects from https://github.com/jakesnell/prototypical-networks.
"""

from typing import Any

import pytorch_lightning as pl
import torch

from kale.predict.losses import proto_loss


class ProtoNetTrainer(pl.LightningModule):
    """ProtoNet trainer class

    Args:
        model (torch.nn.Module): A feature extractor replaced classfier with a flatten layer. Output 1-D feature vectors.
    """

    def __init__(
        self,
        net: torch.nn.Module,
        train_n_way: int = 30,
        train_k_shot: int = 5,
        train_k_query: int = 15,
        val_n_way: int = 5,
        val_k_shot: int = 5,
        val_k_query: int = 15,
        devices: str = "cuda",
        optimizer: str = "SGD",
        lr: float = 0.001,
    ) -> None:
        super().__init__()

        self.train_n_way = train_n_way
        self.train_k_shot = train_k_shot
        self.train_k_query = train_k_query
        self.val_n_way = val_n_way
        self.val_k_shot = val_k_shot
        self.val_k_query = val_k_query
        self.devices = devices
        self.optimizer = optimizer
        self.lr = lr

        # model
        self.model = net

        # loss
        self.loss_train = proto_loss(n_ways=train_n_way, k_query=train_k_query, device=self.devices)
        self.loss_val = proto_loss(n_ways=val_n_way, k_query=val_k_query, device=self.devices)

    def forward(self, x, k_shots, n_ways) -> torch.Tensor:
        x = x.to(self.devices)
        supports = x[0][0:k_shots]
        queries = x[0][k_shots:]
        for image in x[1:]:
            supports = torch.cat((supports, image[0:k_shots]), dim=0)
            queries = torch.cat((queries, image[k_shots:]), dim=0)
        feature_sup = self.model(supports).reshape(n_ways, k_shots, -1)
        feature_que = self.model(queries)
        return feature_sup, feature_que

    def compute_loss(self, feature_sup, feature_que, mode="train") -> tuple:
        """
        Compute loss and accuracy. Here we use the same loss function for both training and validation,
        which is related to Euclidean distance.

        Args:
            feature_sup (torch.Tensor): Support features.
            feature_que (torch.Tensor): Query features.
            mode (str): Mode of the trainer, "train", "val" or "test".

        Returns:
            loss (torch.Tensor): Loss value.
            return_dict (dict): Dictionary of loss and accuracy.
        """
        loss, acc = eval(f"self.loss_{mode}")(feature_sup, feature_que)
        return_dict = {"{}_loss".format(mode): loss.item(), "{}_acc".format(mode): acc}
        return loss, return_dict

    def training_step(self, batch: Any, batch_idx: int) -> torch.Tensor:
        """
        Training step. Compute loss and accuracy, and log them by self.log_dict. For training,
        log on each step and each epoch. For validation and testing, only log on each epoch.
        This way can avoid using on_training_epoch_end() and on_validation_epoch_end().
        """
        images, _ = batch
        feature_sup, feature_que = self.forward(images, self.train_k_shot, self.train_n_way)
        loss, log_metrics = self.compute_loss(feature_sup, feature_que, mode="train")
        self.log_dict(log_metrics, on_step=True, on_epoch=True, prog_bar=True, logger=True)
        return loss

    def validation_step(self, batch: Any, batch_idx: int) -> None:
        """Compute and return the validation loss and log_metrics on one step."""
        images, _ = batch
        feature_sup, feature_que = self.forward(images, self.val_k_shot, self.val_n_way)
        _, log_metrics = self.compute_loss(feature_sup, feature_que, mode="val")
        self.log_dict(log_metrics, on_step=False, on_epoch=True, prog_bar=True, logger=True)

    def test_step(self, batch: Any, batch_idx: int) -> None:
        """Compute and return the test loss and log_metrics on one step."""
        images, _ = batch
        feature_sup, feature_que = self.forward(images, self.val_k_shot, self.val_n_way)
        _, log_metrics = self.compute_loss(feature_sup, feature_que, mode="val")
        self.log_dict(log_metrics, on_step=False, on_epoch=True, prog_bar=True, logger=True)

    def configure_optimizers(self) -> torch.optim.Optimizer:
        """
        Configure optimizer for training. Can be modified to support different optimizers from torch.optim.
        """
        optimizer = eval(f"torch.optim.{self.optimizer}")(self.model.parameters(), lr=self.lr)
        return optimizer
