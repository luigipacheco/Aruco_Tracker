import numpy as np
import cv2
import cv2.aruco as aruco
import glob
import serial
import time
import sys
import random as rnd

# checkerboard Dimensions
cbrow = 6 #cvcol orig 6
cbcol = 9 #cvrow  orig 7

centerx= 320
centery = 240
tolerance =10
res = 1

cap = cv2.VideoCapture(1)
# termination criteria
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((cbrow*cbcol,3), np.float32)
objp[:,:2] = np.mgrid[0:cbcol,0:cbrow].T.reshape(-1,2)

# Arrays to store object points and image points from all the images.
objpoints = [] # 3d point in real world space
imgpoints = [] # 2d points in image plane.

images = glob.glob('calib_images/*.jpg')

for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

    # Find the chess board corners
    ret, corners = cv2.findChessboardCorners(gray, (cbcol,cbrow),None)

    # If found, add object points, image points (after refining them)
    if ret == True:
        objpoints.append(objp)
        corners2 = cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),criteria)
        imgpoints.append(corners2)

        # Draw and display the corners
        img = cv2.drawChessboardCorners(img, (cbcol,cbrow), corners2,ret)


ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1],None,None)

moveX = centerx
moveY = centery
while (True):
    ret, frame = cap.read()
    # operations on the frame come here
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    aruco_dict = aruco.Dictionary_get(aruco.DICT_ARUCO_ORIGINAL )
    parameters = aruco.DetectorParameters_create()

    #lists of ids and the corners beloning to each id
    corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)


    font = cv2.FONT_HERSHEY_SIMPLEX #font for displaying text (below)


    if np.all(ids != None):

        rvec, tvec ,_ = aruco.estimatePoseSingleMarkers(corners, 0.05, mtx, dist) #Estimate pose of each marker and return the values rvet and tvec---different from camera coefficients
        #(rvec-tvec).any() # get rid of that nasty numpy value array error

        for i in range(0, ids.size):
            aruco.drawAxis(frame, mtx, dist, rvec[i], tvec[i],0.02)  # Draw Axis
        aruco.drawDetectedMarkers(frame, corners) #Draw A square around the markers
        print("vector is " )
        print(tvec[i][0][0])


        avgx = int((corners[0][0][0][0]+corners[0][0][1][0]+corners[0][0][2][0]+corners[0][0][3][0])/4)  #use central cordinates from aruco
        avgy = int((corners[0][0][0][1] + corners[0][0][1][1] + corners[0][0][2][1] + corners[0][0][3][1]) / 4) #use central cordinates from aruco

        # if avgx < (centerx - tolerance):
        #     moveX= int((centerx-avgx/res)+ avgx)
        # elif avgx > (centerx - tolerance):
        #     moveX= int(((avgx-centerx)/res) + centerx)

        #avgx = int((corners[0][0][0][0] + corners[0][0][1][0] + corners[0][0][2][0] + corners[0][0][3][0]) / 4)
        # print(avgx,",",avgy)

        if tvec[i][0][0] < (0 - tolerance):
            moveX= int((centerx-avgx/res)+ avgx)
        elif tvec[i][0][0] > (centerx - tolerance):
            moveX= int(((avgx-centerx)/res) + centerx)

        # avgx = int((corners[0][0][0][0] + corners[0][0][1][0] + corners[0][0][2][0] + corners[0][0][3][0]) / 4)
        # print(avgx,",",avgy)

        data = "X{0:d}Y{1:d}".format(avgx, avgy)
        # print("output = '" + data + "'")

        ###### DRAW ID #####
        strg = ''
        for i in range(0, ids.size):
            strg += str(ids[i][0])+', '

        cv2.putText(frame, "Id: " + strg, (0,64), font, 1, (0,255,0),2,cv2.LINE_AA)


    else:
        ##### DRAW "NO IDS" #####
        cv2.putText(frame, "No Ids", (0,64), font, 1, (0,255,0),2,cv2.LINE_AA)
        moveX= centerx
        moveY= centery
        data = "X{0:d}Y{1:d}".format(moveX, moveY)
        print("output = '" + data + "'")
        arduino.write(data.encode())

    # Display the resulting frame
    cv2.imshow('frame',frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()