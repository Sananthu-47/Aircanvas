import cv2
import numpy as np
import time

class drawingCanvas():
    def __init__(self):
        self.penrange = np.load('penrange.npy')
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3,800) #width
        self.cap.set(4,720) #height
        self.canvas = None
        self.kernel = np.ones((5,5),np.uint8)
        #initial position on pen 
        self.x1,self.y1=0,0
        self.thicknes = 5
        self.colorArray = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 255, 255),(0, 0, 0)] #BGRY
        self.colorIndex = 0
        self.pen_img = cv2.imread('aircanvas_assets/pen.png',1)
        self.pen_img = cv2.resize(self.pen_img,(50,50),fx=950,fy=0)
        self.eraser_img = cv2.imread('aircanvas_assets/eraser.png',1) #1 - color image
        self.eraser_img = cv2.resize(self.eraser_img,(50,50),fx=950,fy=0)
        self.switch = 'Pen'
        self.prevColor = 0
        # With this variable we will monitor the time between previous switch.
        self.last_switch = time.time()
        self.draw()


    def draw(self):
        while True:
            _, self.frame = self.cap.read()
            self.frame = cv2.flip( self.frame, 1 )

            if self.canvas is None:
                self.canvas = np.zeros_like(self.frame)
            
            mask=self.CreateMask()
            contours=self.ContourDetect(mask)
            self.drawLine(contours)
            self.display(mask)
            self.drawColorTab()
            k = cv2.waitKey(1) & 0xFF
            self.takeAction(k)
            
            #if esc key is pressed exit
            if k == 27:
                break  
                  
    def CreateMask(self):
        hsv = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV) 
        lower_range = self.penrange[0]
        upper_range = self.penrange[1]
        mask = cv2.inRange(hsv, lower_range, upper_range)
        mask = cv2.erode(mask, self.kernel, iterations=1) # shrink the image to smaller pixel
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel)
        mask = cv2.dilate(mask, self.kernel, iterations=1) # Dilation expands the image pixels , adds pixels object boundaries
        return mask
    
    def ContourDetect(self,mask):
        # Find Contours
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return contours
    
    def drawLine(self,contours):
        #if contour area is not none and is greater than 100 draw the line
        if contours and cv2.contourArea(max(contours, key = cv2.contourArea)) > 100:                
            c = max(contours, key = cv2.contourArea)    
            x2,y2,w,h = cv2.boundingRect(c)

            # =========================================================================

            cnt = sorted(contours, key = cv2.contourArea, reverse = True)[0]
            # Get the radius of the enclosing circle around the found contour
            ((x,y), radius) = cv2.minEnclosingCircle(cnt)
            # Calculating the center of the detected contour
            M = cv2.moments(cnt)
            center = (int(M['m10'] / M['m00']), int(M['m01'] / M['m00']))
            # Draw the circle around the object
            cv2.circle(self.frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)

            # =====================================================================================

            # Switch the images depending upon what we're using, pen or eraser.
            if self.switch != 'Pen':
                self.frame[5: 55 , 650: 700] = self.eraser_img
                cv2.circle(self.frame, (int(x), int(y)), int(radius), (255,255,255), -1)
            else:
                cv2.circle(self.frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
                self.frame[5: 55 , 650: 700] = self.pen_img

            # Make the thickness of the brush to radius of the detected object for eraser
            if(self.switch == 'Eraser'):
                self.thicknes = int(radius)

            # If the initial position of the countour is 0,0 then make it to the current x and y
            if self.x1 == 0 and self.y1 == 0:
                self.x1,self.y1= x2,y2
            # From here it is the code to choose the pen/erarser and the colors
            elif center[1] <= 65:
                if 40 <= center[0] <= 140: # Clear Button
                    self.canvas[67:,:,:] = 0
                elif 160 <= center[0] <= 255 and self.switch == 'Pen':
                    self.colorIndex = 0 # Blue
                elif 275 <= center[0] <= 370 and self.switch == 'Pen':
                    self.colorIndex = 1 # Green
                elif 390 <= center[0] <= 485 and self.switch == 'Pen':
                    self.colorIndex = 2 # Red
                elif 505 <= center[0] <= 600 and self.switch == 'Pen':
                    self.colorIndex = 3 # Yellow
                elif 650 <= center[0] <= 700  and (time.time()-self.last_switch) > 1:
                    self.last_switch = time.time()
                    if self.switch == 'Pen':
                        self.switch = 'Eraser'
                        self.thicknes = int(radius)
                        self.prevColor = self.colorIndex
                        self.colorIndex = 4
                    else:
                        self.switch = 'Pen'
                        self.thicknes = 5
                        self.colorIndex = self.prevColor
                    
            else:
                # Draw the line on the canvas only if the center is above 65 from y axis
                self.canvas = cv2.line(self.canvas, (self.x1,self.y1),(center), self.colorArray[self.colorIndex], self.thicknes) #(image,start,end,color,thick)
                    
            #New point becomes the previous point 
            self.x1,self.y1= center
        else:
            # If there were no contours detected then make x1,y1 = 0 (reset)
            self.x1,self.y1 =0,0   

    def drawColorTab(self):
        self.canvas = cv2.rectangle(self.canvas, (40,1), (140,65), (255,255,255), -1)
        cv2.putText(self.canvas, "CLEAR", (49, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2, cv2.LINE_AA)
        self.canvas = cv2.rectangle(self.canvas, (160,1), (255,65), self.colorArray[0], -1)
        cv2.putText(self.canvas, "BLUE", (185, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
        self.canvas = cv2.rectangle(self.canvas, (275,1), (370,65), self.colorArray[1], -1)
        cv2.putText(self.canvas, "GREEN", (298, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
        self.canvas = cv2.rectangle(self.canvas, (390,1), (485,65), self.colorArray[2], -1)
        cv2.putText(self.canvas, "RED", (420, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
        self.canvas = cv2.rectangle(self.canvas, (505,1), (600,65), self.colorArray[3], -1)
        cv2.putText(self.canvas, "YELLOW", (520, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 2, cv2.LINE_AA)
    # ========================================================================================================  
    
    def display(self,mask):
        # Merge the canvas and the frame.
        self.frame = cv2.add(self.frame,self.canvas)
        cv2.imshow('frame',self.frame)
        cv2.imshow('canvas',self.canvas)
        cv2.imshow('mask',mask)
    
    def takeAction(self,k):
        # When c is pressed clear the entire canvas
        if k == ord('c'):
            self.canvas = None
        #press e to change between eraser mode and writing mode
        if (k==ord('e') and self.switch == 'Pen'):
            self.prevColor = self.colorIndex
            self.colorIndex = 4
            self.switch = 'Eraser'
        elif (k==ord('e') and self.switch == 'Eraser'):
            self.colorIndex = self.prevColor
            self.thicknes = 5
            self.switch = 'Pen'

                   
if __name__ == '__main__':
    drawingCanvas()
    
cv2.destroyAllWindows()