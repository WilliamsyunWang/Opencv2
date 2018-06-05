import cv2
import numpy
import time
from numpy import long

'''
    视频管理
'''

class CaptureManager(object):

    def __init__(self,capture,previewWindowManager = None,shouldMirrorPreview = False):

        self.previewWindowManager = previewWindowManager
        self.shouldMirrorPreview = shouldMirrorPreview

        #定义非公有变量,单下划线开始,为保护变量,只有类对象或子类对象可以访问 protected
        #如果以双下划线开始,为私有成员变量,只有类对象自已可以访问,像private
        self._capture = capture
        self._channel = 0
        self._enteredFrame = False
        self._frame = None
        self._imageFilename = None
        self._videoFilename = None
        self._videoEncoding = None
        self._videoWriter = None

        self._startTime = None
        self._framesElapsed = long(0)
        self._fpsEstimate = None

    @property
    def channel(self):
        return self._channel

    @channel.setter
    def channel(self,value):
        if self._channel != value:
            self._channel = value
            self._frame = None

    @property
    def frame(self):
        if self._enteredFrame and self._frame is None:
            _,self._frame = self._capture.retrieve()
        return self._frame

    @property
    def isWritingImage(self):

        return self._imageFilename is not None

    @property
    def isWritingVideo(self):
        return self._videoFilename is not None

    #只能同步一帧
    def enterFrame(self):
        """Capture the next frame,if any."""
        if self._capture is not None:
        #but first,check that any previous frame was exited.
            #assert not self._enteredFrame,'previous enterFrame() had no matching exitFrame()'

            if self._capture is not None:
                self._enteredFrame = self._capture.grab()



    def exitFrame(self):
        """可以从当前通道中取得图像,估计帧率,显示图像,执行暂停的请求,向文件中写入图像"""

        #计算帧率
        if self.frame is None:
            self._enteredFrame = False
            return

        #Update the FPS estimate and related variables.通过窗体显示图像
        if self._framesElapsed == 0:
            self._startTime = time.time()
        else:
            timeElapsed = time.time() - self._startTime
            self._fpsEstimate = self._framesElapsed/timeElapsed
        self._framesElapsed += 1

        #Draw to the Window,if any.保存图像文件
        if self.previewWindowManager is not None:
            if self.shouldMirrorPreview:
                mirroredFrame = numpy.fliplr(self._frame).copy()
                self.previewWindowManager.show(mirroredFrame)
            else:
                self.previewWindowManager.show(self._frame)

        #Write to the image file,if any.保存图像文件
        if self.isWritingImage:
            cv2.imwrite(self._imageFilename,self._frame)
            self._imageFilename = None

        #Write to the video file,if any.保存视频文件
        self._writeVideoFrame()

        #Release the frame.释放资源
        self._frame = None
        self.enteredFrame = False

    def writeImage(self,filename):
       """Write the next exited frame to an image file."""#保存图片,公有函数
       self._imageFilename = filename

    def startWritingVideo(self,filename,encoding = cv2.VideoWriter_fourcc('I','4','2','0')):
        """Start writing exited frames to a video file."""#开始保存视频,公有函数
        self._videoFilename = filename
        self._videoEncoding = encoding

    def stopWritingVideo(self):
        self._videoEncoding = None
        self._videoFilename = None

    def _writeVideoFrame(self):#视频写入,公有函数

        if not self.isWritingVideo:
            return

        if self._videoWriter is None:
            fps = self._capture.get(cv2.CAP_PROP_FPS)
            if fps == 0.0:
                #抓住的帧数是不知道的,因此使用一个估计
                if self._framesElapsed < 20:
                    #等待更多的帧出现,这样估计就更稳定了
                    return
                else:
                    fps = self._fpsEstimate
            size = (int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH)),int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
            self._videoWriter = cv2.VideoWriter(self._videoFilename,self._videoEncoding,fps,size)
            self._videoWriter.write(self._frame)


'''
    窗口管理,支持键盘事件
'''
class WindowManager(object):
    def __init__(self,windowName,keypressCallback = None):
                       #窗体名称#按键回调函数
        self.keypressCallback = keypressCallback

        self._windowName = windowName
        self._isWindowCreated = False

    @property

    def isWindowCreated(self):#检查窗体是否被创建
        return self._isWindowCreated

    def creatWindow(self):#创建窗体
        cv2.namedWindow(self._windowName)
        self._isWindowCreated = True

    def show(self,frame):#显示图像
        cv2.imshow(self._windowName,frame)

    def destroyWindow(self):#关闭窗体释放资源
        cv2.destroyWindow(self._windowName)
        self._isWindowCreated = False

    def processEvents(self):
        keycode = cv2.waitKey(1)
        if self.keypressCallback is not None and  keycode != -1:
            #Discard any non-ASCII info encoded by GTY.
            keycode &= 0xFF
            self.keypressCallback(keycode)