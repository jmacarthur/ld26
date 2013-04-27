import random

def initMaze():
    global maxdist
    maxdist = 0

def makeMaze(grid, sx, sy, distance):
    global maxdist
    width = len(grid)
    height = len(grid[0])

    dx = [ 1, 0, -1 , 0 ]
    dy = [ 0, -1, 0, 1 ]
    if(distance > maxdist):
        maxdist = distance
        print "Longest path so far = %d"%maxdist
    d = random.choice([0,1,2,3])
    routes = []
    for t in range(0,4):
        tx = sx + dx[(d+t)%4]*2
        ty = sy + dy[(d+t)%4]*2
        if(tx > 0 and ty > 0 and tx < width and ty < width):
            if(grid[tx][ty] == 1):
                td = (d+t)%4
                grid[sx+dx[td]][sy+dy[td]] = 0
                grid[tx][ty] = 0
                routes.append(makeMaze(grid,tx,ty,distance+2))
    maxroute = 0
    route = []
    for r in routes:
        if(len(r)>maxroute):
            route = r
            maxroute = r
    route.append((sx,sy))
    return route
    

    
    
    
