bl_info = \
    {
        "name" : "Projection Tools",
        "author" : "Steve Peters",
        "version" : (1, 0, 0),
        "blender" : (2, 7, 8),
        "location" : "View 3D > Edit Mode > Tool Shelf",
        "description" :
            "Projection tools allows for deformation of a mesh via a projected texture \
            It does this by first assigning vertex colors, and then deforms the mesh based \
            on the vertex normal and the assigned vertex color",
        "warning" : "",
        "wiki_url" : "",
        "tracker_url" : "",
        "category" : "Pro Tools",
    }


'''
Steve Peters
CC3 - Attribution required
3/9/2017
'''


import bpy
import os       #for texture file import
import bmesh

#math stuff
import math
import numpy as np

from collections import defaultdict      #to store vertex colors in a dictionary
from mathutils import Color              #To perform math operations on color objects

import time                              #For timing our functions to improve performance

##############################################################################################
#Create GUI panel
#multi-panel - http://blender.stackexchange.com/questions/41933/bl-context-multiple-areas
##############################################################################################
class ProjectionToolsPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    #bl_context = "objectmode"
    bl_category = "ProTools"
    bl_label = "Projection Tools"

    def draw(self, context):
        scene = context.scene
        
        TheCol = self.layout.column(align=True)
        TheCol.operator("mesh.prot_paint_vertices", text="Paint Vertices")
        TheCol.operator("mesh.prot_displace_vertices", text="Displace Vertices")
        TheCol.prop(context.scene, "ProT_rotate_texture_90")
        TheCol.prop(context.scene,"ProT_texture_scale")
        TheCol.prop(context.scene,"ProT_disp_scale")
        TheCol.prop(context.scene,"ProT_Xnoise_scale")
        TheCol.prop(context.scene,"ProT_Ynoise_scale")
        
        
    #end draw
contexts = ["objectmode", "vertexpaint"]

for c in contexts:
    propdic = {"bl_idname": "ProTools.%s" % c, "bl_context": c, }
    projectionToolsPanel = type("ProTools%s" % c, (ProjectionToolsPanel,),propdic)


##############################################################################################
#Load image
##############################################################################################
class ProT_PaintVertices(bpy.types.Operator):
    bl_idname = "mesh.prot_paint_vertices"
    bl_label = "Paint Vertices"
    bl_options = {"UNDO"}
    
    def invoke(self, context, event):
        # Load image file. Change here if the snippet folder is 
        # not located in you home directory.
        realpath = os.path.expanduser('~/Documents/Blender/ProjectionTools/WoodBase.png')
        try:
            img = bpy.data.images.load(realpath)
        except:
            raise NameError("Cannot load image %s" % realpath)
            
        #store image data in a list since texture lookup is slowwwwww
        #http://blender.stackexchange.com/questions/3673/why-is-accessing-image-data-so-slow
        pix = img.pixels[:]
        
        realpath2 = os.path.expanduser('~/Documents/Blender/ProjectionTools/noise.png')
        try:
            img2 = bpy.data.images.load(realpath2)
        except:
            raise NameError("Cannot load image %s" % realpath2)
            
        #store image data in a list since texture lookup is slowwwwww
        #http://blender.stackexchange.com/questions/3673/why-is-accessing-image-data-so-slow
        noisepix = img2.pixels[:]
        
        if context.scene.ProT_rotate_texture_90 == True:
            print("TODO!!!!, reorder values in pix list so that input image is effectively rotated")
        

        ##############################################################################################
        #http://blender.stackexchange.com/questions/32584/set-vertex-normals-to-vertex-color-in-python
        ##############################################################################################

        bpy.ops.object.mode_set(mode='OBJECT')
        # vertex colour data
        current_obj = bpy.context.active_object 
        mesh = current_obj.data

        if mesh.vertex_colors:
            vcol_layer = mesh.vertex_colors.active
        else:
            vcol_layer = mesh.vertex_colors.new()

        print("*"*40)

        polygons = np.array(mesh.polygons)
        verts = np.array(mesh.vertices)
        imageWidth = int(2048)

        scale = context.scene.ProT_texture_scale
        
        XNoiseStrength = context.scene.ProT_Xnoise_scale
        YNoiseStrength = context.scene.ProT_Ynoise_scale
        
        start = time.time()
        for poly in polygons:
                for loop_index in poly.loop_indices:
                    loop_vert_index = mesh.loops[loop_index].vertex_index

                    color = [1 , 1, 0]

                    #vcol_layer.data[loop_index].color = color
                    
                    #vcol_layer.data[loop_index].color = mesh.vertices[loop_vert_index].normal
                    #color = mesh.vertices[loop_vert_index].normal
                    
                    #get vertex global/local positions
                    #http://blender.stackexchange.com/questions/1311/how-can-i-get-vertex-positions-from-a-mesh
                    vPos = verts[loop_vert_index].co
                    #color = vPos
                    
                    #get color information from imported image
                    #https://blenderartists.org/forum/showthread.php?195230-im-getpixel()-or-equivalent-in-Blender-2-5
                    #Where ypos/xpos are measured from the bottom left of the image to the top right.
                    #The channel offsets are as follows

                        #R = 0
                        #G = 1
                        #B = 2
                        #A = 3
                        
                    #bpy.data.images['efeu1.png'].pixels[4 * (xpos + imageWidth * ypos) + channelOffset]
                    
                    workingPosX = vPos.x
                    workingPosY = vPos.y
                    
                    channelOffset = 0       #since we're working with black and white
                    noise = 1#noisepix[ 4 * ((int(workingPosX) + imageWidth * int(workingPosY))) + channelOffset]
                    
                    workingPosX = math.pow(abs(workingPosX), (XNoiseStrength * noise))
                    workingPosY = math.pow(abs(workingPosY), (YNoiseStrength * noise))
                    
                    workingPosY = (math.pow(workingPosX, 2) + math.pow(workingPosY, 2)) / 2
                    workingPosX = vPos.z
                    workingPosX *= scale
                    workingPosY *= scale
                    
                    #cast to integers so they can be used for list indices
                    workingPosX = int(workingPosX)
                    workingPosY = int(workingPosY)
                    
                    #xpos = int((math.sqrt(vPos.x**2 * scale + vPos.y**2* scale)) % imageWidth)
                    #ypos = int(vPos.z * scale)
                    
                    
                    #pixPos = 4 * ((xpos + imageWidth * ypos) % imageWidth) + channelOffset
                    
                    #!!!!!Multiply the pixel color read from the texture by a masking value(possible on the blue channel)
                    #invert this value so if there is no blue value, blue will == 1 and give the full texture
                    #read value, otherwise it will interpolate between the masked value
                    pixPos = 4 * ((workingPosX + imageWidth * workingPosY)) + channelOffset
                    
                    col = pix[pixPos]
                    color = [col, col, col]
                    
                    vcol_layer.data[loop_index].color = color

                    #print("painting vert",loop_index, "to color ", color[0], color[1], color[2])


        end = time.time()
        print('Vertex Painting Time : ' + str(end - start))
        mesh.update()
        
        bpy.ops.object.mode_set(mode='VERTEX_PAINT')
        return{"FINISHED"}
    
    
    

class ProT_DisplaceVertices(bpy.types.Operator):
    bl_idname = "mesh.prot_displace_vertices"
    bl_label = "Paint Vertices"
    bl_options = {"UNDO"}
    
    def invoke(self, context, event):
        
        

        offset = context.scene.ProT_disp_scale

        #Get a reference to our working mesh
        current_obj = bpy.context.active_object 
        mesh = current_obj.data
              
        # Get a BMesh representation of the active mesh
        bm = bmesh.new()   # create an empty BMesh
        bm.from_mesh(mesh)   # fill it in from a Mesh
         
        if mesh.vertex_colors:
            vcol_layer = mesh.vertex_colors.active
        else:
            vcol_layer = mesh.vertex_colors.new()

        mesh.vertex_colors.active = vcol_layer
        
        ##############################################################################################
        #Store our average vertex colors in a dictionary
        #Get all relevant colors for each vertex and average them
        #http://blender.stackexchange.com/questions/2162/select-vertex-if-vertex-color-is-dark
        ##############################################################################################

        tk = defaultdict(list)

        color_layer = mesh.vertex_colors['Col']
        
        i = 0
        for poly in mesh.polygons:
            for idx in poly.loop_indices:
                loop = mesh.loops[idx]
                color = color_layer.data[i].color
                tk[loop.vertex_index].append(color)
                i += 1
        
        #function to average a list of colors for a single vertex
        def avg_col(cols):
            avg_col = Color((0.0, 0.0, 0.0))
            #avg_col = [0.0, 0.0, 0.0]
            for col in cols:
                avg_col += col/len(cols)
            return avg_col

        vcol_averages = {k: avg_col(v) for k, v in tk.items()}
        

        print('Displacement Time!! - switch to edit mode')
        bpy.ops.object.mode_set(mode='EDIT')
        
        #modify the mesh
        for i, vert in enumerate (bm.verts):
            vertOffset = vert.normal * offset * vcol_averages[i].r

            #vert.co = vert.co + vertOffset
            vert.co += vertOffset 
        
        bpy.ops.object.mode_set(mode='OBJECT')
            
        # Finish up, write the bmesh back to the mesh
        bm.to_mesh(mesh)
        
        return{"FINISHED"}
        
#call the register class upon initialization to simplify installation as an addon
#and to create scene variable which classes can reference
def register():
    bpy.utils.register_class(ProjectionToolsPanel)
    bpy.utils.register_class(ProT_PaintVertices)
    bpy.utils.register_class(ProT_DisplaceVertices)
    
    bpy.types.Scene.ProT_rotate_texture_90 = bpy.props.BoolProperty \
        (
        name = "Rotate Texture 90 Degrees",
        description = "Rotates the input texture by 90 degrees",
        default = False
        )

    bpy.types.Scene.ProT_texture_scale = bpy.props.FloatProperty \
        (
        name = "Scale of applied texture",
        description = "Controls the scale of the texture applied to the mesh",
        default = 1000.0
        )
        
    bpy.types.Scene.ProT_Xnoise_scale = bpy.props.FloatProperty \
        (
        name = "X noise strength",
        description = "Controls the strength of noise influence in the X axis",
        default = 1.0
        )
        
    bpy.types.Scene.ProT_Ynoise_scale = bpy.props.FloatProperty \
        (
        name = "Y noise strength",
        description = "Controls the strength of noise influence in the Y axis",
        default = 1.0
        )
        
    bpy.types.Scene.ProT_disp_scale = bpy.props.FloatProperty \
        (
        name = "Displacement amount",
        description = "Controls the amount that the mesh is displaced",
        default = 0.005
        )
        
    
    
def unregister():
    bpy.utils.unregister_class(ProjectionToolsPanel)
    bpy.utils.unregister_class(ProT_PaintVertices)
    bpy.utils.unregister_class(ProT_DisplaceVertices)
    
    del bpy.types.Scene.ProT_rotate_texture_90
    del bpy.types.ProT_texture_scale
    del bpy.types.ProT_disp_scale
    
    
#boilerplate which will invoke our registration routine in the situations (like the Text Editor) where Blender doesn't do it for us:
if __name__ == "__main__":
    register()