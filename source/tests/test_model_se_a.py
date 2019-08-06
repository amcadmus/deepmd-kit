import dpdata,os,sys,json,unittest
import numpy as np
import tensorflow as tf
from common import Data

from deepmd.RunOptions import RunOptions
from deepmd.DataSystem import DataSystem
from deepmd.DescrptSeA import DescrptSeA
from deepmd.Fitting import EnerFitting
from deepmd.Model import Model
from deepmd.common import j_must_have, j_must_have_d, j_have

global_ener_float_precision = tf.float64
global_tf_float_precision = tf.float64
global_np_float_precision = np.float64

def gen_data() :
    tmpdata = Data(rand_pert = 0.1, seed = 1)
    sys = dpdata.LabeledSystem()
    sys.data['coords'] = tmpdata.coord
    sys.data['atom_types'] = tmpdata.atype
    sys.data['cells'] = tmpdata.cell
    nframes = tmpdata.nframes
    natoms = tmpdata.natoms
    sys.data['coords'] = sys.data['coords'].reshape([nframes,natoms,3])
    sys.data['cells'] = sys.data['cells'].reshape([nframes,3,3])
    sys.data['energies'] = np.zeros([nframes,1])
    sys.data['forces'] = np.zeros([nframes,natoms,3])
    sys.data['virials'] = []
    sys.to_deepmd_npy('system', prec=np.float64)    

class TestModel(unittest.TestCase):
    def setUp(self) :
        gen_data()

    def test_model(self):
        jfile = 'water_se_a.json'
        with open(jfile) as fp:
            jdata = json.load (fp)
        run_opt = RunOptions(None) 
        systems = j_must_have(jdata, 'systems')
        set_pfx = j_must_have(jdata, 'set_prefix')
        batch_size = j_must_have(jdata, 'batch_size')
        test_size = j_must_have(jdata, 'numb_test')
        batch_size = 1
        test_size = 1
        stop_batch = j_must_have(jdata, 'stop_batch')
        rcut = j_must_have (jdata['model']['descriptor'], 'rcut')
        
        data = DataSystem(systems, set_pfx, batch_size, test_size, rcut, run_opt = None)
        
        test_data = data.get_test ()
        numb_test = 1
        
        bias_atom_e = data.compute_energy_shift()

        descrpt = DescrptSeA(jdata['model']['descriptor'])
        fitting = EnerFitting(jdata['model']['fitting_net'], descrpt)
        model = Model(jdata['model'], descrpt, fitting)

        davg, dstd = model.compute_dstats([test_data['coord']], [test_data['box']], [test_data['type']], [test_data['natoms_vec']], [test_data['default_mesh']])

        t_prop_c           = tf.placeholder(tf.float32, [5],    name='t_prop_c')
        t_energy           = tf.placeholder(global_ener_float_precision, [None], name='t_energy')
        t_force            = tf.placeholder(global_tf_float_precision, [None], name='t_force')
        t_virial           = tf.placeholder(global_tf_float_precision, [None], name='t_virial')
        t_atom_ener        = tf.placeholder(global_tf_float_precision, [None], name='t_atom_ener')
        t_coord            = tf.placeholder(global_tf_float_precision, [None], name='i_coord')
        t_type             = tf.placeholder(tf.int32,   [None], name='i_type')
        t_natoms           = tf.placeholder(tf.int32,   [model.ntypes+2], name='i_natoms')
        t_box              = tf.placeholder(global_tf_float_precision, [None, 9], name='i_box')
        t_mesh             = tf.placeholder(tf.int32,   [None], name='i_mesh')
        is_training        = tf.placeholder(tf.bool)
        t_fparam = None

        energy, force, virial, atom_ener, atom_virial \
            = model.build (t_coord, 
                           t_type, 
                           t_natoms, 
                           t_box, 
                           t_mesh,
                           t_fparam,
                           davg = davg,
                           dstd = dstd,
                           bias_atom_e = bias_atom_e, 
                           suffix = "se_a", 
                           reuse = False)

        feed_dict_test = {t_prop_c:        test_data['prop_c'],
                          t_energy:        test_data['energy']              [:numb_test],
                          t_force:         np.reshape(test_data['force']    [:numb_test, :], [-1]),
                          t_virial:        np.reshape(test_data['virial']   [:numb_test, :], [-1]),
                          t_atom_ener:     np.reshape(test_data['atom_ener'][:numb_test, :], [-1]),
                          t_coord:         np.reshape(test_data['coord']    [:numb_test, :], [-1]),
                          t_box:           test_data['box']                 [:numb_test, :],
                          t_type:          np.reshape(test_data['type']     [:numb_test, :], [-1]),
                          t_natoms:        test_data['natoms_vec'],
                          t_mesh:          test_data['default_mesh'],
                          is_training:     False}

        sess = tf.Session()
        sess.run(tf.global_variables_initializer())
        [e, f, v] = sess.run([energy, force, virial], 
                             feed_dict = feed_dict_test)

        e = e.reshape([-1])
        f = f.reshape([-1])
        v = v.reshape([-1])
        refe = [6.135449167779321300e+01]
        reff = [7.799691562262310585e-02,9.423098804815030483e-02,3.790560997388224204e-03,1.432522403799846578e-01,1.148392791403983204e-01,-1.321871172563671148e-02,-7.318966526325138000e-02,6.516069212737778116e-02,5.406418483320515412e-04,5.870713761026503247e-02,-1.605402669549013672e-01,-5.089516979826595386e-03,-2.554593467731766654e-01,3.092063507347833987e-02,1.510355029451411479e-02,4.869271842355533952e-02,-1.446113274345035005e-01,-1.126524434771078789e-03]
        refv = [-6.076776685178300053e-01,1.103174323630009418e-01,1.984250991380156690e-02,1.103174323630009557e-01,-3.319759402259439551e-01,-6.007404107650986258e-03,1.984250991380157036e-02,-6.007404107650981921e-03,-1.200076017439753642e-03]
        refe = np.reshape(refe, [-1])
        reff = np.reshape(reff, [-1])
        refv = np.reshape(refv, [-1])

        places = 10
        for ii in range(e.size) :
            self.assertAlmostEqual(e[ii], refe[ii], places = places)
        for ii in range(f.size) :
            self.assertAlmostEqual(f[ii], reff[ii], places = places)
        for ii in range(v.size) :
            self.assertAlmostEqual(v[ii], refv[ii], places = places)