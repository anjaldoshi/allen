from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import sys, numpy, json, h5py, random
from PIL import Image

totalImages = 384
sw = sh = width = height = textures = maskTextures =  currImage = iNext = iPrev = zoom1 = zoom2 = fData1 = fData2 = fwd = rvs = MouseX = MouseY = hover = 0
zoomFactor = 1.0
image = []
featureOffset = []
featureSize = []
traces = []
masks = []
randRGB = []

def init():
    global width, height, textures, maskTextures, traces, featureOffset, featureSize, masks, randRGB
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

    with open('roi_taces.txt', 'r') as fh:
        traces = json.load(fh)

    for data in range(totalImages+1):
        im = Image.open('dataset3/' + str(data) + '.png')
        image.append(im.tobytes("raw", "RGBA", 0, -1))
        width = im.size[0]
        height = im.size[1]
        #featureOffset.append((numpy.random.randint(low=50, high=900), (numpy.random.randint(low=50, high=800))))
    for data in range(len(masks)):    
        featureOffset.append((offX[data]*(sw/(2*width)), offY[data]*(sw/(2*width))))
        featureSize.append((fsizeX[data], fsizeY[data]))
        r = random.uniform(0, 0.2)
        g = random.uniform(0, 0.2)
        b = random.uniform(0, 0.2)
        randRGB.append((r, g, b))
    
    print(max(featureOffset))

    textures = glGenTextures(3)

    glBindTexture(GL_TEXTURE_2D, textures[0])
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, image[0])

    glBindTexture(GL_TEXTURE_2D, textures[1])
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, image[0])

    glBindTexture(GL_TEXTURE_2D, textures[2])
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, image[0])

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
    global currImage
    if fwd == 1:
        if currImage < totalImages:
            currImage += 1
        else:
            currImage = 0
    if rvs == 1:
        if currImage > 0:
            currImage -= 1
        else:
            currImage = totalImages
        
    glBindTexture(GL_TEXTURE_2D, textures[0])
    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_BGRA, GL_UNSIGNED_BYTE, image[currImage])


def updateImage():
    global iNext, iPrev, currImage
    if iNext == 1:
        if currImage < totalImages:
            currImage +=1
        else:
            currImage = 0
    elif iPrev == 1:
        if currImage > 0:
            currImage -=1
        else:
            currImage = totalImages
    else:
        return

    iNext = iPrev = 0

    glBindTexture(GL_TEXTURE_2D, textures[0])
    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_BGRA, GL_UNSIGNED_BYTE, image[currImage])
    glActiveTexture(GL_TEXTURE0)


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


def featureZoom():
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
    s = "Feature Zoom 1:"
    for ch in s:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))

    if zoom1 == 1:
        glBegin(GL_LINE_LOOP)
        glVertex2f(0.1, 0.1)
        glVertex2f(0.1, sw/5-0.1)
        glVertex2f(sw/5, sw/5-0.1)
        glVertex2f(sw/5, 0.1)
        glEnd()

    glPopMatrix()

    glViewport(int(sw/4), int(sh-sw/2.4), int(sw/5), int(sw/5))
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, int(sw/5), int(sw/5), 0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glBindTexture(GL_TEXTURE_2D, textures[2])
    glEnable(GL_TEXTURE_2D)
    glPushMatrix()
    glClear(GL_DEPTH_BUFFER_BIT)
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
    s = "Feature Zoom 2:"
    for ch in s:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))

    if zoom2 == 1:
        glBegin(GL_LINE_LOOP)
        glVertex2f(0.1, 0.1)
        glVertex2f(0.1, sw/5-0.1)
        glVertex2f(sw/5, sw/5-0.1)
        glVertex2f(sw/5, 0.1)
        glEnd()
    glPopMatrix()


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
    s1 = 'Feature selected: ' + str(fData1)
    for ch in s1:
        glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))

    glRasterPos2f(20, (sw/5)/3)
    s1 = 'Location: ' + str(featureOffset[fData1][0]) + ', ' + str(featureOffset[fData1][1])
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
    
    glViewport(30, int(sh-sw/2.4), int(sw/5), int(sw/5))
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
    s1 = 'Feature selected: ' + str(fData2)
    for ch in s1:
        glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))

    glRasterPos2f(20, (sw/5)/3)
    s1 = 'Location: ' + str(featureOffset[fData2][0]) + ', ' + str(featureOffset[fData2][1])
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


def plotTraces():
    glColor3ub(255, 255, 255)
    glViewport(0, 100, sw, 100)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, sw, 100, 0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glBegin(GL_LINES)
    glVertex2f(0, 0)
    glVertex2f(sw, 0)
    glVertex2f(0, 100-0.1)
    glVertex2f(sw, 100-0.1)
    glEnd()
    glBegin(GL_LINES)
    for point in range(1,385):
        glVertex2f((point-1)*5, (traces[point-1])/50-50)
        glVertex2f(point*5, (traces[point])/50-50)
    glEnd()



def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_BLEND)
    glBlendFunc(GL_ONE, GL_ZERO)
    drawImages()
    glBlendFunc(GL_CONSTANT_COLOR, GL_ONE)
    for feature in range(len(masks)):
        glBlendColor(randRGB[feature][0], randRGB[feature][1], randRGB[feature][2], 1)
        drawOverlay(feature)
    glDisable(GL_BLEND)
    featureZoom()
    featureDetails()
    plotTraces()
    playVideo()
    glutSwapBuffers()


def Timer(value):
    glutPostRedisplay()
    glutTimerFunc(30, Timer, 0)


def mouseAction(button, state, x, y):
    global fData1, fData2
    if state == GLUT_DOWN and button == GLUT_LEFT_BUTTON:
        if x < int((sw/2)+featureOffset[currImage][0]+featureSize[currImage][0]) and x > int((sw/2)+featureOffset[currImage][0]) and y < int(featureOffset[currImage][1]+featureSize[currImage][1]) and y > int(featureOffset[currImage][1]):
            if zoom1 == 1:
                glBindTexture(GL_TEXTURE_2D, textures[1])
                glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_BGRA, GL_UNSIGNED_BYTE, image[currImage])
                fData1 = currImage
            elif zoom2 == 1:
                glBindTexture(GL_TEXTURE_2D, textures[2])
                glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_BGRA, GL_UNSIGNED_BYTE, image[currImage])
                fData2 = currImage
    glutPostRedisplay()   


def zoomLocation(x, y):
    global zoomFactor, MouseX, MouseY
    if x > int(sw/2) and x <= sw and y >= 0 and y < int((sw/2)*(height/width)) and hover == 1:
        MouseX = x - sw/2
        MouseY = y
        glBindTexture(GL_TEXTURE_2D, textures[1])
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_BGRA, GL_UNSIGNED_BYTE, image[currImage])
        zoomFactor = 7.5
    else:
        glBindTexture(GL_TEXTURE_2D, textures[1])
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_BGRA, GL_UNSIGNED_BYTE, image[fData1])
        zoomFactor = 1.0
        MouseX = MouseY = 0
    glutPostRedisplay()       


def changeImage(bkey, x, y):
    global iNext, iPrev, zoom1, zoom2, fwd, rvs, hover
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
    sw = 1920
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