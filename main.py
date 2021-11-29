from re import L
from trainer import Trainer
from dataset import FaceDataset, Grooo_type_Dataloader
from arcface import ArcFaceModel
from losses import ArcFaceLoss, ElasticArcFaceLoss
from optimizer import SAM

import os
import json
import torch
from PIL import ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

CONFIG_FILE = "configs/arcface_train.json"

if __name__ == '__main__':
    with open(CONFIG_FILE, "r") as jsonfile:
        config = json.load(jsonfile)

    # Get train and val dataset
    dataloader = Grooo_type_Dataloader(root_dir=config['root_dir'],
                                       val_size = 0.2,
                                       random_seed = 42,
                                       batch_size_train=64,
                                       batch_size_val=32)

    train_loader, val_loader = dataloader.get_dataloaders(num_worker=8)
    num_classes = dataloader.num_classes
    print("Number of classes: {num_classes}".format(num_classes=num_classes))

    # Get the path of pretrained model
    if config['use_pretrained']:
        pretrained_path = config['pretrained_model_path']
    else:
        pretrained_path = None

    # init model and train it
    if config['loss'] == 'ArcFace':
        loss_function = ArcFaceLoss()
        use_elasticloss = False
    elif config['loss'] == 'ElasticArcFace':
        loss_function = ElasticArcFaceLoss()
        use_elasticloss = True

    model = ArcFaceModel(backbone_name=config['backbone'], 
                        input_size=[112,112],
                        num_classes=num_classes,
                        use_pretrained=config['use_pretrained'],
                        pretrained_path=pretrained_path,
                        freeze=config['freeze_model'],
                        use_elasticloss=True,
                        type_of_freeze='body_only')

    n_epochs = config['n_epochs']

    if config['use_improved_optim']:
        optimizer = SAM(model.parameters(), lr=config['learning_rate'], momentum=0.9)
    else:
        optimizer = torch.optim.Adam(model.parameters(), lr=config['learning_rate'])
    
    
    trainer = Trainer(model=model,
                      n_epochs=n_epochs,
                      optimizer=optimizer,
                      loss_function=loss_function,
                      train_loader=train_loader,
                      val_loader=val_loader)

    trained_model = trainer.train(use_sam=config['use_improved_optim'], loss_verbose=False)

    # Save the best model
    if config['save_model']:
        torch.save(trained_model.state_dict(), 'logs/arcface_'+config['backbone']+'.pth')