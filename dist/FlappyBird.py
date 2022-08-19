import pygame
import random
from cmath import sqrt
import cv2
import time
import os
import mediapipe as mp
cap = cv2.VideoCapture(0)
class handDetector():
    def __init__(self, mode=False, maxHands=2, detectionCon=0.5, trackCon=0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(self.mode, self.maxHands,
                                        self.detectionCon, self.trackCon)
        self.mpDraw = mp.solutions.drawing_utils

    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        # print(results.multi_hand_landmarks)

        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms,
                                               self.mpHands.HAND_CONNECTIONS)
        return img

    def findPosition(self, img, handNo=0, draw=True):

        lmList = []
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]
            for id, lm in enumerate(myHand.landmark):
                # print(id, lm)
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                # print(id, cx, cy)
                lmList.append([id, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)

        return lmList

detector = handDetector(detectionCon=1)

def Distance(a,b):
    x = a[1] - b[1]
    y = a[2] - b[2]
    return sqrt(x*x + y*y )
click = False
pygame.init()
# value
scaleScreen = [400,700]
yFloor = 100
xFloor = 0
clock = pygame.time.Clock()
speed = 5
scaleBird = [50,50]
posBird = [100,100]
birdIndex = 0
distanceY = 200
distanceX = 250
gravity = 0.7
birdMovement = 0
birdJump = 8
scaleTube = 50
score = 0
checkScore = [0,0,0]
game_font = pygame.font.Font('04B_19.ttf',35)
state = "home"
die = False
running = True
# create display
screen = pygame.display.set_mode((scaleScreen[0],scaleScreen[1]))
pygame.display.set_caption(":)")
# load images
background = pygame.transform.scale(pygame.image.load("assets/background-night.png"),(scaleScreen[0],scaleScreen[1] - yFloor))
floor = pygame.transform.scale(pygame.image.load("assets/floor.png"),(scaleScreen[0],yFloor))
bird_up = pygame.transform.scale(pygame.image.load("assets/yellowbird-upflap.png"),(scaleBird[0],scaleBird[1]))
bird_mid = pygame.transform.scale(pygame.image.load("assets/yellowbird-midflap.png"),(scaleBird[0],scaleBird[1]))
bird_down = pygame.transform.scale(pygame.image.load("assets/yellowbird-downflap.png"),(scaleBird[0],scaleBird[1]))
tube = []
tube_up = []
xTube = []
for i in range(3):
    x = random.randint(50,350)
    xTube.append(distanceX*(i+3))
    tube.append(pygame.transform.scale(pygame.image.load("assets/pipe-green.png"),(scaleTube,x)))
    tube_up.append(pygame.transform.scale(pygame.image.load("assets/pipe-green.png"),(scaleTube,scaleScreen[1] - x - distanceY - yFloor)))
    tube[i] = pygame.transform.rotate(tube[i],180)
bird = [bird_up,bird_mid,bird_down]
# function
def drawFloor():
    global xFloor
    screen.blit(floor,(xFloor,scaleScreen[1] - yFloor))
    screen.blit(floor,(xFloor + scaleScreen[0],scaleScreen[1] - yFloor))
    if xFloor <= -scaleScreen[0]:
        xFloor = 0
    xFloor -= speed
def drawBird():
    screen.blit(bird[birdIndex],(posBird[0],posBird[1]))
def gravityBird():
    global birdMovement
    birdMovement += gravity
    posBird[1] += birdMovement
def moveBird():
    global birdMovement
    birdMovement = 0
    birdMovement = -birdJump
def drawTube():
    global xTube,score
    for i in range(3):
        screen.blit(tube[i],(xTube[i],0))
        screen.blit(tube_up[i],(xTube[i],tube[i].get_height() + distanceY))
        xTube[i] -= speed
        if checkScore[i] == 0 and xTube[i] + 50 <= posBird[0]:
            checkScore[i] = 1
            score += 1
            score_sound.play()
        if (xTube[i] <= - scaleTube):
            x = random.randint(50,350)
            yRandom = random.randint(50,350)
            tube[i] = pygame.transform.scale(tube[i],(scaleTube,yRandom))
            tube_up[i] = pygame.transform.scale(tube_up[i],(scaleTube,scaleScreen[1] - yFloor - distanceY - yRandom))
            xTube[i] = 3*distanceX - scaleTube
            checkScore[i] = 0
        if posBird[0] + 50 >= xTube[i] and posBird[0] <= xTube[i] + 50:
            if (posBird[1] <= tube[i].get_height()) or posBird[1] >= tube[i].get_height() + distanceY:
                if state == "play":
                    gameOver()
        if posBird[1] <= 0 or posBird[1] >= 600:
            if state == "play":
                gameOver()
def scoreFlappybird():
    score_surface = game_font.render(f'Score: {int(score)}',True,(255,255,255))
    score_rect = score_surface.get_rect(center = (216,100))
    screen.blit(score_surface,score_rect)
def gameOver():
    global state,gravity,birdMovement,speed,die
    state = "game over"
    hit_sound.play()
    die = True
    gravity = 0
    birdMovement = 0
    speed = 0
# create timer
birdflap = pygame.USEREVENT
pygame.time.set_timer(birdflap,200)
e = 0
flap_sound = pygame.mixer.Sound('sound/sfx_wing.wav')
hit_sound = pygame.mixer.Sound('sound/sfx_hit.wav')
score_sound = pygame.mixer.Sound('sound/sfx_point.wav')
while running:
    clock.tick(120)
    ret , frame = cap.read()
    f = detector.findHands(frame)
    lmList = detector.findPosition(f,draw=False)
    if len(lmList) != 0:
        if Distance(lmList[4],lmList[8]).real < 25 and state == "play":
            if click == False:
                click = True
                moveBird()
                flap_sound.play()
        else:
            click = False
    cv2.imshow("Hello",frame)
    if cv2.waitKey(1) == ord("q"):
        break
    if state == "home":
        screen.blit(pygame.transform.scale(pygame.image.load("assets/message.png"),(scaleScreen[0],scaleScreen[1])),(0,0))
    else:
        screen.blit(background,(0,0))
        drawFloor()
        gravityBird()
        drawTube()
        scoreFlappybird()
        drawBird()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if state == "home":
                state = "play"
            if event.key == pygame.K_SPACE:
                if state == "play":
                    moveBird()
                    flap_sound.play()
                elif state == "game over" and posBird[1] == scaleScreen[1] - yFloor - 50: 
                    posBird = [100,100]
                    
                    distanceY = 200
                    distanceX = 250
                    gravity = 0.7
                    speed = 5
                    bird[birdIndex] = pygame.transform.rotate(bird[birdIndex],(90))
                    birdMovement = 0
                    birdIndex = 0
                    score = 0
                    die = False
                    e = 0
                    for i in range(3):
                        xTube[i] = distanceX*(i+3)
                    state = "play"
        if event.type == birdflap and state == "play":
            if birdIndex < 2:
                birdIndex += 1
            else:
                birdIndex = 0
    if die == True:
        if e == 0:
            bird[birdIndex] = pygame.transform.rotate(bird[birdIndex],(-90))
            e = 1
        if posBird[1] < scaleScreen[1] - yFloor -50:
            posBird[1] += 7
        else:
            posBird[1] = scaleScreen[1] - yFloor - 50
            screen.blit(pygame.transform.scale(pygame.image.load("assets/gameover.png"),(400,100)),(0,300))
    pygame.display.flip()
pygame.quit()
cap.release()
cv2.destroyAllWindows()