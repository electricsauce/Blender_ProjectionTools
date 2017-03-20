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
import os                               #for texture file import
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
class ProToolsProjectionPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "ProTools"
    bl_label = "Projection Tools"
    
    def draw(self, context):
        layout = self.layout
        #wm = context.window_manager
        #scene = context.scene
        
        TheCol = self.layout.column(align=True)
        
        row = layout.row()
        
        #image preview - todo
        #TheCol.template_preview( bpy.data.textures["bpy.context.ProT_ImageTexturePath"])
        
        #find a way to cache this so that it only needs to stored when the texture is initially loaded
        TheCol.prop(context.scene,"ProT_ImageTexturePath")
        #Pix = TheCol.prop(context.scene,"ProT_ImageTexturePath")
        TheCol.prop(context.scene,"ProT_use_bch")
        
        TheCol.prop(context.scene,"ProT_use_noise_tex")
        if context.scene.ProT_use_noise_tex:
            TheCol.prop(context.scene,"ProT_NoiseTexturePath")
            TheCol.prop(context.scene,"ProT_noise_texture_scale")
            TheCol.prop(context.scene,"ProT_noise_texture_strength")
            TheCol.prop(context.scene,"ProT_use_X_noise")
            TheCol.prop(context.scene,"ProT_use_Y_noise")
            
        TheCol.operator("mesh.prot_paint_vertices", text="Paint Vertices")
        TheCol.prop(context.scene,"ProT_rotate_texture_90")
        TheCol.prop(context.scene,"ProT_texture_scale")
        TheCol.prop(context.scene,"ProT_Xnoise_scale")
        TheCol.prop(context.scene,"ProT_Ynoise_scale")
        
        TheCol.prop(context.scene,"ProT_CC_X")
        TheCol.prop(context.scene,"ProT_CC_Y")
        
        
    #end draw
    
class ProToolsDisplacementPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "ProTools"
    bl_label = "Displacement Tools"
    
    def draw(self, context):
        layout = self.layout
        
        TheCol = self.layout.column(align=True)
                
        TheCol.operator("mesh.prot_displace_vertices", text="Displace Vertices")
        TheCol.operator("mesh.prot_displace_vertices_method2", text="Displace Vertices_no copy")
        TheCol.prop(context.scene,"ProT_disp_scale")
    
#Allows us to use our panel in more than one context. Very helpful when applying
#vertex colors
contexts = ["objectmode", "vertexpaint"]

for c in contexts:
    propdic = {"bl_idname": "ProTools.%s" % c, "bl_context": c, }
    projectionToolsPanel = type("ProTools%s" % c, (ProToolsProjectionPanel,),propdic)

#simple linear interpolation
def lerp(num, min, max):
    return min + ((max - min) * num)

##############################################################################################
#Load image
##############################################################################################
def ProT_Update_Main_Texture(self, context):
    start = time.time()
    print ("Caching main texture")
    
    '''
    # Load image file. Change here if the snippet folder is 
    # not located in you home directory.
    realpath = context.scene.ProT_ImageTexturePath
    try:
        img = bpy.data.images.load(realpath)
    except:
        raise NameError("Cannot load image %s" % realpath)
        
    #store image data in a list since texture lookup is slowwwwww
    #http://blender.stackexchange.com/questions/3673/why-is-accessing-image-data-so-slow
    pix = np.array(img.pixels[:])
    '''
    end = time.time()
    print('Image Storage Time : ' + str(end - start))
    return None

def ProT_Update_Noise_Texture(self, context):
    start = time.time()
    print ("Caching noise texture")
    
    end = time.time()
    print('Image Storage Time : ' + str(end - start))
    return None


class ProT_PaintVertices(bpy.types.Operator):
    bl_idname = "mesh.prot_paint_vertices"
    bl_label = "Paint Vertices"
    bl_options = {"UNDO"}
    
    def invoke(self, context, event):
        start = time.time()
        
        # Load image file. 
        realpath = context.scene.ProT_ImageTexturePath
        try:
            img = bpy.data.images.load(realpath)
        except:
            raise NameError("Cannot load image %s" % realpath)
            
        #store image data in a list since texture lookup is slowwwwww
        #http://blender.stackexchange.com/questions/3673/why-is-accessing-image-data-so-slow
        pix = np.array(img.pixels[:])
                
        if context.scene.ProT_use_noise_tex:
            realpath2 = context.scene.ProT_NoiseTexturePath
            try:
                img2 = bpy.data.images.load(realpath2)
            except:
                raise NameError("Cannot load image %s" % realpath2)
            
            #store image data in a list since texture lookup is slowwwwww
            #http://blender.stackexchange.com/questions/3673/why-is-accessing-image-data-so-slow
            noisepix = img2.pixels[:]
            
        
        #Rotate image via a numpy array
        #reshape to a 3D array and rotate
        #then reduce back to a 1D array for further use
        if context.scene.ProT_rotate_texture_90 == True:
            print("TODO!!!!, reorder values in pix list so that input image is effectively rotated")
        
            pix = np.reshape((pix), ( 2048, 2048, 4))     
            pix = np.rot90(pix)
            pix = np.ravel(pix)
        
        
        end = time.time()
        print('Image Storage Time : ' + str(end - start))
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
        
        CCX = context.scene.ProT_CC_X
        CCY = context.scene.ProT_CC_Y
        
        start = time.time()
        
        '''
        //Get input direction
			float3 projDir_x = float3(sin(_ProjDirX), cos(_ProjDirX), 0.0f);
			float3 projDir_y = float3(0.0f, sin(_ProjDirY), cos(_ProjDirY));

			//create third othogonal vector
			float3 tov_0 = projDir_x;
			float3 tov_1 = cross(projDir_y, projDir_x);
			float3 tov_2 = cross(projDir_x, tov_1);

			//InverseTransformMatrix
			float it0 = dot(IN.coords, tov_0);
			float it1 = dot(IN.coords, tov_2);
			float it2 = dot(IN.coords, tov_1);
			
			float4 WorldPos = float4(it0, it1, it2, 0.0);
			half2 workingPos = WorldPos.xy;

			workingPos.x = workingPos.x + _CircleCenterX;
			workingPos.y = workingPos.y + _CircleCenterY;

			float2 tempPos = float2((workingPos.x + workingPos.y) / 2, WorldPos.z);

			workingPos.x = pow(abs(workingPos.x), lerp(_XNoiseStrength, (_XNoiseStrength * (tex2D(_NoiseMap, tempPos) * _NoiseMapStrength)), _UseXNoiseMap));
			workingPos.y = pow(abs(workingPos.y), lerp(_YNoiseStrength, (_YNoiseStrength * (tex2D(_NoiseMap, tempPos) * _NoiseMapStrength)), _UseYNoiseMap));

			workingPos.y = (workingPos.x + workingPos.y) / 2;
			workingPos.x = WorldPos.z;

			workingPos *= _TexScale;

			fixed4 c = tex2D(_MainTex, workingPos);

			o.Albedo = c.rgb *_Color;


			half3 tempNormal = UnpackNormal(tex2D(_BumpMap, workingPos));
			tempNormal.z = tempNormal.z / _NormalStrength;
			o.Normal = tempNormal;


			// Metallic comes from slider variables
			o.Metallic = _Metallic;
			o.Smoothness = c.w * _Glossiness;
			o.Alpha = c.a;
            '''
        
        for poly in polygons:
                for loop_index in poly.loop_indices:
                    loop_vert_index = mesh.loops[loop_index].vertex_index

                    color = [1 , 1, 0]
                    
                    #get vertex global/local positions
                    #http://blender.stackexchange.com/questions/1311/how-can-i-get-vertex-positions-from-a-mesh
                    vPos = verts[loop_vert_index].co
                    
                    #if you want to bake position information to the mesh
                    #color = vPos
                    
                    
                    workingPosX = vPos.x + CCX
                    workingPosY = vPos.y + CCY
                    
                    channelOffset = 0       #since we're working with black and white
                    
                    tempX = (workingPosX + workingPosY) / 2
                    tempY = vPos.z
                    
                    tempX = tempX * context.scene.ProT_noise_texture_scale
                    tempY = tempY * context.scene.ProT_noise_texture_scale
                    
                    tempX = tempX % imageWidth
                    tempY = tempY % imageWidth
                    
                    if context.scene.ProT_use_noise_tex:
                        noise = noisepix[ 4 * ((int(tempX) + imageWidth * int(tempY))) + channelOffset]
                        noise *= context.scene.ProT_noise_texture_strength
                    
                    else:
                        noise = 1
                    
                    #Edge case, raising 0 to a negative exponent causes error
                    #modify the perceived values of the vector coordinates by the noise map values
                    if workingPosX != 0:
                        if context.scene.ProT_use_X_noise:
                            workingPosX = (abs(workingPosX) ** (XNoiseStrength * noise))
                        else:
                            workingPosX = (abs(workingPosX) ** XNoiseStrength)
                    if workingPosY != 0:
                        if context.scene.ProT_use_X_noise:
                            workingPosY = (abs(workingPosY) ** (YNoiseStrength * noise))
                        else:
                            workingPosY = (abs(workingPosY) ** YNoiseStrength)
                    
                    workingPosY = (workingPosX + workingPosY) / 2
                    workingPosX = vPos.z
                    workingPosX *= scale
                    workingPosY *= scale
                    
                    #cast to integers so they can be used for list indices
                    workingPosX = int(workingPosX % imageWidth)
                    workingPosY = int(workingPosY % imageWidth)
                    
                    
                    #!!!!!Multiply the pixel color read from the texture by a masking value(possible on the blue channel)
                    #invert this value so if there is no blue value, blue will == 1 and give the full texture
                    #read value, otherwise it will interpolate between the masked value
                    
                    #get color information from imported image
                    #https://blenderartists.org/forum/showthread.php?195230-im-getpixel()-or-equivalent-in-Blender-2-5
                    #Where ypos/xpos are measured from the bottom left of the image to the top right.
                    #The channel offsets are as follows

                        #R = 0
                        #G = 1
                        #B = 2
                        #A = 3
                        
                    pixPos = 4 * ((workingPosX + imageWidth * workingPosY)) + channelOffset
                    storedColor = vcol_layer.data[loop_index].color
                    
                    if context.scene.ProT_use_bch:                        
                        mask = 1 - lerp(storedColor.b, 0.0, 1.0)
                    
                    else:
                        mask = 1
                    
                    col = pix[pixPos] * mask
                    color = [col * mask, storedColor.g, storedColor.b]
                    vcol_layer.data[loop_index].color = color

                    #print("painting vert",loop_index, "to color ", color[0], color[1], color[2])

        mesh.update()
        end = time.time()
        print('Vertex Painting Time : ' + str(end - start))
                
        bpy.ops.object.mode_set(mode='VERTEX_PAINT')
        return{"FINISHED"}
    
    
#create a copy of the mesh and displace the vertices    

class ProT_DisplaceVertices(bpy.types.Operator):
    bl_idname = "mesh.prot_displace_vertices"
    bl_label = "Paint Vertices"
    bl_options = {"UNDO"}
    
    def invoke(self, context, event):
        
        start = time.time()

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
        
        bpy.ops.object.mode_set(mode='EDIT')
        
        #modify the mesh
        for i, vert in enumerate (bm.verts):
            vertOffset = vert.normal * offset * vcol_averages[i].r

            #vert.co = vert.co + vertOffset
            vert.co += vertOffset 
        
        bpy.ops.object.mode_set(mode='OBJECT')
            
        # Finish up, write the bmesh back to the mesh
        bm.to_mesh(mesh)
        
        end = time.time()
        print('Dispalcement Time : ' + str(end - start))
        
        return{"FINISHED"}
    
#Displace the mesh by using bmesh to move the verts in the orignal mesh without making a copy
#will cause a crash if the bmesh is tesselated or the number of verts is changed
#http://blender.stackexchange.com/questions/35278/cant-write-bmesh-object-back-to-mesh-datablock

class ProT_DisplaceVertices_method2(bpy.types.Operator):
    bl_idname = "mesh.prot_displace_vertices_method2"
    bl_label = "Paint Vertices"
    bl_options = {"UNDO"}
    
    def invoke(self, context, event):
        
        start = time.time()

        offset = context.scene.ProT_disp_scale

        #Get a reference to our working mesh
        current_obj = bpy.context.active_object 
        mesh = current_obj.data
                 
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
        
        bpy.ops.object.mode_set(mode='EDIT')
        # Get a BMesh representation of the active mesh
        bm = bmesh.from_edit_mesh(mesh)   # create a bmesh copy
        
        #modify the mesh
        for i, vert in enumerate (bm.verts):
            vertOffset = vert.normal * offset * vcol_averages[i].r

            #vert.co = vert.co + vertOffset
            vert.co += vertOffset 
                    
        # Update mesh, so we see the changes.
        bmesh.update_edit_mesh(mesh, False, False)
        bpy.ops.object.mode_set(mode='OBJECT')

        # Because we did not add or remove geometry,
        # tessface=False and destructive=False can be used.
        # DO NOT DO THIS IF YOU CHANGED GEOMETRY!
        # Blender will crash otherwise.
        
        end = time.time()
        print('Dispalcement Time : ' + str(end - start))
        
        return{"FINISHED"}
    
    
#call the register class upon initialization to simplify installation as an addon
#and to create scene variable which classes can reference
def register():
    bpy.utils.register_class(ProToolsProjectionPanel)
    bpy.utils.register_class(ProToolsDisplacementPanel)
    bpy.utils.register_class(ProT_PaintVertices)
    bpy.utils.register_class(ProT_DisplaceVertices)
    bpy.utils.register_class(ProT_DisplaceVertices_method2)
    
    #bpy.utils.register_class(ProT_Test)
    
    bpy.types.Scene.ProT_ImageTexturePath = bpy.props.StringProperty(name="Browse Image:",
        #attr="main_image_path",# this a variable that will set or get from the scene
        description="Main image texture file path",
        maxlen= 1024,
        subtype='FILE_PATH',
        default= "",
        update = ProT_Update_Main_Texture)
        
    bpy.types.Scene.ProT_NoiseTexturePath = bpy.props.StringProperty(name="Browse Image:",
        #attr="noise_image_path",# this a variable that will set or get from the scene
        description="Noise texture file path",
        maxlen= 1024,
        subtype='FILE_PATH',
        default= "",
        update = ProT_Update_Noise_Texture)
 
    bpy.types.Scene.ProT_use_bch = bpy.props.BoolProperty \
        (
        name = "Use blue channel masking",
        description = "Use blue channel vertex color information for masking",
        default = False
        )
    
    bpy.types.Scene.ProT_use_noise_tex = bpy.props.BoolProperty \
        (
        name = "Use noise texture",
        description = "Multiplies the noise strength by a noise texture. 1 otherwise.",
        default = False
        )
        
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

    bpy.types.Scene.ProT_noise_texture_scale = bpy.props.FloatProperty \
        (
        name = "noise texture scale",
        description = "Controls the scale of the noise texture",
        default = 1.0
        )
        
    bpy.types.Scene.ProT_noise_texture_strength = bpy.props.FloatProperty \
        (
        name = "noise texture strength",
        description = "Controls the strength of the noise texture",
        default = 1.0
        )
   
    bpy.types.Scene.ProT_Xnoise_scale = bpy.props.FloatProperty \
        (
        name = "X noise strength",
        description = "Controls the strength of noise influence in the X axis",
        default = 2.0
        )

    bpy.types.Scene.ProT_use_X_noise = bpy.props.BoolProperty \
        (
        name = "Use X Noise",
        description = "Use texture to deform on X axis",
        default = True
        )
        
    bpy.types.Scene.ProT_use_Y_noise = bpy.props.BoolProperty \
        (
        name = "Use Y Noise",
        description = "Use texture to deform on Y axis",
        default = False
        )
                
    bpy.types.Scene.ProT_Ynoise_scale = bpy.props.FloatProperty \
        (
        name = "Y noise strength",
        description = "Controls the strength of noise influence in the Y axis",
        default = 2.0
        )
        
    bpy.types.Scene.ProT_disp_scale = bpy.props.FloatProperty \
        (
        name = "Displacement amount",
        description = "Controls the amount that the mesh is displaced",
        default = 0.01
        )
        
    bpy.types.Scene.ProT_CC_X = bpy.props.FloatProperty \
        (
        name = "Circle Center X axis",
        description = "Controls the location of the circle center on the X axis",
        default = 0.0
        )
        
    bpy.types.Scene.ProT_CC_Y = bpy.props.FloatProperty \
        (
        name = "Circle Center Y axis",
        description = "Controls the location of the circle center on the Y axis",
        default = 0.0
        )
        
        
        
    
    
def unregister():
    bpy.utils.unregister_class(ProToolsProjectionPanel)
    bpy.utils.unregister_class(ProToolsDisplacementPanel)
    bpy.utils.unregister_class(ProT_PaintVertices)
    bpy.utils.unregister_class(ProT_DisplaceVertices)
    bpy.utils.unregister_class(ProT_DisplaceVertices_method2)
    
    del bpy.types.Scene.ProT_ImageTexturePath
    del bpy.Types.Scene.ProT_NoiseTexturePath
    del bpy.types.Scene.ProT_rotate_texture_90
    del bpy.types.Scene.ProT_use_bch
    
    del bpy.types.ProT_texture_scale
    del bpy.types.ProT_noise_texture_scale
    del bpy.types.ProT_noise_texture_strength
    del bpy.types.ProT_Xnoise_scale
    del bpy.types.ProT_use_X_noise
    del bpy.types.ProT_Ynoise_scale
    del bpy.types.ProT_use_Y_noise
    del bpy.types.ProT_disp_scale
    del bpy.types.ProT_CC_X
    del bpy.types.ProT_CC_Y
    
    
    
#boilerplate which will invoke our registration routine in the situations (like the Text Editor) where Blender doesn't do it for us:
if __name__ == "__main__":
    register()
    
    
    
##############################################################################################
#Notes
##############################################################################################
'''
Image preview icons 
http://blender.stackexchange.com/questions/32335/how-to-implement-custom-icons-for-my-script-addon




Use X, Y noise boolean
'''