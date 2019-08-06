import os,sys,warnings
import numpy as np
import tensorflow as tf
from deepmd.common import ClassArg

from deepmd.RunOptions import global_tf_float_precision
from deepmd.RunOptions import global_np_float_precision
from deepmd.RunOptions import global_ener_float_precision
from deepmd.RunOptions import global_cvt_2_tf_float
from deepmd.RunOptions import global_cvt_2_ener_float

class LossStd () :
    def __init__ (self, jdata, starter_learning_rate) :
        self.starter_learning_rate = starter_learning_rate
        args = ClassArg()\
            .add('start_pref_e',        float,  default = 0.02)\
            .add('limit_pref_e',        float,  default = 1.00)\
            .add('start_pref_f',        float,  default = 1000)\
            .add('limit_pref_f',        float,  default = 1.00)\
            .add('start_pref_v',        float,  default = 0)\
            .add('limit_pref_v',        float,  default = 0)\
            .add('start_pref_ae',       float,  default = 0)\
            .add('limit_pref_ae',       float,  default = 0)\
            .add('start_pref_pf',       float,  default = 0)\
            .add('limit_pref_pf',       float,  default = 0)        
        class_data = args.parse(jdata)
        self.start_pref_e = class_data['start_pref_e']
        self.limit_pref_e = class_data['limit_pref_e']
        self.start_pref_f = class_data['start_pref_f']
        self.limit_pref_f = class_data['limit_pref_f']
        self.start_pref_v = class_data['start_pref_v']
        self.limit_pref_v = class_data['limit_pref_v']
        self.start_pref_ae = class_data['start_pref_ae']
        self.limit_pref_ae = class_data['limit_pref_ae']
        self.start_pref_pf = class_data['start_pref_pf']
        self.limit_pref_pf = class_data['limit_pref_pf']
        self.has_e = (self.start_pref_e != 0 or self.limit_pref_e != 0)
        self.has_f = (self.start_pref_f != 0 or self.limit_pref_f != 0)
        self.has_v = (self.start_pref_v != 0 or self.limit_pref_v != 0)
        self.has_ae = (self.start_pref_ae != 0 or self.limit_pref_ae != 0)
        self.has_pf = (self.start_pref_pf != 0 or self.limit_pref_pf != 0)

    def build (self, 
               learning_rate,
               natoms,
               prop_c,
               energy, 
               energy_hat,
               force,
               force_hat, 
               virial,
               virial_hat, 
               atom_ener,
               atom_ener_hat, 
               atom_pref,
               suffix):
        l2_ener_loss = tf.reduce_mean( tf.square(energy - energy_hat), name='l2_'+suffix)

        force_reshape = tf.reshape (force, [-1])
        force_hat_reshape = tf.reshape (force_hat, [-1])
        atom_pref_reshape = tf.reshape (atom_pref, [-1])
        l2_force_loss = tf.reduce_mean (tf.square(force_hat_reshape - force_reshape), name = "l2_force_" + suffix)
        l2_pref_force_loss = tf.reduce_mean (tf.multiply(tf.square(force_hat_reshape - force_reshape), atom_pref_reshape), name = "l2_pref_force_" + suffix)

        virial_reshape = tf.reshape (virial, [-1])
        virial_hat_reshape = tf.reshape (virial_hat, [-1])
        l2_virial_loss = tf.reduce_mean (tf.square(virial_hat_reshape - virial_reshape), name = "l2_virial_" + suffix)

        atom_ener_reshape = tf.reshape (atom_ener, [-1])
        atom_ener_hat_reshape = tf.reshape (atom_ener_hat, [-1])
        l2_atom_ener_loss = tf.reduce_mean (tf.square(atom_ener_hat_reshape - atom_ener_reshape), name = "l2_atom_ener_" + suffix)

        atom_norm  = 1./ global_cvt_2_tf_float(natoms[0]) 
        atom_norm_ener  = 1./ global_cvt_2_ener_float(natoms[0]) 
        pref_e = global_cvt_2_ener_float(prop_c[0] * (self.limit_pref_e + (self.start_pref_e - self.limit_pref_e) * learning_rate / self.starter_learning_rate) )
        pref_f = global_cvt_2_tf_float(prop_c[1] * (self.limit_pref_f + (self.start_pref_f - self.limit_pref_f) * learning_rate / self.starter_learning_rate) )
        pref_v = global_cvt_2_tf_float(prop_c[2] * (self.limit_pref_v + (self.start_pref_v - self.limit_pref_v) * learning_rate / self.starter_learning_rate) )
        pref_ae= global_cvt_2_tf_float(prop_c[3] * (self.limit_pref_ae+ (self.start_pref_ae-self.limit_pref_ae) * learning_rate / self.starter_learning_rate) )
        pref_pf= global_cvt_2_tf_float(prop_c[4] * (self.limit_pref_pf+ (self.start_pref_pf-self.limit_pref_pf) * learning_rate / self.starter_learning_rate) )

        l2_loss = 0
        if self.has_e :
            l2_loss += atom_norm_ener * (pref_e * l2_ener_loss)
        if self.has_f :
            l2_loss += global_cvt_2_ener_float(pref_f * l2_force_loss)
        if self.has_v :
            l2_loss += global_cvt_2_ener_float(atom_norm * (pref_v * l2_virial_loss))
        if self.has_ae :
            l2_loss += global_cvt_2_ener_float(pref_ae * l2_atom_ener_loss)
        if self.has_pf :
            l2_loss += global_cvt_2_ener_float(pref_pf * l2_pref_force_loss)

        return l2_loss, l2_ener_loss, l2_force_loss, l2_virial_loss, l2_atom_ener_loss, l2_pref_force_loss