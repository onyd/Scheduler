import numpy as np
from PIL import Image


class ImageConcatenator:
    @staticmethod
    def horizontal_concatenate(dest_filename, *image_filenames):
        imgs = [Image.open(i) for i in image_filenames]
        min_height = min(*[i.size[1] for i in imgs])
        imgs_comb = np.hstack(
            [np.asarray(i.resize((i.size[0], min_height))) for i in imgs])

        # save that beautiful picture
        imgs_comb = Image.fromarray(imgs_comb)
        imgs_comb.save(dest_filename)

    @staticmethod
    def vertical_concatenate(dest_filename, *image_filenames):
        imgs = [Image.open(i) for i in image_filenames]
        min_width = min(*[i.size[0] for i in imgs])
        imgs_comb = np.vstack(
            [np.asarray(i.resize((min_width, i.size[1]))) for i in imgs])

        # save that beautiful picture
        imgs_comb = Image.fromarray(imgs_comb)
        imgs_comb.save(dest_filename)
