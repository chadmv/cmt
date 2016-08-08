import os
import maya.cmds as cmds
from cmt.test import TestCase
import cmt.cqueue.core as core
import cmt.cqueue.fields as fields


class Component(core.Component):
    sphere_name = fields.CharField('sphere_name')
    radius = fields.FloatField('radius', default=1.0)

    def execute(self):
        cmds.polySphere(name=self.sphere_name.value(), radius=self.radius.value())


class ContainerComponent(core.Component):
    spheres = fields.ArrayField('spheres')
    container = fields.ContainerField('sphere', parent=spheres)
    sphere_name = fields.CharField('sphere_name', parent=container)
    radius = fields.FloatField('radius', default=1.0, parent=container)

    def execute(self):
        for sphere in self.spheres:
            name = sphere['sphere_name'].value()
            radius = sphere['radius'].value()
            cmds.polySphere(name=name, radius=radius)


class CComponentTests(TestCase):
    def test_get_component_fields(self):
        comp = Component()
        self.assertIsInstance(comp.sphere_name, fields.CharField)
        self.assertIsInstance(comp.radius, fields.FloatField)

    def test_component_data_is_initialized(self):
        comp = Component()
        data = comp.data()
        expected = {
            'component_name': 'test_cmt_cqueue',
            'enabled': True,
            'break_point': False,
            'sphere_name': '',
            'radius': 1.0,
            'uuid': comp.uuid,
        }
        self.assertDictEqual(expected, data)

    def test_component_name_generated_from_module(self):
        comp = Component()
        self.assertEqual('test_cmt_cqueue', comp.name())

    def test_component_execute(self):
        comp = Component()
        comp.set_data({
            'sphere_name': 'test',
            'radius': 5.5,
        })
        comp.execute()
        self.assertTrue(cmds.objExists('test'))
        self.assertEqual(5.5, cmds.getAttr('polySphere1.radius'))

    def test_component_set_data(self):
        comp = Component()
        comp.set_data({
            'sphere_name': 'test',
            'radius': 5.5,
        })
        data = comp.data()
        expected = {
            'component_name': 'test_cmt_cqueue',
            'enabled': True,
            'break_point': False,
            'sphere_name': 'test',
            'radius': 5.5,
            'uuid': comp.uuid,
        }
        self.assertDictEqual(expected, data)

    def test_component_data_set_data_forces_type(self):
        comp = Component()
        comp.set_data({
            'sphere_name': 'test',
            'radius': '5.5',
        })
        data = comp.data()
        expected = {
            'component_name': 'test_cmt_cqueue',
            'enabled': True,
            'break_point': False,
            'sphere_name': 'test',
            'radius': 5.5,
            'uuid': comp.uuid,
        }
        self.assertDictEqual(expected, data)

    def test_component_data_with_array_of_containers_is_correct(self):
        comp = ContainerComponent()
        data = comp.data()
        expected = {
            'component_name': 'test_cmt_cqueue',
            'enabled': True,
            'break_point': False,
            'uuid': comp.uuid,
            'spheres': [
                {'radius': 1.0, 'sphere_name': ''},
            ]
        }
        self.assertDictEqual(expected, data)

    def test_set_component_data_with_array_of_containers_is_correct(self):
        data = {
            'spheres': [
                {'sphere_name': 'sphere1', 'radius': 2.5},
                {'sphere_name': 'sphere2', 'radius': 5.0},
            ]
        }
        comp = ContainerComponent()
        comp.set_data(data)
        data = comp.data()
        expected = {
            'component_name': 'test_cmt_cqueue',
            'enabled': True,
            'break_point': False,
            'uuid': comp.uuid,
            'spheres': [
                {'sphere_name': 'sphere1', 'radius': 2.5},
                {'sphere_name': 'sphere2', 'radius': 5.0},
            ]
        }
        self.assertDictEqual(expected, data)

    def test_execute_component_with_array_of_containers(self):
        data = {
            'spheres': [
                {'sphere_name': 'sphere1', 'radius': 2.5},
                {'sphere_name': 'sphere2', 'radius': 5.0},
            ]
        }
        comp = ContainerComponent()
        comp.set_data(data)
        comp.execute()
        self.assertTrue(cmds.objExists('sphere1'))
        self.assertEqual(2.5, cmds.getAttr('polySphere1.radius'))
        self.assertTrue(cmds.objExists('sphere2'))
        self.assertEqual(5.0, cmds.getAttr('polySphere2.radius'))

    def test_instantiate_component_from_constructor(self):
        name = 'blah_blah'
        comp = Component(sphere_name=name, radius=10.0)
        self.assertFalse(cmds.objExists(name))
        comp.execute()
        self.assertTrue(cmds.objExists(name))
        self.assertEqual(10.0, cmds.getAttr('polySphere1.radius'))


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

    def test_add_component_to_queue(self):
        queue = core.ComponentQueue()
        comp = Component()
        queue.add(comp)
        self.assertEqual(1, queue.length())
        self.assertEqual(0, queue.index(comp))

    def test_remove_component_by_index(self):
        queue = core.ComponentQueue()
        comp = Component()
        queue.add(comp)
        removed_comp = queue.remove(0)
        self.assertEqual(0, queue.length())
        self.assertIs(comp, removed_comp)

    def test_remove_component_by_instance(self):
        queue = core.ComponentQueue()
        comp = Component()
        queue.add(comp)
        removed_comp = queue.remove(comp)
        self.assertEqual(0, queue.length())
        self.assertIs(comp, removed_comp)

    def test_execute_queue(self):
        queue = core.ComponentQueue()
        comp = Component(sphere_name='sphere1')
        queue.add(comp)
        comp = Component(sphere_name='sphere2')
        queue.add(comp)
        queue.execute()
        self.assertTrue(cmds.objExists('sphere1'))
        self.assertTrue(cmds.objExists('sphere2'))

    def test_disable_component(self):
        queue = core.ComponentQueue()
        comp = Component(sphere_name='sphere1', enabled=False)
        queue.add(comp)
        comp = Component(sphere_name='sphere2')
        queue.add(comp)
        queue.execute()
        self.assertFalse(cmds.objExists('sphere1'))
        self.assertTrue(cmds.objExists('sphere2'))

    def test_component_break_point(self):
        queue = core.ComponentQueue()
        comp = Component(sphere_name='sphere1', break_point=True)
        queue.add(comp)
        comp = Component(sphere_name='sphere2')
        queue.add(comp)
        queue.execute()
        self.assertTrue(cmds.objExists('sphere1'))
        self.assertFalse(cmds.objExists('sphere2'))

    def test_queue_data(self):
        queue = core.ComponentQueue()
        comp1 = Component(sphere_name='sphere1')
        queue.add(comp1)
        comp2 = Component(sphere_name='sphere2', radius=2.0)
        queue.add(comp2)
        data = queue.data()
        expected = [
            {
                'component_name': 'test_cmt_cqueue',
                'enabled': True,
                'break_point': False,
                'uuid': comp1.uuid,
                'sphere_name': 'sphere1',
                'radius': 1.0,
            },
            {
                'component_name': 'test_cmt_cqueue',
                'enabled': True,
                'break_point': False,
                'uuid': comp2.uuid,
                'sphere_name': 'sphere2',
                'radius': 2.0,
            }
        ]
        self.assertEqual(expected, data)

    def test_load_queue_from_data(self):
        queue = core.ComponentQueue()
        comp1 = Component(sphere_name='sphere1')
        queue.add(comp1)
        comp2 = Component(sphere_name='sphere2')
        queue.add(comp2)
        data = queue.data()
        queue = core.load_data(data)
        queue.execute()
        self.assertTrue(cmds.objExists('sphere1'))
        self.assertTrue(cmds.objExists('sphere2'))

    def test_export_queue(self):
        queue = core.ComponentQueue()
        comp1 = Component(sphere_name='sphere1')
        queue.add(comp1)
        comp2 = Component(sphere_name='sphere2')
        queue.add(comp2)
        file_path = self.get_temp_filename('queue.json')
        queue.export(file_path)
        queue = core.load_queue(file_path)
        queue.execute()
        self.assertTrue(cmds.objExists('sphere1'))
        self.assertTrue(cmds.objExists('sphere2'))

