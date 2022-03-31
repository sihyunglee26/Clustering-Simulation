import pygame
import random
import report

'''
Define constants
'''
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 500
SCREEN_COLOR = (0, 0, 0) # black
LANE_WIDTH = 19
LANE_COLOR = (220, 220, 220) # gray
LANE_NAME_COLOR = (255, 255, 255) # white
TO_LEFT = 1
TO_RIGHT= 2
CAR_WIDTH = 10
CAR_LENGTH = 20
CAR_COLOR = (50, 200, 50) # greenish
CAR_COLOR_ACCIDENT = (200, 50, 50) # redish
CAR_COLOR_VAR = 50
CAR_SPEED = 10
CAR_SPEED_VAR = 3
CAR_SAFE_DISTANCE = CAR_LENGTH * 2
CAR_CHANGE_LANE_RATE = 0.2

'''
Defind a Road object
'''
class Road():
    def __init__(self, pygame, name, font, y_top, directions):
        self.pygame = pygame
        self.name = font.render(name, True, LANE_NAME_COLOR)
        self.y_top = y_top
        self.lanes = []        
        for idx, direction in enumerate(directions):
            self.lanes.append(Lane(pygame, y_top + (idx+1) * (LANE_WIDTH+1), direction, self))

        # Configure lanes before and after, which will be used for changing lanes
        for idx, lane in enumerate(self.lanes):
            if (idx-1 >= 0) and (self.lanes[idx-1].direction == lane.direction):
                lane.before = self.lanes[idx-1]
                #print(idx, "before exists")
            if (idx+1 < len(self.lanes)) and (self.lanes[idx+1].direction == lane.direction):
                lane.after = self.lanes[idx+1]
                #print(idx, "after exists")

    def add_car(self):
        lane = self.lanes[random.randrange(0, len(self.lanes))]
        lane.add_car()           
        
    def paint_on(self, screen):        
        for lane in self.lanes:
            lane.paint_on(screen)            
        screen.blit(self.name, (0, self.y_top))

    def move(self, batch):
        for lane in self.lanes:
            lane.move(batch)

    def find_lane_on_mouse_pos(self, x, y):
        for lane in self.lanes:
            if lane.include_pos(x, y):
                return lane
        return None
    
'''
Defind a Lane object
'''
class Lane():
    def __init__(self, pygame, y_top, direction, road):
        self.pygame = pygame
        self.surf = pygame.Surface((SCREEN_WIDTH, LANE_WIDTH))  # X/Y size
        self.surf.fill(LANE_COLOR)
        
        # Position the lane and get its Rectangle object
        self.centerY = y_top + LANE_WIDTH/2
        self.rect = self.surf.get_rect(center=(SCREEN_WIDTH/2, self.centerY))
        
        self.direction = direction
        self.road = road
        self.cars = []
        self.before = None
        self.after = None

    def add_car(self):
        if self.direction == TO_LEFT:
            if (len(self.cars) == 0) or (self.cars[-1].rect.right < SCREEN_WIDTH - CAR_SAFE_DISTANCE):
                self.cars.append(Car(self.pygame, SCREEN_WIDTH - CAR_LENGTH/2, self.centerY, self.direction, self, self.road))
        elif self.direction == TO_RIGHT:
            if (len(self.cars) == 0) or (self.cars[-1].rect.left > CAR_SAFE_DISTANCE):
                self.cars.append(Car(self.pygame, CAR_LENGTH/2, self.centerY, self.direction, self, self.road))
        
    def paint_on(self, screen):
        screen.blit(self.surf, self.rect)
        for car in self.cars:
            car.rect.centery = self.centerY
            car.paint_on(screen)
            
    def move(self, batch):
        # Initialize x_preceding_car for keeping a safe distance between consecutive cars
        if self.direction == TO_LEFT:
            self.x_preceding_car = 0 - (CAR_SAFE_DISTANCE * 2)            
        elif self.direction == TO_RIGHT:
            self.x_preceding_car = SCREEN_WIDTH + (CAR_SAFE_DISTANCE * 2)
            
        # Move each car on the lane
        self.cars = [car for car in self.cars if car.move(batch)]        # Only cars visible on the screen remain in the list

    def can_change_lane(self, car, add):
        if car.direction == TO_LEFT:
            id_nearest_car = self.find_nearest_car_to_left(car, 0, len(self.cars)-1)
            if ((id_nearest_car < 0) or (self.cars[id_nearest_car].rect.right + CAR_SAFE_DISTANCE < car.rect.left)) and \
               ((id_nearest_car+1 >= len(self.cars)) or (car.rect.right < self.cars[id_nearest_car+1].rect.left - CAR_SAFE_DISTANCE)):
                    if add:                    
                        self.cars.insert(id_nearest_car+1, car)
                    return True
        elif car.direction == TO_RIGHT:
            id_nearest_car = self.find_nearest_car_to_right(car, 0, len(self.cars)-1)
            if ((id_nearest_car < 0) or (car.rect.right < self.cars[id_nearest_car].rect.left - CAR_SAFE_DISTANCE)) and \
               ((id_nearest_car+1 >= len(self.cars)) or (self.cars[id_nearest_car+1].rect.right + CAR_SAFE_DISTANCE < car.rect.left)):
                    if add:                    
                        self.cars.insert(id_nearest_car+1, car)
                    return True
        return False

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

    def include_pos(self, x, y):
        if (self.rect.left <= x) and (x <= self.rect.right) and\
               (self.rect.top <= y) and (y <= self.rect.bottom):
            return True
        return False

    def find_nearest_car_to_mouse_pos(self, x, y):
        min_distance = SCREEN_WIDTH
        min_distance_car = None
        for car in self.cars:
            if abs(x - car.rect.centerx) < min_distance:
                min_distance = abs(x - car.rect.centerx)
                min_distance_car = car
        return min_distance_car
    
'''
Define a Car object by extending pygame.sprite.Sprite
The surface drawn on the screen is an attribute of a Car object
'''
class Car():
    def __init__(self, pygame, x, y, direction, lane, road):        
        self.surf = pygame.Surface((CAR_LENGTH, CAR_WIDTH))  # X/Y size
        self.color = (CAR_COLOR[0]+random.randrange(-CAR_COLOR_VAR,CAR_COLOR_VAR),
                        CAR_COLOR[1]+random.randrange(-CAR_COLOR_VAR,CAR_COLOR_VAR),
                        CAR_COLOR[2]+random.randrange(-CAR_COLOR_VAR,CAR_COLOR_VAR))
        self.surf.fill(self.color)
        self.rect = self.surf.get_rect(center=(x,y))
        self.direction = direction
        self.speed = random.randint(CAR_SPEED-CAR_SPEED_VAR, CAR_SPEED+CAR_SPEED_VAR)        
        self.lane = lane
        self.road = road
        self.accident = False

    def paint_on(self, screen):        
        screen.blit(self.surf, self.rect)
        
    # Return True if this car remains on the current lane. Return False otherwise.
    def move(self, batch):
        prev_x = self.rect.centerx
        if self.direction == TO_LEFT:            
            if not self.accident:
                self.rect.move_ip(-self.speed, 0)
            
            # If the preceding car is near, reduce speed or change lane
            if self.rect.left < self.lane.x_preceding_car + CAR_SAFE_DISTANCE:
                if self.change_lane():
                    return False
                else:
                    self.rect.left = min(self.lane.x_preceding_car + CAR_SAFE_DISTANCE, self.rect.left + self.speed)
                    self.lane.x_preceding_car = self.rect.right
                    if (self.rect.centerx == prev_x):
                        batch.report(self, report.EVENT_STOP)
                        #report.report_queue.append(report.Report(self, self.rect.centerx, self.rect.centery, self.lane,\
                        #                              report.EVENT_STOP))
                        #print("report a stop")
            else:
                self.lane.x_preceding_car = self.rect.right
            
            if (self.rect.left < 0):
                return False
            
        elif self.direction == TO_RIGHT:
            if not self.accident:
                self.rect.move_ip(self.speed, 0)

            # If the preceding car is near, reduce speed or change lane
            if self.rect.right > self.lane.x_preceding_car - CAR_SAFE_DISTANCE:
                if self.change_lane():
                    return False
                else:
                    self.rect.right = max(self.lane.x_preceding_car - CAR_SAFE_DISTANCE, self.rect.left - self.speed)
                    self.lane.x_preceding_car = self.rect.left
                    if (self.rect.centerx == prev_x):
                        batch.report(self, report.EVENT_STOP)
                        #report.report_queue.append(report.Report(self, self.rect.centerx, self.rect.centery, self.lane,\
                        #                               report.EVENT_STOP))
                        #print("report a stop")
            else:                    
                self.lane.x_preceding_car = self.rect.left
            
            if (self.rect.right > SCREEN_WIDTH):
                return False
            
        return True

    def change_lane(self):
        # Find empty lanes
        lanes = []
        if (self.lane.before != None) and (self.lane.before.can_change_lane(self, add=False)):
            lanes.append(self.lane.before)
        if (self.lane.after != None) and (self.lane.after.can_change_lane(self, add=False)):
            lanes.append(self.lane.after)

        # Change lanes probabilistically
        if len(lanes)>0 and random.randrange(1,100) <= (CAR_CHANGE_LANE_RATE * 100):     
            if (len(lanes) == 1):
                lane = lanes[0]
            else:
                lane = lanes[random.randrange(0,len(lanes)-1)]
            lane.can_change_lane(self, add=True)
            self.lane = lane                
            return True
            
        return False

    def toggle_accident(self, batch):
        if not self.accident:
            self.accident = True
            self.prev_color = self.color
            self.color = (CAR_COLOR_ACCIDENT[0]+random.randrange(-CAR_COLOR_VAR,CAR_COLOR_VAR),
                        CAR_COLOR_ACCIDENT[1]+random.randrange(-CAR_COLOR_VAR,CAR_COLOR_VAR),
                        CAR_COLOR_ACCIDENT[2]+random.randrange(-CAR_COLOR_VAR,CAR_COLOR_VAR))
            self.surf.fill(self.color)
            batch.report(self, report.EVENT_ACCIDENT)
            #report.report_queue.append(report.Report(self, self.rect.centerx, self.rect.centery, self.lane,\
            #                                           report.EVENT_ACCIDENT))
            #print("report an accident")
        else:
            self.accident = False
            self.color = self.prev_color
            self.surf.fill(self.color)
