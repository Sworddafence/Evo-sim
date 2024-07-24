import pygame
import math
import random
from pygame.locals import *

class App:
    def __init__(self):
        self._running = True
        self._display_surf = None
        self.size = self.width, self.height = 1000, 1000
        self.blob_x, self.blob_y = self.width // 2, self.height // 2  # Initial position of the blob
        self.blob_speed = 1  # Speed of the blob movement
        self.angle = 0  # Initial angle of the blob
        self.rotation_speed = 1  # Speed of rotation
        self.vision_cone_angle = 60  # Vision cone angle in degrees
        self.vision_cone_distance = 200  # Vision cone distance

        self.food_list = []  # List to store multiple food items
        self.num_food = 5  # Number of food items

    def on_init(self):
        pygame.init()
        self._display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self._running = True
        self._image_surf = pygame.image.load("blob.png").convert_alpha()
        self.food_surf = pygame.image.load("food.png").convert_alpha()  # Load the food image
        self.font = pygame.font.SysFont("Arial", 18)  # Initialize the font

        # Initialize food positions
        self.init_food()

    def init_food(self):
        self.food_list = []
        for _ in range(self.num_food):
            food_x = random.randint(0, self.width - self.food_surf.get_width())
            food_y = random.randint(0, self.height - self.food_surf.get_height())
            self.food_list.append((food_x, food_y))

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False

    def on_loop(self):
        keys = pygame.key.get_pressed()
        if keys[K_a]:
            self.angle += self.rotation_speed
        if keys[K_d]:
            self.angle -= self.rotation_speed

        # Keep angle between 0 and 360
        self.angle %= 360

        if keys[K_w]:
            # Calculate the movement in the direction of the angle
            radian_angle = math.radians(self.angle)
            self.blob_x += self.blob_speed * math.cos(radian_angle)
            self.blob_y -= self.blob_speed * math.sin(radian_angle)
        if keys[K_s]:
            # Calculate the movement in the opposite direction of the angle
            radian_angle = math.radians(self.angle)
            self.blob_x -= self.blob_speed * math.cos(radian_angle)
            self.blob_y += self.blob_speed * math.sin(radian_angle)

        # Check for collision with any food item
        for food in self.food_list[:]:
            if self.check_collision(food):
                self.food_list.remove(food)  # Remove the food item
                self.food_list.append(self.reset_food())  # Add a new food item

        # Check if any food is in the vision cone
        for food in self.food_list:
            if self.is_food_in_vision_cone(food):
                print("Food is in the vision cone!")

    def check_collision(self, food):
        # Define the size of the blob and food images for collision detection
        blob_rect = pygame.Rect(self.blob_x - self._image_surf.get_width() // 2,
                                self.blob_y - self._image_surf.get_height() // 2,
                                self._image_surf.get_width(), self._image_surf.get_height())
        food_x, food_y = food
        food_rect = pygame.Rect(food_x, food_y,
                                self.food_surf.get_width(), self.food_surf.get_height())
        # Check if the rectangles overlap
        return blob_rect.colliderect(food_rect)

    def is_food_in_vision_cone(self, food):
        # Vector from the blob to the food
        food_x, food_y = food
        to_food_x = food_x - self.blob_x
        to_food_y = food_y - self.blob_y
        food_distance = math.sqrt(to_food_x ** 2 + to_food_y ** 2)

        # Check if the food is within the cone distance
        if food_distance > self.vision_cone_distance:
            return False

        # Direction the blob is facing
        radian_angle = math.radians(self.angle)
        vision_dir_x = math.cos(radian_angle)
        vision_dir_y = -math.sin(radian_angle)

        # Dot product to find the angle between the blob's direction and the vector to the food
        angle_to_food = math.atan2(to_food_x, to_food_y) 

        # Angle between the direction of the blob and the vector to the food
        degrees_to_food = (math.degrees(angle_to_food) - 90) % 360
        angle_between = abs(self.angle - degrees_to_food)
        return angle_between < self.vision_cone_angle / 2

    def reset_food(self):
        # Reposition the food to a new location
        food_x = random.randint(0, self.width - self.food_surf.get_width())
        food_y = random.randint(0, self.height - self.food_surf.get_height())
        return (food_x, food_y)

    def on_render(self):
        self._display_surf.fill((0, 0, 0))  # Clear the screen with black

        # Render the blob image
        rotated_image = pygame.transform.rotate(self._image_surf, self.angle)
        rect = rotated_image.get_rect(center=(self.blob_x, self.blob_y))
        self._display_surf.blit(rotated_image, rect.topleft)

        # Render the food images
        for food in self.food_list:
            self._display_surf.blit(self.food_surf, food)

        # Draw the vision cone
        self.draw_vision_cone()

        # Render the angle and position as text
        angle_text = self.font.render(f"Angle: {self.angle:.2f}", True, (255, 255, 255))
        position_text = self.font.render(f"Position: ({self.blob_x:.2f}, {self.blob_y:.2f})", True, (255, 255, 255))
        self._display_surf.blit(angle_text, (10, 10))
        self._display_surf.blit(position_text, (10, 30))

        pygame.display.flip()

    def draw_vision_cone(self):
        # Calculate the cone vertices
        radian_angle = math.radians(self.angle)
        cone_points = [(self.blob_x, self.blob_y)]

        # Points at the edge of the vision cone
        for angle_offset in [-self.vision_cone_angle / 2, self.vision_cone_angle / 2]:
            cone_angle = radian_angle + math.radians(angle_offset)
            cone_point_x = self.blob_x + self.vision_cone_distance * math.cos(cone_angle)
            cone_point_y = self.blob_y - self.vision_cone_distance * math.sin(cone_angle)
            cone_points.append((cone_point_x, cone_point_y))
        
        # Draw the vision cone
        pygame.draw.polygon(self._display_surf, (0, 255, 0, 50), cone_points, 1)  # Green with some transparency

    def on_cleanup(self):
        pygame.quit()

    def on_execute(self):
        if self.on_init() == False:
            self._running = False

        while self._running:
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            self.on_render()
        self.on_cleanup()

if __name__ == "__main__":
    theApp = App()
    theApp.on_execute()
