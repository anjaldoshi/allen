from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import sys, numpy
from PIL import Image

totalImages = 99
sw = sh = width = height = textures = currImage = iNext = iPrev = zoom1 = zoom2 = fData1 = fData2 = fwd = rvs = 0
image = []
features = []

def init():
    global width, height, textures
    glClearColor(0.0,0.0,0.0,0.0)

    for data in range(100):
        im = Image.open('dataset/' + str(data) + '.png')
        image.append(im.tobytes("raw", "RGBA", 0, -1))
        features.append((numpy.random.randint(low=50, high=900), (numpy.random.randint(low=50, high=800))))
        #image = numpy.array(list(im.getdata()), numpy.int8)
   
    width = im.size[0]
    height = im.size[1]

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
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, image[0])

    glBindTexture(GL_TEXTURE_2D, textures[2])
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, image[0])


def playVideo():
    global currImage
    if fwd == 1:
        glBindTexture(GL_TEXTURE_2D, textures[0])
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_BGRA, GL_UNSIGNED_BYTE, image[currImage])
        if currImage < totalImages:
            currImage += 1
        else:
            currImage = 0
    if rvs == 1:
        glBindTexture(GL_TEXTURE_2D, textures[0])
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_BGRA, GL_UNSIGNED_BYTE, image[currImage])
        if currImage > 0:
            currImage -= 1
        else:
            currImage = totalImages


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
    #glPopMatrix()
    glDisable(GL_TEXTURE_2D) 
    glColor3ub(255, 255, 255)
    glRasterPos(20, 20)
    s = str(currImage)
    for ch in s:
        glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , ord(ch))
   

def drawOverlay():
    glColor3ub(255,255,255)
    glBegin(GL_LINE_LOOP)
    glVertex2f(features[currImage][0] - 20, features[currImage][1] - 20)
    glVertex2f(features[currImage][0] + 20, features[currImage][1] - 20)
    glVertex2f(features[currImage][0] + 20, features[currImage][1] + 20)
    glVertex2f(features[currImage][0] - 20, features[currImage][1] + 20)
    glEnd()
    glPopMatrix()


def featureZoom():
    glViewport(int(sw/4), int(sh-sw/4.8), int(sw/5), int(sw/5))
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, int(sw/5), int(sw/5), 0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glBindTexture(GL_TEXTURE_2D, textures[1])
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
    s1 = 'Location: ' + str(features[fData1][0]) + ', ' + str(features[fData1][1])
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
    s1 = 'Location: ' + str(features[fData2][0]) + ', ' + str(features[fData2][1])
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


def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    drawImages()
    drawOverlay()
    featureZoom()
    featureDetails()
    playVideo()
    glutSwapBuffers()


def Timer(value):
    glutPostRedisplay()
    glutTimerFunc(30, Timer, 0)


def mouseAction(button, state, x, y):
    global fData1, fData2
    if state == GLUT_DOWN and button == GLUT_LEFT_BUTTON:
        if x < int((sw/2)+features[currImage][0]+20) and x > int((sw/2)+features[currImage][0]-20) and y < int(features[currImage][1]+20) and y > int(features[currImage][1]-20):
            if zoom1 == 1:
                glBindTexture(GL_TEXTURE_2D, textures[1])
                glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_BGRA, GL_UNSIGNED_BYTE, image[currImage])
                fData1 = currImage
            elif zoom2 == 1:
                glBindTexture(GL_TEXTURE_2D, textures[2])
                glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_BGRA, GL_UNSIGNED_BYTE, image[currImage])
                fData2 = currImage
    glutPostRedisplay()   


def changeImage(bkey, x, y):
    global iNext, iPrev, zoom1, zoom2, fwd, rvs
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
    glutKeyboardFunc(changeImage)
    glutSpecialFunc(specialKeys)
    init()
    glutDisplayFunc(display)
    Timer(0)
    glutMainLoop()