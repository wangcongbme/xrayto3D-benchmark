import wandb
import torch
from pathlib import Path
from torch.utils.data.dataloader import DataLoader
from torch.optim import Adam
import pytorch_lightning as pl
import os
from XrayTo3DShape import (
    get_dataset,
    TLPredictorExperiment,
    CustomAutoEncoder,
    BaseExperiment,
    AutoencoderExperiment,
    parse_training_arguments,
    get_model,
    get_model_config,
    get_loss,
    get_anatomy_from_path,
    model_experiment_dict,
    get_transform_from_model_name
)
import XrayTo3DShape
from monai.utils.misc import set_determinism
from pytorch_lightning.loggers.wandb import WandbLogger
from pytorch_lightning import seed_everything
from pytorch_lightning.callbacks import ModelCheckpoint

anatomy_resolution  = {'totalseg_femur':(128,1.0),
                       'totalseg_ribs':(320,1.0),
                       'totalseg_hips':(288,1.0),
                       'verse2019':(96,1.0),
                       'verse2020':(96,1.0),
                       'femur':(128,1.0),
                       'rib':(320,1.0),
                       'hip':(288,1.0),
                       'verse':(96,1.0),
                       }




def update_args(args):
    args.anatomy = get_anatomy_from_path(args.trainpaths)

    # assert the resolution and size agree for each anatomy
    orig_size,orig_res = anatomy_resolution[args.anatomy]
    assert int(args.size * args.res) == int(orig_size * orig_res), f'({args.size},{args.res}) does not match ({orig_size},{orig_res})'
    args.experiment_name = model_experiment_dict[args.model_name]


    if args.gpu == 0:
        args.precision = 16 # use bfloat16 on RTX 3090
    else:
        args.precision = 32

if __name__ == "__main__":

    args = parse_training_arguments()
    update_args(args)
    SEED = 12345
    lr = args.lr
    NUM_EPOCHS = args.epochs
    IMG_SIZE = args.size
    ANATOMY = args.anatomy
    LOSS_NAME = args.loss
    IMG_RESOLUTION = args.res
    BATCH_SIZE = args.batch_size
    WANDB_PROJECT = args.wandb_project
    model_name = args.model_name
    experiment_name = args.experiment_name
    WANDB_EXPERIMENT_GROUP = args.model_name
    WANDB_TAGS = [WANDB_EXPERIMENT_GROUP,ANATOMY,LOSS_NAME,*args.tags]

    set_determinism(seed=SEED)
    seed_everything(seed=SEED)

    train_transforms = get_transform_from_model_name(model_name,image_size=IMG_SIZE,resolution=IMG_RESOLUTION)

    
    train_loader = DataLoader(
        get_dataset(args.trainpaths, transforms=train_transforms),
        batch_size=BATCH_SIZE,
        num_workers=args.num_workers,
        shuffle=True,
        drop_last=True
    )
    val_loader = DataLoader(
        get_dataset(args.valpaths, transforms=train_transforms),
        batch_size=BATCH_SIZE,
        num_workers=args.num_workers,
        shuffle=False,
        drop_last=False
    )

    print(f'training samples {len(train_loader.dataset)} validation samples {len(val_loader.dataset)}')
    model = get_model(model_name=args.model_name,image_size=IMG_SIZE)
    MODEL_CONFIG = get_model_config(model_name,IMG_SIZE)
    # save hyperparameters
    HYPERPARAMS = {'IMG_SIZE':IMG_SIZE,'RESOLUTION':IMG_RESOLUTION,'BATCH_SIZE':BATCH_SIZE,'LR':lr,'SEED':SEED,'ANATOMY':ANATOMY,'MODEL_NAME':model_name,'LOSS':LOSS_NAME,'EXPERIMENT_NAME':experiment_name}
    HYPERPARAMS.update(MODEL_CONFIG)

    loss_function = get_loss(loss_name=LOSS_NAME,anatomy=ANATOMY,image_size=IMG_SIZE,lambda_bce=args.lambda_bce,lambda_dice=args.lambda_dice,device=f'cuda:{args.gpu}') 
    optimizer = Adam(model.parameters(), lr)

    # load pytorch lightning module
    experiment:BaseExperiment = getattr(XrayTo3DShape.experiments,experiment_name)(model,optimizer,loss_function,BATCH_SIZE)
    if experiment_name == CustomAutoEncoder.__name__:
        experiment.make_sparse = args.make_sparse
    if experiment_name == TLPredictorExperiment.__name__:
        ae_model = get_model(model_name=CustomAutoEncoder.__name__,image_size=IMG_SIZE)
        if Path(args.load_autoencoder_from).exists():
            checkpoint = torch.load(args.load_autoencoder_from)
        else:
            raise ValueError(f'autoencoder checkpoint {args.laod_autoencoder_from} does not exist')
        for key in list(checkpoint['state_dict'].keys()):
            checkpoint['state_dict'][key.replace('model.', '')] = checkpoint['state_dict'].pop(key)
        checkpoint['state_dict'].pop('loss_function.pos_weight')
        ae_model.load_state_dict(checkpoint['state_dict'])
        experiment.set_decoder(ae_model) #type: ignore
    if args.debug:
        # print(model)
        batch = next(iter(train_loader))
        input,output = experiment.get_input_output_from_batch(batch)

        pred_logits = experiment.model(*input)
        if experiment_name == AutoencoderExperiment.__name__:
            pred_logits, latent_vec = pred_logits
        if experiment_name == TLPredictorExperiment.__name__:
            pred_logits = ae_model.latent_vec_decode(pred_logits)
        print('pred shape',pred_logits.shape,'gt shape',output.shape)
        print('\n Groundtruth',torch.min(output),torch.max(output))
        print('\n Input',torch.min(*input),torch.max(*input))
        print('\n logits',torch.min((pred_logits)),torch.max((pred_logits)))
        loss = experiment.loss_function(pred_logits,output)
        print('\n Loss',loss)
    else:
        # loggers
        wandb_logger = WandbLogger(save_dir='runs/',project=WANDB_PROJECT,group=WANDB_EXPERIMENT_GROUP,tags=WANDB_TAGS)
        wandb_logger.watch(model,log_graph=False)
        wandb_logger.log_hyperparams(HYPERPARAMS)
        
        checkpoint_callback = ModelCheckpoint(monitor='val/loss',mode='min',save_last=True,save_top_k=args.top_k_checkpoints,filename='epoch={epoch}-step={step}-val_loss={val/loss:.2f}-val_acc={val/dice:.2f}',auto_insert_metric_name=False)
        trainer = pl.Trainer(accelerator=args.accelerator,precision=args.precision,max_epochs=NUM_EPOCHS,devices=[args.gpu],deterministic=False,log_every_n_steps=1,auto_select_gpus=True,logger=[wandb_logger],callbacks=[checkpoint_callback],enable_progress_bar=True,enable_checkpointing=True,max_steps=args.steps)

        trainer.fit(experiment,train_loader,val_loader)


        wandb.finish()