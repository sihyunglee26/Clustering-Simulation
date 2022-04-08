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
TIME_ADDCAR = 200  # Add a new car every 200 ms
TIME_MOVECAR = 80 # Move car every 80 ms
TIME_CHANGE_SIGNAL = 5000 # Change traffic signal bettwen RED and GREEN every 5,000 ms
TIME_AMBER_SIGNAL = 1000
TIME_BATCH = 20000  # Begin a new batch every 20,000 ms
FRAME_PER_SECOND = 30 # screen update rate

'''
Initiate a PyGame, roads, and events
'''
pygame.init()
screen = pygame.display.set_mode([traffic.SCREEN_WIDTH, traffic.SCREEN_HEIGHT]) # Create a drawing sufrace
font_street_name = pygame.font.SysFont(None, traffic.LANE_WIDTH)

'''
Add or modify roads here
'''
# Scenario 1 - two wide streets
roads = []
roads.append(traffic.Road(pygame, "Street #1", font_street_name, 100,\
                          traffic.HORIZONTAL, [4,4]))
roads.append(traffic.Road(pygame, "Street #2", font_street_name, 350,\
                          traffic.VERTICAL, [4,4]))

# Scenario 2 - four streets
'''
roads.append(traffic.Road(pygame, "Street #1", font_street_name, 100,\
                          traffic.HORIZONTAL, [3,3]))
roads.append(traffic.Road(pygame, "Street #2", font_street_name, 700,\
                          traffic.VERTICAL, [2,2]))
roads.append(traffic.Road(pygame, "Street #3", font_street_name, 300,\
                          traffic.VERTICAL, [2,2]))
roads.append(traffic.Road(pygame, "Street #4", font_street_name, 350,\
                          traffic.HORIZONTAL, [1,1]))
'''

traffic.find_overlaps(roads)            # Sanity check
intersections = traffic.add_intersections(roads)
traffic.find_lanes_for_new_cars(roads)

ADDCAR = pygame.USEREVENT + 1
pygame.time.set_timer(ADDCAR, TIME_ADDCAR)
MOVECAR = pygame.USEREVENT + 2
pygame.time.set_timer(MOVECAR, TIME_MOVECAR)

CHANGE_SIGNAL = pygame.USEREVENT + 3
max_signal_count = int(TIME_CHANGE_SIGNAL / TIME_AMBER_SIGNAL)
pygame.time.set_timer(CHANGE_SIGNAL, int(TIME_CHANGE_SIGNAL/max_signal_count))
signal_count = 0

batch = report.Batch(pygame, 1, TIME_BATCH) # Create the first batch instance
NEWBATCH = pygame.USEREVENT + 4
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
            road.add_newCar()       
                
        elif event.type == MOVECAR: # Move cars on a regular basis            
            for road in roads:
                road.move(batch)
            batch.process_reports()     # Process reports            
            
        elif event.type == CHANGE_SIGNAL: # Change traffic signal at intersections
            signal_count = (signal_count + 1) % max_signal_count
            if signal_count == max_signal_count - 1:
                for it in intersections:
                    # Disallow entrance to all lanes during AMBER period
                    for lane in it.signal_group[it.current_signal]:
                        lane.trafficLight = traffic.REDLIGHT
            elif signal_count == 0: 
                for it in intersections:                
                    it.current_signal = (it.current_signal + 1) % len(it.signal_group)
                    # Allow entrance to lanes with GREEN light
                    for lane in it.signal_group[it.current_signal]:
                        lane.trafficLight = traffic.GO

        elif event.type == NEWBATCH: # Begin a new batch
            batch = report.Batch(pygame, batch.batch_num+1, TIME_BATCH)           
            
        elif event.type == MOUSEBUTTONUP: # Create/release an accident upon a mouse click
            x, y = pygame.mouse.get_pos()
            car = traffic.find_car_nearest_to_mouse_pos(roads, x, y)
            if car != None:
                car.toggle_accident(batch)
                batch.process_reports()     # Process reports
            else:
                print("No car found on the lane at mouse position")
                
    '''
    Redraw screen
    '''
    screen.fill(traffic.SCREEN_COLOR)  # Fill the background with white        
    for road in roads:
        road.paint_on(screen)
    for road in roads:
        road.paint_cars_on(screen)    
    batch.paint_on(screen)
    pygame.display.flip()   # Display updates on the screen
    
    clock.tick(FRAME_PER_SECOND)  # Ensure that updates occur at the specified frames per second

pygame.quit()
