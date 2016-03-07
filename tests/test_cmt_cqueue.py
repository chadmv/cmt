import unittest
import os
import sys
import maya.cmds as cmds
from cmt.test import TestCase
import cmt.cqueue.core as core


class Component(core.Component):
    def __init__(self, sphere_name, **kwargs):
        super(Component, self).__init__(**kwargs)
        self.sphere_name = sphere_name

    def execute(self):
        cmds.polySphere(name=self.sphere_name)

    def _data(self):
        return {
            'sphere_name': self.sphere_name
        }


class CQueueTests(TestCase):

    def test_get_components(self):
        components = core.get_components()
        self.assertIn('cmt.cqueue.components.file', components)

    def test_component_base_data(self):
        comp = core.Component()
        data = comp.data()
        expected = {
            'name': 'cmt.cqueue.core',
            'enabled': True,
            'break_point': False,
            'uuid': comp.uuid,
        }
        self.assertDictEqual(expected, data)

    def test_component_name_generated_from_module(self):
        comp = Component('sphere2')
        self.assertEqual('test_cmt_cqueue', comp.name())

    def test_add_component_to_queue(self):
        queue = core.ComponentQueue()
        comp = Component('sphere1')
        queue.add(comp)
        self.assertEqual(1, queue.length())
        self.assertEqual(0, queue.index(comp))

    def test_remove_component_by_index(self):
        queue = core.ComponentQueue()
        comp = Component('sphere1')
        queue.add(comp)
        removed_comp = queue.remove(0)
        self.assertEqual(0, queue.length())
        self.assertIs(comp, removed_comp)

    def test_remove_component_by_instance(self):
        queue = core.ComponentQueue()
        comp = Component('sphere1')
        queue.add(comp)
        removed_comp = queue.remove(comp)
        self.assertEqual(0, queue.length())
        self.assertIs(comp, removed_comp)

    def test_execute_queue(self):
        queue = core.ComponentQueue()
        comp = Component('sphere1')
        queue.add(comp)
        comp = Component('sphere2')
        queue.add(comp)
        queue.execute()
        self.assertTrue(cmds.objExists('sphere1'))
        self.assertTrue(cmds.objExists('sphere2'))

    def test_disable_component(self):
        queue = core.ComponentQueue()
        comp = Component('sphere1', enabled=False)
        queue.add(comp)
        comp = Component('sphere2')
        queue.add(comp)
        queue.execute()
        self.assertFalse(cmds.objExists('sphere1'))
        self.assertTrue(cmds.objExists('sphere2'))

    def test_component_break_point(self):
        queue = core.ComponentQueue()
        comp = Component('sphere1', break_point=True)
        queue.add(comp)
        comp = Component('sphere2')
        queue.add(comp)
        queue.execute()
        self.assertTrue(cmds.objExists('sphere1'))
        self.assertFalse(cmds.objExists('sphere2'))

    def test_queue_data(self):
        queue = core.ComponentQueue()
        comp1 = Component('sphere1')
        queue.add(comp1)
        comp2 = Component('sphere2')
        queue.add(comp2)
        data = queue.data()
        expected = [
            {
                'name': 'test_cmt_cqueue',
                'enabled': True,
                'break_point': False,
                'uuid': comp1.uuid,
                'sphere_name': 'sphere1',
            },
            {
                'name': 'test_cmt_cqueue',
                'enabled': True,
                'break_point': False,
                'uuid': comp2.uuid,
                'sphere_name': 'sphere2',
            }
        ]
        self.assertEqual(expected, data)

    def test_load_queue_from_data(self):
        queue = core.ComponentQueue()
        comp1 = Component('sphere1')
        queue.add(comp1)
        comp2 = Component('sphere2')
        queue.add(comp2)
        data = queue.data()
        queue = core.load_data(data)
        queue.execute()
        self.assertTrue(cmds.objExists('sphere1'))
        self.assertTrue(cmds.objExists('sphere2'))

    def test_export_queue(self):
        queue = core.ComponentQueue()
        comp1 = Component('sphere1')
        queue.add(comp1)
        comp2 = Component('sphere2')
        queue.add(comp2)
        file_path = self.get_temp_filename('queue.json')
        queue.export(file_path)
        queue = core.load_queue(file_path)
        queue.execute()
        self.assertTrue(cmds.objExists('sphere1'))
        self.assertTrue(cmds.objExists('sphere2'))


