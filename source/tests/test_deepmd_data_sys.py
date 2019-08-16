import os,sys,shutil,copy
import numpy as np
import tensorflow as tf
import unittest

from deepmd.DataSystem import DeepmdDataSystem
from deepmd.RunOptions import global_np_float_precision

if global_np_float_precision == np.float32 :
    places = 6
else:
    places = 12

class TestDataSystem (unittest.TestCase) :
    def setUp (self) :
        self.nsys = 4
        self.nframes = [3, 6, 5, 4]
        self.natoms = [3, 4, 6, 5]
        self.atom_type = [[1, 0, 0], 
                          [2, 1, 0, 2],
                          [0, 0, 1, 1, 2, 1],
                          [0, 2, 2, 0, 0]]
        self.test_ndof = 2
        self.sys_name = []
        self.nset = 3
        for ii in range(self.nsys) :
            sys_name = 'sys_%d' % ii
            self.sys_name.append(sys_name)
            os.makedirs(sys_name, exist_ok = True)
            np.savetxt(os.path.join(sys_name, 'type.raw'), 
                       self.atom_type[ii], 
                       fmt = '%d')
            for jj in range(self.nset) :
                set_name = os.path.join(sys_name, 'set.%03d' % jj)
                os.makedirs(set_name, exist_ok = True)
                path = os.path.join(set_name, 'coord.npy')
                val = np.random.random([self.nframes[ii]+jj, self.natoms[ii]*3])
                np.save(path, val)
                path = os.path.join(set_name, 'box.npy')
                val = np.random.random([self.nframes[ii]+jj, 9]) * 10
                np.save(path, val)
                path = os.path.join(set_name, 'test.npy')
                val = np.random.random([self.nframes[ii]+jj, self.natoms[ii]*self.test_ndof])
                np.save(path, val)
                
    def tearDown(self):
        for ii in range(self.nsys) :
            sys_name = 'sys_%d' % ii
            shutil.rmtree(sys_name)            

    def test_ntypes(self) :
        batch_size = 3
        test_size = 2
        ds = DeepmdDataSystem(self.sys_name, batch_size, test_size, 2.0)
        ds.add('test', self.test_ndof, atomic = True, must = True)
        ds.add('null', self.test_ndof, atomic = True, must = False)
        self.assertEqual(ds.get_ntypes(), 3)
        self.assertEqual(ds.get_nbatches(), [2, 4, 3, 2])
        self.assertEqual(ds.get_nsystems(), self.nsys)
        self.assertEqual(list(ds.get_batch_size()), [batch_size]*4)
        

    def test_get_test(self):
        batch_size = 3
        test_size = 2
        ds = DeepmdDataSystem(self.sys_name, batch_size, test_size, 2.0)
        ds.add('test', self.test_ndof, atomic = True, must = True)
        ds.add('null', self.test_ndof, atomic = True, must = False)
        sys_idx = 0
        data = ds.get_test(sys_idx=sys_idx)
        self.assertEqual(list(data['type'][0]), list(np.sort(self.atom_type[sys_idx])))
        self._in_array(np.load('sys_0/set.002/coord.npy'),
                       ds.get_sys(sys_idx).idx_map,
                       3, 
                       data['coord'])
        self._in_array(np.load('sys_0/set.002/test.npy'),
                       ds.get_sys(sys_idx).idx_map,
                       self.test_ndof,
                       data['test'])
        self.assertAlmostEqual(np.linalg.norm(np.zeros([self.nframes[sys_idx]+2,
                                                        self.natoms[sys_idx]*self.test_ndof])
                                              -
                                              data['null']
        ), 0.0)
        sys_idx = 2
        data = ds.get_test(sys_idx=sys_idx)
        self.assertEqual(list(data['type'][0]), list(np.sort(self.atom_type[sys_idx])))
        self._in_array(np.load('sys_2/set.002/coord.npy'),
                       ds.get_sys(sys_idx).idx_map,
                       3, 
                       data['coord'])
        self._in_array(np.load('sys_2/set.002/test.npy'),
                       ds.get_sys(sys_idx).idx_map,
                       self.test_ndof,
                       data['test'])
        self.assertAlmostEqual(np.linalg.norm(np.zeros([self.nframes[sys_idx]+2,
                                                        self.natoms[sys_idx]*self.test_ndof])
                                              -
                                              data['null']
        ), 0.0)
        

    def test_get_batch(self):
        batch_size = 3
        test_size = 2
        ds = DeepmdDataSystem(self.sys_name, batch_size, test_size, 2.0)
        ds.add('test', self.test_ndof, atomic = True, must = True)
        ds.add('null', self.test_ndof, atomic = True, must = False)
        sys_idx = 0
        data = ds.get_batch(sys_idx=sys_idx)
        self.assertEqual(list(data['type'][0]), list(np.sort(self.atom_type[sys_idx])))
        self._in_array(np.load('sys_0/set.000/coord.npy'),
                       ds.get_sys(sys_idx).idx_map,
                       3, 
                       data['coord'])
        self._in_array(np.load('sys_0/set.000/test.npy'),
                       ds.get_sys(sys_idx).idx_map,
                       self.test_ndof,
                       data['test'])
        self.assertAlmostEqual(np.linalg.norm(np.zeros([batch_size,
                                                        self.natoms[sys_idx]*self.test_ndof])
                                              -
                                              data['null']
        ), 0.0)
        data = ds.get_batch(sys_idx=sys_idx)
        self.assertEqual(list(data['type'][0]), list(np.sort(self.atom_type[sys_idx])))
        self._in_array(np.load('sys_0/set.001/coord.npy'),
                       ds.get_sys(sys_idx).idx_map,
                       3, 
                       data['coord'])
        self._in_array(np.load('sys_0/set.001/test.npy'),
                       ds.get_sys(sys_idx).idx_map,
                       self.test_ndof,
                       data['test'])
        self.assertAlmostEqual(np.linalg.norm(np.zeros([batch_size, 
                                                        self.natoms[sys_idx]*self.test_ndof])
                                              -
                                              data['null']
        ), 0.0)
        data = ds.get_batch(sys_idx=sys_idx)
        self.assertEqual(list(data['type'][0]), list(np.sort(self.atom_type[sys_idx])))
        self._in_array(np.load('sys_0/set.000/coord.npy'),
                       ds.get_sys(sys_idx).idx_map,
                       3, 
                       data['coord'])
        self._in_array(np.load('sys_0/set.000/test.npy'),
                       ds.get_sys(sys_idx).idx_map,
                       self.test_ndof,
                       data['test'])
        self.assertAlmostEqual(np.linalg.norm(np.zeros([batch_size, 
                                                        self.natoms[sys_idx]*self.test_ndof])
                                              -
                                              data['null']
        ), 0.0)
        sys_idx = 2
        data = ds.get_batch(sys_idx=sys_idx)
        self.assertEqual(list(data['type'][0]), list(np.sort(self.atom_type[sys_idx])))
        self._in_array(np.load('sys_2/set.000/coord.npy'),
                       ds.get_sys(sys_idx).idx_map,
                       3, 
                       data['coord'])
        self._in_array(np.load('sys_2/set.000/test.npy'),
                       ds.get_sys(sys_idx).idx_map,
                       self.test_ndof,
                       data['test'])
        self.assertAlmostEqual(np.linalg.norm(np.zeros([batch_size, 
                                                        self.natoms[sys_idx]*self.test_ndof])
                                              -
                                              data['null']
        ), 0.0)
        data = ds.get_batch(sys_idx=sys_idx)
        self.assertEqual(list(data['type'][0]), list(np.sort(self.atom_type[sys_idx])))
        self._in_array(np.load('sys_2/set.001/coord.npy'),
                       ds.get_sys(sys_idx).idx_map,
                       3, 
                       data['coord'])
        self._in_array(np.load('sys_2/set.001/test.npy'),
                       ds.get_sys(sys_idx).idx_map,
                       self.test_ndof,
                       data['test'])
        self.assertAlmostEqual(np.linalg.norm(np.zeros([batch_size, 
                                                        self.natoms[sys_idx]*self.test_ndof])
                                              -
                                              data['null']
        ), 0.0)
        data = ds.get_batch(sys_idx=sys_idx)
        self.assertEqual(list(data['type'][0]), list(np.sort(self.atom_type[sys_idx])))
        self._in_array(np.load('sys_2/set.001/coord.npy'),
                       ds.get_sys(sys_idx).idx_map,
                       3, 
                       data['coord'])
        self._in_array(np.load('sys_2/set.001/test.npy'),
                       ds.get_sys(sys_idx).idx_map,
                       self.test_ndof,
                       data['test'])
        self.assertAlmostEqual(np.linalg.norm(np.zeros([batch_size, 
                                                        self.natoms[sys_idx]*self.test_ndof])
                                              -
                                              data['null']
        ), 0.0)
        data = ds.get_batch(sys_idx=sys_idx)
        self.assertEqual(list(data['type'][0]), list(np.sort(self.atom_type[sys_idx])))
        self._in_array(np.load('sys_2/set.000/coord.npy'),
                       ds.get_sys(sys_idx).idx_map,
                       3, 
                       data['coord'])
        self._in_array(np.load('sys_2/set.000/test.npy'),
                       ds.get_sys(sys_idx).idx_map,
                       self.test_ndof,
                       data['test'])
        self.assertAlmostEqual(np.linalg.norm(np.zeros([batch_size, 
                                                        self.natoms[sys_idx]*self.test_ndof])
                                              -
                                              data['null']
        ), 0.0)


    def _idx_map(self, target, idx_map, ndof):
        natoms = len(idx_map)
        target = target.reshape([-1, natoms, ndof])
        target = target[:,idx_map,:]
        target = target.reshape([-1, natoms * ndof])
        return target        

    def _in_array(self, target, idx_map, ndof, array):
        target = self._idx_map(target, idx_map, ndof)
        all_find = []
        for ii in array :
            find = False
            for jj in target :
                if np.linalg.norm(ii - jj) < 1e-5 :
                    find = True
            all_find.append(find)
        for idx,ii in enumerate(all_find) :
            self.assertTrue(ii, msg = 'does not find frame %d in array' % idx)

                