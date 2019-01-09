# Enhanced Variational U-net for Pose-Guided Dance Sequence Generation
This project aims at using Variotional Autoencoders with adversarial learning in order to transfer a pose from one person to another maintaining the clothing and other semantic details. We generate dance sequences via frame-to-frame transfer.

This is an extension to the work done by Esser et. al titled 'A Variational U-Net for Conditional Appearance and Shape Generation'. 

The improved model with adversarial training using output pf a pretrained VGG19 model, combined with perceptual loss gives robustness to the model for complex poses. The new model also captures semantic details (eg. skin color, clothing details, etc) better than the original model.

Results and a supplemental video for this project can be found here:
https://drive.google.com/open?id=1HbuDx-_JgvLN-OHeShfChESON2t1a59I
