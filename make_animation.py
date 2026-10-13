import bpy
import math
import os

bpy.ops.wm.read_factory_settings(use_empty=True)

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.fps = 30
scene.frame_start = 1
scene.frame_end = 120

frames_dir = r'<workspace>\Blender\frames'
os.makedirs(frames_dir, exist_ok=True)
scene.render.filepath = frames_dir + r'\frame_'

world = bpy.data.worlds.new('World')
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes['Background']
bg.inputs[0].default_value = (0.02, 0.03, 0.08, 1.0)
bg.inputs[1].default_value = 1.0

def get_fcurves(obj):
    ad = obj.animation_data
    if not ad or not ad.action:
        return []
    fcs = []
    for layer in ad.action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                fcs.extend(cb.fcurves)
    return fcs

def make_mat(name, color, metallic=0.0, roughness=0.3, emission=None, emission_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    if emission:
        bsdf.inputs['Emission Color'].default_value = (*emission, 1.0)
        bsdf.inputs['Emission Strength'].default_value = emission_strength
    return m

gold = make_mat('Gold', (1.0, 0.6, 0.1), metallic=1.0, roughness=0.15)
ground_mat = make_mat('Ground', (0.05, 0.05, 0.1), metallic=0.2, roughness=0.4)

bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
plane = bpy.context.object
plane.data.materials.append(ground_mat)

bpy.ops.mesh.primitive_monkey_add(size=2.5, location=(0, 0, 2.5))
suzanne = bpy.context.object
suzanne.data.materials.append(gold)
bpy.ops.object.shade_smooth()
subd = suzanne.modifiers.new('Subd', 'SUBSURF')
subd.levels = 2

suzanne.rotation_euler = (0, 0, 0)
suzanne.keyframe_insert('rotation_euler', frame=1)
suzanne.rotation_euler = (0, 0, math.radians(720))
suzanne.keyframe_insert('rotation_euler', frame=120)
suzanne.location.z = 2.5
suzanne.keyframe_insert('location', frame=1)
suzanne.location.z = 3.5
suzanne.keyframe_insert('location', frame=30)
suzanne.location.z = 2.5
suzanne.keyframe_insert('location', frame=60)
suzanne.location.z = 3.5
suzanne.keyframe_insert('location', frame=90)
suzanne.location.z = 2.5
suzanne.keyframe_insert('location', frame=120)
for fc in get_fcurves(suzanne):
    for kp in fc.keyframe_points:
        kp.interpolation = 'BEZIER'

orbit = bpy.data.objects.new('Orbit', None)
scene.collection.objects.link(orbit)
orbit.rotation_euler = (0, 0, 0)
orbit.keyframe_insert('rotation_euler', frame=1)
orbit.rotation_euler = (0, 0, math.radians(-360))
orbit.keyframe_insert('rotation_euler', frame=120)
for fc in get_fcurves(orbit):
    for kp in fc.keyframe_points:
        kp.interpolation = 'LINEAR'

colors = [
    ((0.9, 0.1, 0.2), (1.0, 0.2, 0.3)),
    ((0.1, 0.8, 0.3), (0.2, 1.0, 0.4)),
    ((0.1, 0.4, 1.0), (0.3, 0.6, 1.0)),
    ((1.0, 0.8, 0.1), (1.0, 0.9, 0.3)),
    ((0.8, 0.2, 1.0), (0.9, 0.4, 1.0)),
    ((0.1, 0.9, 0.9), (0.3, 1.0, 1.0)),
]
for i, (base, emit) in enumerate(colors):
    ang = i * math.tau / 6
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.5,
        location=(4.2 * math.cos(ang), 4.2 * math.sin(ang), 1.0))
    s = bpy.context.object
    s.data.materials.append(make_mat(f'Ball{i}', base, metallic=0.6, roughness=0.2,
        emission=emit, emission_strength=2.0))
    s.parent = orbit
    s.keyframe_insert('location', frame=1)
    s.location.z = 2.2
    s.keyframe_insert('location', frame=30 + i * 5)
    s.location.z = 1.0
    s.keyframe_insert('location', frame=60 + i * 5)
    fc = next(f for f in get_fcurves(s) if f.data_path == 'location' and f.array_index == 2)
    for kp in fc.keyframe_points:
        kp.interpolation = 'BEZIER'
    cyc = fc.modifiers.new('CYCLES')

bpy.ops.object.light_add(type='AREA', location=(5, -5, 8))
key = bpy.context.object
key.data.energy = 1500
key.data.shape = 'DISK'
key.data.size = 5
key.rotation_euler = (math.radians(30), 0, math.radians(45))

bpy.ops.object.light_add(type='AREA', location=(-6, 4, 5))
fill = bpy.context.object
fill.data.energy = 800
fill.data.color = (0.4, 0.6, 1.0)
fill.rotation_euler = (math.radians(60), 0, math.radians(-120))

bpy.ops.object.light_add(type='AREA', location=(0, 6, 3))
rim = bpy.context.object
rim.data.energy = 1000
rim.data.color = (1.0, 0.5, 0.2)
rim.rotation_euler = (math.radians(100), 0, math.radians(180))

bpy.ops.object.camera_add(location=(11, -11, 8))
cam = bpy.context.object
scene.camera = cam
target = bpy.data.objects.new('Target', None)
scene.collection.objects.link(target)
target.location = (0, 0, 2.0)
con = cam.constraints.new('TRACK_TO')
con.target = target
con.track_axis = 'TRACK_NEGATIVE_Z'
con.up_axis = 'UP_Y'

scene.frame_set(45)
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = r'<workspace>\Blender\preview.png'
bpy.ops.render.render(write_still=True)

scene.render.filepath = frames_dir + r'\frame_'
bpy.ops.render.render(animation=True)
print('DONE')
