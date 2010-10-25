import os
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.io as nio           # Data i/o
import nipype.interfaces.spm as spm          # spm
import nipype.algorithms.misc as misc
import nodes
from nipype.interfaces.dcm2nii import Dcm2nii

data_dir = os.path.abspath('/media/sdb2/laura_study/DATA_4_chis/')

task_dict = {
             'AG_1240':17.5, 'AG_1241':13.1,'AG_1247':10,'AG_1251':6,'AG_1255':3,'AG_1256':10,
                'AG_1257':9,'AG_1260':9, 'AG_1261':5.7,'AG_1262':10, 
                'AG_1264':7}

info = dict(t_map=[['subject_id', 'spmT_0003.img']],
            spm_mat_file=[['subject_id', 'SPM.mat']],
            mask=[['subject_id', 'mask.img']],
            expert_thresholded_map=[['subject_id', 'threshold']],
            struct=[['subject_id']],
            tumour_mask=[['subject_id']] )

infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']),
                     name="infosource")
infosource.iterables = ('subject_id', task_dict.keys())

datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id', 'threshold'],
                                               outfields=info.keys()),
                     name = 'datasource')
datasource.inputs.base_directory = data_dir
datasource.inputs.template = 'func/%s/*/%s'
datasource.inputs.field_template = dict(expert_thresholded_map='func/%s/*/AG*%s.img',
                                        struct='SPGRs/%s/*.img',
                                        tumour_mask='SPGRs/%s/tumour.nii')
datasource.inputs.template_args = info

struct_analyze2nii = pe.Node(interface = spm.Analyze2nii(), name="struct_analyze2nii")

threshold = pe.Node(interface = spm.Threshold(), name="threshold_topo_fdr_with_fwe")
threshold.inputs.contrast_index = 3
threshold.iterables = ('extent_threshold', [0,   10])

thresholdGGMM = pe.Node(interface=nodes.ThresholdGGMM(no_deactivation_class=True),name="ThresholdGGMM")

threshold_l2 = pe.Node(interface = spm.Threshold(), name="threshold_topo_fdr_with_ggmm")
threshold_l2.inputs.contrast_index = 3
threshold_l2.inputs.use_fwe_correction = False
threshold_l2.iterables = ('extent_threshold', [0,   10])

expert_distance = pe.Node(interface=misc.Distance(), name="expert_distance")


analyze2nii = pe.Node(interface = Dcm2nii(), name="analyze2nii")
fix_affine = pe.Node(interface=misc.ModifyAffine(), name="fix_affine")
reslice = pe.Node(interface=spm.Coregister(), name="reslice")

convert_pipeline = pe.Workflow(name="analyze2nifti")
convert_pipeline.connect([(analyze2nii, fix_affine, [('converted_files', 'volumes')]),
                          (fix_affine, reslice, [('transformed_volumes', 'source')])])

convert_manual = convert_pipeline.clone("convert_manual")
convert_mask = convert_pipeline.clone("convert_mask")
convert_t_map = convert_pipeline.clone("convert_t_map")


def get_th(subjec_id):
    num_th = task_dict[subjec_id]
    return str(num_th).replace('.','d')

compare_pipeline = pe.Workflow(name="compare_pipeline")
compare_pipeline.base_dir = os.path.abspath("workdir")
compare_pipeline.connect([(infosource, datasource, [('subject_id', 'subject_id'),
                                                    (('subject_id', get_th), 'threshold')]),
                                                                              
                          (datasource, struct_analyze2nii, [('struct', 'analyze_file')]),
                          
                          (datasource, convert_manual, [('expert_thresholded_map', 'analyze2nii.source_names')]),
                          (struct_analyze2nii, convert_manual, [('nifti_file', 'reslice.target')]),
                          
                          (datasource, convert_mask, [('mask', 'analyze2nii.source_names')]),
                          (struct_analyze2nii, convert_mask, [('nifti_file', 'reslice.target')]),
                          
                          (datasource, convert_t_map, [('t_map', 'analyze2nii.source_names')]),
                          (struct_analyze2nii, convert_t_map, [('nifti_file', 'reslice.target')]),
                          
                          (datasource, threshold,[('spm_mat_file','spm_mat_file')]),
                          (convert_t_map, threshold, [('fix_affine.transformed_volumes','stat_image')]),
                          
                          (convert_t_map, thresholdGGMM,[('fix_affine.transformed_volumes', 'stat_image')]),
                          (convert_mask, thresholdGGMM,[('fix_affine.transformed_volumes', 'mask_file')]),
                          
                          (datasource, threshold_l2,[('spm_mat_file','spm_mat_file')]),
                          (convert_t_map, threshold_l2, [('fix_affine.transformed_volumes','stat_image')]),
                          (thresholdGGMM, threshold_l2,[('threshold','height_threshold')]),
                          
                          (datasource, expert_distance, [('tumour_mask','volume1')]),
                          (convert_manual, expert_distance, [('fix_affine.transformed_volumes','volume2')])               
                          ])
compare_pipeline.run()