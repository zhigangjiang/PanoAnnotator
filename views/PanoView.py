
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import data
import utils

class PanoView(QLabel):

    def __init__(self, parent=None):
        super(PanoView, self).__init__(parent)

        self.__isAvailable = False
        self.__mainWindow = None
        self.__mainScene = None

        self.__panoPixmap = QPixmap()

        self.__mode = 0 # 0: select mode 1: add point
        self.__lastPos = QPoint()

        self.isLayoutLineEnable = True
        self.isLayoutPointEnable = True
        self.isLayoutFinalWallEnable = False

    #####
    #Comstum Method
    #####
    def initByScene(self, scene):

        self.__mainScene = scene
        self.__panoPixmap = self.__mainScene.getPanoColorPixmap()

        self.__isAvailable = True

    def createGeoPoint(self, sceenPos):
        
        coords = utils.pos2coords(sceenPos, 
                                            (self.width(), self.height()))
        geoPoint = data.GeoPoint(self.__mainScene, coords)

        return geoPoint

    def modeSwitch(self, mode):

        if self.__mode == mode:
            self.__mode = 0
        else:
            self.__mode = mode

    def selectByCoords(self, coords):
        
        vec =  utils.coords2xyz(coords, 1)

        def choose(self, obj):
            select = self.__mainWindow.selectObjects
            select.remove(obj) if obj in select else select.append(obj)

        for wall in self.__mainScene.label.getLayoutWalls():
            if wall.checkRayHit(vec):
                choose(self, wall)
                return

        floor = self.__mainScene.label.getLayoutFloor()
        ceiling = self.__mainScene.label.getLayoutCeiling()
        choose(self, floor) if vec[1] <= 0 else choose(self, ceiling)
    

    #####
    #Override
    #####
    def paintEvent(self, event):

        if self.__isAvailable:
            qp = QPainter()

            qp.begin(self)
            qp.drawPixmap(0, 0, self.width(), self.height(), self.__panoPixmap)

            if self.isLayoutPointEnable:

                for point in self.__mainScene.label.getLayoutPoints():

                    if point in self.__mainWindow.selectObjects:
                        qp.setPen(QPen(Qt.yellow, 2, Qt.SolidLine))
                    else:
                        qp.setPen(QPen(Qt.red, 2, Qt.SolidLine))

                    pos = utils.coords2pos(point.coords, 
                                                    (self.width(), self.height()))
                    qp.drawEllipse(QPoint(pos[0], pos[1]), 5, 5)
                    #qp.drawLine(pos[0], 0, pos[0], self.height())

            def drawMeshProj(self, obj):

                points = obj.meshProj
                pnum = len(points)
                for i in range(pnum):
                    pos1 = utils.coords2pos(points[i], (self.width(), self.height()))
                    pos2 = utils.coords2pos(points[(i+1)%pnum], 
                                            (self.width(), self.height()))
                    if abs(pos1[0] - pos2[0]) > self.width()/10:
                        continue
                    qp.drawLine(pos1[0], pos1[1], pos2[0], pos2[1])

            if self.isLayoutLineEnable:

                #draw all obj first
                qp.setPen(QPen(Qt.blue, 2, Qt.SolidLine))
                for wall in  self.__mainScene.label.getLayoutWalls():
                    drawMeshProj(self, wall)

                floor = self.__mainScene.label.getLayoutFloor()
                ceiling = self.__mainScene.label.getLayoutCeiling()
                if floor is not None:
                    drawMeshProj(self, floor)
                if ceiling is not None:
                    drawMeshProj(self, ceiling) 

                #darw selected obj again
                qp.setPen(QPen(Qt.yellow, 2, Qt.SolidLine))
                for obj in self.__mainWindow.selectObjects:
                    if type(obj) == data.WallPlane or type(obj) == data.FloorPlane:
                        drawMeshProj(self, obj)
            

            qp.setPen(QPen(Qt.black, 2, Qt.SolidLine))
            qp.drawText(10, 10, "Mode : {0}".format(self.__mode))

            qp.end()

        self.__mainWindow.updateViews()

    def mousePressEvent(self, event):
        self.__lastPos = event.pos()

    def mouseMoveEvent(self, event):

        dx = event.x() - self.__lastPos.x()
        dy = event.y() - self.__lastPos.y()

        self.__mainWindow.updateViews()

    def mouseReleaseEvent(self, event):

        screenPos = (event.pos().x(),event.pos().y())
        if self.__isAvailable:
   
            if event.button() == Qt.LeftButton:
                if self.__mode == 0:
                    self.selectByCoords((event.x()/self.width(),
                                        event.y()/self.height()))
                elif self.__mode == 1:
                    geoPoint = self.createGeoPoint(screenPos)
                    self.__mainScene.label.addLayoutPoint(geoPoint)
                    self.__mainWindow.updateListView()

            elif event.button() == Qt.RightButton:
                self.__mainScene.label.delLastLayoutPoints()
                self.__mainWindow.updateListView()
                
        self.__mainWindow.updateViews()
    
    def wheelEvent(self,event):
        
        dy = float(event.angleDelta().y())

        for obj in self.__mainWindow.selectObjects:
            if type(obj) is data.WallPlane:
                self.__mainScene.label.moveWallByNormal(obj, dy/3000)
                
            elif type(obj) is data.FloorPlane and not obj.isCeiling():
                newH = self.__mainScene.label.getCameraHeight() - float(dy)/1000
                self.__mainScene.label.setCameraHeight(newH)

            elif type(obj) is data.FloorPlane and obj.isCeiling():
                newH = self.__mainScene.label.getLayoutHeight() + float(dy)/1000
                self.__mainScene.label.setLayoutHeight(newH)

        self.__mainWindow.updateViews()

    def keyPressEvent(self, event):

        if(event.key() == Qt.Key_Control):
            self.__mode = 1
            self.__mainWindow.selectObjects = []
        
        if(event.key() == Qt.Key_S):
            self.__mainScene.label.genManhLayoutWalls()
            self.__mainWindow.updateListView()
                                    
        elif(event.key() == Qt.Key_X):
            self.__mainScene.label.cleanLayout()
            self.__mainWindow.updateListView()

        elif(event.key() == Qt.Key_D):
            self.__mainScene.label.delLayoutWalls(self.__mainWindow.selectObjects)
            self.__mainWindow.updateListView()
            self.__mainWindow.selectObjects = []

        elif(event.key() == Qt.Key_M):
            self.__mainScene.label.mergeLayoutWalls(self.__mainWindow.selectObjects)
            self.__mainWindow.updateListView()
            self.__mainWindow.selectObjects = []

        if (event.key() == Qt.Key_1):
            self.isLayoutLineEnable = not self.isLayoutLineEnable

        elif (event.key() == Qt.Key_2):
            self.isLayoutPointEnable = not self.isLayoutPointEnable

        self.__mainWindow.updateViews()
        
    def keyReleaseEvent(self, event):
        self.__mode = 0

    def enterEvent(self, event):
        self.setFocus(True)
    
    def leaveEvent(self, event):
        pass


    def setMainWindow(self, mainWindow):
        self.__mainWindow = mainWindow