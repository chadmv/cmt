import os
import maya.cmds as cmds
from cmt.test import TestCase
import cmt.cqueue.core as core
import cmt.cqueue.fields as fields


class Component(core.Component):
    def __init__(self, sphere_name='', **kwargs):
        super(Component, self).__init__(**kwargs)
        self.sphere_name = fields.CharField(name='sphere_name', value=sphere_name)
        self.add_field(self.sphere_name)

    def execute(self):
        cmds.polySphere(name=self.sphere_name.value())


class ContainerComponent(core.Component):
    def __init__(self, spheres=None, **kwargs):
        super(ContainerComponent, self).__init__(**kwargs)
        self.array_field = fields.ArrayField(name='spheres')
        self.add_field(self.array_field)
        if spheres is None:
            spheres = [{'sphere_name': 'sphere1'}]
        for sphere in spheres:
            container = fields.ContainerField(name='sphere', parent=self.array_field)
            fields.CharField(name='sphere_name', value=sphere['sphere_name'], parent=container)
            fields.FloatField(name='radius', value=sphere.get('radius', 1.0), parent=container)

    def execute(self):
        for sphere in self.array_field:
            name = sphere[0].value()
            radius = sphere[1].value()
            cmds.polySphere(name=name, radius=radius)


class CQueueTests(TestCase):

    def test_get_components(self):
        components = core.get_components()
        self.assertIn('cmt.cqueue.components.file', components)

    def test_extract_component_module_path(self):
        result = []
        result = core.extract_component_module_path('cmt.cqueue.components',
                                                    files=['__init__.py', 'skeleton.py', 'skeleton.pyc'],
                                                    full_path=os.path.join('cmt', 'cqueue', 'components'),
                                                    root=os.path.join('cmt', 'cqueue', 'components', 'rig'),
                                                    result=result)
        self.assertListEqual(['cmt.cqueue.components.rig.skeleton'], result)

    def test_component_base_data(self):
        comp = core.Component()
        data = comp.data()
        expected = {
            'component_name': 'cmt.cqueue.core',
            'enabled': True,
            'break_point': False,
            'uuid': comp.uuid,
        }
        self.assertDictEqual(expected, data)

    def test_component_data_with_array_of_containers_is_correct(self):
        spheres = [
            {'sphere_name': 'sphere1', 'radius': 2.5},
            {'sphere_name': 'sphere2', 'radius': 5.0},
        ]
        comp = ContainerComponent(spheres)
        data = comp.data()
        expected = {
            'component_name': 'test_cmt_cqueue',
            'enabled': True,
            'break_point': False,
            'uuid': comp.uuid,
            'spheres': [
                {'radius': 2.5, 'sphere_name': 'sphere1'},
                {'radius': 5.0, 'sphere_name': 'sphere2'},
            ]
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
                'component_name': 'test_cmt_cqueue',
                'enabled': True,
                'break_point': False,
                'uuid': comp1.uuid,
                'sphere_name': 'sphere1',
            },
            {
                'component_name': 'test_cmt_cqueue',
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

