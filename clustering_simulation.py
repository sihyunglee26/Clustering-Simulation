import pygame
import random
import traffic            # traffic.py needs to be in the same directory
import report           # report.py needs to be in the same directory
'''
reference of pygame library: https://realpython.com/pygame-a-primer/
'''

'''
Import and define constants
'''
from pygame.locals import *     # Import all constants (e.g., "QUIT" for window-closing events)
TIME_ADDCAR = 200  # Add a new car every 200 milliseconds
TIME_MOVECAR = 80 # Move car every 80 milliseconds
TIME_BATCH = 20000  # Begin a new batch every 20,000 milliseconds
FRAME_PER_SECOND = 30 # screen update rate

'''
Initiate a PyGame, roads, and events
'''
pygame.init()
screen = pygame.display.set_mode([traffic.SCREEN_WIDTH, traffic.SCREEN_HEIGHT]) # Create a drawing sufrace
font_street_name = pygame.font.SysFont(None, traffic.LANE_WIDTH)

roads = []
roads.append(traffic.Road(pygame, "Street #1", font_street_name, 50,\
                          [traffic.TO_LEFT, traffic.TO_LEFT, traffic.TO_LEFT,\
                           traffic.TO_RIGHT, traffic.TO_RIGHT, traffic.TO_RIGHT]))
roads.append(traffic.Road(pygame, "Street #2", font_street_name, 220,\
                          [traffic.TO_LEFT, traffic.TO_LEFT,\
                           traffic.TO_RIGHT, traffic.TO_RIGHT]))

ADDCAR = pygame.USEREVENT + 1
pygame.time.set_timer(ADDCAR, TIME_ADDCAR)
MOVECAR = pygame.USEREVENT + 2
pygame.time.set_timer(MOVECAR, TIME_MOVECAR)

batch = report.Batch(pygame, 1, TIME_BATCH)
NEWBATCH = pygame.USEREVENT + 3
pygame.time.set_timer(NEWBATCH, TIME_BATCH)

clock = pygame.time.Clock()

'''
Main loop
'''
running = True
while running:
    '''
    Process events
    '''
    for event in pygame.event.get():
        if event.type == QUIT:   # If the user closes the window, terminate the program
            running = False        
            
        elif event.type == ADDCAR:  # Add a new car on a regular basis
            road = roads[random.randrange(0, len(roads))]
            road.add_car()            
                
        elif event.type == MOVECAR: # Move cars on a regular basis
            for road in roads:
                road.move(batch)            
            batch.process_reports()     # Process reports

        elif event.type == NEWBATCH: # Begin a new batch
            batch = report.Batch(pygame, batch.batch_num+1, TIME_BATCH)           
            
        elif event.type == MOUSEBUTTONUP: # Create an accident upon a mouse click
            x, y = pygame.mouse.get_pos()
            for road in roads:
                lane = road.find_lane_on_mouse_pos(x, y)
                if lane != None:
                    break                
            if lane != None:
                car = lane.find_nearest_car_to_mouse_pos(x, y)
                if car != None:
                    car.toggle_accident(batch)
                    batch.process_reports()     # Process reports
                else:
                    print("No car found on the lane")
            else:
                print("No lane found")
                
    '''
    Redraw screen
    '''
    screen.fill(traffic.SCREEN_COLOR)  # Fill the background with white        
    for road in roads:
        road.paint_on(screen)
    batch.paint_on(screen)
    pygame.display.flip()   # Display updates on the screen

    clock.tick(FRAME_PER_SECOND)  # Ensure that updates occur at the specified frames per second

pygame.quit()
