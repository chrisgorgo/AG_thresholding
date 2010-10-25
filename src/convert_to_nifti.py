import nipype.externals.pynifti as nb
import numpy as np

image_filename2 = "/media/sdb2/laura_study/DATA_4_chis/SPGRs/AG_1247/T2.hdr"

nii2 = nb.load(image_filename2)

affine = nii2.get_affine()
flip_matrix = np.eye(4)
#flip_matrix[0,0] = -1
affine = np.dot(flip_matrix,affine)

data = nii2.get_data()

nb.save(nb.Nifti1Image(data, affine, nii2.get_header()), "new_T2.nii")