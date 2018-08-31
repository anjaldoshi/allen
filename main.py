#!/usr/bin/env python
"""This Script opens up the sepcified hdf5 files and loads its datasets"""

#pylint: disable=unused-wildcard-import
import sys
import random
import numpy as np
import h5py
import argschema
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

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
        self.mask_offset = []
        self.mask_size = []
        self.traces = []
        self.rand_rgb = []
        self.textures = 0
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
        self.stop_zoom = 0
        self.is_inside = 0
        self.zoom_factor = 1.0
        self.pixel_data_type = GL_UNSIGNED_BYTE
        self.lmin = 0
        self.lmax = 0
        self.hide_masks = False
        self.num_mask_selected = 0
        self.masks_selected = [0, 0]
        self.trace_start = 1
        self.trace_end = 1000
        self.hide_traces = False

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
        self.traces = self.traces[:, :]
        self.traces = np.asarray(self.traces, dtype=np.float16)
        self.trace_min = np.min(self.traces)
        self.trace_max = np.max(self.traces)
        trace_file.close()


    def intensity_normalization(self, image):
        return (np.clip((image - self.lmin) / (self.lmax - self.lmin), 0, 1)*255).astype(np.uint8)

    def calculate_mask_data(self):
        """
        Recalculate mask offset and size on the basis of image and window size
        """
        self.mask_offset.clear()
        self.mask_size.clear()
        for data in range(len(self.masks)):
            self.mask_offset.append((self.offset_x[data]*(self.window_width/(2*self.image_width)), self.offset_y[data]*(self.window_width/(2*self.image_width))))
            self.mask_size.append((self.size_x[data]*(self.window_width/(2*self.image_width)), self.size_y[data]*(self.window_width/(2*self.image_width))))

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
        #Generate texture for the video
        glBindTexture(GL_TEXTURE_2D, self.textures[0])
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE, self.image_width, self.image_height, 0,
                     GL_LUMINANCE, self.pixel_data_type, self.video_frame)

        #Generate texture for zoom window
        glBindTexture(GL_TEXTURE_2D, self.textures[1])
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE, self.image_width, self.image_height, 0, GL_LUMINANCE, self.pixel_data_type, self.video_frame)

        self.calculate_mask_data()

        # Generate textures for the segmentation masks
        self.mask_textures = glGenTextures(len(self.masks))
        for num in range(len(self.masks)):
            glBindTexture(GL_TEXTURE_2D, self.mask_textures[num])
            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE, len(self.masks[num][0]), len(self.masks[num]), 0, GL_LUMINANCE, GL_UNSIGNED_BYTE, self.masks[num])
            #Assign random RGB values for each mask
            r = random.uniform(0, 0.15)
            g = random.uniform(0, 0.15)
            b = random.uniform(0, 0.15)
            self.rand_rgb.append((r, g, b))

        #Generate Textures for selected masks
        self.mask_select_textures = glGenTextures(2)
        for i in range(2):
            glBindTexture(GL_TEXTURE_2D, self.mask_select_textures[i])
            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE, len(self.masks[i][0]), len(self.masks[i]), 0, GL_LUMINANCE, GL_UNSIGNED_BYTE, self.masks[i])


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
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))


    def draw_masks(self, mask_num):
        """
        Draw masks as overlay on top of the video frames
        """
        glBindTexture(GL_TEXTURE_2D, self.mask_textures[mask_num])
        glEnable(GL_TEXTURE_2D)
        glPushMatrix()
        glTranslatef(self.mask_offset[mask_num][0], self.mask_offset[mask_num][1], 0)
        glClear(GL_DEPTH_BUFFER_BIT)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(0.0, len(self.masks[mask_num])*(self.window_width/(2*self.image_width)), 0.0)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(len(self.masks[mask_num][0])*(self.window_width/(2*self.image_width)), len(self.masks[mask_num])*(self.window_width/(2*self.image_width)), 0.0)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(len(self.masks[mask_num][0])*(self.window_width/(2*self.image_width)), 0.0, 0.0)
        glEnd()
        glPopMatrix()
        glDisable(GL_TEXTURE_2D)

    def draw_zoom_texture(self):
        """
        Draw Zoom texture and map the respective video frame
        """
        glViewport(int(self.window_width/4), int(self.window_height-self.window_width/5), int(self.window_width/5), int(self.window_width/5))
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
        glTranslatef(((-self.mouse_x)*3+self.window_width/10)*self.is_inside, ((-self.mouse_y*(self.image_width/self.image_height))*3+self.window_width/10)*self.is_inside, 0)
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


    def display_selected_masks(self, num):
        mask_tex_height = int((int((self.window_width/2)*(self.image_height/self.image_width))-(self.window_width/5))/2)-15
        mask_tex_width = int(mask_tex_height*(len(self.masks[num][0])/len(self.masks[num])))

        glViewport(int(self.window_width/4), int(self.window_height-(self.window_width/4.8) - (mask_tex_height*(num+1))-(10*num)),  mask_tex_width, mask_tex_height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, mask_tex_width, mask_tex_height, 0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glBindTexture(GL_TEXTURE_2D, self.mask_select_textures[num])
        glEnable(GL_TEXTURE_2D)
        glPushMatrix()
        glClear(GL_DEPTH_BUFFER_BIT)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(0.0, mask_tex_height, 0.0)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(mask_tex_width, mask_tex_height, 0.0)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(mask_tex_width, 0.0, 0.0)
        glEnd()
        glDisable(GL_TEXTURE_2D)

        glBegin(GL_LINE_LOOP)
        glVertex2f(0.1, 0.1)
        glVertex2f(0.1, mask_tex_height-0.1)
        glVertex2f(mask_tex_width, mask_tex_height-0.1)
        glVertex2f(mask_tex_width, 0.1)
        glEnd()

        glPopMatrix()


    def display_mask_details(self, num):
        mask_tex_height = int((int((self.window_width/2)*(self.image_height/self.image_width))-(self.window_width/5))/2)-15
        glViewport(30, int(self.window_height-(self.window_width/4.8) - (mask_tex_height*(num+1))-(10*num)), int(self.window_width/4.5), mask_tex_height)
        glLoadIdentity()
        gluOrtho2D(0, int(self.window_width/4.5), mask_tex_height, 0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glBegin(GL_LINE_LOOP)
        glVertex2f(0.1, 0.1)
        glVertex2f(0.1, mask_tex_height-0.1)
        glVertex2f(self.window_width/9, mask_tex_height-0.1)
        glVertex2f(self.window_width/9, 0.1)
        glEnd()
        glRasterPos2f(20, 30)
        s1 = 'Feature selected: ' + str(self.masks_selected[num])
        for ch in s1:
            glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))

        glRasterPos2f(20, mask_tex_height/2)
        s1 = 'Location: ' + str(self.mask_offset[self.masks_selected[num]][0]) + ', ' + str(self.mask_offset[self.masks_selected[num]][1])
        for ch in s1:
            glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))

        glRasterPos2f(20, mask_tex_height/1.1)
        s1 = "Size: " + str(self.mask_size[self.masks_selected[num]][0]) + ', ' + str(self.mask_size[self.masks_selected[num]][1])
        for ch in s1:
            glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))


    def plot_traces(self, num):
        trace_tex_height = int((self.window_height-(self.window_width/2)*(self.image_height/self.image_width))/2)-30
        glColor3ub(255, 255, 255)
        glViewport(0, int(self.window_height-(self.window_width/2)*(self.image_height/self.image_width)-(trace_tex_height*(num+1)) -(15*(num+1))), self.window_width, trace_tex_height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, self.window_width, 0, trace_tex_height)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glBegin(GL_LINES)
        glVertex2f(0, 0.1)
        glVertex2f(self.window_width, 0.1)
        glVertex2f(0, trace_tex_height-0.1)
        glVertex2f(self.window_width, trace_tex_height-0.1)
        glEnd()
        glBegin(GL_LINES)
        glVertex2f(self.window_width/2, 0)
        glVertex2f(self.window_width/2, trace_tex_height)
        glEnd()
        glRasterPos2f(20, trace_tex_height-30)
        s1 = 'Trace for feature: ' + str(self.masks_selected[num])
        for ch in s1:
            glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))
        if self.current_frame < len(self.buffer_video_frame)-500 and self.current_frame >= 500:
            self.trace_start = self.current_frame - 500
            self.trace_end = self.current_frame + 500
        else:
            if self.current_frame < 500:
                self.trace_start = 1
                self.trace_end = 1000
            elif self.current_frame > len(self.buffer_video_frame)-500:
                self.trace_start = self.current_frame - 500
                self.trace_end = len(self.buffer_video_frame)
        glBegin(GL_LINES)
        for point in range(self.trace_start, self.trace_end):
            glVertex2f((self.window_width/2 - self.current_frame*2) + (point - 1) * 2, self.traces[self.masks_selected[num]][point-1]/(self.trace_max/trace_tex_height))
            glVertex2f((self.window_width/2 - self.current_frame*2) + point * 2, self.traces[self.masks_selected[num]][point]/(self.trace_max/trace_tex_height))
        glEnd()


    def show_state_details(self):
        glColor3ub(255, 255, 255)
        glViewport(30, int(self.window_height - self.window_width/5), int(self.window_width/5), int(self.window_width/5))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, int(self.window_width/5), int(self.window_width/5), 0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glBegin(GL_LINE_LOOP)
        glVertex2f(0.1, 0.1)
        glVertex2f(0.1, self.window_width/5-0.1)
        glVertex2f(self.window_width/5, self.window_width/5-0.1)
        glVertex2f(self.window_width/5, 0.1)
        glEnd()

        glBegin(GL_LINES)
        glVertex2f(0, (self.window_width/5)/2)
        glVertex2f(self.window_width/5, (self.window_width/5)/2)
        glEnd()

        glRasterPos2f(20, (self.window_width/5)/7)
        s1 = 'Allen Institute for Brain Science'
        for ch in s1:
            glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))

        glRasterPos2f(20, (self.window_width/5)/4)
        s1 = '2P Video Analysis'
        for ch in s1:
            glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))

        glRasterPos2f(20, (self.window_width/5)/2.75)
        s1 = "Created By:"
        for ch in s1:
            glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))

        glRasterPos2f(20, (self.window_width/5)/2.25)
        s1 = "John Galbraith & Anjal Doshi"
        for ch in s1:
            glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))

        glRasterPos2f(20, (self.window_width/5)/1.7)
        s1 = 'Video Autoplay: ' + ('Forward' if self.forward else 'Reverse' if self.reverse else 'Paused')
        for ch in s1:
            glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))

        glRasterPos2f(20, (self.window_width/5)/1.45)
        s1 = 'Zoom Freeze: ' + ('On' if self.stop_zoom == 1 else 'Off')
        for ch in s1:
            glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))

        glRasterPos2f(20, (self.window_width/5)/1.25)
        s1 = 'Hide Masks: ' + ('On' if self.hide_masks else 'Off')
        for ch in s1:
            glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))

        glRasterPos2f(20, (self.window_width/5)/1.125)
        s1 = 'Hide Traces: ' + ('On' if self.hide_traces else 'Off')
        for ch in s1:
            glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))


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
        glEnable(GL_BLEND)
        glBlendFunc(GL_ONE, GL_ZERO)
        self.draw_video()
        glBlendFunc(GL_CONSTANT_COLOR, GL_ONE)
        if not self.hide_masks:
            for num in range(len(self.masks)):
                glBlendColor(self.rand_rgb[num][0], self.rand_rgb[num][1], self.rand_rgb[num][2], 1)
                self.draw_masks(num)
        glDisable(GL_BLEND)
        self.draw_zoom_texture()
        for i in range(self.num_mask_selected):
            self.display_selected_masks(i)
            self.display_mask_details(i)
            if not self.hide_traces:
                self.plot_traces(i)
        self.show_state_details()
        self.update_video_frame()
        glutSwapBuffers()

    def timer(self, value):
        glutPostRedisplay()
        glutTimerFunc(1, self.timer, value)


    def change_size(self, w, h):

        ratio = 1*w/h

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glViewport(0, 0, w, h)
        gluPerspective(45, ratio, 1, 1000)
        glMatrixMode(GL_MODELVIEW)
        self.window_height = h
        self.window_width = w
        self.calculate_mask_data()


    def mouse_click_listener(self, button, state, x, y):
        if state == GLUT_DOWN and button == GLUT_LEFT_BUTTON:
            if x > int(self.window_width/2) and y < int(self.window_width/2*(self.image_height/self.image_width)):
                for i in range(len(self.mask_offset)):
                    if x < int(self.window_width/2 + self.mask_offset[i][0] + self.mask_size[i][0]) and x > int(self.window_width/2 + self.mask_offset[i][0]) and y < int(self.mask_offset[i][1] + self.mask_size[i][1]) and y > self.mask_offset[i][1]:
                        if self.num_mask_selected == 0:
                            self.masks_selected[self.num_mask_selected] = i
                            glBindTexture(GL_TEXTURE_2D, self.mask_select_textures[self.num_mask_selected])
                            glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, len(self.masks[i][0]), len(self.masks[i]), GL_LUMINANCE, GL_UNSIGNED_BYTE, self.masks[i])
                            self.num_mask_selected += 1
                        else:
                            self.num_mask_selected = 1
                            self.masks_selected[self.num_mask_selected] = i
                            glBindTexture(GL_TEXTURE_2D, self.mask_select_textures[self.num_mask_selected])
                            glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, len(self.masks[i][0]), len(self.masks[i]), GL_LUMINANCE, GL_UNSIGNED_BYTE, self.masks[i])
                            self.num_mask_selected += 1
                        break

        glutPostRedisplay()


    def zoom_location(self, x, y):
        if x > int(self.window_width/2) and x <= self.window_width and y >= 0 and y < int((self.window_width/2)*(self.image_height/self.image_width)) and self.stop_zoom == 0:
            self.mouse_x = x - self.window_width/2
            self.mouse_y = y
            self.zoom_factor = 7.5
            self.is_inside = 1
        elif self.stop_zoom == 1:
            pass
        else:
            self.zoom_factor = 1.0
            self.mouse_x = self.mouse_y = 0
            self.is_inside = 0

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
            if self.stop_zoom == 0:
                self.stop_zoom = 1
            else:
                self.stop_zoom = 0
        elif key == 'n' or key == 'N':
            image_ref = self.buffer_video_frame[self.current_frame, :, :]
            image_ref = image_ref.transpose(1, 0)
            self.lmin = np.percentile(image_ref, 1)
            self.lmax = np.percentile(image_ref, 100)
        elif key == ' ':
            self.forward = self.reverse = False
        elif key == 'b' or key == 'B':
            self.current_frame = 0
        elif key == 'h' or key == 'H':
            if self.hide_masks:
                self.hide_masks = False
            else:
                self.hide_masks = True
        elif key == 'c' or key == 'C':
            self.num_mask_selected = 0
            self.masks_selected = [0, 0]
        elif key == 't' or key == 'T':
            if self.hide_traces:
                self.hide_traces = False
            else:
                self.hide_traces = True

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
    glutMouseFunc(session1.mouse_click_listener)
    glutPassiveMotionFunc(session1.zoom_location)
    glutDisplayFunc(session1.display)
    glutReshapeFunc(session1.change_size)
    session1.init()
    session1.timer(0)
    glutMainLoop()

if __name__ == '__main__':
    main()
