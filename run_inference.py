import torch

from scipy.misc import imread, imsave, imresize
import matplotlib.pyplot as plt
import numpy as np
from path import Path
import argparse
from tqdm import tqdm

from models import DispResNet6
from utils import tensor2array

parser = argparse.ArgumentParser(description='Inference script for DispNet learned with \
                                 Structure from Motion Learner inference on KITTI and CityScapes Dataset',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

#parser.add_argument("--pretrained",  type=str, help="pretrained DispNet path",default='/home/roit/models/cc/official/dispnet_k.pth.tar')
parser.add_argument("--pretrained",  type=str, help="pretrained DispNet path",default='/home/roit/models/supervised/a/dispnet_model_best.pth.tar')

parser.add_argument("--img-height", default=128, type=int, help="Image height")
parser.add_argument("--img-width", default=192, type=int, help="Image width")
parser.add_argument("--no-resize", action='store_true', help="no resizing is done")

parser.add_argument("--dataset-list", default=None, type=str, help="Dataset list file")
parser.add_argument("--dataset-dir",
                    #default='/home/roit/datasets/kitti_small/data', type=str,help="Dataset directory")
                    default='/home/roit/datasets/MC_128192/2019_10_16_16_59/imgs', type=str,help="Dataset directory")

parser.add_argument("--output-dir", default='output', type=str, help="Output directory")
parser.add_argument("--output-disp", action='store_true', help="save disparity img",default=True)
parser.add_argument("--output-depth", action='store_true', help="save depth img",default=True)
parser.add_argument("--img-exts", default=['png', 'jpg', 'bmp'], nargs='*', type=str, help="images extensions to glob")


def main():
    args = parser.parse_args()
    if not(args.output_disp or args.output_depth):
        print('You must at least output one value !')
        return

    disp_net = DispResNet6().cuda()
    weights = torch.load(args.pretrained)
    disp_net.load_state_dict(weights['state_dict'])
    disp_net.eval()

    dataset_dir = Path(args.dataset_dir)
    output_dir = Path(args.output_dir)
    output_dir.makedirs_p()

    disp_dir = output_dir/dataset_dir.stem+'_disp'
    depth_dir = output_dir/dataset_dir.stem+'_depth'
    disp_dir.makedirs_p()
    depth_dir.makedirs_p()

    if args.dataset_list is not None:
        with open(args.dataset_list, 'r') as f:
            test_files = [dataset_dir/file for file in f.read().splitlines()]
    else:
        test_files = sum([dataset_dir.files('*.{}'.format(ext)) for ext in args.img_exts], [])

    print('{} files to test'.format(len(test_files)))



    for file in tqdm(test_files):

        img = imread(file).astype(np.float32)

        h,w,_ = img.shape
        if (not args.no_resize) and (h != args.img_height or w != args.img_width):
            img = imresize(img, (args.img_height, args.img_width)).astype(np.float32)
        img = np.transpose(img, (2, 0, 1))

        tensor_img = torch.from_numpy(img).unsqueeze(0)
        tensor_img = ((tensor_img/255 - 0.5)/0.2).cuda()

        disp = disp_net(tensor_img)#输出为单通道，
        depth = 1/disp#第一个batch

        '''
        if args.output_disp:
            disp = disp.cpu().data.numpy()
            disp=disp[0][0]*255
            plt.imsave(disp_dir/'{}.{}'.format(file.stem,'png'), disp,cmap='bone')
        if args.output_depth:
            depth=depth.cpu().data.numpy()
            depth=depth[0][0]*255
            plt.imsave(depth_dir/'{}.{}'.format(file.stem,'png'), depth,cmap='bone')
        '''

        if args.output_disp:
            disp=tensor2array(disp[0],colormap='bone')
            disp=np.transpose(disp,[1,2,0])
            plt.imsave(disp_dir/'{}.{}'.format(file.stem,'png'), disp,cmap='bone')
        if args.output_depth:
            depth=tensor2array(depth[0],colormap='bone')
            depth=np.transpose(depth,[1,2,0])
            plt.imsave(depth_dir/'{}.{}'.format(file.stem,'png'), depth,cmap='bone')



if __name__ == '__main__':
    main()
