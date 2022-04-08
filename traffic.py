import pygame
import random
import itertools
import report
import math

'''
Define constants
'''
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 500
SCREEN_COLOR = (0, 0, 0) # Black
LANE_WIDTH = 19
LANE_COLOR = (220, 220, 220) # Gray
LANE_NAME_COLOR = (255, 255, 255) # White

HORIZONTAL = 1
VERTICAL = 2
TO_LEFT = 3
TO_RIGHT= 4
TO_BOTTOM = 5
TO_TOP = 6

GO = 100
REDLIGHT = 101  # Red light
BLOCKED = 102   # Preceding car is near

CAR_WIDTH = 10
CAR_LENGTH = 20
CAR_COLOR = (50, 200, 50) # Greenish
CAR_COLOR_ACCIDENT = (200, 50, 50) # Redish
CAR_COLOR_VAR = 50
CAR_SPEED = 10
CAR_SPEED_VAR = 3
CAR_SAFE_DISTANCE = CAR_LENGTH * 1.5
CAR_CHANGE_LANE_RATE_BLOCKED = 0.2  # Rate of chaining lanes when blocked


'''
Defind a Road object
'''
class Road():
    '''
    Constructor of a Road object
    orientation: HORIZONTAL or VERTICAL
    num_lanes: # of to-left and to-right lanes for a HORIZONTAL road
                            # of to-bottom and to-top lanes for a VERTICAL road
    position: top y coordinate for a horizontal road
                     left x coordinate for a vertical road
    '''
    def __init__(self, pygame, name, font, position, orientation, num_lanes):
        self.pygame = pygame
        self.name = font.render(name, True, LANE_NAME_COLOR)
        self.name_str = name
        self.position = position
        self.intersections = []
        self.lanes_for_new_cars = []
        
        if orientation != HORIZONTAL and orientation != VERTICAL:
            raise ValueError('Illegal orientation is used')
        self.orientation = orientation

        # Sanity check for num_lanes
        if len(num_lanes) != 2:
            raise ValueError('num_lanes requires two integers')
        if num_lanes[0]<0 or num_lanes[1]<0:
            raise ValueError('num_lanes requires two integers >=0')
        if (num_lanes[0]==0 and num_lanes[1]==0):
            raise ValueError('At least one element of num_lanes must be >0')

        # Add lanes
        self.lanes = []        
        if self.orientation == HORIZONTAL:
            for idx in range(num_lanes[0]):
                self.lanes.append(Lane(pygame, TO_LEFT, position + (self.name.get_height() + 2) + idx * (LANE_WIDTH+1), self))
            for idx in range(num_lanes[1]):
                self.lanes.append(Lane(pygame, TO_RIGHT, position + (self.name.get_height() + 2) + (idx+num_lanes[0]) * (LANE_WIDTH+1), self))
        elif self.orientation == VERTICAL:
            for idx in range(num_lanes[0]):
                self.lanes.append(Lane(pygame, TO_BOTTOM, position + (self.name.get_width() + 2) + idx * (LANE_WIDTH+1), self))
            for idx in range(num_lanes[1]):
                self.lanes.append(Lane(pygame, TO_TOP, position + (self.name.get_width() + 2) + (idx+num_lanes[1]) * (LANE_WIDTH+1), self))  

        configure_lanes_before_after(self.lanes)
        
    def add_newCar(self):
        if len(self.lanes_for_new_cars) == 1:
            self.lanes_for_new_cars[0].add_newCar()
        elif len(self.lanes_for_new_cars) > 1:
            lane = self.lanes_for_new_cars[random.randrange(0, len(self.lanes_for_new_cars))]
            lane.add_newCar()
        
    def paint_on(self, screen):        
        for lane in self.lanes:
            lane.paint_on(screen)
        if self.orientation == HORIZONTAL:
            screen.blit(self.name, (0, self.position))
        elif self.orientation == VERTICAL:
            screen.blit(self.name, (self.position, 20))

    def paint_cars_on(self, screen):
        for lane in self.lanes:
            lane.paint_cars_on(screen)
            
    def move(self, batch):
        for lane in self.lanes:
            lane.move(batch)

    def find_lanes_on_mouse_pos(self, x, y):
        lanes = []
        for lane in self.lanes:
            if lane.include_pos(x, y):
                lanes.append(lane)
        return lanes

    def on_the_same_road_with(self, road):
        if isinstance(road, Road):
            return self == road
        elif isinstance(road, Intersection):
            for r in road.roads:
                if self == r:
                    return True
            return False
        else:
            return False
        
    def intersect(self, road):
        if self.orientation == HORIZONTAL and road.orientation == VERTICAL:
            return self, road
        elif self.orientation == VERTICAL and road.orientation == HORIZONTAL:
            return road, self
        return None

    def overlap(self, road):
        if self.orientation == HORIZONTAL and road.orientation == HORIZONTAL:
            max_top = max(self.position, road.position)            
            min_bottom = min(self.lanes[-1].rect.bottom, road.lanes[-1].rect.bottom)
            if max_top <= min_bottom:
                return True
        elif self.orientation == VERTICAL and road.orientation == VERTICAL:
            max_left = max(self.position, road.position)            
            min_right = min(self.lanes[-1].rect.right, road.lanes[-1].rect.right)
            if max_left <= min_right:
                return True            
        return False
    
'''
For each pair of roads with same orientation,
                    check to see whether they overlap
'''
def find_overlaps(roads):
    comb = itertools.combinations(roads, 2)
    for pair in comb:
        if pair[0].overlap(pair[1]):
            raise ValueError(pair[0].name_str + ' and ' + pair[1].name_str + ' overlap') 

'''
Find lanes where new cars can be added
'''
def find_lanes_for_new_cars(roads):
    for road in roads:
        if isinstance(road, Intersection):            
            continue
        
        road.lanes_for_new_cars.clear()
        for lane in road.lanes:
            if (lane.direction == TO_LEFT and lane.rect.right == SCREEN_WIDTH) or\
                (lane.direction == TO_RIGHT and lane.rect.left == 0) or\
                (lane.direction == TO_BOTTOM and lane.rect.top == 0) or\
                (lane.direction == TO_TOP and lane.rect.bottom == SCREEN_HEIGHT):
                road.lanes_for_new_cars.append(lane)

    
'''
Define a Lane object
'''
class Lane():
    '''
    Constructor of a Lane object
    position: top y coordinate for a horizontal lane
                     left x coordinate for a vertical lane
    '''
    def __init__(self, pygame, direction, position, road):
        self.pygame = pygame

        # Position the lane and get its Rectangle object
        self.direction = direction
        self.position = position
        self.center = position + LANE_WIDTH/2
        if self.direction == TO_LEFT or self.direction == TO_RIGHT:
            self.surf = pygame.Surface((SCREEN_WIDTH, LANE_WIDTH))  # X/Y size
            self.rect = self.surf.get_rect(center=(SCREEN_WIDTH/2, self.center))            
        elif self.direction == TO_BOTTOM or self.direction == TO_TOP:
            self.surf = pygame.Surface((LANE_WIDTH, SCREEN_HEIGHT))  # X/Y size
            self.rect = self.surf.get_rect(center=(self.center, SCREEN_HEIGHT/2))            
        self.surf.fill(LANE_COLOR)

        self.road = road
        self.cars = []
        self.before = None
        self.after = None
        self.next = []      # connected lanes
        self.trafficLight = GO

        self.blocking_lanes = []                 # Other lanes that cross (thus possibly block) this lane

    def update_size(self, left, top, width, height):
        self.rect.update(left, top, width, height)
        self.surf = pygame.transform.scale(self.surf, (width, height))        
    
    def add_newCar(self):
        if self.direction == TO_LEFT and self.rect.right == SCREEN_WIDTH:
            if (len(self.cars) == 0) or (self.cars[-1].rect.right < self.rect.right - CAR_SAFE_DISTANCE):
                self.cars.append(Car(self.pygame, self.road, self, self.rect.right - CAR_LENGTH/2, self.center))
        elif self.direction == TO_RIGHT and self.rect.left == 0:
            if (len(self.cars) == 0) or (self.cars[-1].rect.left > self.rect.left + CAR_SAFE_DISTANCE):
                self.cars.append(Car(self.pygame, self.road, self, self.rect.left + CAR_LENGTH/2, self.center))
        elif self.direction == TO_BOTTOM and self.rect.top == 0:
            if (len(self.cars) == 0) or (self.cars[-1].rect.top > self.rect.top + CAR_SAFE_DISTANCE):
                self.cars.append(Car(self.pygame, self.road, self, self.center, self.rect.top + CAR_LENGTH/2))                                      
        elif self.direction == TO_TOP and self.rect.bottom == SCREEN_HEIGHT:
            if (len(self.cars) == 0) or (self.cars[-1].rect.bottom < self.rect.bottom - CAR_SAFE_DISTANCE):
                self.cars.append(Car(self.pygame, self.road, self, self.center, self.rect.bottom - CAR_LENGTH/2))
         
    def paint_on(self, screen):
        screen.blit(self.surf, self.rect)        

    def paint_cars_on(self, screen):
        for car in self.cars:
            # Adjust each car's center to the lane's center, as the car might have changed lanes
            if self.direction == TO_LEFT or self.direction == TO_RIGHT:
                car.rect.centery = self.center      
            elif self.direction == TO_BOTTOM or self.direction == TO_TOP:
                car.rect.centerx = self.center
            car.paint_on(screen)
            
    def move(self, batch):
        # Initialize position of preceding car for keeping a safe distance between consecutive cars
        if self.direction == TO_LEFT:
            self.x_preceding_car = self.rect.left - (CAR_SAFE_DISTANCE * 2)            
        elif self.direction == TO_RIGHT:
            self.x_preceding_car = self.rect.right + (CAR_SAFE_DISTANCE * 2)
        elif self.direction == TO_BOTTOM:
            self.y_preceding_car = self.rect.bottom + (CAR_SAFE_DISTANCE * 2)
        elif self.direction == TO_TOP:
            self.y_preceding_car = self.rect.top - (CAR_SAFE_DISTANCE * 2)            

        self.status_preceding_car = GO
        
        # Move each car on the lane
        self.cars = [car for car in self.cars if car.move(batch)]        # Only cars visible on the screen remain in the list

    '''
    Return (True, idx) if car can be inserted into this lane's cars[idx]
    Otherwise, return (False, None)
    '''
    def can_change_lane(self, car, add):
        safe_distance = CAR_SAFE_DISTANCE * 2
        
        if self.direction == TO_LEFT:
            # Check to see if cars on this lane blocks entrance
            id_nearest_car = self.find_nearest_car_to_left(car, 0, len(self.cars)-1)
            if ( (id_nearest_car >= 0) and (car.rect.left < self.cars[id_nearest_car].rect.right + safe_distance) ) or\
               ( (id_nearest_car+1 < len(self.cars)) and (self.cars[id_nearest_car+1].rect.left - safe_distance < car.rect.right)):
                return False, None
            
            # Check to see if cars on lanes that cross this lane blocks entrance
            for blocking_lane in self.blocking_lanes:
                for c in blocking_lane.cars:
                    if self.include_car(c) and not car.outside_safe_distance_from(c, safe_distance, self.direction):
                        return False, None

            # Check to see if cars on this lane's next lane blocks entrance        
            if car.rect.left - car.speed <= self.rect.left + safe_distance:
                for next_lane in self.next:
                    if next_lane.trafficLight == REDLIGHT and car.rect.left < next_lane.rect.right + safe_distance:
                        return False, None
                    if len(next_lane.cars) > 0 and car.rect.left < next_lane.cars[-1].rect.right + safe_distance:
                        return False, None
                    for blocking_lane in next_lane.blocking_lanes:
                        for c in blocking_lane.cars:
                            if next_lane.include_car(c) and car.rect.left < c.rect.right + safe_distance:
                                return False, None

            return True, id_nearest_car+1
        
        elif self.direction == TO_RIGHT:
            # Check to see if cars on this lane blocks entrance
            id_nearest_car = self.find_nearest_car_to_right(car, 0, len(self.cars)-1)
            if ( (id_nearest_car >= 0) and (self.cars[id_nearest_car].rect.left - safe_distance < car.rect.right ) ) or\
               ( (id_nearest_car+1 < len(self.cars)) and (car.rect.left < self.cars[id_nearest_car+1].rect.right + safe_distance)):
                return False, None

            # Check to see if cars on lanes that cross this lane blocks entrance
            for blocking_lane in self.blocking_lanes:
                for c in blocking_lane.cars:
                    if self.include_car(c) and not car.outside_safe_distance_from(c, safe_distance, self.direction):
                        return False, None

            # Check to see if cars on this lane's next lane blocks entrance                
            if self.rect.right - safe_distance <= car.rect.right + car.speed:
                for next_lane in self.next:
                    if next_lane.trafficLight == REDLIGHT and next_lane.rect.left - safe_distance < car.rect.right:
                        return False, None
                    if len(next_lane.cars) > 0 and next_lane.cars[-1].rect.left - safe_distance < car.rect.right:
                        return False, None
                    for blocking_lane in next_lane.blocking_lanes:
                        for c in blocking_lane.cars:
                            if next_lane.include_car(c) and c.rect.left - safe_distance < car.rect.right:
                                return False, None

            return True, id_nearest_car+1
                
        elif self.direction == TO_BOTTOM:
            # Check to see if cars on this lane blocks entrance
            id_nearest_car = self.find_nearest_car_to_bottom(car, 0, len(self.cars)-1)
            if ( (id_nearest_car >= 0) and (self.cars[id_nearest_car].rect.top - safe_distance < car.rect.bottom ) ) or\
               ( (id_nearest_car+1 < len(self.cars)) and (car.rect.top < self.cars[id_nearest_car+1].rect.bottom + safe_distance)):
                return False, None

            # Check to see if cars on lanes that cross this lane blocks entrance
            for blocking_lane in self.blocking_lanes:
                for c in blocking_lane.cars:
                    if self.include_car(c) and not car.outside_safe_distance_from(c, safe_distance, self.direction):
                        return False, None

            # Check to see if cars on this lane's next lane blocks entrance                  
            if self.rect.bottom - safe_distance <= car.rect.bottom + car.speed:
                for next_lane in self.next:
                    if next_lane.trafficLight == REDLIGHT and next_lane.rect.top - safe_distance < car.rect.bottom:
                        return False, None
                    if len(next_lane.cars) > 0 and next_lane.cars[-1].rect.top - safe_distance < car.rect.bottom:
                        return False, None
                    for blocking_lane in next_lane.blocking_lanes:
                        for c in blocking_lane.cars:
                            if next_lane.include_car(c) and c.rect.top - safe_distance < car.rect.bottom:
                                return False, None

            return True, id_nearest_car+1
        
        elif self.direction == TO_TOP:
            # Check to see if cars on this lane blocks entrance
            id_nearest_car = self.find_nearest_car_to_top(car, 0, len(self.cars)-1)
            if ( (id_nearest_car >= 0) and (car.rect.top < self.cars[id_nearest_car].rect.bottom + safe_distance) ) or\
               ( (id_nearest_car+1 < len(self.cars)) and (self.cars[id_nearest_car+1].rect.top - safe_distance < car.rect.bottom)):
                return False, None

            # Check to see if cars on lanes that cross this lane blocks entrance
            for blocking_lane in self.blocking_lanes:
                for c in blocking_lane.cars:
                    if self.include_car(c) and not car.outside_safe_distance_from(c, safe_distance, self.direction):
                        return False, None
                    
            # Check to see if cars on this lane's next lane blocks entrance                            
            if car.rect.top - car.speed <= self.rect.top + safe_distance:
                for next_lane in self.next:
                    if next_lane.trafficLight == REDLIGHT and car.rect.top < next_lane.rect.bottom + safe_distance:
                        return False, None
                    if len(next_lane.cars) > 0 and car.rect.top < next_lane.cars[-1].rect.bottom + safe_distance:
                        return False, None
                    for blocking_lane in next_lane.blocking_lanes:
                        for c in blocking_lane.cars:
                            if next_lane.include_car(c) and car.rect.top < c.rect.bottom + safe_distance:
                                return False, None

            return True, id_nearest_car+1        
        
    def find_nearest_car_to_left(self, car, id_left, id_right):         # Perform binary search to find the nearest car
        if (id_left > id_right):
            return id_right   # If a car with the same position is not found, return the car to the nearest front
        
        id_mid = int((id_left+id_right)/2)
        if (self.cars[id_mid].rect.left == car.rect.left):
            return id_mid
        elif (self.cars[id_mid].rect.left < car.rect.left):
            return self.find_nearest_car_to_left(car, id_mid+1, id_right)
        else:
            return self.find_nearest_car_to_left(car, id_left, id_mid-1)

    def find_nearest_car_to_right(self, car, id_left, id_right):         # Perform binary search to find the nearest car
        if (id_left > id_right):
            return id_right   # If a car with the same position is not found, return the car to the nearest front
        
        id_mid = int((id_left+id_right)/2)
        if (self.cars[id_mid].rect.left == car.rect.left):
            return id_mid
        elif (self.cars[id_mid].rect.left < car.rect.left):
            return self.find_nearest_car_to_right(car, id_left, id_mid-1)            
        else:
            return self.find_nearest_car_to_right(car, id_mid+1, id_right)

    def find_nearest_car_to_bottom(self, car, id_top, id_bottom):         # Perform binary search to find the nearest car
        if (id_top > id_bottom):
            return id_bottom   # If a car with the same position is not found, return the car to the nearest front
        
        id_mid = int((id_top+id_bottom)/2)
        if (self.cars[id_mid].rect.top == car.rect.top):
            return id_mid
        elif (self.cars[id_mid].rect.top < car.rect.top):
            return self.find_nearest_car_to_bottom(car, id_top, id_mid-1)            
        else:
            return self.find_nearest_car_to_bottom(car, id_mid+1, id_bottom)

    def find_nearest_car_to_top(self, car, id_top, id_bottom):         # Perform binary search to find the nearest car
        if (id_top > id_bottom):
            return id_bottom   # If a car with the same position is not found, return the car to the nearest front
        
        id_mid = int((id_top+id_bottom)/2)
        if (self.cars[id_mid].rect.top == car.rect.top):
            return id_mid
        elif (self.cars[id_mid].rect.top < car.rect.top):
            return self.find_nearest_car_to_left(car, id_mid+1, id_bottom)
        else:
            return self.find_nearest_car_to_left(car, id_top, id_mid-1)
        
    def include_pos(self, x, y):
        if (self.rect.left <= x) and (x <= self.rect.right) and\
               (self.rect.top <= y) and (y <= self.rect.bottom):
            return True
        return False

    def find_nearest_car_to_mouse_pos(self, x, y):
        min_distance_car = None
        
        if self.direction == TO_LEFT or self.direction == TO_RIGHT:
            min_distance = SCREEN_WIDTH
            for car in self.cars:
                if abs(x - car.rect.centerx) < min_distance:
                    min_distance = abs(x - car.rect.centerx)
                    min_distance_car = car
                    
        elif self.direction == TO_BOTTOM or self.direction == TO_TOP:
            min_distance = SCREEN_HEIGHT
            for car in self.cars:
                if abs(y - car.rect.centery) < min_distance:
                    min_distance = abs(y - car.rect.centery)
                    min_distance_car = car
        
        return min_distance_car

    def include_car(self, car):
        maxtop = max(self.rect.top, car.rect.top)
        minbottom = min(self.rect.bottom, car.rect.bottom)
        if (maxtop < minbottom):
            maxleft = max(self.rect.left, car.rect.left)
            minright = min(self.rect.right, car.rect.right)
            if (maxleft < minright):
                return True
        return False


# Configure lanes before and after, which will be used for changing lanes
def configure_lanes_before_after(lanes):
    for idx, lane in enumerate(lanes):
        if (idx-1 >= 0) and (lanes[idx-1].direction == lane.direction):
            lane.before = lanes[idx-1]
            #print(idx, "before exists")
        if (idx+1 < len(lanes)) and (lanes[idx+1].direction == lane.direction):
            lane.after = lanes[idx+1]
            #print(idx, "after exists")


'''
Define a Car object by extending pygame.sprite.Sprite
The surface drawn on the screen is an attribute of a Car object
'''
class Car():
    def __init__(self, pygame, road, lane, x, y):
        self.road = road
        self.lane = lane       
        
        if self.lane.direction == TO_LEFT or self.lane.direction == TO_RIGHT:
            self.surf = pygame.Surface((CAR_LENGTH, CAR_WIDTH))  # X/Y size
        elif self.lane.direction == TO_BOTTOM or self.lane.direction == TO_TOP:
            self.surf = pygame.Surface((CAR_WIDTH, CAR_LENGTH))  # X/Y size

        self.color = (CAR_COLOR[0]+random.randrange(-CAR_COLOR_VAR,CAR_COLOR_VAR),
                        CAR_COLOR[1]+random.randrange(-CAR_COLOR_VAR,CAR_COLOR_VAR),
                        CAR_COLOR[2]+random.randrange(-CAR_COLOR_VAR,CAR_COLOR_VAR))     
        self.surf.fill(self.color)
        self.rect = self.surf.get_rect(center=(x,y))
        self.speed = random.randint(CAR_SPEED-CAR_SPEED_VAR, CAR_SPEED+CAR_SPEED_VAR)                
        self.accident = False                

    def outside_safe_distance_from(self, car, safe_distance, direction):
        if direction == TO_LEFT or direction == TO_RIGHT:
            if car.rect.right + safe_distance <= self.rect.left or\
               self.rect.right < car.rect.left - safe_distance:
                return True
            else:
                return False
        elif direction == TO_BOTTOM or direction == TO_TOP:
            if car.rect.bottom + safe_distance <= self.rect.top or\
               self.rect.bottom < car.rect.top - safe_distance:
                return True
            else:
                return False
        
    def paint_on(self, screen):        
        screen.blit(self.surf, self.rect)

    '''
    Find the farthest distance that this can can go at the current round,
                        considering other cars and traffic lights
    '''
    def find_farthest_to_go(self):
        if self.lane.direction == TO_LEFT:            
            limit = self.lane.x_preceding_car + CAR_SAFE_DISTANCE            
            reason = BLOCKED

            # Consider cars on lanes the cross this lane
            for blocking_lane in self.lane.blocking_lanes:
                for c in blocking_lane.cars:
                    if self.lane.include_car(c) and c.rect.right < self.rect.left:
                        limit = max(limit, c.rect.right + CAR_SAFE_DISTANCE)                        

            # Consider cars and traffic lights on lanes the this lane continues on
            if self.rect.left - self.speed <= self.lane.rect.left + CAR_SAFE_DISTANCE:
                for next_lane in self.lane.next:
                    if next_lane.trafficLight == REDLIGHT:
                        limit = max(limit, next_lane.rect.right + CAR_SAFE_DISTANCE)                        
                        if limit == next_lane.rect.right + CAR_SAFE_DISTANCE:
                            reason = REDLIGHT                        
                        break   # At a red light, no need to check other conditions that provide looser limits
                    
                    if len(next_lane.cars) > 0:
                        limit = max(limit, next_lane.cars[-1].rect.right + CAR_SAFE_DISTANCE)                        
                        
                    for blocking_lane in next_lane.blocking_lanes:
                        for c in blocking_lane.cars:
                            if next_lane.include_car(c):
                                limit = max(limit, c.rect.right + CAR_SAFE_DISTANCE)                                
                                
        elif self.lane.direction == TO_RIGHT:
            limit = self.lane.x_preceding_car - CAR_SAFE_DISTANCE            
            reason = BLOCKED

            # Consider cars on lanes the cross this lane
            for blocking_lane in self.lane.blocking_lanes:
                for c in blocking_lane.cars:
                    if self.lane.include_car(c) and self.rect.right < c.rect.left:
                        limit = min(limit, c.rect.left - CAR_SAFE_DISTANCE)                        

            # Consider cars and traffic lights on lanes the this lane continues on            
            if self.lane.rect.right - CAR_SAFE_DISTANCE <= self.rect.right + self.speed:
                for next_lane in self.lane.next:
                    if next_lane.trafficLight == REDLIGHT:
                        limit = min(limit, next_lane.rect.left - CAR_SAFE_DISTANCE)                        
                        if limit == next_lane.rect.left - CAR_SAFE_DISTANCE:
                            reason = REDLIGHT                        
                        break   # At a red light, no need to check other conditions that provide looser limits
                    
                    if len(next_lane.cars) > 0:
                        limit = min(limit, next_lane.cars[-1].rect.left - CAR_SAFE_DISTANCE)                        
                        
                    for blocking_lane in next_lane.blocking_lanes:
                        for c in blocking_lane.cars:
                            if next_lane.include_car(c):
                                limit = min(limit, c.rect.left - CAR_SAFE_DISTANCE)
                                
        elif self.lane.direction == TO_BOTTOM:
            limit = self.lane.y_preceding_car - CAR_SAFE_DISTANCE            
            reason = BLOCKED

            # Consider cars on lanes the cross this lane
            for blocking_lane in self.lane.blocking_lanes:
                for c in blocking_lane.cars:
                    if self.lane.include_car(c) and self.rect.bottom < c.rect.top:
                        limit = min(limit, c.rect.top - CAR_SAFE_DISTANCE)                        

            # Consider cars and traffic lights on lanes the this lane continues on            
            if self.lane.rect.bottom - CAR_SAFE_DISTANCE <= self.rect.bottom + self.speed:
                for next_lane in self.lane.next:
                    if next_lane.trafficLight == REDLIGHT:
                        limit = min(limit, next_lane.rect.top - CAR_SAFE_DISTANCE)                        
                        if limit == next_lane.rect.top - CAR_SAFE_DISTANCE:
                            reason = REDLIGHT                        
                        break   # At a red light, no need to check other conditions that provide looser limits
                    
                    if len(next_lane.cars) > 0:
                        limit = min(limit, next_lane.cars[-1].rect.top - CAR_SAFE_DISTANCE)                        
                        
                    for blocking_lane in next_lane.blocking_lanes:
                        for c in blocking_lane.cars:
                            if next_lane.include_car(c):
                                limit = min(limit, c.rect.top - CAR_SAFE_DISTANCE)                                

        elif self.lane.direction == TO_TOP:            
            limit = self.lane.y_preceding_car + CAR_SAFE_DISTANCE            
            reason = BLOCKED

            # Consider cars on lanes the cross this lane
            for blocking_lane in self.lane.blocking_lanes:
                for c in blocking_lane.cars:
                    if self.lane.include_car(c) and c.rect.bottom < self.rect.top:
                        limit = max(limit, c.rect.bottom + CAR_SAFE_DISTANCE)

            # Consider cars and traffic lights on lanes the this lane continues on                                    
            if self.rect.top - self.speed <= self.lane.rect.top + CAR_SAFE_DISTANCE:
                for next_lane in self.lane.next:
                    if next_lane.trafficLight == REDLIGHT:
                        limit = max(limit, next_lane.rect.bottom + CAR_SAFE_DISTANCE)                        
                        if limit == next_lane.rect.bottom + CAR_SAFE_DISTANCE:
                            reason = REDLIGHT                        
                        break   # At a red light, no need to check other conditions that provide looser limits
                    
                    if len(next_lane.cars) > 0:
                        limit = max(limit, next_lane.cars[-1].rect.bottom + CAR_SAFE_DISTANCE)                        
                        
                    for blocking_lane in next_lane.blocking_lanes:
                        for c in blocking_lane.cars:
                            if next_lane.include_car(c):
                                limit = max(limit, c.rect.bottom + CAR_SAFE_DISTANCE)                                
                                
        return limit, reason

    '''
    Move this car.
    Return True if this car remains on the current lane. Return False otherwise.
    '''    
    def move(self, batch):   
        if self.lane.direction == TO_LEFT:
            if self.accident:
                self.lane.x_preceding_car = self.rect.right                
                self.lane.status_preceding_car = BLOCKED                
                return True

            limit, reason = self.find_farthest_to_go()

            prev_lane = self.lane
            prev_left = self.rect.left
            if limit <= self.rect.left - self.speed:    # GO
                self.rect.left = self.rect.left - self.speed    # Move at the assigned speed
                self.lane.x_preceding_car = self.rect.right                
                self.lane.status_preceding_car = GO
            else:   # REDLIGHT or BLOCKED
                '''
                At a red light, cars from different lanes may not stop along the same line,
                        because they have come at diffrent speeds, and thus
                        they can see the red light at different positions
                '''
                if (limit < self.rect.left):    # Do not move beyond the limit
                    self.rect.left = limit
                    
                if reason == REDLIGHT:  # REDLIGHT                    
                    self.lane.x_preceding_car = self.rect.right                
                    self.lane.status_preceding_car = REDLIGHT
                    
                else: # BLOCKED
                    if self.change_lane_v2(CAR_CHANGE_LANE_RATE_BLOCKED):
                        pass
                    else:
                        self.lane.x_preceding_car = self.rect.right
                        if self.lane.status_preceding_car == REDLIGHT:
                            pass # Blocked because preceding cars stop at a red light
                        else:
                            # Blocked because of accidents or congestion
                            self.lane.status_preceding_car == BLOCKED
                            if self.rect.left == prev_left: # Could not move at all, thus send a report
                                batch.report(self, report.EVENT_STOP)                                
                                self.change_color()                
            
            if self.rect.left < self.lane.rect.left: # Add to the next lane
                self.add_to_next_lane()                

            if self.lane != prev_lane or self.rect.left < self.lane.rect.left:
                return False    # Lane changed
            else:            
                return True     # Lane remains the same            
            
        elif self.lane.direction == TO_RIGHT:            
            if self.accident:
                self.lane.x_preceding_car = self.rect.left                
                self.lane.status_preceding_car = BLOCKED                
                return True

            limit, reason = self.find_farthest_to_go()

            prev_lane = self.lane
            prev_right = self.rect.right
            if self.rect.right + self.speed <= limit:    # GO
                self.rect.right = self.rect.right + self.speed    # Move at the assigned speed
                self.lane.x_preceding_car = self.rect.left                
                self.lane.status_preceding_car = GO
            else:   # REDLIGHT or BLOCKED
                '''
                At a red light, cars from different lanes may not stop along the same line,
                        because they have come at diffrent speeds, and thus
                        they can see the red light at different positions
                '''
                if (self.rect.right < limit):    # Do not move beyond the limit
                    self.rect.right = limit
                    
                if reason == REDLIGHT:  # REDLIGHT                    
                    self.lane.x_preceding_car = self.rect.left                
                    self.lane.status_preceding_car = REDLIGHT
                    
                else: # BLOCKED
                    if self.change_lane_v2(CAR_CHANGE_LANE_RATE_BLOCKED):
                        pass
                    else:
                        self.lane.x_preceding_car = self.rect.left
                        if self.lane.status_preceding_car == REDLIGHT:
                            pass # Blocked because preceding cars stop at a red light
                        else:
                            # Blocked because of accidents or congestion
                            self.lane.status_preceding_car == BLOCKED
                            if self.rect.right == prev_right: # Could not move at all, thus send a report
                                batch.report(self, report.EVENT_STOP)                                
                                self.change_color()                
            
            if self.lane.rect.right < self.rect.right: # Add to the next lane
                self.add_to_next_lane()                

            if self.lane != prev_lane or self.lane.rect.right < self.rect.right:
                return False    # Lane changed
            else:            
                return True     # Lane remains the same                       

        elif self.lane.direction == TO_BOTTOM:            
            if self.accident:
                self.lane.y_preceding_car = self.rect.top                
                self.lane.status_preceding_car = BLOCKED                
                return True

            limit, reason = self.find_farthest_to_go()

            prev_lane = self.lane
            prev_bottom = self.rect.bottom
            if self.rect.bottom + self.speed <= limit:    # GO
                self.rect.bottom = self.rect.bottom + self.speed    # Move at the assigned speed
                self.lane.y_preceding_car = self.rect.top                
                self.lane.status_preceding_car = GO
            else:   # REDLIGHT or BLOCKED
                '''
                At a red light, cars from different lanes may not stop along the same line,
                        because they have come at diffrent speeds, and thus
                        they can see the red light at different positions
                '''
                if (self.rect.bottom < limit):    # Do not move beyond the limit
                    self.rect.bottom = limit
                    
                if reason == REDLIGHT:  # REDLIGHT                    
                    self.lane.y_preceding_car = self.rect.top
                    self.lane.status_preceding_car = REDLIGHT
                    
                else: # BLOCKED
                    if self.change_lane_v2(CAR_CHANGE_LANE_RATE_BLOCKED):
                        pass
                    else:
                        self.lane.y_preceding_car = self.rect.top
                        if self.lane.status_preceding_car == REDLIGHT:
                            pass # Blocked because preceding cars stop at a red light
                        else:
                            # Blocked because of accidents or congestion
                            self.lane.status_preceding_car == BLOCKED
                            if self.rect.bottom == prev_bottom: # Could not move at all, thus send a report
                                batch.report(self, report.EVENT_STOP)                                
                                self.change_color()                
            
            if self.lane.rect.bottom < self.rect.bottom: # Add to the next lane
                self.add_to_next_lane()                

            if self.lane != prev_lane or self.lane.rect.bottom < self.rect.bottom:
                return False    # Lane changed
            else:            
                return True     # Lane remains the same                        

        elif self.lane.direction == TO_TOP:            
            if self.accident:
                self.lane.y_preceding_car = self.rect.bottom
                self.lane.status_preceding_car = BLOCKED                
                return True

            limit, reason = self.find_farthest_to_go()

            prev_lane = self.lane
            prev_top = self.rect.top
            if limit <= self.rect.top - self.speed:    # GO
                self.rect.top = self.rect.top - self.speed    # Move at the assigned speed
                self.lane.y_preceding_car = self.rect.bottom
                self.lane.status_preceding_car = GO
            else:   # REDLIGHT or BLOCKED
                '''
                At a red light, cars from different lanes may not stop along the same line,
                        because they have come at diffrent speeds, and thus
                        they can see the red light at different positions
                '''
                if (limit < self.rect.top):    # Do not move beyond the limit
                    self.rect.top = limit
                    
                if reason == REDLIGHT:  # REDLIGHT                    
                    self.lane.y_preceding_car = self.rect.bottom
                    self.lane.status_preceding_car = REDLIGHT
                    
                else: # BLOCKED
                    if self.change_lane_v2(CAR_CHANGE_LANE_RATE_BLOCKED):
                        pass
                    else:
                        self.lane.y_preceding_car = self.rect.bottom
                        if self.lane.status_preceding_car == REDLIGHT:
                            pass # Blocked because preceding cars stop at a red light
                        else:
                            # Blocked because of accidents or congestion
                            self.lane.status_preceding_car == BLOCKED
                            if self.rect.top == prev_top: # Could not move at all, thus send a report
                                batch.report(self, report.EVENT_STOP)                                
                                self.change_color()                
            
            if self.rect.top < self.lane.rect.top: # Add to the next lane
                self.add_to_next_lane()                

            if self.lane != prev_lane or self.rect.top < self.lane.rect.top:
                return False    # Lane changed
            else:            
                return True     # Lane remains the same            

    '''
    Move this car to the lane that the current lane continues on
    '''
    def add_to_next_lane(self):
        if len(self.lane.next) > 0:                     # If a next lane exists, the car continues on the next lane
            # Select a next lane to continue
            if len(self.lane.next) == 1:
                lane = self.lane.next[0]
            else:
                lane = self.lane.next[random.randrange(0,len(self.lane.next)-1)]
            
            self.road = lane.road
            self.lane = lane            
            lane.cars.append(self)
        else:
            pass    # Move outside the screen

    '''
    Switch into lanes before and after the current lane
    '''
    def change_lane_v2(self, probability):
        # Find empty lanes
        lanes = []
        if self.lane.before != None:
            yes, idx = self.lane.before.can_change_lane(self, add=False)
            if yes:
                lanes.append((self.lane.before, idx))
        if self.lane.after != None:
            yes, idx = self.lane.after.can_change_lane(self, add=False)
            if yes:
                lanes.append((self.lane.after, idx))

        # Change lanes probabilistically
        if len(lanes)>0 and random.randrange(1,100) <= (probability * 100):     
            if (len(lanes) == 1):
                lane, idx = lanes[0]
            else:
                lane, idx = lanes[random.randrange(0,len(lanes)-1)]
            lane.cars.insert(idx, self)            
            self.lane = lane
            return True
            
        return False
  
    def change_color(self):
            self.color = (CAR_COLOR[0]+random.randrange(-CAR_COLOR_VAR,CAR_COLOR_VAR),
                        CAR_COLOR[1]+random.randrange(-CAR_COLOR_VAR,CAR_COLOR_VAR),
                        CAR_COLOR[2]+random.randrange(-CAR_COLOR_VAR,CAR_COLOR_VAR))
            self.surf.fill(self.color)
            
    def toggle_accident(self, batch):
        if not self.accident:
            self.accident = True
            self.prev_color = self.color
            self.color = (CAR_COLOR_ACCIDENT[0]+random.randrange(-CAR_COLOR_VAR,CAR_COLOR_VAR),
                        CAR_COLOR_ACCIDENT[1]+random.randrange(-CAR_COLOR_VAR,CAR_COLOR_VAR),
                        CAR_COLOR_ACCIDENT[2]+random.randrange(-CAR_COLOR_VAR,CAR_COLOR_VAR))
            self.surf.fill(self.color)
            batch.report(self, report.EVENT_ACCIDENT)
            
        else:
            self.accident = False
            self.color = self.prev_color
            self.surf.fill(self.color)

    def distance_from(self, x, y):
        return math.sqrt((self.rect.centerx - x)**2 + (self.rect.centery-y)**2)

def find_car_nearest_to_mouse_pos(roads, x, y):
    for road in roads:
        lanes_on_mouse_pos = road.find_lanes_on_mouse_pos(x, y)
        if len(lanes_on_mouse_pos) > 0:
            break
        
    if len(lanes_on_mouse_pos) > 0:
        cars_on_mouse_pos = []
        for lane in lanes_on_mouse_pos:
            car = lane.find_nearest_car_to_mouse_pos(x, y)
            if car != None:
                cars_on_mouse_pos.append(car)

        if (len(cars_on_mouse_pos) > 0):
            car_nearest_to_mouse_pos = None
            min_distance = math.inf
            for car in cars_on_mouse_pos:
                distance = car.distance_from(x,y)
                if (distance < min_distance):
                    min_distance = distance
                    car_nearest_to_mouse_pos = car
            return car
        else:
            return None
        
    else:
        return None

'''
Define an Intersection object
'''
class Intersection():
    def __init__(self, left, right, top, bottom, roads):
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom
        self.roads = roads        
        
        '''
        surrounding_lanes[0]: lanes on the left side of intersection heading to the left
        surrounding_lanes[1]: lanes on the left side of intersection heading to the right
        surrounding_lanes[2]: lanes on the bottom side of intersection heading to the bottom
        surrounding_lanes[3]: lanes on the bottom side of intersection heading to the top
        surrounding_lanes[4]: lanes on the right side of intersection heading to the left
        surrounding_lanes[5]: lanes on the right side of intersection heading to the right
        surrounding_lanes[6]: lanes on the top side of intersection heading to the bottom
        surrounding_lanes[7]: lanes on the top side of intersection heading to the top
        '''
        self.surrounding_lanes = [ [] for _ in range(8) ]  # Lanes surrounding the intersection
        self.lanes = []                                   # Lanes on the intersection        
        
        self.signal_group = []                     # Group of lanes in the same signal groups
        self.current_signal = 0
        
        # Added for consistency with Road objects
        self.lanes_for_new_cars = []        
        self.name_str = '-'.join([road.name_str for road in self.roads])
        
    def add_newCar(self):            
        pass

    def paint_on(self, screen):        
        for lane in self.lanes:
            lane.paint_on(screen)

    def paint_cars_on(self, screen):
        for lane in self.lanes:
            lane.paint_cars_on(screen)
    
    def move(self, batch):
        for lane in self.lanes:
            lane.move(batch)            

    def find_lanes_on_mouse_pos(self, x, y):
        lanes = []
        for lane in self.lanes:
            if lane.include_pos(x, y):
                lanes.append(lane)
        return lanes
    
    def on_the_same_road_with(self, road):
        if isinstance(road, Road):
            for r in self.roads:
                if r == road:
                    return True
            return False
        elif isinstance(road, Intersection):
            for r1 in self.roads:
                for r2 in road.roads:
                    '''
                    Two intersections are considered being on the same road
                                        if they contain one road in common
                                        because accidents in one intersection can influence the other
                    '''
                    if r1 == r2:    
                        return True
            return False
        else:
            return False
        
    # connect surrounding lanes of the same direction
    def connect_surrounding_lanes_same_direction(self, idx_from, idx_to):
        group = []
        for lanePair in zip(self.surrounding_lanes[idx_from], self.surrounding_lanes[idx_to]):
            from_lane, to_lane = lanePair[0], lanePair[1]            
            new_lane = Lane(from_lane.pygame, from_lane.direction, from_lane.position, self)
            if from_lane.direction == TO_LEFT:
                new_lane.update_size(to_lane.rect.right, to_lane.rect.top, self.right - self.left, new_lane.rect.height)
            elif from_lane.direction == TO_RIGHT:
                new_lane.update_size(from_lane.rect.right, from_lane.rect.top, self.right - self.left, new_lane.rect.height)
            elif from_lane.direction == TO_BOTTOM:
                new_lane.update_size(from_lane.rect.left, from_lane.rect.bottom, new_lane.rect.width, self.bottom - self.top)
            elif from_lane.direction == TO_TOP:
                new_lane.update_size(to_lane.rect.left, to_lane.rect.bottom, new_lane.rect.width, self.bottom - self.top)
            new_lane.next.append(to_lane)
            from_lane.next.append(new_lane)            
            self.lanes.append(new_lane)
            group.append(new_lane)                  
        return group

'''
For each pair of intersecting roads R1 and R2,
                    add lanes for switching between roads
'''
def add_intersections(roads):    
    '''
    Find all intersections
    '''
    intersections = []
    road_combinations = itertools.combinations(roads, 2)
    for pair in road_combinations:
        pairOrdered = pair[0].intersect(pair[1])
        if pairOrdered != None:
            roadH, roadV = pairOrdered[0], pairOrdered[1]
            left, right, top, bottom = roadV.lanes[0].rect.left, roadV.lanes[-1].rect.right,\
                              roadH.lanes[0].rect.top, roadH.lanes[-1].rect.bottom
            it = Intersection(left, right, top, bottom, [roadH, roadV])
            roadH.intersections.append((left,right,it))
            roadV.intersections.append((top,bottom,it))
            intersections.append(it)
            #print(it.top, it.bottom, it.left, it.right)

    '''
    At each intersection, divide each lane into two,
                        one before the intersection and the other after the intersection
    '''
    for road in roads:        
        road.intersections = sorted(road.intersections, key=lambda x: x[0]) # Sort by left or top coordinates to divide from left to right (from top to bottom)
        prev_lanes = road.lanes
        for it in road.intersections:
            #print(road.name_str, it)
            new_lanes = []
            for lane in prev_lanes:
                if road.orientation == HORIZONTAL:
                    lane.update_size(lane.rect.left, lane.rect.top, it[0] - lane.rect.left, lane.rect.height)                    
                    new_lane = Lane(lane.pygame, lane.direction, lane.position, lane.road)
                    new_lane.update_size(it[1], new_lane.rect.top, new_lane.rect.right - it[1], new_lane.rect.height)
                    if lane.direction == TO_LEFT:
                        it[2].surrounding_lanes[0].append(lane)
                        it[2].surrounding_lanes[5].append(new_lane)
                    elif lane.direction == TO_RIGHT:
                        it[2].surrounding_lanes[1].append(lane)
                        it[2].surrounding_lanes[4].append(new_lane)
                elif road.orientation == VERTICAL:
                    lane.update_size(lane.rect.left, lane.rect.top, lane.rect.width, it[0] - lane.rect.top)
                    new_lane = Lane(lane.pygame, lane.direction, lane.position, lane.road)
                    new_lane.update_size(new_lane.rect.left, it[1], new_lane.rect.width, new_lane.rect.bottom-it[1])                    
                    if lane.direction == TO_BOTTOM:
                        it[2].surrounding_lanes[7].append(lane)
                        it[2].surrounding_lanes[2].append(new_lane)
                    elif lane.direction == TO_TOP:
                        it[2].surrounding_lanes[6].append(lane)
                        it[2].surrounding_lanes[3].append(new_lane)
                new_lanes.append(new_lane)
                #print(lane.rect.top, lane.rect.bottom, lane.rect.left, lane.rect.right)
                #print(new_lane.rect.top, new_lane.rect.bottom, new_lane.rect.left, new_lane.rect.right)
                
            configure_lanes_before_after(new_lanes)            
            prev_lanes = new_lanes
            road.lanes.extend(new_lanes)
            #print(len(new_lanes),'new lanes added, so a total of', len(road.lanes))
        
    '''
    At each intersection, connect surrounding lanes
                        with new straight or curved lines
    '''
    for it in intersections:
        # Signal group 1
        group1 = it.connect_surrounding_lanes_same_direction(5,0)
        add_blocking_lanes(group1, it.surrounding_lanes[6])
        group1a = it.connect_surrounding_lanes_same_direction(1,4)
        add_blocking_lanes(group1a, it.surrounding_lanes[2])
        
        group1.extend(group1a)
        configure_lanes_before_after(group1)
        it.signal_group.append(group1)

        # Signal group 2
        group2 = it.connect_surrounding_lanes_same_direction(7,2)
        add_blocking_lanes(group2, it.surrounding_lanes[0])
        group2a = it.connect_surrounding_lanes_same_direction(3,6)
        add_blocking_lanes(group2a, it.surrounding_lanes[4])
        
        group2.extend(group2a)
        configure_lanes_before_after(group2)
        it.signal_group.append(group2)

        # Configure blocking lanes
        add_blocking_lanes(group1, group2)
        add_blocking_lanes(group2, group1)
       
    '''
    At each intersection, randomly order signal groups 
    '''
    for it in intersections:
        random.shuffle(it.signal_group)
        for idx, group in enumerate(it.signal_group):
            if idx == it.current_signal:
                for lane in group:
                    lane.trafficLight = GO
            else:
                for lane in group:
                    lane.trafficLight = REDLIGHT
                    
    roads.extend(intersections)
    '''
    for road in roads:
        print(road.name_str)
        for lane in road.lanes:
            print(lane.rect.top, lane.rect.bottom, lane.rect.left, lane.rect.right)
    '''
    return intersections

def add_blocking_lanes(to_lanes, blocking_lanes):
    for lane in to_lanes:
        lane.blocking_lanes.extend(blocking_lanes)
        #print(lane.rect, len(lane.blocking_lanes))
