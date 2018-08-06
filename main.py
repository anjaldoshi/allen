from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import sys, numpy, json, h5py, h5py_cache, random
from PIL import Image

totalImages = 999
sw = sh = width = height = textures = maskTextures = maskZoom = currImage = iNext = iPrev = zoom1 = zoom2 = fwd = rvs = MouseX = MouseY = hover = frame_count = start_time = end_time = fps = maskZoomCount = 0
traceStart = 1
traceEnd = 1000
zoomFactor = 1.0
image = []
featureImage = []
bufferImage = []
featureOffset = []
featureSize = []
traces = []
masks = []
randRGB = []
maskSelected = [0,0,0]

def init():
    global image, bufferImage, width, height, textures, maskTextures, maskZoom, traces, featureOffset, featureSize, masks, randRGB
    glClearColor(0.0,0.0,0.0,0.0)

    hf  = h5py.File('mask.h5', 'r')
    off = hf.get('offset') 
    offX = off['x']
    offY = off['y']
    fsize = hf.get('size')
    fsizeX =  fsize['x']
    fsizeY = fsize['y']
    masks = hf.get('mask')
    masks = masks[:,:,:]
    masks = masks.transpose(0, 2, 1)

    hf2 = h5py.File('roi_traces.h5', 'r')
    traces = hf2.get('data')
    traces = traces[:,:]

    hf3 = h5py_cache.File('motion_corrected_video.h5', 'r', chunk_cache_mem_size=1024**2*2000)
    bufferImage = hf3.get('data')
    image = bufferImage[0,:,:]
    image = image.transpose(1,0)
    width = len(image[0])
    height = len(image)

    hf.close()
    hf2.close()

    # for data in range(400):
    #     im = Image.open('dataset3/' + str(data) + '.png')
    #     im = im.transpose(Image.FLIP_TOP_BOTTOM)
    #     image.append(im.tobytes("raw", "RGBA", 0, -1))
    #     width = im.size[0]
    #     height = im.size[1]
        #featureOffset.append((numpy.random.randint(low=50, high=900), (numpy.random.randint(low=50, high=800))))
    for data in range(len(masks)):    
        featureOffset.append((offX[data]*(sw/(2*width)), offY[data]*(sw/(2*width))))
        featureSize.append((fsizeX[data]*(sw/(2*width)), fsizeY[data]*(sw/(2*width))))
        r = random.uniform(0, 0.2)
        g = random.uniform(0, 0.2)
        b = random.uniform(0, 0.2)
        randRGB.append((r, g, b))
    
    textures = glGenTextures(3)

    glBindTexture(GL_TEXTURE_2D, textures[0])
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE, width, height, 0, GL_LUMINANCE, GL_SHORT, image)

    glBindTexture(GL_TEXTURE_2D, textures[1])
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE, width, height, 0, GL_LUMINANCE, GL_SHORT, image)


    maskZoom = glGenTextures(3)
    for i in range(3):
        glBindTexture(GL_TEXTURE_2D, maskZoom[i])
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE, len(masks[i][0]), len(masks[i]), 0, GL_LUMINANCE, GL_UNSIGNED_BYTE, masks[i])

    # glGenBuffers(1, pbo)
    # glBindBuffer(GL_PIXEL_UNPACK_BUFFER, pbo)
    # glBufferData(GL_PIXEL_UNPACK_BUFFER, width*height*4, 0, GL_STREAM_DRAW)

    maskTextures = glGenTextures(817)
    for num in range(817):
        glBindTexture(GL_TEXTURE_2D, maskTextures[num])
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE, len(masks[num][0]), len(masks[num]), 0, GL_LUMINANCE, GL_UNSIGNED_BYTE, masks[num])



def playVideo():
    global currImage, image
    if fwd == 1:
        if currImage < len(bufferImage)-1:
            currImage += 1
        else:
            currImage = 0
    if rvs == 1:
        if currImage > 0:
            currImage -= 1
        else:
            currImage = len(bufferImage)-1

    image = bufferImage[currImage,:,:]
    image = image.transpose(1,0)    
    glBindTexture(GL_TEXTURE_2D, textures[0])
    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_LUMINANCE, GL_SHORT, image)


def updateImage():
    global iNext, iPrev, currImage, image
    if iNext == 1:
        if currImage < len(bufferImage)-1:
            currImage +=1
        else:
            currImage = 0
    elif iPrev == 1:
        if currImage > 0:
            currImage -=1
        else:
            currImage = len(bufferImage)-1
    else:
        return

    iNext = iPrev = 0

    image = bufferImage[currImage,:,:]
    image = image.transpose(1,0)
    glBindTexture(GL_TEXTURE_2D, textures[0])
    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_LUMINANCE, GL_SHORT, image)
    #glActiveTexture(GL_TEXTURE0)



def drawImages():
    glViewport(int(sw/2), int(sh-(sw/2)*(height/width)), int(sw/2), int((sw/2)*(height/width)))
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, int(sw/2), int((sw/2)*(height/width)), 0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glBindTexture(GL_TEXTURE_2D, textures[0])
    glEnable(GL_TEXTURE_2D)
    glPushMatrix()
    glClear(GL_DEPTH_BUFFER_BIT)
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0)
    glVertex3f(0.0, 0.0, 0.0)
    glTexCoord2f(0.0, 1.0)
    glVertex3f(0.0, (sw/2)*(height/width), 0.0)
    glTexCoord2f(1.0, 1.0)
    glVertex3f(sw/2, (sw/2)*(height/width), 0.0)
    glTexCoord2f(1.0, 0.0)
    glVertex3f(sw/2, 0.0, 0.0)
    glEnd()
    glPopMatrix()
    glDisable(GL_TEXTURE_2D) 
    glColor3ub(255, 255, 255)
    glRasterPos(20, 20)
    s = str(currImage)
    for ch in s:
        glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))
   
    


def drawOverlay(feature):
    glBindTexture(GL_TEXTURE_2D, maskTextures[feature])
    glEnable(GL_TEXTURE_2D)
    glPushMatrix()
    glTranslatef(featureOffset[feature][0], featureOffset[feature][1], 0)
    glClear(GL_DEPTH_BUFFER_BIT)
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0)
    glVertex3f(0.0, 0.0, 0.0)
    glTexCoord2f(0.0, 1.0)
    glVertex3f(0.0, len(masks[feature])*(sw/(2*width)), 0.0)
    glTexCoord2f(1.0, 1.0)
    glVertex3f(len(masks[feature][0])*(sw/(2*width)), len(masks[feature])*(sw/(2*width)), 0.0)
    glTexCoord2f(1.0, 0.0)
    glVertex3f(len(masks[feature][0])*(sw/(2*width)), 0.0, 0.0)
    glEnd()
    glPopMatrix()
    glDisable(GL_TEXTURE_2D)
#     glColor3ub(255,255,255)
#     glBegin(GL_LINE_LOOP)
#     glVertex2f(featureOffset[features][0], featureOffset[features][1])
#     glVertex2f(featureOffset[features][0] + featureSize[features][0], featureOffset[features][1])
#     glVertex2f(featureOffset[features][0] + featureSize[features][0], featureOffset[features][1] + featureSize[features][1])
#     glVertex2f(featureOffset[features][0], featureOffset[features][1] + featureSize[features][1])
#     glEnd()


def hoverZoom():
    glViewport(int(sw/4), int(sh-sw/4.8), int(sw/5), int(sw/5))
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    #gluOrtho2D((MouseX - sw/10)*zoomFactor, (MouseX + sw/10)*zoomFactor, (MouseY + sw/10)*zoomFactor, (MouseY - sw/10)*zoomFactor)
    gluOrtho2D(0, int(sw/5), int(sw/5), 0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glBindTexture(GL_TEXTURE_2D, textures[1])
    glEnable(GL_TEXTURE_2D)
    glPushMatrix()
    glClear(GL_DEPTH_BUFFER_BIT)
    glTranslatef(((-MouseX)*3+sw/10)*hover, ((-MouseY*(width/height))*3+sw/10)*hover, 0)
    glScalef(zoomFactor, zoomFactor, 1.0)
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0)
    glVertex3f(0.0, 0.0, 0.0)
    glTexCoord2f(0.0, 1.0)
    glVertex3f(0.0, sw/5, 0.0)
    glTexCoord2f(1.0, 1.0)
    glVertex3f(sw/5, sw/5, 0.0)
    glTexCoord2f(1.0, 0.0)
    glVertex3f(sw/5, 0.0, 0.0)
    glEnd()
    glDisable(GL_TEXTURE_2D)
    
    glColor3ub(255, 255, 255)
    glRasterPos2f(20, 20)
    s = "Hover to Zoom:"
    for ch in s:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))

    glPopMatrix()



def displayMaskZoom(num):
    glViewport(int(sw/4), int(sh-(sw/4.6) - len(masks[num])*(3*(num+1)) - (15*num)), int(len(masks[num][0]))*3, int(len(masks[num]))*3)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, int(len(masks[num][0]))*3, int(len(masks[num]))*3, 0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glBindTexture(GL_TEXTURE_2D, maskZoom[num])
    glEnable(GL_TEXTURE_2D)
    glPushMatrix()
    glClear(GL_DEPTH_BUFFER_BIT)
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0)
    glVertex3f(0.0, 0.0, 0.0)
    glTexCoord2f(0.0, 1.0)
    glVertex3f(0.0, len(masks[num])*3, 0.0)
    glTexCoord2f(1.0, 1.0)
    glVertex3f(len(masks[num][0])*3, len(masks[num])*3, 0.0)
    glTexCoord2f(1.0, 0.0)
    glVertex3f(len(masks[num][0])*3, 0.0, 0.0)
    glEnd()
    glDisable(GL_TEXTURE_2D)

    glBegin(GL_LINE_LOOP)
    glVertex2f(0.1, 0.1)
    glVertex2f(0.1, len(masks[num])*3-0.1)
    glVertex2f(len(masks[num][0])*3, len(masks[num])*3-0.1)
    glVertex2f(len(masks[num][0])*3, 0.1)
    glEnd()

    glPopMatrix()


def displayMaskDetails(num):
    glViewport(30, int(sh-(sw/4.6) - len(masks[num])*(3*(num+1)) - (15*num)), int(sw/5), int(len(masks[num]))*3)
    glLoadIdentity()
    gluOrtho2D(0, int(sw/5), int(len(masks[num]))*3, 0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glBegin(GL_LINE_LOOP)
    glVertex2f(0.1, 0.1)
    glVertex2f(0.1, len(masks[num])*3-0.1)
    glVertex2f(sw/5, len(masks[num])*3-0.1)
    glVertex2f(sw/5, 0.1)
    glEnd()
    glRasterPos2f(20, 20)
    s1 = 'Feature selected: ' + str(maskSelected[num])
    for ch in s1:
        glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))

    glRasterPos2f(20, len(masks[num]))
    s1 = 'Location: ' + str(featureOffset[maskSelected[num]][0]) + ', ' + str(featureOffset[maskSelected[num]][1])
    for ch in s1:
        glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))
    
    glRasterPos2f(20, len(masks[num])*2)
    s1 = "Area: " + str(featureSize[maskSelected[num]][0]) + ', ' + str(featureSize[maskSelected[num]][1])
    for ch in s1:
        glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))


def featureDetails():
    glColor3ub(255, 255, 255)
    glViewport(30, int(sh-sw/4.8), int(sw/5), int(sw/5))
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, int(sw/5), int(sw/5), 0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glBegin(GL_LINE_LOOP)
    glVertex2f(0.1, 0.1)
    glVertex2f(0.1, sw/5-0.1)
    glVertex2f(sw/5, sw/5-0.1)
    glVertex2f(sw/5, 0.1)
    glEnd()
    glRasterPos2f(20, (sw/5)/5)
    s1 = 'Feature selected: ' + str(0)
    for ch in s1:
        glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))

    glRasterPos2f(20, (sw/5)/3)
    s1 = 'Location: ' + str(featureOffset[0][0]) + ', ' + str(featureOffset[0][1])
    for ch in s1:
        glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))
    
    glRasterPos2f(20, (sw/5)/2)
    s1 = "Area: 1600px"
    for ch in s1:
        glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))
    
    glRasterPos2f(20, (sw/5)/1.5)
    s1 = "Perimeter: 160px"
    for ch in s1:
        glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))
    
    # glViewport(30, int(sh-sw/2.4), int(sw/5), int(sw/5))
    # glMatrixMode(GL_PROJECTION)
    # glLoadIdentity()
    # gluOrtho2D(0, int(sw/5), int(sw/5), 0)
    # glMatrixMode(GL_MODELVIEW)
    # glLoadIdentity()
    # glBegin(GL_LINE_LOOP)
    # glVertex2f(0.1, 0.1)
    # glVertex2f(0.1, sw/5-0.1)
    # glVertex2f(sw/5, sw/5-0.1)
    # glVertex2f(sw/5, 0.1)
    # glEnd()
    # glRasterPos2f(20, (sw/5)/5)
    # s1 = 'Feature selected: ' + str(0)
    # for ch in s1:
    #     glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))

    # glRasterPos2f(20, (sw/5)/3)
    # s1 = 'Location: ' + str(featureOffset[0][0]) + ', ' + str(featureOffset[0][1])
    # for ch in s1:
    #     glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))
    
    # glRasterPos2f(20, (sw/5)/2)
    # s1 = "Area: 1600px"
    # for ch in s1:
    #     glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))
    
    # glRasterPos2f(20, (sw/5)/1.5)
    # s1 = "Perimeter: 160px"
    # for ch in s1:
    #     glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))


def plotTraces(num):
    global traceStart, traceEnd
    glColor3ub(255, 255, 255)
    glViewport(0, int(sh-(sw/2)*(height/width)-(110*(num+1))), sw, 90)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, sw, 0, 90)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glBegin(GL_LINES)
    glVertex2f(0, 0.1)
    glVertex2f(sw, 0.1)
    glVertex2f(0, 90-0.1)
    glVertex2f(sw, 90-0.1)
    glEnd()
    glBegin(GL_LINES)
    glVertex2f(sw/2, 0)
    glVertex2f(sw/2, 90)
    glEnd()
    if currImage < len(bufferImage)-500 and currImage >= 500:
        traceStart = currImage - 500
        traceEnd = currImage + 500
    else:
        if currImage < 500:
            traceStart = 1
            traceEnd = 1000
        elif currImage > len(bufferImage)-500:
            traceStart = currImage - 500
            traceEnd = len(bufferImage)
    #glScalef(1.0, -1.0, 1.0)
    glBegin(GL_LINES)
    # if currImage > traceEnd - 400 and currImage < len(bufferImage)-400:
    #     traceEnd += 400
    #     traceStart += 400
    # if currImage < traceStart + 400 and currImage > 400:
    #     traceStart -= 400
    #     traceEnd -= 400
    for point in range(traceStart, traceEnd):
        glVertex2f((sw/2-currImage*2)+(point-1)*2, traces[maskSelected[num]][point-1]/250-15)
        glVertex2f((sw/2-currImage*2)+point*2, traces[maskSelected[num]][point]/250-15)
    glEnd()


def drawFPS():
    glViewport(0, sh-40, 30, 30)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, 30, 30, 0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glColor3ub(255, 255, 255)
    glRasterPos2f(10,10)
    for ch in str(fps):
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))


def display():
    global image, frame_count, end_time, start_time, fps
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_BLEND)
    glBlendFunc(GL_ONE, GL_ZERO)
    drawImages()
    glBlendFunc(GL_CONSTANT_COLOR, GL_ONE)
    for feature in range(len(masks)):
        glBlendColor(randRGB[feature][0], randRGB[feature][1], randRGB[feature][2], 1)
        drawOverlay(feature)
    glDisable(GL_BLEND)
    hoverZoom()
    for i in range(maskZoomCount):
        displayMaskZoom(i)
        displayMaskDetails(i)
        plotTraces(i)
    featureDetails()
    playVideo()
    frame_count += 1
    end_time = glutGet(GLUT_ELAPSED_TIME)
    if end_time - start_time > 100:
        fps =  int(frame_count*1000/(end_time-start_time))
        frame_count = 0
        start_time = end_time
    drawFPS()
    glutSwapBuffers()


def Timer(value):
    glutPostRedisplay()
    glutTimerFunc(30, Timer, 0)


def mouseAction(button, state, x, y):
    global maskZoomCount, maskSelected
    if state == GLUT_DOWN and button == GLUT_LEFT_BUTTON:
        if x > int(sw/2) and y < int(sw/2*(height/width)):
            for i in range(len(featureOffset)):
                if x < int(sw/2 + featureOffset[i][0] + featureSize[i][0]) and x > int(sw/2 + featureOffset[i][0]) and y < int(featureOffset[i][1] + featureSize[i][1]) and y > featureOffset[i][1]:
                    if(maskZoomCount < 3):
                        maskSelected[maskZoomCount] = i
                        glBindTexture(GL_TEXTURE_2D, maskZoom[maskZoomCount])
                        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, len(masks[i][0]), len(masks[i]), GL_LUMINANCE, GL_UNSIGNED_BYTE, masks[i])
                        maskZoomCount += 1
                    else:
                        maskZoomCount = 2
                        maskSelected[maskZoomCount] = i
                        glBindTexture(GL_TEXTURE_2D, maskZoom[maskZoomCount])
                        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, len(masks[i][0]), len(masks[i]), GL_LUMINANCE, GL_UNSIGNED_BYTE, masks[i])
                    break

    glutPostRedisplay()   


def zoomLocation(x, y):
    global zoomFactor, MouseX, MouseY, featureImage
    if x > int(sw/2) and x <= sw and y >= 0 and y < int((sw/2)*(height/width)) and hover == 1:
        MouseX = x - sw/2
        MouseY = y
        glBindTexture(GL_TEXTURE_2D, textures[1])
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_LUMINANCE, GL_SHORT, image)
        zoomFactor = 7.5
    else:
        featureImage = bufferImage[0,:,:]
        featureImage = featureImage.transpose(1,0)
        glBindTexture(GL_TEXTURE_2D, textures[1])
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_LUMINANCE, GL_SHORT, featureImage)
        zoomFactor = 1.0
        MouseX = MouseY = 0
    glutPostRedisplay()       


def changeImage(bkey, x, y):
    global iNext, iPrev, zoom1, zoom2, fwd, rvs, hover, maskZoomCount, maskSelected
    key = bkey.decode("utf-8")
    if key == chr(27):
        sys.exit()
    elif key == 'd':
        iNext = 1
        updateImage()
    elif key == 'a':
        iPrev = 1
        updateImage()
    elif key == '1':
        zoom1 = 1
        zoom2 = 0
    elif key == '2':
        zoom1 = 0
        zoom2 = 1
    elif key == ' ':
        fwd = rvs = 0
    elif key == 'c':
        maskZoomCount = 0
        maskSelected = [0,0,0]
    elif key == 'z':
        if hover == 0:
            hover = 1
        else:
            hover = 0
    
    glutPostRedisplay()


def specialKeys(key, x, y):
    global fwd, rvs
    if key == GLUT_KEY_RIGHT:
        fwd = 1
        rvs = 0
    elif key == GLUT_KEY_LEFT:
        fwd = 0
        rvs = 1
    #glutPostRedisplay()

if __name__ == '__main__':
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH)
    sw = glutGet(GLUT_SCREEN_WIDTH)
    sh = glutGet(GLUT_SCREEN_HEIGHT)
    #sw = 1920
    glutInitWindowSize(sw, sh)
    glutCreateWindow("2P Image Analysis")
    glutFullScreen()
    glutMouseFunc(mouseAction)
    glutPassiveMotionFunc(zoomLocation)
    glutKeyboardFunc(changeImage)
    glutSpecialFunc(specialKeys)
    init()
    glutDisplayFunc(display)
    Timer(0)
    glutMainLoop()