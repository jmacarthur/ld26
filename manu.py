import pygame
from pygame.locals import *
import random
import math
import array
from globs import *
from polylib import *
from mazegen import makeMaze, initMaze
import pygame.sndarray

class Player:
    def __init__(self):
        self.x = -(BS/2)
        self.y = -(BS/2)
        self.rot = 0
        self.speed = 0

class Follower:
    def __init__(self, player):
        self.x = player.x-128*math.cos(player.rot)
        self.y = player.y-128*math.sin(player.rot)

def init():
    global screen, clock, maze, shipPoly, player, speed, trailsBitmap, trailsX, trailsY, miniMap, numSprite, windscreenPoly, letterSprite, lightPoly, follower, idleSound, vanSound, vanStartSound, hornSound
    pygame.mixer.pre_init(frequency=8000,size=-16,channels=2)
    pygame.init()
    screen = pygame.display.set_mode((640,480))
    pygame.display.set_caption('Stop following me')
    clock = pygame.time.Clock()
    numSprite = pygame.image.load("data/numbers.gif")
    numSprite = pygame.transform.scale(numSprite, (numSprite.get_width()*3,numSprite.get_height()*3))
    numSprite.set_colorkey((255,255,255))
    letterSprite = pygame.image.load("data/letters.gif")
    letterSprite = pygame.transform.scale(letterSprite, (letterSprite.get_width()*3,letterSprite.get_height()*3))
    letterSprite.set_colorkey((255,255,255))
    maze = [0]*GS
    for i in range(0,GS): maze[i] = [0]*GS
    random.seed(2013)
    createMaze(maze)
    #shipPoly = [ (0,2), (2,-2), (0,-1), (-2,-2), (0,2) ]

    shipPoly = [ (1.7,2), (2,1.7), (2,-2), (-2,-2), (-2,1.7), (-1.7,2), (1.7,2) ]
    shipPoly = polyScale(shipPoly, 8)
    shipPoly = polyRotate(shipPoly, -math.pi/2 ) # Adjust so it faces to 0 radians

    windscreenPoly = [ (1.5,1.5), (1.5,1.0), (-1.5, 1.0), (-1.5,1.5) ]
    windscreenPoly = polyScale(windscreenPoly, 8)
    windscreenPoly = polyRotate(windscreenPoly, -math.pi/2)

    beamWidth = 2
    beamLength = 10
    lightPoly = [ (1.7,2), (1.7+beamWidth,2+beamLength), (1.7-beamWidth,2+beamLength), (1.7,2), (-1.7,2), (-1.7+beamWidth,2+beamLength), (-1.7-beamWidth,2+beamLength), (-1.7,2) ]
    lightPoly = polyScale(lightPoly, 8)
    lightPoly = polyRotate(lightPoly, -math.pi/2)

    player = Player()
    follower = Follower(player)

    trailsBitmap = pygame.Surface((640,480))
    trailsBitmap.fill(ROADCOLOUR)
    trailsX = 0
    trailsY = 0
    miniMap = pygame.Surface((64,64))
    drawMiniMap(miniMap, maze)
    idleSound = pygame.mixer.Sound("vanidle-8000.wav")
    vanSound = pygame.mixer.Sound("vannoise.wav")
    vanStartSound = pygame.mixer.Sound("vannoise-startup.wav")
    hornSound = pygame.mixer.Sound("horn8000.wav")
def drawMiniMap(surface, maze):
    surface.fill((0,0,0))
    for x in range(0,GS):
        for y in range(0,GS):
            if(maze[x][y]==1): 
                surface.set_at((x,y),(127,127,0))
            elif(maze[x][y]==2): 
                surface.set_at((x,y),(255,0,255))
            elif(maze[x][y]==3): 
                surface.set_at((x,y),(0,255,0))

def playerReset():
    global player
    player = Player()
    vanSound.stop()
    vanStartSound.play()

def createMaze(maze):
    for x in range(0,GS):
        for y in range(0,GS):
            maze[x][y] = 1
    initMaze()
    route = makeMaze(maze, 1,1,0)

    print "Route through maze: "
    print route
    global routeLen
    routeLen = len(route)
    print "Route length %d"%routeLen
    for (x,y) in route:
        maze[x][y] = 2
    (fx,fy) = route[0]
    maze[fx][fy] = 5

def getMaze(x,y):
    if(x<0 or x>= GS or y<0 or y>=GS): return 1
    return maze[x][y]

def makeTrail(x,y):
    pygame.draw.circle(trailsBitmap, (0,0,0), (int(x) % 640, int(y)%480), 2)

def dist((x1,y1), (x2,y2)):
    dx = x2-x1
    dy = y2-y1
    return math.sqrt(dx*dx+dy*dy)

def loop():
    global trailsX
    saveQueue = []
    saveDir = []
    frameCount = 0
    progress = 0
    repairBill = 0
    oldPos = []
    oldDir = []
    chaseVanX = 0
    chaseVanY = 0
    chaseVanD = 0
    flashTimeout = 0
    timeout = 150
    playerReset()
    hornTimeout = 0
    while 1:
        clock.tick(50)
        screen.fill((127,127,127))
        offX = int(320-player.x) % 640
        w = 640-offX
        offY = int(-240+player.y) % 480
        h = 480-offY
        screen.blit(trailsBitmap,(0,0), (w, offY, offX, h))
        screen.blit(trailsBitmap,(offX,0),(0,offY,w,h))

        screen.blit(trailsBitmap,(0,h),(w,0,640,512))
        screen.blit(trailsBitmap,(offX, h), (0,0, 640,512))

        dead = False
        shipRotPoly = polyRotate(shipPoly,player.rot)
        shipTransPoly = polyTranslate(shipRotPoly,320,240)
        

        for x in range(int(player.x/BS)-1,int(player.x/BS)+6):
            for y in range(int(player.y/BS)-1,int(player.y/BS)+5):
                if(getMaze(x,y) == 1):
                    pygame.draw.rect(screen, (255,255,255), (x*BS-player.x,y*BS-player.y,BS,BS))
                    if polyIntersectsBlock(shipTransPoly, x*BS-player.x,y*BS-player.y):
                        dead = True
                        expletive = random.choice(["DAMN", "OOPS"])
                        drawText(screen, 320+64, 240-64, expletive)
                elif(getMaze(x,y) == 2):
                    if (x,y) in saveQueue:
                        pygame.draw.circle(screen, (255,255,255), (int(x*BS-player.x+BS/2),int(y*BS-player.y+BS/2)),8)
                    else:
                        pygame.draw.circle(screen, (192,192,192), (int(x*BS-player.x+BS/2),int(y*BS-player.y+BS/2)),8)
                elif(getMaze(x,y) == 3):
                        pygame.draw.circle(screen, (0,255,0), (int(x*BS-player.x+BS/2),int(y*BS-player.y+BS/2)),8)
                elif(getMaze(x,y) == 4):
                        pygame.draw.circle(screen, (255,255,0), (int(x*BS-player.x+BS/2),int(y*BS-player.y+BS/2)),8)
                elif(getMaze(x,y) == 5):
                        pygame.draw.circle(screen, (0,255,0), (int(x*BS-player.x+BS/2),int(y*BS-player.y+BS/2)),16)

        #screen.blit(miniMap, (0,0))

        pygame.draw.polygon(screen, (255,255,255), shipTransPoly)

        wRotPoly = polyRotate(windscreenPoly, player.rot)
        wTransPoly = polyTranslate(wRotPoly, 320,240)
        pygame.draw.polygon(screen, (0,0,0), wTransPoly)

        if(len(oldPos)>10):
            (fx,fy) = oldPos.pop(0)
            d = oldDir.pop(0)
            chaseVanX = fx
            chaseVanY = fy
            chaseVanD = d
            
        shipRotPoly = polyRotate(shipPoly,chaseVanD)
        shipTransPoly = polyTranslate(shipRotPoly,320+chaseVanX-player.x,240+chaseVanY-player.y)
        pygame.draw.polygon(screen, (255,0,0), shipTransPoly)

        shipRotPoly = polyRotate(windscreenPoly,chaseVanD)
        shipTransPoly = polyTranslate(shipRotPoly,320+chaseVanX-player.x,240+chaseVanY-player.y)
        pygame.draw.polygon(screen, (0,0,0), shipTransPoly)


        flashTimeout -= 1
        if(flashTimeout<=4):
            lRotPoly = polyRotate(lightPoly, chaseVanD)
            lTransPoly = polyTranslate(lRotPoly, 320+chaseVanX-player.x,240+chaseVanY-player.y)
            pygame.draw.polygon(screen, (255,255,0), lTransPoly)
            if(flashTimeout <=0):
                flashTimeout = random.randint(0,400)

        hornTimeout -= 1
        if(hornTimeout<=0):
            hornSound.play()
            hornTimeout = random.randint(0,200)


        pygame.display.flip()
        if(dead):           
            playerReset()
            timeout = 120
            repairBill += 1
            if(len(saveQueue)>1):
                saveQueue.pop()
                saveDir.pop()
                (gridx,gridy) = saveQueue[-1]
                player.rot = saveDir[-1]
                player.x = gridx*BS+BS/2-320
                player.y = gridy*BS+BS/2-240


        keys = pygame.key.get_pressed()
        if(keys[K_LEFT]): player.rot -= TURNRATE
        if(keys[K_RIGHT]): player.rot += TURNRATE
        if(keys[K_s]): player.speed = 1 # cheat
        if(player.speed < MAXSPEED or keys[K_UP]):
            player.speed = player.speed + 0.02
        if(player.speed > MAXSPEED and not keys[K_UP]):
            player.speed -= 0.05

        dx = player.speed*math.cos(player.rot)
        dy = player.speed*math.sin(player.rot)
        makeTrail(player.x+8*math.cos(player.rot+math.pi/2),player.y+8*math.sin(player.rot+math.pi/2))
        makeTrail(player.x+8*math.cos(player.rot-math.pi/2),player.y+8*math.sin(player.rot-math.pi/2))
        pygame.draw.rect(trailsBitmap, ROADCOLOUR, (int(player.x+320-8)%640, 0, 8,480))
        pygame.draw.rect(trailsBitmap, ROADCOLOUR, (int(player.x-320)%640, 0, 8,480))
        pygame.draw.rect(trailsBitmap, ROADCOLOUR, (0,int(player.y+240-8)%480, 640,8))
        pygame.draw.rect(trailsBitmap, ROADCOLOUR, (0,int(player.y-240)%480, 640,8))
        if(player.x - (trailsX*256) > 256): trailsX+=1
        if(len(oldPos)<=0 or dist(oldPos[-1], (player.x, player.y)) > 5):
               oldPos.append((player.x,player.y))
               oldDir.append((player.rot))
        player.x += dx
        player.y += dy
        gridx = int((player.x+320) / BS)
        gridy = int((player.y+240) / BS)
        if(maze[gridx][gridy]==3):
            maze[gridx][gridy]=4
            progress += 1
            print "Progress: %d of %d (%d%%)"%(progress,routeLen,int(100*progress/routeLen))
        elif(maze[gridx][gridy]==2):
            if((gridx,gridy) not in saveQueue):
                saveQueue.append((gridx,gridy))
                saveDir.append(player.rot)
        if(maze[gridx][gridy]==5 or keys[K_w]):
            print "Game complete!"
            print "You finished the game in %f seconds"%(frameCount / 50.0)
            print "Van repair bill: %d quid"%(repairBill*50)
            return (frameCount, repairBill)
        frameCount += 1
        if(timeout > 0):
            timeout -= 1
            if(timeout == 0):
                vanSound.play(loops=-1)

        for event in pygame.event.get():
            if event.type == QUIT:
                exit(0)
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE or event.key == K_q:
                    exit(0)

def titleScreen():
    titlescreen = pygame.image.load("data/titlescreen.gif")
    while 1:
        screen.blit(titlescreen, (0,0))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == QUIT:
                exit(0)
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE or event.key == K_q:
                    exit(0)
                elif event.key == K_SPACE:
                    return 0
                elif event.key == K_s:
                    return 1

def drawChar(surface, x, y, c):
    pos = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ".find(c)+1
    surface.blit(letterSprite, (x,y), (pos*FONTSCALE*3,0,FONTSCALE*3,5*FONTSCALE))
   

def drawText(surface, x, y, string):
    if(len(string)==0):
        return
    c = string[0]
    drawChar(surface, x, y, c)
    x+=4*FONTSCALE
    drawText(surface, x, y, string[1:])


def drawDigit(surface, x, y, d):
    surface.blit(numSprite, (x,y), (d*3*3,0,3*3,5*3))

def drawNumber(surface, x, y, num):
    if(num==0):
        drawDigit(surface,x,y,0)
        return x-(3*3+2)
    while(num > 0):
        d = num % 10
        drawDigit(surface, x, y, d)
        x -= (3*3+2)
        num = int(num / 10)
    return x
        

def winScreen(frames,repair):
    titlescreen = pygame.image.load("data/winscreen.gif")
    titlescreen = pygame.transform.scale(titlescreen, (640,480))
    while 1:
        screen.blit(titlescreen, (0,0,640,480))

        drawNumber(screen,550,220,int(frames/50))

        xpos = drawNumber(screen,600,300,repair*50)
        drawDigit(screen, xpos, 300, 10)

        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == QUIT:
                exit(0)
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE or event.key == K_q:
                    exit(0)
                elif event.key == K_SPACE:
                    return

def infoScreen():
    infoscreen = pygame.image.load("data/infoscreen.gif")
    infoscreen = pygame.transform.scale(infoscreen, (640,480))
    while 1:
        screen.blit(infoscreen, (0,0,640,480))
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == QUIT:
                exit(0)
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE or event.key == K_q:
                    exit(0)
                elif event.key == K_SPACE:
                    return


init()
while 1:
    playerReset()
    idleSound.play(loops=-1)
    while(titleScreen()==1):
        infoScreen()    
    idleSound.stop()
    vanSound.stop()
    (frames, repair) = loop()
    vanSound.stop()
    winScreen(frames, repair)
