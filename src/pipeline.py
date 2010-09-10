import os
import nipype.interfaces.utility as util     # utility
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.interfaces.io as nio           # Data i/o
from nipype.interfaces.dcm2nii import Dcm2nii

data_dir = os.path.abspath('/media/sdb2/laura_study/DATA_4_chis/Data_4_chris/')

subject_list = ['AG_1240', 'AG_1241','AG_1247','AG_1251','AG_1255','AG_1256',
                'AG_1257','AG_1260', 'AG_1261','AG_1262', 'AG_1264']

info = dict(t_map=[['subject_id', 'spmT_0003.img']])

infosource = pe.Node(interface=util.IdentityInterface(fields=['subject_id']),
                     name="infosource")
infosource.iterables = ('subject_id', subject_list)

datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],
                                               outfields=['t_map', 'struct']),
                     name = 'datasource')
datasource.inputs.base_directory = data_dir
datasource.inputs.template = '%s/*/%s'
datasource.inputs.template_args = info

analyze2nii = pe.Node(interface = Dcm2nii(), name="analyze2nii")

compare_pipeline = pe.Workflow(name="compare_pipeline")
compare_pipeline.base_dir = os.path.abspath("workdir")
compare_pipeline.connect([(infosource, datasource, [('subject_id', 'subject_id')]),
                          (datasource, analyze2nii, [('t_map', 'source_names')])
                          ])
compare_pipeline.run()