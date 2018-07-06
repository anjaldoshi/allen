#define GL_GLEXT_PROTOTYPES

#include <GL/glut.h>
#include <GL/glu.h>
#include <GL/gl.h>
#include <stdlib.h>
#include <stdio.h>
#include "SOIL.h"
#include "glext.h"
#include <iostream>
#include <cstring>
#include <vector>
#include <time.h>
using namespace std;

GLuint textures[3];
GLuint pbo[2];

int width, height, sw, sh;
int iNext = 0, iPrev = 0, x = 0, z = 0, zoom1 = 0, zoom2 = 0, fData1 = 0, fData2 = 0, frame_count = 0, fwd = 0, rvs = 0;
vector<unsigned char*> image;
vector<vector<float>> features;
int start_time =  0 , end_time;

const int DATA_SIZE = 512 * 450 * 4;

void genTexture(void){
    static int index = 0;
    int nextIndex = 0;
    if(iNext == 1){
        if(x < 99){
            x++;
            z++;
        }
        else{
            x = z = 0;
        }
    }else if(iPrev == 1){
        if(x > 0){
            x--;
            z--;
        }
        else{
            x = z = 99;
        }
    }else{
        return;
    }
    iNext = iPrev = 0;

    index = (index + 1) % 2;
    nextIndex = (index + 1) % 2;

    glBindTexture(GL_TEXTURE_2D, textures[0]);
    //glBindBufferARB(GL_PIXEL_UNPACK_BUFFER_ARB, pbo[index]);
    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_BGRA, GL_UNSIGNED_BYTE, image[x]);
    // glBindBufferARB(GL_PIXEL_UNPACK_BUFFER_ARB, pbo[nextIndex]);
    // glBufferDataARB(GL_PIXEL_UNPACK_BUFFER_ARB, DATA_SIZE, 0, GL_STREAM_DRAW_ARB);
    // GLubyte* ptr = (GLubyte*)glMapBufferARB(GL_PIXEL_UNPACK_BUFFER_ARB, GL_WRITE_ONLY_ARB);
    //     // update data directly on the mapped buffer
    // memcpy(ptr, (GLubyte*)image[x], DATA_SIZE);
    // glUnmapBufferARB(GL_PIXEL_UNPACK_BUFFER_ARB); // release pointer to mapping buffer
    // glBindBufferARB(GL_PIXEL_UNPACK_BUFFER_ARB, 0);
    glActiveTexture(GL_TEXTURE0);
}

void playVideo(){
    if(fwd == 1){
        glBindTexture(GL_TEXTURE_2D, textures[0]);
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_BGRA, GL_UNSIGNED_BYTE, image[x]);
        if(x<99){
            x++;
            z++;
        }else{
            x = z = 0;
        }
    }

    if(rvs == 1){
        glBindTexture(GL_TEXTURE_2D, textures[0]);
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_BGRA, GL_UNSIGNED_BYTE, image[x]);
        if(x > 0){
            x--;
            z--;
        }else{
            x = z = 99;
        }
    }
}

void init(void) {
    glClearColor(0.0, 0.0, 0.0, 0.0);
    //glEnable(GL_DEPTH_TEST);
    // The following two lines enable semi transparent
    glEnable(GL_BLEND);
    glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    glShadeModel(GL_FLAT);
    float fx = 50.0, fy = 50.0;
    for(int i = 0; i < 100; i++){
        char fileName[32];
        sprintf(fileName, "dataset/%d.png", i);
        image.push_back(SOIL_load_image(fileName, &width, &height, 0, SOIL_LOAD_AUTO));
        fx = (rand() % (900 + 1 - 50)) + 50;
        fy = (rand() % (800 + 1 - 50)) + 50;
        features.push_back(vector<float>());
        features[i].push_back(fx);
        features[i].push_back(fy);
        //cout<<features[i][0]<<", "<<features[i][1]<<endl;
    }
    //cout<<features.size()<<endl;
 

    glGenTextures(3, textures);
    glBindTexture(GL_TEXTURE_2D, textures[0]);
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1);
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexImage2D(GL_TEXTURE_2D, 0, 4, width, height, 0, GL_BGRA, GL_UNSIGNED_BYTE, image[0]);
    //glBindTexture(GL_TEXTURE_2D, 0);

    glBindTexture(GL_TEXTURE_2D, textures[1]);
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1);
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    //float color[4] = {1.0, 1.0, 0.0, 1.0};
    //glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, color);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_BGRA, GL_UNSIGNED_BYTE, image[0]);

    glBindTexture(GL_TEXTURE_2D, textures[2]);
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1);
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    //glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, color);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_BGRA, GL_UNSIGNED_BYTE, image[0]);

    glGenBuffersARB(2, pbo);
    glBindBufferARB(GL_PIXEL_UNPACK_BUFFER_ARB, pbo[0]);
    glBufferDataARB(GL_PIXEL_UNPACK_BUFFER_ARB, DATA_SIZE, 0, GL_STREAM_DRAW_ARB);
    glBindBufferARB(GL_PIXEL_UNPACK_BUFFER_ARB, pbo[1]);
    glBufferDataARB(GL_PIXEL_UNPACK_BUFFER_ARB, DATA_SIZE, 0, GL_STREAM_DRAW_ARB);
    glBindBufferARB(GL_PIXEL_UNPACK_BUFFER_ARB, 0);
}

void drawImages(){
    glViewport(sw/2, sh-((sw/2)*(GLfloat)(height)/(GLfloat)(width)), sw/2, (sw/2)*(GLfloat)(height)/(GLfloat)(width));
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    //gluPerspective(45.0, (GLfloat)(width)/(GLfloat)(height), 0.1, 500.0);
    gluOrtho2D(0, sw/2, (sw/2) * (GLfloat)(height)/(GLfloat)(width), 0);
    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();
    glBindTexture(GL_TEXTURE_2D, textures[0]);
    glEnable(GL_TEXTURE_2D);
    glPushMatrix();
    glClear(GL_DEPTH_BUFFER_BIT);
    //glTranslatef(0, 0, -2.4);
    //glScalef(zoomFactor, zoomFactor, zoomFactor);
    glBegin(GL_QUADS);
        glTexCoord2f(0.0, 0.0);
        glVertex3f(0.0, 0.0, 0.0);
        glTexCoord2f(0.0, 1.0);
        glVertex3f(0.0, (sw/2) * (GLfloat)(height)/(GLfloat)(width), 0.0);
        glTexCoord2f(1.0, 1.0);
        glVertex3f(sw/2, (sw/2) * (GLfloat)(height)/(GLfloat)(width), 0.0);
        glTexCoord2f(1.0, 0.0);
        glVertex3f(sw/2, 0.0, 0.0);
    glEnd();
    //glPopMatrix();
    glDisable(GL_TEXTURE_2D);
    glColor3ub(255, 255, 255);
    glRasterPos2f(20, 20);
    string s = to_string(x);
    for(int i = 0; i < s.size(); i++){
        glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , s[i]);
    }
}

void drawOverlay(){
    glColor3ub(255,255,255);
    //glPushMatrix();
    // move quad back a bit so it's above Z=0
    //glTranslatef(0,0,-0.5);
    //glScalef(50,50,50);
    glBegin(GL_LINE_LOOP);
        glVertex2f(features[z][0] - 20, features[z][1] - 20);
        glVertex2f(features[z][0] + 20, features[z][1] - 20);
        glVertex2f(features[z][0] + 20, features[z][1] + 20);
        glVertex2f(features[z][0] - 20, features[z][1] + 20);
    glEnd();
    glPopMatrix();
}

void featureZoom(){
    glViewport(sw/4, sh-sw/4.8, sw/5, sw/5);
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    //gluPerspective(45.0, (GLfloat)(width)/(GLfloat)(height), 0.1, 500.0);
    gluOrtho2D(0, sw/5, sw/5, 0);
    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();
    glBindTexture(GL_TEXTURE_2D, textures[1]);
    glEnable(GL_TEXTURE_2D);
    glPushMatrix();
    glClear(GL_DEPTH_BUFFER_BIT);
    //glTranslatef(0, 0, -2.4);
    //glScalef(zoomFactor, zoomFactor, zoomFactor);
    glBegin(GL_QUADS);
        glTexCoord2f(0.0, 0.0);
        glVertex3f(0.0, 0.0, 0.0);
        glTexCoord2f(0.0, 1.0);
        glVertex3f(0.0, sw/5, 0.0);
        glTexCoord2f(1.0, 1.0);
        glVertex3f(sw/5, sw/5, 0.0);
        glTexCoord2f(1.0, 0.0);
        glVertex3f(sw/5, 0.0, 0.0);
    glEnd();
    glDisable(GL_TEXTURE_2D);
    
    glColor3ub(255, 255, 255);
    glRasterPos2f(20, 20);
    string s = "Feature Zoom 1:";
    for(int i = 0; i < s.size(); i++){
        glutBitmapCharacter( GLUT_BITMAP_HELVETICA_12 , s[i]);
    }
    
    if(zoom1==1){
        glBegin(GL_LINE_LOOP);
            glVertex2f(0.1, 0.1);
            glVertex2f(0.1, sw/5-0.1);
            glVertex2f(sw/5, sw/5-0.1);
            glVertex2f(sw/5, 0.1);
        glEnd();
    }
    glPopMatrix();

    glViewport(sw/4, sh - sw/2.4, sw/5, sw/5);
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    //gluPerspective(45.0, (GLfloat)(width)/(GLfloat)(height), 0.1, 500.0);
    gluOrtho2D(0, sw/5, sw/5, 0);
    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();
    glBindTexture(GL_TEXTURE_2D, textures[2]);
    glEnable(GL_TEXTURE_2D);
    glPushMatrix();
    glClear(GL_DEPTH_BUFFER_BIT);
    //glTranslatef(0, 0, -2.4);
    //glScalef(zoomFactor, zoomFactor, zoomFactor);
    glBegin(GL_QUADS);
        glTexCoord2f(0.0, 0.0);
        glVertex3f(0.0, 0.0, 0.0);
        glTexCoord2f(0.0, 1.0);
        glVertex3f(0.0, sw/5, 0.0);
        glTexCoord2f(1.0, 1.0);
        glVertex3f(sw/5, sw/5, 0.0);
        glTexCoord2f(1.0, 0.0);
        glVertex3f(sw/5, 0.0, 0.0);
    glEnd();
    glDisable(GL_TEXTURE_2D);
    glColor3ub(255, 255, 255);
    glRasterPos2f(20, 20);
    s = "Feature Zoom 2:";
    for(int i = 0; i < s.size(); i++){
        glutBitmapCharacter( GLUT_BITMAP_HELVETICA_12 , s[i]);
    }

    if(zoom2==1){
        glBegin(GL_LINE_LOOP);
            glVertex2f(0.1, 0.1);
            glVertex2f(0.1, sw/5-0.1);
            glVertex2f(sw/5, sw/5-0.1);
            glVertex2f(sw/5, 0.1);
        glEnd();
    }
    glPopMatrix();
}
void featureDetails(){
    glColor3ub(255, 255, 255);
    glViewport(30.0, sh-sw/4.8, sw/5, sw/5);
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    gluOrtho2D(0, sw/5, sw/5, 0);
    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();
    glBegin(GL_LINE_LOOP);
        glVertex2f(0.1, 0.1);
        glVertex2f(0.1, sw/5-0.1);
        glVertex2f(sw/5, sw/5-0.1);
        glVertex2f(sw/5, 0.1);
    glEnd();
    glRasterPos2f(20, (sw/5)/5);
    char c1[100];
    sprintf(c1, "Feature selected: %d", fData1);
    string s1(c1);
    for(int i = 0; i < s1.size(); i++){
        glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , s1[i]);
    }  
    sprintf(c1, "Location: %.0f, %.0f", features[fData1][0], features[fData1][1]);
    s1 = c1;
    glRasterPos2f(20, (sw/5)/3);
    for(int i = 0; i < s1.size(); i++){
        glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , s1[i]);
    }
    s1 = "Area: 1600px";
    glRasterPos2f(20, (sw/5)/2);
    for(int i = 0; i < s1.size(); i++){
        glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , s1[i]);
    }
    s1 = "Perimeter: 160px";
    glRasterPos2f(20, (sw/5)/1.5);
    for(int i = 0; i < s1.size(); i++){
        glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , s1[i]);
    }     
     

    glViewport(30.0, sh - sw/2.4, sw/5, sw/5);
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    gluOrtho2D(0, sw/5, sw/5, 0);
    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();
    glBegin(GL_LINE_LOOP);
        glVertex2f(0.1, 0.1);
        glVertex2f(0.1, sw/5-0.1);
        glVertex2f(sw/5, sw/5-0.1);
        glVertex2f(sw/5, 0.1);
    glEnd();
    glRasterPos2f(20, (sw/5)/5);
    char c2[100];
    sprintf(c2, "Feature selected: %d\n", fData2);
    string s2(c2);
    for(int i = 0; i < s2.size(); i++){
        glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , s2[i]);
    } 
    sprintf(c2, "Location: %.0f, %.0f", features[fData2][0], features[fData2][1]);
    glRasterPos2f(20, (sw/5)/3);
    s2 = c2;
    for(int i = 0; i < s2.size(); i++){
        glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , s2[i]);
    }
    s2 = "Area: 1600px";
    glRasterPos2f(20, (sw/5)/2);
    for(int i = 0; i < s2.size(); i++){
        glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , s2[i]);
    }
    s2 = "Perimeter: 160px";
    glRasterPos2f(20, (sw/5)/1.5);
    for(int i = 0; i < s2.size(); i++){
        glutBitmapCharacter( GLUT_BITMAP_HELVETICA_18 , s2[i]);
    }    
}

void display(void) {
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    drawImages();
    drawOverlay();
    featureZoom();
    featureDetails();
    playVideo();
    // frame_count++;
    // end_time = glutGet(GLUT_ELAPSED_TIME);
    // if(end_time - start_time > 100){
    //     cout<<"FPS: "<<frame_count * 1000/ (end_time - start_time)<<endl;
    //     frame_count = 0;
    //     start_time = end_time;
    // }
    glutSwapBuffers();
}

void Timer(int iUnused){
    glutPostRedisplay();
    glutTimerFunc(30, Timer, 0);
}

void myReshape(int w, int h) {
    glViewport(0, 0, w, h);
}

void mouseAction(int button, int state, int x, int y){
    if (state == GLUT_DOWN ){
		if ( button == GLUT_LEFT_BUTTON ){
            if(x < ((sw/2)+features[z][0]+20) && x > ((sw/2)+features[z][0]-20) && y < (features[z][1]+20) && y > (features[z][1]-20) ){
                if(zoom1 == 1){
                    glBindTexture(GL_TEXTURE_2D, textures[1]);
                    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_BGRA, GL_UNSIGNED_BYTE, image[z]);
                    fData1 = z;
                }else if(zoom2 == 1){
                    glBindTexture(GL_TEXTURE_2D, textures[2]);
                    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_BGRA, GL_UNSIGNED_BYTE, image[z]);
                    fData2 = z;
                }
                cout<<"Feature "<<z<<" Selected"<<endl;
            }
		}
	}

   glutPostRedisplay();
}

void changeImage(unsigned char key, int x, int y){
    if(key == 'd'){
        iNext = 1; 
        genTexture();
    }
    else if(key == 'a'){
        iPrev = 1; 
        genTexture();
    }
    else if(key == '1'){
        zoom1 = 1;
        zoom2 = 0;
    }else if(key == '2'){
        zoom2 = 1;
        zoom1 = 0;
    }else if(key == ' '){
        cout<<"Video Paused"<<endl;
        fwd = rvs = 0;
    }
    else if(key == 27){
        image.clear();
        features.clear();
        exit(0);
    }
    glutPostRedisplay();
}

void specialKeys(int key, int x, int y){
    if(key == GLUT_KEY_RIGHT){
        fwd = 1;
        rvs = 0;
    }else if(key == GLUT_KEY_LEFT){
        fwd = 0;
        rvs = 1;
    }
}


void idle()
{
    glutPostRedisplay();
}


int main(int argc, char** argv) {
    glutInit(&argc, argv);
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH);
    sw = glutGet(GLUT_SCREEN_WIDTH);
    sh = glutGet(GLUT_SCREEN_HEIGHT);
    sw = 1920;
    glutInitWindowSize(sw, sh);
    glutCreateWindow("2P Image Analysis");
    glutFullScreen();
    glutMouseFunc(mouseAction);
    glutKeyboardFunc(changeImage);
    glutSpecialFunc(specialKeys);
    init();
    glutReshapeFunc(myReshape);
    glutDisplayFunc(display);
    Timer(0);
    //glutIdleFunc(idle);
    glutMainLoop();
    return 0;
}
