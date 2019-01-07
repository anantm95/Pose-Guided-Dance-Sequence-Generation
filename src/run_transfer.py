import os

source_image = '/home/nidhi/whiteboy/00126_4.jpg'
source_pose = '/home/nidhi/whiteboy/00126_4.npy'
target_images = os.listdir('/home/nidhi/VUNet/vunet/data/custom/nidhi_floss/resized/') 
target_image_paths = ['/home/nidhi/VUNet/vunet/data/custom/nidhi_floss/resized/' + x for x in target_images]
target_poses = os.listdir('/home/nidhi/VUNet/vunet/data/custom/nidhi_floss/openpose/')
target_pose_paths = ['/home/nidhi/VUNet/vunet/data/custom/nidhi_floss/openpose/' + x for x in target_poses]

for i in range(len(target_image_paths)):
    t_path = target_image_paths[i]
    t_pose = target_pose_paths[i]
    command = 'python main.py --config deepfashion.yaml  --mode transfer --checkpoint deepfashion1_pretrained/checkpoints/model.ckpt-100000.data-00000-of-00001 --src_img ' + source_image + ' --tar_img ' + t_path + ' --src_jo ' + source_pose + ' --tar_jo ' + t_pose

    os.system(command)
             
               
               
               