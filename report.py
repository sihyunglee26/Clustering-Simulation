import time
import math
import pygame
import random

'''
Define constants
'''
EVENT_ACCIDENT = 1
EVENT_STOP = 2
CLUSTER_BOUNDARY = 100          # A cluster's radius = distance between centroid and farthest point + CUSTER_BOUNDARY
CLUSTER_COLOR = (50, 50, 200)   # Bluish
CLUSTER_COLOR_VAR = 50
CLUSTER_WIDTH = 2                       # Line thickness
CLUSTER_MOVING_AVERAGE_WEIGHT = 0.1
BATCH_FONT_SIZE = 30
BATCH_NAME_COLOR = (255, 255, 255) # white

'''
Define distance functions
'''
def distance(x1, y1, lane1, time1, event1,\
                         x2, y2, lane2, time2, event2):
    if not lane1.road.on_the_same_road_with(lane2.road):
        return math.inf     # For two reports to be close, their roads must be the same
    
    return math.sqrt(distance_position(x1, y1, x2, y2)**2 +\
                            distance_time(time1, time2)**2 +\
                            distance_event(event1, event2)**2)

def distance_position(x1, y1, x2, y2):
    return math.sqrt((x1-x2)**2 + (y1-y2)**2)    

def distance_time(time1, time2):
    return math.sqrt((time1-time2)**2)

def distance_event(event1, event2):
    return math.sqrt((event1-event2)**2)

'''
Define a Report object
'''
class Report():
    def __init__(self, reporter, x, y, lane, event):
        self.reporter = reporter
        self.x = x
        self.y = y
        self.lane = lane        
        self.time = int(time.time()) # current time in seconds        
        self.event = event        
        
'''
Define a Cluster object
'''
class Cluster():
    def __init__(self, pygame, report):
        self.pygame = pygame
        self.x = report.x
        self.y = report.y
        self.lane = report.lane
        self.time = report.time
        self.event = report.event
        self.reports = [report]
        self.radius = CLUSTER_BOUNDARY
        self.max_distance = 0
        self.color = report.reporter.color
        #self.color = (CLUSTER_COLOR[0]+random.randrange(-CLUSTER_COLOR_VAR,CLUSTER_COLOR_VAR),
        #               CLUSTER_COLOR[1]+random.randrange(-CLUSTER_COLOR_VAR,CLUSTER_COLOR_VAR),
        #                CLUSTER_COLOR[2]+random.randrange(-CLUSTER_COLOR_VAR,CLUSTER_COLOR_VAR))
        
    def distance(self, report):
        return distance(self.x, self.y, self.lane, self.time, self.event,\
                         report.x, report.y, report.lane, report.time, report.event)

    def insert(self, report):
        if not self.lane.road.on_the_same_road_with(report.lane.road):    # For a report to belong to a cluster, their roads must be the same
            return

        # Insert the new report into the report list
        self.reports.append(report)

        '''
        Method #1: Centroid is a weighted moving average of reports
                Compared to having a fixed centroid,
                            this way is better to differentiate accidents in one direction
                                                                                    vs. those that affect both directions
        '''
        # Update centroid as a weighted moving average of reports
        self.x = self.x * (1 - CLUSTER_MOVING_AVERAGE_WEIGHT)\
                         + report.x * CLUSTER_MOVING_AVERAGE_WEIGHT
        self.y = self.y * (1 - CLUSTER_MOVING_AVERAGE_WEIGHT)\
                         + report.y * CLUSTER_MOVING_AVERAGE_WEIGHT
        self.time = self.time * (1 - CLUSTER_MOVING_AVERAGE_WEIGHT)\
                         + report.time * CLUSTER_MOVING_AVERAGE_WEIGHT         
        self.event = self.event * (1 - CLUSTER_MOVING_AVERAGE_WEIGHT)\
                         + report.event * CLUSTER_MOVING_AVERAGE_WEIGHT

        # Update radius        
        max_distance = 0
        for r in self.reports:
            distance = self.distance(r)
            if max_distance < distance:
                max_distance = distance
        self.radius = max_distance + CLUSTER_BOUNDARY
        
        '''
        Method #2: X/Y of centroid remains at the position of the initial report
        '''
        '''
        # Update only the time of centroid
        self.time = report.time

        # Update radius
        distance = self.distance(report)
        if (distance  > self.max_distance):
            self.max_distance = distance
            self.radius = self.max_distance + CLUSTER_BOUNDARY
        '''
        
        '''
        Method #3: Centroid is updated upon every new report
        '''
        '''
        # Update centroid as the average of all reports in the cluster
        n = len(self.reports) - 1
        n_new = len(self.reports)
        self.x = (self.x * n + report.x) / n_new
        self.y = (self.y * n + report.y) / n_new
        self.time = (self.time * n + report.time) / n_new
        self.event = (self.event * n + report.event) / n_new

        # Update radius
        max_distance = 0
        for r in self.reports:
            distance = self.distance(r)
            if max_distance < distance:
                max_distance = distance
        self.radius = max_distance + CLUSTER_BOUNDARY
        '''
        
    def include_report(self, report):
        distance_to_report = self.distance(report)
        return (distance_to_report <= self.radius, distance_to_report)

    def include_cluster(self, cluster):
        distance_to_cluster = distance(self.x, self.y, self.lane, self.time, self.event,\
                         cluster.x, cluster.y, cluster.lane, cluster.time, cluster.event)
        return distance_to_cluster <= self.radius

    def combine_with(self, cluster):
        # Extend report list
        self.reports.extend(cluster.reports)

        # Update x, y, time, and event as the average of all reports
        self.x = 0
        self.y = 0
        self.time = 0
        self.event = 0
        for report in self.reports:
            self.x += report.x
            self.y += report.y
            self.time += report.time
            self.event += report.event
        self.x = self.x / len(self.reports)
        self.y = self.y / len(self.reports)
        self.time = self.time / len(self.reports)
        self.event = self.event / len(self.reports)        
        
        # Update radius
        max_distance = 0
        for report in self.reports:
            distance = self.distance(report)
            if max_distance < distance:
                max_distance = distance
        self.radius = max_distance + CLUSTER_BOUNDARY

        # Update color with the average color of two clusters
        self.color = (int((self.color[0]+cluster.color[0])/2), int((self.color[1]+cluster.color[1])/2), int((self.color[2]+cluster.color[2])/2))
        
    def paint_on(self, screen):
        if len(self.reports) <= 10: # Show only significant clusters and exclude those with temporary congestion
            return

        # Draw a circle that represents this cluster
        self.pygame.draw.circle(screen, self.color, [self.x,self.y], self.radius, CLUSTER_WIDTH)

        # Show the number of reports that belong to this cluster
        font_report_num = self.pygame.font.SysFont(None, min(len(self.reports)+20,100))        
        report_num = font_report_num.render(str(len(self.reports)), True, self.color)
        screen.blit(report_num, (self.x, self.y))       


'''
Define a batch object
'''
class Batch():
    def __init__(self, pygame, batch_num, time_batch):
        self.pygame = pygame
        self.report_queue = []
        self.cluster_list = []
        self.batch_num = batch_num
        self.font_batch_num = pygame.font.SysFont(None, BATCH_FONT_SIZE)        
        self.begin_time = pygame.time.get_ticks()    # get time in milliseconds since pygame.init() was called
        self.end_time = self.begin_time + time_batch
        self.time_batch = time_batch
        
    def paint_on(self, screen):
        remaining_time = int((self.end_time - self.pygame.time.get_ticks())/1000) + 1        
        batch_num_object = self.font_batch_num.render("batch #" + str(self.batch_num) + " (" + str(remaining_time) + "/" + str(int(self.time_batch/1000)) + " secs remain)", True, BATCH_NAME_COLOR)
        screen.blit(batch_num_object, (0,0))
        for cluster in self.cluster_list:
            cluster.paint_on(screen)

    def report(self, car, event):
        self.report_queue.append(Report(car, car.rect.centerx, car.rect.centery, car.lane, event))
        
    def process_reports(self):    
        for report in self.report_queue:
            min_distance = math.inf
            nearest_cluster = None
            for cluster in self.cluster_list:
                include, distance = cluster.include_report(report)
                if include and (distance < min_distance):
                    nearest_cluster = cluster
                    min_distance = distance
                    
            if nearest_cluster != None:
                # If a nearest cluster exists, push the report into the cluster
                nearest_cluster.insert(report)
            else:
                # Otherwise, create a new cluster with the report
                self.cluster_list.append(Cluster(self.pygame, report))
        
        self.report_queue.clear()

        self.combine_clusters()
        
        # print clusters
        #for idx, cluster in enumerate(self.cluster_list):
        #    print(idx, len(cluster.reports), cluster.x, cluster.y, cluster.time, cluster.event, cluster.radius)            
    
    def combine_clusters(self):
        for cluster in self.cluster_list:
            cluster.combined = False      
        
        for i in range(0, len(self.cluster_list)-2):
            c1 = self.cluster_list[i]
            if c1.combined:
                continue            
            for j in range(i+1, len(self.cluster_list)-1):
                c2 = self.cluster_list[j]
                if c2.combined:
                    continue                
                if c1.include_cluster(c2) or c2.include_cluster(c1):
                    c1.combine_with(c2)
                    c2.combined = True
                    print("two clusters combined")
                    
        new_cluster_list = []
        for cluster in self.cluster_list:
            if not cluster.combined:
                new_cluster_list.append(cluster)

        self.cluster_list = new_cluster_list
