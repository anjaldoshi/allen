#!/usr/bin/env python
"""This Script opens up the sepcified hdf5 files and loads its datasets"""

#pylint: disable=unused-wildcard-import
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from pyrr import matrix44, Vector3
import numpy as np
import random
import h5py
import sys
import argschema


#   Setting Up ArgScehma
class HDF5Schema(argschema.ArgSchema):
    """
    HDF5 Schema
    """
    dataset = argschema.fields.List(argschema.fields.String(), cli_as_single_argument=True)

class URISchema(argschema.ArgSchema):
    """
    URI Schema
    """
    uri = argschema.fields.InputFile()
    hdf5 = argschema.fields.Nested(HDF5Schema)

class TopSchema(argschema.ArgSchema):
    """
    Top Schema
    """
    video = argschema.fields.Nested(URISchema)
    segmentation = argschema.fields.Nested(URISchema)
    traces = argschema.fields.Nested(URISchema)


def compile_vertex_shader(source):
    """Compile a vertex shader from source."""
    vertex_shader = glCreateShader(GL_VERTEX_SHADER)
    glShaderSource(vertex_shader, source)
    glCompileShader(vertex_shader)
    result = glGetShaderiv(vertex_shader, GL_COMPILE_STATUS)
    if not(result):
        raise RuntimeError(glGetShaderInfoLog(vertex_shader))
    return vertex_shader

def compile_fragment_shader(source):
    """Compile a fragment shader from source."""
    fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
    glShaderSource(fragment_shader, source)
    glCompileShader(fragment_shader)
    result = glGetShaderiv(fragment_shader, GL_COMPILE_STATUS)
    if not(result):
        raise RuntimeError(glGetShaderInfoLog(fragment_shader))
    return fragment_shader


def link_shader_program(vertex_shader, fragment_shader):
    """Create a shader program with from compiled shaders."""
    program = glCreateProgram()
    glAttachShader(program, vertex_shader)
    glAttachShader(program, fragment_shader)
    glLinkProgram(program)
    # check linking error
    result = glGetProgramiv(program, GL_LINK_STATUS)
    if not(result):
        raise RuntimeError(glGetProgramInfoLog(program))
    return program

# Vertex Shader
VS = """
#version 330
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec2 aTexCoords;
layout (location = 2) in vec3 translate_mask;

uniform mat4 vp;

out vec2 TexCoords;

void main() {
    TexCoords = aTexCoords;

    gl_Position = vp * vec4(aPos + translate_mask, 1.0f);
}
"""

FS = """
#version 330

in vec2 TexCoords;
out vec4 color;
uniform sampler2D maskTexture;

void main() {
    color = texture(maskTexture, TexCoords);
}
"""

# Main Pipleine Starts here
class Session:
    """
    Creates sessions
    """
    def __init__(self, sw, sh):
        """
        Constructor to initialize variables
        """
        self.buffer_video_frame = []
        self.video_frame = []
        self.masks = []
        self.offset = []
        self.size = []
        self.traces = []
        self.textures = 0
        self.mask_textures = 0
        self.image_width = 0
        self.image_height = 0
        self.window_width = sw
        self.window_height = sh
        self.next_frame = False
        self.prev_frame = False
        self.forward = False
        self.reverse = False
        self.current_frame = 0
        self.mouse_x = 0
        self.mouse_y = 0
        self.hover = 0
        self.zoom_factor = 1.0
        self.pixel_data_type = GL_UNSIGNED_BYTE
        self.lmin = 0
        self.lmax = 0

    def load_hdf5(self):
        """
        Opens hdf5 files and loads its datasets
        """
        #Get input data from the json file or command line
        data = argschema.ArgSchemaParser(schema_type=TopSchema)
        input_args = data.args

        #Open 2P video hdf5 file and load its content
        video_file = h5py.File(input_args['video']['uri'], 'r')
        self.buffer_video_frame = video_file.get(input_args['video']['hdf5']['dataset'][0])

        #open segemenation file and load its datasets
        mask_file = h5py.File(input_args['segmentation']['uri'], 'r')
        self.masks = mask_file.get(input_args['segmentation']['hdf5']['dataset'][0])
        self.masks = self.masks[:, :, :]
        self.masks = self.masks.transpose(0, 2, 1)
        offset = mask_file.get(input_args['segmentation']['hdf5']['dataset'][1])
        self.offset_x = offset['x']
        self.offset_y = offset['y']
        size = mask_file.get(input_args['segmentation']['hdf5']['dataset'][2])
        self.size_x = size['x']
        self.size_y = size['y']
        mask_file.close()

        #Open ROI Trace hdf5 file and load its content
        trace_file = h5py.File(input_args['traces']['uri'], 'r')
        self.traces = trace_file.get(input_args['traces']['hdf5']['dataset'][0])
        trace_file.close()


    def intensity_normalization(self, image):
        return (np.clip((image - self.lmin) / (self.lmax - self.lmin), 0, 1)*255).astype(np.uint8)


    def init(self):
        """
        Clear screen color and initialize textures
        """

        glClearColor(0.0, 0.0, 0.0, 0.0)

        self.load_hdf5()

        rand_images = random.sample(range(len(self.buffer_video_frame)-1), 25)

        reference_image = []
        for image in rand_images:
            reference_image.append(self.buffer_video_frame[image, :, :])

        self.lmin = np.percentile(reference_image, 1)
        self.lmax = np.percentile(reference_image, 100)

        self.video_frame = self.buffer_video_frame[0, :, :]
        self.video_frame = self.video_frame.transpose(1, 0)
        self.video_frame = self.intensity_normalization(self.video_frame)

        self.image_width = len(self.video_frame[0])
        self.image_height = len(self.video_frame)

        self.textures = glGenTextures(2)

        glBindTexture(GL_TEXTURE_2D, self.textures[0])
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE, self.image_width, self.image_height, 0,
                     GL_LUMINANCE, self.pixel_data_type, self.video_frame)


        glBindTexture(GL_TEXTURE_2D, self.textures[1])
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE, self.image_width, self.image_height, 0, GL_LUMINANCE, self.pixel_data_type, self.video_frame)

        for data in range(len(self.masks)):
            self.offset.append((self.offset_x[data]*(self.window_width/(2*self.image_width)), self.offset_y[data]*(self.window_width/(2*self.image_width))))
            self.size.append((self.size_x[data]*(self.window_width/(2*self.image_width)), self.size_y[data]*(self.window_width/(2*self.image_width))))

        self.mask_textures = glGenTextures(len(self.masks))
        for num in range(len(self.masks)):
            glBindTexture(GL_TEXTURE_2D, self.mask_textures[num])
            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE, len(self.masks[num][0]), len(self.masks[num]), 0, GL_LUMINANCE, GL_UNSIGNED_BYTE, self.masks[num])

        vs = compile_vertex_shader(VS)
        fs = compile_fragment_shader(FS)
        self.shaders_program = link_shader_program(vs, fs)

        instance_array = []
        for num in range (len(self.masks)):
            translation = Vector3([0.0, 0.0, 0.0])
            translation.x = self.offset[num][0]
            translation.y = self.offset[num][1]
            # translation.x = float(num*0.5)
            # translation.y = float(num*0.5)
            instance_array.append(translation)

        instance_array = np.array(instance_array, np.float32).flatten()

        instance_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, instance_vbo)
        glBufferData(GL_ARRAY_BUFFER, instance_array.itemsize * len(instance_array), instance_array, GL_STATIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

        m_w = len(self.masks[0][0])*(self.window_width/(2*self.image_width))
        m_h = len(self.masks[0])*(self.window_width/(2*self.image_width))

        #                Positions    | Texture_Coords
        mask_vertices = [0.0, 0.0, 0.0, 0.0, 0.0,
                         0.0, m_h, 0.0, 0.0, 1.0,
                         m_w, m_h, 0.0, 1.0, 1.0,

                         0.0, 0.0, 0.0, 0.0, 0.0,
                         m_w, m_h, 0.0, 1.0, 1.0,
                         m_w, 0.0, 0.0, 1.0, 0.0]

        # mask_vertices = [-0.5, -0.5,  0.5, 0.0, 0.0,
        #                   0.5, -0.5,  0.5, 1.0, 0.0,
        #                   0.5,  0.5,  0.5, 1.0, 1.0,

        #                   0.5, -0.5,  0.5, 1.0, 0.0,
        #                  -0.5,  0.5,  0.5, 0.0, 1.0,
        #                  -0.5, -0.5,  0.5, 0.0, 0.0]


        mask_vertices = np.array(mask_vertices, dtype=np.float32)

        self.mask_vao = glGenVertexArrays(1)
        mask_vbo = glGenBuffers(1)
        glBindVertexArray(self.mask_vao)
        glBindBuffer(GL_ARRAY_BUFFER, mask_vbo)
        glBufferData(GL_ARRAY_BUFFER, mask_vertices.itemsize * len(mask_vertices), mask_vertices, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, mask_vertices.itemsize*5, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, mask_vertices.itemsize*5, ctypes.c_void_p(12))

        glEnableVertexAttribArray(2)
        glBindBuffer(GL_ARRAY_BUFFER, instance_vbo)
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glVertexAttribDivisor(2, 1)



    def draw_video(self):
        """
        Draw Texture and Map Video Frame to it
        """

        glViewport(int(self.window_width/2),
                   int(self.window_height-(self.window_width/2)*
                       (self.image_height/self.image_width)),
                   int(self.window_width/2), int((self.window_width/2)*
                                                 (self.image_height/self.image_width)))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, int(self.window_width/2),
                   int((self.window_width/2)*(self.image_height/self.image_width)), 0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glBindTexture(GL_TEXTURE_2D, self.textures[0])
        glEnable(GL_TEXTURE_2D)
        glPushMatrix()
        glClear(GL_DEPTH_BUFFER_BIT)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(0.0, (self.window_width/2)*(self.image_height/self.image_width), 0.0)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(self.window_width/2,
                   (self.window_width/2)*(self.image_height/self.image_width), 0.0)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(self.window_width/2, 0.0, 0.0)
        glEnd()
        glPopMatrix()
        glDisable(GL_TEXTURE_2D)
        glColor3ub(255, 255, 255)
        glRasterPos(20, 20)
        s = str(self.current_frame)
        for ch in s:
            glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))


    def draw_zoom_texture(self):
        """
        Draw Zoom texture and map the respective video frame
        """
        glViewport(int(self.window_width/4), int(self.window_height-self.window_width/4.8), int(self.window_width/5), int(self.window_width/5))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        #gluOrtho2D((MouseX - self.window_width/10)*zoomFactor, (MouseX + self.window_width/10)*zoomFactor, (MouseY + self.window_width/10)*zoomFactor, (MouseY - self.window_width/10)*zoomFactor)
        gluOrtho2D(0, int(self.window_width/5), int(self.window_width/5), 0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glBindTexture(GL_TEXTURE_2D, self.textures[1])
        glEnable(GL_TEXTURE_2D)
        glPushMatrix()
        glClear(GL_DEPTH_BUFFER_BIT)
        glTranslatef(((-self.mouse_x)*3+self.window_width/10)*self.hover, ((-self.mouse_y*(self.image_width/self.image_height))*3+self.window_width/10)*self.hover, 0)
        glScalef(self.zoom_factor, self.zoom_factor, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(0.0, self.window_width/5, 0.0)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(self.window_width/5, self.window_width/5, 0.0)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(self.window_width/5, 0.0, 0.0)
        glEnd()
        glDisable(GL_TEXTURE_2D)

        glColor3ub(255, 255, 255)
        glRasterPos2f(20, 20)
        s = "Hover to Zoom:"
        for ch in s:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))

        glPopMatrix()


    def draw_masks(self):
        glUseProgram(self.shaders_program)
        glViewport(int(self.window_width/2),
                   int(self.window_height-(self.window_width/2)*
                       (self.image_height/self.image_width)),
                   int(self.window_width/2), int((self.window_width/2)*
                                                 (self.image_height/self.image_width)))
        view = matrix44.create_from_translation(Vector3([0.0, 0.0, 0.0]))
        projection = matrix44.create_orthogonal_projection_matrix(0, self.window_width/2, (self.window_width/2)*(self.image_height/self.image_width), 0, -1, 1)
        vp = matrix44.multiply(view, projection)
        vp_loc = glGetUniformLocation(self.shaders_program, "vp")
        glUniformMatrix4fv(vp_loc, 1, GL_FALSE, vp)
        glBindTexture(GL_TEXTURE_2D, self.mask_textures[414])
        glBindVertexArray(self.mask_vao)
        glDrawArraysInstanced(GL_TRIANGLES, 0, 6, len(self.masks))
        glBindVertexArray(0)


    def update_video_frame(self):
        """
        Updates video with next or previous frame depending on the key pressed
        """
        if self.next_frame or self.forward:
            if self.current_frame < len(self.buffer_video_frame) - 1:
                self.current_frame += 1
            else:
                self.current_frame = 0
        elif self.prev_frame or self.reverse:
            if self.current_frame > 0:
                self.current_frame -= 1
            else:
                self.current_frame = len(self.buffer_video_frame) - 1

        self.prev_frame = self.next_frame = False

        self.video_frame = self.buffer_video_frame[self.current_frame, :, :]
        self.video_frame = self.video_frame.transpose(1, 0)
        self.video_frame = self.intensity_normalization(self.video_frame)

        glBindTexture(GL_TEXTURE_2D, self.textures[0])
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, self.image_width,
                        self.image_height, GL_LUMINANCE, self.pixel_data_type, self.video_frame)
        glBindTexture(GL_TEXTURE_2D, self.textures[1])
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, self.image_width,
                        self.image_height, GL_LUMINANCE, self.pixel_data_type, self.video_frame)

    def display(self):
        """
        Display everything to screen
        """
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # self.draw_video()
        self.draw_masks()
        # self.draw_zoom_texture()
        # self.update_video_frame()
        glutSwapBuffers()

    def Timer(self, value):
        glutPostRedisplay()
        glutTimerFunc(1, self.Timer, 0)


    def change_size(self, w, h):

        ratio = 1*w/h

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glViewport(0, 0, w, h)
        gluPerspective(45, ratio, 1, 1000)
        glMatrixMode(GL_MODELVIEW)
        self.window_height = h
        self.window_width = w


    def zoom_location(self, x, y):
        if x > int(self.window_width/2) and x <= self.window_width and y >= 0 and y < int((self.window_width/2)*(self.image_height/self.image_width)) and self.hover == 1:
            self.mouse_x = x - self.window_width/2
            self.mouse_y = y
            self.zoom_factor = 7.5
        else:
            self.zoom_factor = 1.0
            self.mouse_x = self.mouse_y = 0

        glutPostRedisplay()


    def key_listener(self, bkey, x, y):
        """
        Keyboard Listener
        """
        key = bkey.decode("utf-8")

        if key == chr(27):
            sys.exit()

        elif key == 'd' or key == 'D':
            self.next_frame = True
            self.update_video_frame()

        elif key == 'a' or key == 'A':
            self.prev_frame = True
            self.update_video_frame()

        elif key == 'z' or key == 'Z':
            if self.hover == 0:
                self.hover = 1
            else:
                self.hover = 0
        elif key == 'n' or key == 'N':
            image_ref = self.buffer_video_frame[self.current_frame, :, :]
            image_ref = image_ref.transpose(1, 0)
            self.lmin = np.percentile(image_ref, 1)
            self.lmax = np.percentile(image_ref, 100)
        elif key == ' ':
            self.forward = self.reverse = False
        elif key == 'b' or key =='B':
            self.current_frame = 0

        glutPostRedisplay()


    def special_keys(self, key, x, y):
        """
        Special Keys
        """
        if key == GLUT_KEY_RIGHT:
            self.forward = True
            self.reverse = False
        if key == GLUT_KEY_LEFT:
            self.forward = False
            self.reverse = True



def main():
    """
    Main File to set up opengl context
    """

    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH)
    s_w = glutGet(GLUT_SCREEN_WIDTH)
    s_h = glutGet(GLUT_SCREEN_HEIGHT)
    glutInitWindowSize(s_w, s_h)
    glutCreateWindow("2P Image Analysis")
    glutFullScreen()
    session1 = Session(s_w, s_h)
    glutKeyboardFunc(session1.key_listener)
    glutSpecialFunc(session1.special_keys)
    glutPassiveMotionFunc(session1.zoom_location)
    session1.init()
    glutDisplayFunc(session1.display)
    glutReshapeFunc(session1.change_size)
    session1.Timer(0)
    glutMainLoop()

if __name__ == '__main__':
    main()
