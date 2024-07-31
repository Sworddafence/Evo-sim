import pygame
import math
import random
from pygame.locals import *
import os
import time
import neat
import pickle


# Inputs:
    # Number of food seen
    # Time Since last ate
    # Distance to closest pellet seen
    # Angle to cloeset pellet seen

# Output:
    # Forward 
    # Backward
    # Left
    # Right


#GLOBAL VAR
TOTAL_WIDTH = 1000
TOTAL_HEIGHT = 1000

class Blob:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 1
        self.angle = 0
        self.rotation_speed = 1
        self.vision_cone_angle = 60
        self.vision_cone_distance = 200
        self.seefood = False
        self.num_food_seen = 0
        self.dist_food = 1000
        self.diff_angle = 180
        self.hunger = 0
        self.food_eaten = set()
        self.regions_been = set()
        self.region_in = 5
        self.nearest_wall = 500

    # def move(self, keys):
    #     if keys[K_a]:
    #         self.angle += self.rotation_speed
    #     if keys[K_d]:
    #         self.angle -= self.rotation_speed

        # Keep angle between 0 and 360
        # self.angle %= 360

        # if keys[K_w]:
        #     # Calculate the movement in the direction of the angle
        #     radian_angle = math.radians(self.angle)
        #     self.x += self.speed * math.cos(radian_angle)
        #     self.y -= self.speed * math.sin(radian_angle)
        # if keys[K_s]:
        #     # Calculate the movement in the opposite direction of the angle
        #     radian_angle = math.radians(self.angle)
        #     self.x -= self.speed * math.cos(radian_angle)
        #     self.y += self.speed * math.sin(radian_angle)
    def move(self, output):
        # Assuming the output is [forward, backward, left, right]
        forward, backward, left, right = output
        
        if left > 0.5:
            self.angle += self.rotation_speed
        if right > 0.5:
            self.angle -= self.rotation_speed

        # Keep angle between 0 and 360
        self.angle %= 360

        if forward > 0.5:
            # Calculate the movement in the direction of the angle
            radian_angle = math.radians(self.angle)
            self.x += self.speed * math.cos(radian_angle)
            self.y -= self.speed * math.sin(radian_angle)
        if backward > 0.5:
            # Calculate the movement in the opposite direction of the angle
            radian_angle = math.radians(self.angle)
            self.x -= self.speed * math.cos(radian_angle)
            self.y += self.speed * math.sin(radian_angle)

    def get_region(self):


        if(self.x < 0 or self.x > 1000 or self.y < 0 or self.y > 1000):
            return -1

        region_width = TOTAL_WIDTH // 3
        region_height = TOTAL_HEIGHT // 3

        col = self.x // region_width
        row = self.y // region_height
        self.region_in = int(row * 3 + col)
        return int(row * 3 + col)


    def distance_to_nearest_wall(self):
        distances = [
            self.x,  # Distance to the left wall
            self.y,  # Distance to the top wall
            TOTAL_WIDTH - self.x,  # Distance to the right wall
            TOTAL_HEIGHT - self.y  # Distance to the bottom wall
        ]
        self.nearest_wall = min(distances)

    def update_vision(self, food_list):
        self.num_food_seen = 0
        self.seefood = False
        self.diff_angle = 180
        self.dist_food = 1000

        for food in food_list:
            if self.is_food_in_vision_cone(food):
                self.seefood = True
                self.num_food_seen += 1
        self.hunger += 1

    def check_collision(self, food, blob_image, food_image):
        blob_rect = pygame.Rect(self.x - blob_image.get_width() // 2,
                                self.y - blob_image.get_height() // 2,
                                blob_image.get_width(), blob_image.get_height())
        food_x, food_y = food
        food_rect = pygame.Rect(food_x, food_y,
                                food_image.get_width(), food_image.get_height())
        if( blob_rect.colliderect(food_rect) and not food in self.food_eaten):
            self.food_eaten.add(food)
            return True
        return False
        return blob_rect.colliderect(food_rect)

    def is_food_in_vision_cone(self, food):
        if(food in self.food_eaten):
            return False
        food_x, food_y = food
        to_food_x = food_x - self.x
        to_food_y = food_y - self.y
        food_distance = math.sqrt(to_food_x ** 2 + to_food_y ** 2)

        if food_distance > self.vision_cone_distance:
            return False

        angle_to_food = math.atan2(to_food_x, to_food_y)
        degrees_to_food = (math.degrees(angle_to_food) - 90) % 360
        angle_between = abs(self.angle - degrees_to_food)
        if(angle_between < self.vision_cone_angle / 2 and food_distance < self.dist_food and not food in self.food_eaten):
            self.dist_food = food_distance
            self.diff_angle = self.angle - degrees_to_food
            # print(food in self.food_eaten)
        
        return (angle_between < self.vision_cone_angle / 2 and not food in self.food_eaten)


class App:
    def __init__(self):
        self._running = True
        self._display_surf = None
        self.size = self.width, self.height = 1000, 1000
        self.blob_speed = 1
        self.food_list = []
        self.num_food = 20
        self.blobs = []
        self.num_blobs = 50
        self.genomes = None
        self.config = None

    def on_init(self):
        pygame.init()
        self._display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self._running = True
        self._image_surf = pygame.image.load("blob.png").convert_alpha()
        self.food_surf = pygame.image.load("food.png").convert_alpha()
        self.font = pygame.font.SysFont("Arial", 18)

        self.init_food()
        self.init_blobs()

    def init_food(self):
        self.food_list = []
        for _ in range(self.num_food):
            food_x = random.randint(0, self.width - self.food_surf.get_width())
            food_y = random.randint(0, self.height - self.food_surf.get_height())
            self.food_list.append((food_x, food_y))

    def init_blobs(self):
        for genome_id, genome in self.genomes:
            blob_x = 500
            blob_y = 500
            net = neat.nn.FeedForwardNetwork.create(genome, self.config)
            blob = Blob(blob_x, blob_y)
            blob.genome = genome
            blob.net = net
            genome.fitness = 0
            self.blobs.append(blob)

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False

    def on_loop(self):
        for blob in self.blobs:
            inputs = [blob.num_food_seen, blob.hunger, blob.dist_food, blob.diff_angle, blob.nearest_wall, blob.region_in]
            output = blob.net.activate(inputs)
            blob.move(output)
            blob.update_vision(self.food_list)
            v = blob.get_region()
            blob.regions_been.add(v)
            for food in self.food_list[:]:
                if blob.check_collision(food, self._image_surf, self.food_surf):
                    blob.hunger = 0
                    blob.genome.fitness += 1
                    # print("Some blob ate food!")

    def reset_food(self):
        food_x = random.randint(0, self.width - self.food_surf.get_width())
        food_y = random.randint(0, self.height - self.food_surf.get_height())
        return (food_x, food_y)

    def on_render(self):
        self._display_surf.fill((0, 0, 0))

        for blob in self.blobs:
            rotated_image = pygame.transform.rotate(self._image_surf, blob.angle)
            rect = rotated_image.get_rect(center=(blob.x, blob.y))
            self._display_surf.blit(rotated_image, rect.topleft)

        for food in self.food_list:
            self._display_surf.blit(self.food_surf, food)

        for blob in self.blobs:
            self.draw_vision_cone(blob)

        pygame.display.flip()

    def draw_vision_cone(self, blob):
        radian_angle = math.radians(blob.angle)
        cone_points = [(blob.x, blob.y)]

        for angle_offset in [-blob.vision_cone_angle / 2, blob.vision_cone_angle / 2]:
            cone_angle = radian_angle + math.radians(angle_offset)
            cone_point_x = blob.x + blob.vision_cone_distance * math.cos(cone_angle)
            cone_point_y = blob.y - blob.vision_cone_distance * math.sin(cone_angle)
            cone_points.append((cone_point_x, cone_point_y))

        pygame.draw.polygon(self._display_surf, (0, 255, 0, 50), cone_points, 1)

    def on_cleanup(self): 
        for blob in self.blobs:
            blob.genome.fitness += len(blob.regions_been)
            if(-1 in blob.regions_been):
                blob.genome.fitness -= 5
        pygame.quit()

    def on_execute(self, genomes, config):
        self.genomes = genomes
        self.config = config
        if not self.on_init():
            self._running = False

        tick = 0
        while tick < 30000:
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            self.on_render()
            tick += 1
        self.on_cleanup()


def eval_genomes(genomes, config):
    app = App()
    app.on_execute(genomes, config)




def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(eval_genomes ,50)



if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config_feed_foward.txt")
    run(config_path)

    # theApp = App()
    # theApp.on_execute()
