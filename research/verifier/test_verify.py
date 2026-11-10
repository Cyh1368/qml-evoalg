import unittest
import numpy as np
from verify import closure, verify, repair_generator, invariant_prediction

class VerificationTests(unittest.TestCase):
    def test_closure(self):
        self.assertEqual(len(closure([[1,0,2], [0,2,1]], 3)), 6)
        with self.assertRaises(ValueError):
            closure([[0,0]], 2)
        with self.assertRaises(ValueError):
            closure([[1,0,2], [0,2,1]], 3, limit=3)

    def test_tied_and_untied(self):
        hypothesis = {'n_qubits': 2, 'generators': [[1,0]], 'output_action': 'invariant'}
        tied = [{'gate':'RY','wire':w,'param':'a'} for w in range(2)]
        self.assertTrue(verify(hypothesis,tied,[{'a':0.37}])['sampled_channel_equivariance_pass'])
        untied = [{'gate':'RY','wire':0,'param':'a'}]
        self.assertFalse(verify(hypothesis,untied,[{'a':0.37}])['sampled_channel_equivariance_pass'])
        # A special parameter point can pass; output explicitly denies universal proof.
        report = verify(hypothesis,untied,[{'a':0.0}])
        self.assertTrue(report['sampled_channel_equivariance_pass'])
        self.assertFalse(report['all_parameter_proof'])
        self.assertFalse(report['task_symmetry_validated'])

    def test_repair_projection(self):
        x = np.array([[0,1],[1,0]])
        h = np.kron(x,np.eye(2))
        repaired = repair_generator(h, [[1,0]])
        expected = (h + np.kron(np.eye(2),x))/2
        np.testing.assert_allclose(repaired,expected)
        np.testing.assert_allclose(repair_generator(repaired,[[1,0]]),repaired)
        self.assertLess(np.linalg.norm(repaired-h),np.linalg.norm(h))

    def test_prediction_repair(self):
        predict = lambda x: x[0]**2 + 3*x[1]
        a = invariant_prediction(predict,[1.,2.],[[1,0]])
        b = invariant_prediction(predict,[2.,1.],[[1,0]])
        self.assertEqual(a,b)

if __name__ == '__main__':
    unittest.main()

class TaskValidationTests(unittest.TestCase):
    def test_induced_edge_action(self):
        from verify import graph_edge_action
        # Pairs: 01,02,12; swapping vertices 0 and 1 preserves 01.
        np.testing.assert_array_equal(graph_edge_action([1,2,3],[1,0,2]),[1,3,2])
        with self.assertRaises(ValueError):
            graph_edge_action([1,2],[1,0,2])

    def test_oracle_separates_valid_and_invalid_task(self):
        from verify import validate_task_oracle, graph_edge_action
        inputs = [np.array([1,0,0]), np.array([0,1,0])]
        generators = [[1,0,2],[0,2,1]]
        valid = validate_task_oracle(inputs, lambda x: float(sum(x)),
                                    graph_edge_action,generators,3,provenance='heldout')
        self.assertTrue(valid['tested_label_invariance_pass'])
        self.assertFalse(valid['population_symmetry_proof'])
        invalid = validate_task_oracle(inputs,lambda x: float(x[0]),
                                      graph_edge_action,generators,3,provenance='exploratory')
        self.assertFalse(invalid['tested_label_invariance_pass'])
        self.assertTrue(invalid['adaptive_reuse_warning'])

    def test_invalid_pairs(self):
        from verify import validate_task_pairs
        with self.assertRaises(ValueError):
            validate_task_pairs([1],[[float('nan')]],provenance='heldout')
        with self.assertRaises(ValueError):
            validate_task_pairs([1],[[1]],provenance='unknown')
