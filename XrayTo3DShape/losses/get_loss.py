from torch.nn import BCEWithLogitsLoss,CrossEntropyLoss
from monai.losses.dice import DiceLoss
from .losses_zoo import DiceCELoss
import torch

pos_weights_dict = {'hip':719,'femur':612,'vertebra':23,'rib':5231}

def get_loss(loss_name,**kwargs):
    if loss_name == BCEWithLogitsLoss.__name__:
        return get_WCE(**kwargs)
    elif loss_name == CrossEntropyLoss.__name__:
        return get_CE(**kwargs)
    elif loss_name == DiceLoss.__name__:
        return DiceLoss(sigmoid=True)
    elif loss_name == DiceCELoss.__name__:
        return get_DiceCE(**kwargs,sigmoid=True)
    else:
        raise ValueError(f'invalid loss name {loss_name}')

def get_WCE(anatomy,image_size):
    # Weighted cross-entropy loss
    pos_weight = torch.full([1,image_size,image_size,image_size],pos_weights_dict[anatomy])
    return BCEWithLogitsLoss(pos_weight=pos_weight)

def get_CE(anatomy,image_size):
    # Weighted cross-entropy loss
    pos_weight = torch.full([1,image_size,image_size,image_size],pos_weights_dict[anatomy])
    return CrossEntropyLoss(weight=pos_weight)

def get_DiceCE(anatomy,image_size,sigmoid=True,softmax=False,lambda_dice=1.0,lambda_bce=1.0):
    pos_weight = torch.full([1,image_size,image_size,image_size],pos_weights_dict[anatomy])
    return DiceCELoss(
        softmax=softmax,
        sigmoid=sigmoid,
        ce_pos_weight=pos_weight,
        lambda_dice=lambda_dice,
        lambda_bce=lambda_bce
    )