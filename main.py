#test
import pygame
import math
import sys
import random
import socket
from _thread import *
import pickle

pygame.mixer.pre_init(44100, 16, 2, 4096)  # Initialise mixer before pygame to decrease lag when calling sounds
pygame.init()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 1500, 1000
ROWS, COLUMNS = 10, 15
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Warzone")

FPS = 60

SINGLEPLAYER_GAME_LENGTH = 60

# Images
BACKGROUND_IMAGE = pygame.transform.scale(pygame.image.load("Assets/Images/background.png"),
                                          (SCREEN_WIDTH, SCREEN_HEIGHT)).convert()
PLAYER_PISTOL_IMAGE = pygame.image.load("Assets/Images/player with pistol.png").convert_alpha()
PLAYER_SHOTGUN_IMAGE = pygame.image.load("Assets/Images/player with shotgun.png").convert_alpha()
PLAYER_AUTO_RIFLE_IMAGE = pygame.image.load("Assets/Images/player with auto_rifle.png").convert_alpha()
PLAYER_SNIPER_IMAGE = pygame.image.load("Assets/Images/player with sniper.png").convert_alpha()

ENEMY_PLAYER_PISTOL_IMAGE = pygame.image.load("Assets/Images/enemy player with pistol.png").convert_alpha()
ENEMY_PLAYER_SHOTGUN_IMAGE = pygame.image.load("Assets/Images/enemy player with shotgun.png").convert_alpha()
ENEMY_PLAYER_AUTO_RIFLE_IMAGE = pygame.image.load("Assets/Images/enemy player with auto_rifle.png").convert_alpha()
ENEMY_PLAYER_SNIPER_IMAGE = pygame.image.load("Assets/Images/enemy player with sniper.png").convert_alpha()

BULLET_IMAGE = pygame.image.load("Assets/Images/bullet.png").convert_alpha()
ENEMY_IMAGE = pygame.image.load("Assets/Images/enemy.png").convert_alpha()
WALL_IMAGE = pygame.transform.scale(pygame.image.load("Assets/Images/Wooden Crate.png"), (100, 100)).convert()
FLOOR_IMAGE = pygame.transform.scale(pygame.image.load("Assets/Images/Floor.png"),
                                     (SCREEN_WIDTH, SCREEN_HEIGHT)).convert()
HEALTH_BOX_IMAGE = pygame.transform.scale(pygame.image.load("Assets/Images/health box.png"), (78, 54)).convert_alpha()

CROSSHAIR_SIZE = 60
CROSSHAIR_IMAGE = pygame.transform.scale(pygame.image.load("Assets/Images/crosshair.png").convert_alpha(),
                                         (CROSSHAIR_SIZE, CROSSHAIR_SIZE))
CROSSHAIR_SHOOTING_IMAGE = pygame.transform.scale(
    pygame.image.load("Assets/Images/crosshair shooting.png").convert_alpha(),
    (CROSSHAIR_SIZE, CROSSHAIR_SIZE))

# Sounds
PISTOL_SOUND = pygame.mixer.Sound("Assets/Sounds/pistol.mp3")
SHOTGUN_SOUND = pygame.mixer.Sound("Assets/Sounds/shotgun.mp3")
AUTO_RIFLE_SOUND = pygame.mixer.Sound("Assets/Sounds/auto_rifle.mp3")
SNIPER_SOUND = pygame.mixer.Sound("Assets/Sounds/sniper.mp3")

TAKE_DAMAGE_SOUND = pygame.mixer.Sound("Assets/Sounds/take_damage.mp3")
PLAYER_DEATH_SOUND = pygame.mixer.Sound("Assets/Sounds/player_death.mp3")

pygame.mixer.music.load("Assets/Sounds/background.mp3")


class Entity:
    def __init__(self, position, width, height):
        self.x_pos = position[0]
        self.y_pos = position[1]
        self.width = width
        self.height = height
        self.rect = pygame.Rect(self.x_pos - self.width / 2, self.y_pos - self.height / 2, self.width, self.height)
        self.angle = 0

    def draw(self, image):
        image = pygame.transform.scale(image, (self.width, self.height)).convert_alpha()
        image = pygame.transform.rotate(image, self.angle).convert_alpha()
        rect = image.get_rect(center=(self.x_pos, self.y_pos))

        SCREEN.blit(image, rect)


class Player(Entity):
    def __init__(self, position, width, height, current_weapon):
        super().__init__(position, width, height)
        self.coords = int(self.x_pos // 100), int(self.y_pos // 100)
        self.previous_coords = self.coords
        self.speed = 1.75
        self.current_weapon = current_weapon
        self.shooting = False
        self.health = 100
        self.weapon_cooldown = 0

    def move(self, walls):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_a]:  # left
            self.x_pos -= self.speed
            for wall in walls:
                self.rect.center = self.x_pos, self.y_pos
                if self.rect.colliderect(wall):
                    self.x_pos = wall.right + self.width / 2
                self.rect.center = self.x_pos, self.y_pos

        if keys[pygame.K_d]:  # right
            self.x_pos += self.speed
            for wall in walls:
                self.rect.center = self.x_pos, self.y_pos
                if self.rect.colliderect(wall):
                    self.x_pos = wall.left - self.width / 2 - 1
                self.rect.center = self.x_pos, self.y_pos

        if keys[pygame.K_w]:  # up
            self.y_pos -= self.speed
            for wall in walls:
                self.rect.center = self.x_pos, self.y_pos
                if self.rect.colliderect(wall):
                    self.y_pos = wall.bottom + self.width / 2
                self.rect.center = self.x_pos, self.y_pos

        if keys[pygame.K_s]:  # down
            self.y_pos += self.speed
            for wall in walls:
                self.rect.center = self.x_pos, self.y_pos
                if self.rect.colliderect(wall):
                    self.y_pos = wall.top - self.width / 2 - 1
                self.rect.center = self.x_pos, self.y_pos

        self.coords = int(self.x_pos // 100), int(self.y_pos // 100)

    def rotate(self):
        mouse_position = pygame.mouse.get_pos()
        x_dist = mouse_position[0] - self.x_pos
        y_dist = -(mouse_position[1] - self.y_pos)
        self.angle = math.degrees(math.atan2(y_dist, x_dist)) - 45

    def update(self, walls, bullets, enemies):
        self.move(walls)
        self.rotate()
        self.check_if_hit(bullets, enemies)
        if self.weapon_cooldown > 0:
            self.weapon_cooldown -= 1
        new_bullets = []
        if self.shooting:
            self.shoot(new_bullets)
        return new_bullets

    def check_if_hit(self, bullets, enemies):
        for bullet in bullets:
            if bullet.rect.colliderect(self.rect):
                bullets.remove(bullet)
                self.health -= bullet.damage
                TAKE_DAMAGE_SOUND.play()

        for enemy in enemies:
            if enemy.rect.colliderect(self.rect):
                enemies.remove(enemy)
                self.health -= enemy.damage
                TAKE_DAMAGE_SOUND.play()

        if self.health <= 0:
            PLAYER_DEATH_SOUND.play()

    def switch_weapon(self, keys):
        if keys[pygame.K_1]:
            self.current_weapon = "pistol"
        if keys[pygame.K_2]:
            self.current_weapon = "shotgun"
        if keys[pygame.K_3]:
            self.current_weapon = "auto_rifle"
        if keys[pygame.K_4]:
            self.current_weapon = "sniper"

    def shoot(self, new_bullets):
        if self.weapon_cooldown == 0:
            if self.current_weapon == "pistol":
                self.shoot_pistol(new_bullets)
            if self.current_weapon == "shotgun":
                self.shoot_shotgun(new_bullets)
            if self.current_weapon == "auto_rifle":
                self.shoot_auto_rifle(new_bullets)
            if self.current_weapon == "sniper":
                self.shoot_sniper(new_bullets)

    def shoot_pistol(self, new_bullets):
        bullet = Bullet((self.x_pos, self.y_pos), 12, 0, 12.25, 30)
        new_bullets.append(bullet)
        PISTOL_SOUND.play()
        self.weapon_cooldown = 25

    def shoot_shotgun(self, new_bullets):
        bullet1 = Bullet((self.x_pos, self.y_pos), 8, 0, 9, 35)
        bullet2 = Bullet((self.x_pos, self.y_pos), 8, 8, 9, 35)
        bullet3 = Bullet((self.x_pos, self.y_pos), 8, -8, 9, 35)
        new_bullets.extend([bullet1, bullet2, bullet3])
        SHOTGUN_SOUND.play()
        self.weapon_cooldown = 60

    def shoot_auto_rifle(self, new_bullets):
        if self.weapon_cooldown == 0:
            bullet = Bullet((self.x_pos, self.y_pos), 12, random.randint(-7, 7), 12.25, 25)
            new_bullets.append(bullet)
            AUTO_RIFLE_SOUND.play()
            self.weapon_cooldown = 10

    def shoot_sniper(self, new_bullets):
        bullet = Bullet((self.x_pos, self.y_pos), 16, 0, 20.25, 50)
        new_bullets.append(bullet)
        SNIPER_SOUND.play()
        self.weapon_cooldown = 80

    def draw_crosshair(self):
        if self.shooting:
            SCREEN.blit(CROSSHAIR_SHOOTING_IMAGE,
                        (
                            pygame.mouse.get_pos()[0] - CROSSHAIR_SIZE / 2,
                            pygame.mouse.get_pos()[1] - CROSSHAIR_SIZE / 2))
        else:
            SCREEN.blit(CROSSHAIR_IMAGE,
                        (
                            pygame.mouse.get_pos()[0] - CROSSHAIR_SIZE / 2,
                            pygame.mouse.get_pos()[1] - CROSSHAIR_SIZE / 2))

    def draw_healthbar(self):
        pygame.draw.rect(SCREEN, "red", (550, 925, 400, 50))
        pygame.draw.rect(SCREEN, "green", (550, 925, self.health * 4, 50))

    def display_health(self):  # For multiplayer to display enemy player's health
        if self.health < 0:
            self.health = 0

        if self.health <= 15:
            colour = "red"
        elif self.health <= 40:
            colour = "orange"
        else:
            colour = "green"

        health_text = Text((self.rect.center[0], self.y_pos - self.height / 2), str(self.health),
                           get_font(int(self.width / 5)), colour)
        health_text.draw()


class Bullet(Entity):
    def __init__(self, position, size, spread, speed, damage):
        super().__init__(position, size, size)
        self.spread = spread
        self.speed = speed
        self.damage = damage

        # Set velocity of bullet in x and y directions
        mouse_position = pygame.mouse.get_pos()
        angle = math.atan2(self.y_pos - mouse_position[1], self.x_pos - mouse_position[0]) - math.pi + math.radians(
            self.spread)
        self.velocity = [math.cos(angle) * self.speed, math.sin(angle) * self.speed]

        self.move_in_front_of_player(angle, size)

    def update(self):
        self.x_pos += self.velocity[0]
        self.y_pos += self.velocity[1]
        self.rect.center = self.x_pos, self.y_pos

    # Method to make the bullet spawn in front of the player instead of inside it
    def move_in_front_of_player(self, angle, size):
        x_velocity = math.cos(angle) * (64 + size / 2)
        self.x_pos += x_velocity

        y_velocity = math.sin(angle) * (64 + size / 2)
        self.y_pos += y_velocity

        self.rect.center = self.x_pos, self.y_pos


class Enemy(Entity):
    def __init__(self, position, game_difficulty, health, damage, score, size, speed):
        self.health = health
        self.damage = damage
        self.score = score
        self.speed = speed
        super().__init__(position, size, size)
        self.coords = self.x_pos // 100, self.y_pos // 100
        self.velocity = 0, 0
        self.path = [self.coords]
        self.previous_coords = self.coords

        self.scale_for_game_difficulty(game_difficulty)

    def scale_for_game_difficulty(self, game_difficulty):
        if game_difficulty == "easy":
            scale = 0.8
        elif game_difficulty == "hard":
            scale = 1.3
        else:
            scale = 1

        self.health = int(self.health * scale)
        self.damage *= scale
        self.score = int(self.score * scale)
        self.speed *= scale

    def update_path(self, map, player_coords):
        self.path = self.a_star_pathfinding(map, player_coords)

    def move(self, player_x_pos, player_y_pos):
        # If not in the same node as the player follow the path else move to the player
        if len(self.path) > 1:
            next_node_pos = convert_coords(self.path[1])
            angle = math.atan2(self.y_pos - next_node_pos[1], self.x_pos - next_node_pos[0]) + math.pi
        else:
            angle = math.atan2(self.y_pos - player_y_pos, self.x_pos - player_x_pos) + math.pi

        self.velocity = math.cos(angle) * self.speed, math.sin(angle) * self.speed
        self.x_pos += self.velocity[0]
        self.y_pos += self.velocity[1]

        self.rect.center = (int(self.x_pos), int(self.y_pos))
        self.coords = (self.rect.centerx // 100, self.rect.centery // 100)

    def draw_path(self):
        path = [convert_coords((x, y)) for x, y in self.path]
        if len(path) >= 2:
            pygame.draw.lines(SCREEN, "blue", False, path, 5)

    def update(self, player_pos, bullets):
        self.check_damage(bullets)
        self.move(player_pos[0], player_pos[1])

    def check_damage(self, bullets):
        for bullet in bullets:
            if bullet.rect.colliderect(self.rect):
                bullets.remove(bullet)
                self.health -= bullet.damage

    def display_health(self):
        if self.health < 0:
            self.health = 0

        if self.health <= 15:
            colour = "red"
        elif self.health <= 40:
            colour = "orange"
        else:
            colour = "green"

        health_text = Text((self.rect.center[0], self.y_pos - self.height / 2), str(self.health),
                           get_font(int(self.width / 5)), colour)
        health_text.draw()

    def a_star_pathfinding(self, map, end):
        start_node = Node(None, self.coords)
        end_node = Node(None, end)

        open_list = [start_node]
        closed_list = []

        while open_list:
            # Get the node with the least f value
            current_node = open_list[0]
            current_index = 0
            for index, item in enumerate(open_list):
                if item.f < current_node.f:
                    current_node = item
                    current_index = index

            # Move the node from the open list to the closed list
            open_list.pop(current_index)
            closed_list.append(current_node)

            # Check if the current node is the end node
            if current_node.coords == end_node.coords:
                path = []
                # Create a path going from the end to the start
                while current_node:
                    path.append(current_node.coords)
                    current_node = current_node.parent
                return path[::-1]  # Return the reversed path

            # Create neighbour nodes (left, right, above, below)
            neighbours = []
            for offset in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                neighbour_position = (current_node.coords[0] + offset[0], current_node.coords[1] + offset[1])

                # Check the neighbour is on the map
                if neighbour_position[1] > (len(map) - 1) or neighbour_position[1] < 0 or neighbour_position[0] > (
                        len(map[len(map) - 1]) - 1) or neighbour_position[0] < 0:
                    continue

                # Check the neighbour is not a wall
                if map[neighbour_position[1]][neighbour_position[0]] != 0:
                    continue

                neighbour = Node(current_node, neighbour_position)
                neighbours.append(neighbour)

            for neighbour in neighbours:
                neighbour.g = current_node.g + 1
                # h value is the direct distance between the neighbour and the end node using pythagoras
                neighbour.h = ((neighbour.coords[0] - end_node.coords[0]) ** 2) + (
                        (neighbour.coords[1] - end_node.coords[1]) ** 2) ** 0.5
                neighbour.f = neighbour.g + neighbour.h

                open_list.append(neighbour)


class EasyEnemy(Enemy):
    def __init__(self, position, game_difficulty):
        super().__init__(position, game_difficulty, 50, 10, 5, 50, 2)


class MediumEnemy(Enemy):
    def __init__(self, position, game_difficulty):
        super().__init__(position, game_difficulty, 100, 15, 10, 60, 1.5)


class HardEnemy(Enemy):
    def __init__(self, position, game_difficulty):
        super().__init__(position, game_difficulty, 150, 20, 15, 80, 1)


class HealthBox(Entity):
    def __init__(self, position):
        super().__init__(position, 78, 54)


class Text:
    def __init__(self, position, text, font, text_colour):
        self.text = text
        self.font = font
        self.text_colour = text_colour
        self.render_text = self.font.render(self.text, True, self.text_colour)
        self.rect = self.render_text.get_rect(center=(position[0], position[1]))

    def draw(self):
        SCREEN.blit(self.render_text, self.rect)

    def change_text(self, new_text):
        self.render_text = self.font.render(new_text, True, self.text_colour)


class Button:
    def __init__(self, position, text, font, text_base_colour, text_hovering_colour):
        self.font = font
        self.base_colour = text_base_colour
        self.hovering_colour = text_hovering_colour
        self.text = text
        self.render_text = self.font.render(self.text, True, self.base_colour)
        self.rect = self.render_text.get_rect(center=(position[0], position[1]))
        self.active = False

    def draw(self):
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            text_surface = self.font.render(self.text, True, self.hovering_colour)
        else:
            text_surface = self.font.render(self.text, True, self.base_colour)

        SCREEN.blit(text_surface, self.rect)

    def check_for_input(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos):
            return True
        return False


class InputBox:
    def __init__(self, position, height, text, font, text_colour, highlighted_colour, default_colour,
                 max_length):
        self.rect = pygame.Rect(position[0], position[1], 200, height)
        self.text = text
        self.font = font
        self.text_colour = text_colour
        self.highlighted_colour = highlighted_colour
        self.default_colour = default_colour
        self.max_length = max_length
        self.render_text = self.font.render(text, True, self.text_colour)
        self.active = False

        self.resize()

    def draw(self):
        SCREEN.blit(self.render_text, (self.rect.x + 5, self.rect.y + 5))
        if self.active:
            colour = self.highlighted_colour
        else:
            colour = self.default_colour
        pygame.draw.rect(SCREEN, colour, self.rect, 2)

    def resize(self):
        # Make the box longer if the text requires it
        width = max(200, self.render_text.get_width() + 10)
        self.rect.w = width

    def check_active(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos):
            self.active = True
        else:
            self.active = False

    def change_text(self, event):
        # Add the user input to the input box if it is active
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif len(self.text) < self.max_length:
                    self.text += event.unicode

                self.render_text = self.font.render(self.text, True, self.text_colour)
                self.resize()

    def update(self, event, mouse_pos):
        if event == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.check_active(mouse_pos)
        self.change_text(event)


class Map:
    def __init__(self, position, width, height, selected, map_name):
        self.rect = pygame.Rect(position[0], position[1], width, height)
        self.selected = selected
        self.map_name = map_name
        if map_name != "Random":
            self.map = self.load_map_file()
        self.walls, self.enemy_spawn_points, self.player_spawns = self.load_map()

    def load_map_file(self):
        map = []
        map_file = open(f"Assets/Maps/{self.map_name}.txt", "r")
        lines = map_file.readlines()
        for line in lines:
            row = [int(val) for val in line.strip().split(",")]
            map.append(row)
        map_file.close()
        return map

    def load_map(self):
        walls = []
        enemy_spawn_points = []
        player_spawns = []
        for x in range(0, COLUMNS):
            for y in range(0, ROWS):
                if self.map[y][x] == 1:
                    wall = pygame.Rect(x * 100, y * 100, 100, 100)
                    walls.append(wall)
                if self.map[y][x] == 2:
                    enemy_spawn_points.append((x, y))
                    self.map[y][x] = 0
                if self.map[y][x] == 3:
                    player_spawns.append((x, y))
                    self.map[y][x] = 0
        return walls, enemy_spawn_points, player_spawns

    def draw(self):
        image = pygame.transform.scale(pygame.image.load("Assets/Images/" + self.map_name + ".png"),
                                       (self.rect.width, self.rect.height)).convert()

        SCREEN.blit(image, self.rect)
        if self.selected:
            pygame.draw.rect(SCREEN, "white", self.rect, width=2)

    def check_selected(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos):
            return True
        else:
            return False

    def get_random_empty_cell(self):
        while True:
            random_row = random.randint(1, ROWS - 2)
            random_column = random.randint(1, COLUMNS - 2)
            if self.map[random_row][random_column] == 0:
                return random_row, random_column


class RandomMap(Map):
    def __init__(self, position, width, height, selected):
        self.number_of_walls = 15
        self.number_of_enemy_spawns = 4
        self.number_of_player_spawns = 2
        self.map = [[0 for _ in range(COLUMNS)] for _ in range(ROWS)]
        self.create_random_map()
        super().__init__(position, width, height, selected, "Random")

    def create_random_map(self):
        # Make a border of walls around the map
        for row in range(ROWS):
            for column in range(COLUMNS):
                if row == 0 or row == ROWS - 1 or column == 0 or column == COLUMNS - 1:
                    self.map[row][column] = 1

        # Create wall locations
        for wall in range(self.number_of_walls):
            random_row, random_column = self.get_random_empty_cell()
            self.map[random_row][random_column] = 1

        # Create enemy spawns
        for spawn in range(self.number_of_enemy_spawns):
            random_row, random_column = self.get_random_empty_cell()
            self.map[random_row][random_column] = 2

        # Create player spawns
        for spawn in range(self.number_of_player_spawns):
            random_row, random_column = self.get_random_empty_cell()
            self.map[random_row][random_column] = 3


class Node:
    def __init__(self, parent, coords):
        self.parent = parent
        self.coords = coords

        self.g = 0
        self.h = 0
        self.f = 0


class Network:
    def __init__(self, server_ip, port):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_ip = server_ip
        self.port = port
        self.address = (self.server_ip, self.port)
        self.player, self.map = self.connect()

    def get_player_and_map(self):
        return self.player, self.map

    def connect(self):
        try:
            self.client.connect(self.address)
            return pickle.loads(self.client.recv(2048))
        except Exception as e:
            print(e)

    def send(self, player, bullets):
        try:
            input_data = player, bullets
            self.client.send(pickle.dumps(input_data))

            output_data = pickle.loads(self.client.recv(2048))
            if output_data != "win" and output_data != "lose":
                player = output_data[0]
                bullets = output_data[1]
                return player, bullets
            return output_data
        except Exception as e:
            print(e)


def client_server_interaction(connection, map, players, player_number, player_bullets):
    start_data = players[player_number], map
    connection.sendall(pickle.dumps(start_data))

    end_of_game = False
    while not end_of_game:
        try:
            data = pickle.loads(connection.recv(2048))
            players[player_number] = data[0]
            player_bullets[player_number] = data[1]

            if not data:
                print("Disconnected")
                break
            elif players[1]:  # Only do if 2nd player has joined
                if players[player_number].health <= 0:
                    reply = "lose"
                    end_of_game = True
                elif players[1 - player_number].health <= 0:
                    reply = "win"
                    end_of_game = True
                else:
                    reply = players[1 - player_number], player_bullets[1 - player_number]
            elif players[player_number].health <= 0:
                reply = "lose"
            else:
                reply = None, []

            connection.sendall(pickle.dumps(reply))
        except Exception as e:
            print(e)
            break

    connection.close()


def server_startup(ip, port, max_players, map):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    players = [None, None]
    player_bullets = [[], []]

    try:
        server_socket.bind((ip, port))
    except Exception as e:
        print(e)  # Print why the server couldn't be started

    server_socket.listen(max_players)

    current_player = 0
    while current_player < max_players:
        try:
            server_socket.settimeout(1)
            connection, _ = server_socket.accept()  # _ means it is not used

            # Spawn the player at the first spawn point unless the other player is on it
            if players[0] and (players[0].coords == map.player_spawns[0]):
                players[current_player] = Player(convert_coords(map.player_spawns[1]), 90, 90, "pistol")
            else:
                players[current_player] = Player(convert_coords(map.player_spawns[0]), 90, 90, "pistol")

            start_new_thread(client_server_interaction, (connection, map, players, current_player, player_bullets))
            current_player += 1
        except:
            pass

        # Stop the startup if any of the players die
        for player in players:
            if player and player.health <= 0:
                exit_thread()


def convert_coords(coord):
    return coord[0] * 100 + 50, coord[1] * 100 + 50


def get_font(size):
    return pygame.font.Font("assets/font.ttf", size)


def update_high_scores(new_score):
    # Create a list of high scores from the file
    high_scores = []
    file = open("Assets/high_scores.txt", "r")
    for line in file:
        data = line.strip().split(',')
        high_scores.append((int(data[0]), str(data[1])))
    file.close()

    # Add the new score to the list and sort it
    high_scores.append(new_score)
    high_scores = sorted(high_scores, reverse=True)

    # If the list is longer than 3 then the lowest score is removed
    if len(high_scores) > 5:
        high_scores.pop(5)

    # Write the new high scores to the file
    file = open("Assets/high_scores.txt", "w")
    for item in high_scores:
        file.write(f"{item[0]},{item[1]}\n")  # \n means new line

    return high_scores


def draw_debugging_tools(player, enemies, bullets, enemy_spawn_points, player_spawn_points, clock):
    # Draw hitboxes
    pygame.draw.rect(SCREEN, "red", player.rect, width=2)
    for enemy in enemies:
        pygame.draw.rect(SCREEN, "red", enemy.rect, width=2)
        enemy.draw_path()
    for bullet in bullets:
        pygame.draw.rect(SCREEN, "red", bullet.rect, width=2)

    # Draw grid
    gap = 100
    for y in range(ROWS):
        pygame.draw.line(SCREEN, "black", (0, y * gap), (SCREEN_WIDTH, y * gap))
        for x in range(COLUMNS):
            pygame.draw.line(SCREEN, "black", (x * gap, 0), (x * gap, SCREEN_HEIGHT))

    # Draw enemy spawn points
    for spawn_point in enemy_spawn_points:
        position = convert_coords(spawn_point)
        rect = pygame.Rect(0, 0, 100, 100)
        rect.center = position
        pygame.draw.rect(SCREEN, "green", rect, width=3)

    # Draw player spawn points
    for spawn_point in player_spawn_points:
        position = convert_coords(spawn_point)
        rect = pygame.Rect(0, 0, 100, 100)
        rect.center = position
        pygame.draw.rect(SCREEN, "yellow", rect, width=3)

    # Display fps
    render_text = get_font(20).render(f"FPS: {str(round(clock.get_fps(), 2))}", True, "white")
    rect = render_text.get_rect(center=(120, 950))
    SCREEN.blit(render_text, rect)


def redraw_window(player, enemy_player, walls, bullets, enemies, health_boxes, background_image, text_boxes, buttons,
                  input_boxes):
    SCREEN.blit(background_image, (0, 0))

    for wall in walls:
        SCREEN.blit(WALL_IMAGE, wall)

    for health_box in health_boxes:
        health_box.draw(HEALTH_BOX_IMAGE)

    for bullet in bullets:
        bullet.draw(BULLET_IMAGE)

    for enemy in enemies:
        enemy.draw(ENEMY_IMAGE)
        enemy.display_health()

    if enemy_player:
        if enemy_player.current_weapon == "pistol":
            enemy_player.draw(ENEMY_PLAYER_PISTOL_IMAGE)
        elif enemy_player.current_weapon == "shotgun":
            enemy_player.draw(ENEMY_PLAYER_SHOTGUN_IMAGE)
        elif enemy_player.current_weapon == "auto_rifle":
            enemy_player.draw(ENEMY_PLAYER_AUTO_RIFLE_IMAGE)
        elif enemy_player.current_weapon == "sniper":
            enemy_player.draw(ENEMY_PLAYER_SNIPER_IMAGE)
        enemy_player.display_health()

    if player:
        if player.current_weapon == "pistol":
            player.draw(PLAYER_PISTOL_IMAGE)
        elif player.current_weapon == "shotgun":
            player.draw(PLAYER_SHOTGUN_IMAGE)
        elif player.current_weapon == "auto_rifle":
            player.draw(PLAYER_AUTO_RIFLE_IMAGE)
        elif player.current_weapon == "sniper":
            player.draw(PLAYER_SNIPER_IMAGE)
        player.draw_crosshair()
        player.draw_healthbar()

    for text_box in text_boxes:
        text_box.draw()

    for button in buttons:
        button.draw()

    for input_box in input_boxes:
        input_box.draw()


def single_player(map, game_difficulty, length_of_game):
    pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()

    player = Player(convert_coords(random.choice(map.player_spawns)), 90, 90, "pistol")

    score = 0
    score_text = Text((1350, 30), f"Score: {score}", get_font(20), "white")

    #  Timer that counts down to the end of the game
    timer = length_of_game
    timer_text = Text((240, 30), f"Time remaining: {timer}", get_font(20), "white")
    TIMER_EVENT = pygame.USEREVENT + 0
    pygame.time.set_timer(TIMER_EVENT, 1000)  # Event happens every 1000 milliseconds (1 second)

    current_weapon_text = Text((840, 30), f"Current weapon: {player.current_weapon}", get_font(20), "white")

    text_boxes = [timer_text, current_weapon_text, score_text]

    debugging = False

    enemies = []
    bullets = []
    health_boxes = []

    while timer > 0 and player.health > 0:
        clock.tick(FPS)

        player.previous_coords = player.coords

        #  Events with user inputs
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                player.shooting = True
            if event.type == pygame.MOUSEBUTTONUP:
                player.shooting = False

            if event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()

                player.switch_weapon(keys)
                current_weapon_text.change_text(f"Current weapon: {player.current_weapon}")

                # Set timer to zero to end the game
                if debugging and keys[pygame.K_0]:
                    timer = 0

                # Toggles debugging mode
                if keys[pygame.K_TAB]:
                    debugging = not debugging

            if event.type == TIMER_EVENT:
                timer -= 1
                timer_text.change_text(f"Time remaining: {timer}")

                # Spawn an enemy every second if there are less than 5 enemies already
                if len(enemies) < 5:
                    coords = random.choice(map.enemy_spawn_points)
                    difficulty = random.choice(["easy", "medium", "hard"])
                    if difficulty == "easy":
                        enemy = EasyEnemy(convert_coords(coords), game_difficulty)
                    elif difficulty == "medium":
                        enemy = MediumEnemy(convert_coords(coords), game_difficulty)
                    else:
                        enemy = HardEnemy(convert_coords(coords), game_difficulty)
                    enemy.update_path(map.map, player.coords)
                    enemies.append(enemy)

                # Spawn a health box halfway through the game at a random empty position (not in hard mode)
                if timer == int(length_of_game / 2) and game_difficulty != "hard":
                    y, x = map.get_random_empty_cell()
                    health_box = HealthBox(convert_coords((x, y)))
                    health_boxes.append(health_box)

        # Deletes bullets if they hit a wall
        for bullet in bullets:
            bullet.update()
            for wall in map.walls:
                if bullet.rect.colliderect(wall):
                    bullets.remove(bullet)
                    break  # Break incase two walls are hit

        # Enemies
        for enemy in enemies:
            enemy.previous_coords = enemy.coords
            if enemy.health <= 0:
                enemies.remove(enemy)
                score += enemy.score
                score_text.change_text(f"Score: {score}")
            else:
                enemy.update((player.x_pos, player.y_pos), bullets)

                # Add 50 health to the player when they go to a health box
                for health_box in health_boxes:
                    if player.rect.colliderect(health_box.rect):
                        player.health += 50
                        health_boxes.remove(health_box)
                    if player.health > 100:
                        player.health = 100

            # Only update the path of the enemy if the player or enemy has moved coords
            if player.previous_coords != player.coords or enemy.previous_coords != enemy.coords:
                enemy.update_path(map.map, player.coords)

        bullets.extend(player.update(map.walls, bullets, enemies))

        redraw_window(player, [], map.walls, bullets, enemies, health_boxes, FLOOR_IMAGE, text_boxes, [], [])

        # Debugging mode
        if debugging:
            draw_debugging_tools(player, enemies, bullets, map.enemy_spawn_points, map.player_spawns, clock)

        pygame.display.update()

    pygame.mouse.set_visible(True)
    score_screen(score)  # Show a game finished screen with the score of the player


def main_menu():
    pygame.mixer.music.play()

    main_menu_text = Text((SCREEN_WIDTH / 2, 200), "WARZONE", get_font(100), "black")

    single_player_button = Button((SCREEN_WIDTH / 2, 400), "SINGLEPLAYER", get_font(60), "black", "grey")
    multiplayer_button = Button((SCREEN_WIDTH / 2, 525), "MULTIPLAYER", get_font(60), "black", "grey")
    quit_button = Button((SCREEN_WIDTH / 2, 650), "QUIT", get_font(75), "black", "grey")
    buttons = [single_player_button, multiplayer_button, quit_button]

    while True:
        mouse_position = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if single_player_button.check_for_input(mouse_position):
                    difficulty = difficulty_selection_screen()
                    if not difficulty:  # Go back to the main menu if the back button was pressed
                        break
                    map = map_selection_screen()
                    if map:
                        single_player(map, difficulty, SINGLEPLAYER_GAME_LENGTH)
                if multiplayer_button.check_for_input(mouse_position):
                    try:
                        multiplayer_menu()
                    except:
                        return
                if quit_button.check_for_input(mouse_position):
                    pygame.quit()
                    sys.exit()

        redraw_window(None, [], [], [], [], [], BACKGROUND_IMAGE, [main_menu_text], buttons, [])

        pygame.display.update()


def score_screen(score):
    score_text = Text((SCREEN_WIDTH / 2, 200), f"Your score: {score}", get_font(50), "black")
    enter_name_text = Text((SCREEN_WIDTH / 2, 450), "Enter your name:", get_font(20), "black")
    text_boxes = [score_text, enter_name_text]

    leaderboard_button = Button((SCREEN_WIDTH / 2, 700), "Show Leaderboard", get_font(30), "black", "grey")

    name_input_box = InputBox((650, 500), 40, "", get_font(30), "grey", "grey", "black", 15)

    while True:
        SCREEN.blit(BACKGROUND_IMAGE, (0, 0))

        for text_box in text_boxes:
            text_box.draw()

        leaderboard_button.draw()

        name_input_box.draw()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if leaderboard_button.check_for_input(pygame.mouse.get_pos()):
                    leaderboard_screen(score, name_input_box.text)
                    return  # Return to main menu

            name_input_box.update(event, pygame.mouse.get_pos())

        pygame.display.update()


def leaderboard_screen(score, name):
    high_scores = update_high_scores((score, name))
    score_texts = []
    for count, score in enumerate(high_scores):
        if count == 0:
            place = "1st: "
        elif count == 1:
            place = "2nd: "
        elif count == 2:
            place = "3rd: "
        else:
            place = str(count + 1) + "th: "
        current_score = str(score[0])
        current_name = score[1]
        score_text = Text((SCREEN_WIDTH / 2, 300 + count * 50), str(place + current_name + " - " + current_score),
                          get_font(30), "black")
        score_texts.append(score_text)

    leaderboard_text = Text((SCREEN_WIDTH / 2, 200), "LEADERBOARD", get_font(100), "black")

    main_menu_button = Button((SCREEN_WIDTH / 2, 700), "Main Menu", get_font(50), "black", "grey")

    while True:
        SCREEN.blit(BACKGROUND_IMAGE, (0, 0))

        for score_text in score_texts:
            score_text.draw()
        leaderboard_text.draw()

        main_menu_button.draw()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if main_menu_button.check_for_input(pygame.mouse.get_pos()):
                    return  # Return to main menu

        pygame.display.update()


def map_selection_screen():
    map1 = Map((100, 350), 300, 200, True, "Map1")
    map2 = Map((100, 600), 300, 200, False, "Map2")
    map3 = Map((1100, 350), 300, 200, False, "Map3")
    random_map = RandomMap((1100, 600), 300, 200, False)
    maps = [map1, map2, map3, random_map]

    select_map_text = Text((SCREEN_WIDTH / 2, 200), "Select Map", get_font(100), "black")

    play_button = Button((SCREEN_WIDTH / 2, 500), "PLAY", get_font(75), "black", "grey")
    back_button = Button((SCREEN_WIDTH / 2, 650), "BACK", get_font(75), "black", "grey")
    buttons = [play_button, back_button]

    selected_map = map1

    while True:
        mouse_position = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_button.check_for_input(mouse_position):
                    pygame.mixer_music.pause()
                    return selected_map
                if back_button.check_for_input(mouse_position):
                    return

                for map in maps:
                    map.selected = False
                    if map.check_selected(mouse_position):
                        if not map.selected:
                            selected_map = map

        selected_map.selected = True

        redraw_window(None, [], [], [], [], [], BACKGROUND_IMAGE, [select_map_text], buttons, [])

        for map in maps:
            map.draw()

        pygame.display.update()


def difficulty_selection_screen():
    select_difficulty_text = Text((SCREEN_WIDTH / 2, 200), "Difficulty:", get_font(100), "black")

    easy_button = Button((300, 500), "EASY", get_font(75), "black", "grey")
    normal_button = Button((SCREEN_WIDTH / 2, 500), "NORMAL", get_font(75), "black", "grey")
    hard_button = Button((1200, 500), "HARD", get_font(75), "black", "grey")
    back_button = Button((SCREEN_WIDTH / 2, 650), "BACK", get_font(75), "black", "grey")
    buttons = [easy_button, normal_button, hard_button, back_button]

    while True:
        mouse_position = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if easy_button.check_for_input(mouse_position):
                    return "easy"
                if normal_button.check_for_input(mouse_position):
                    return "normal"
                if hard_button.check_for_input(mouse_position):
                    return "hard"
                if back_button.check_for_input(mouse_position):
                    return

        redraw_window(None, [], [], [], [], [], BACKGROUND_IMAGE, [select_difficulty_text], buttons, [])

        pygame.display.update()


def multiplayer_menu():
    ip_input_box = InputBox((1000, 400), 40, str(socket.gethostbyname(socket.gethostname())), get_font(30), "grey",
                            "grey", "black", 15)
    port_input_box = InputBox((1000, 525), 40, "5555", get_font(30), "grey", "grey", "black", 10)
    input_boxes = [ip_input_box, port_input_box]

    multiplayer_text = Text((SCREEN_WIDTH / 2, 200), "MULTIPLAYER", get_font(100), "black")
    host_ip_text = Text((1200, 375), "Host's IP address:", get_font(20), "black")
    port_text = Text((1075, 500), "Port:", get_font(20), "black")
    text_boxes = [multiplayer_text, host_ip_text, port_text]

    host_button = Button((SCREEN_WIDTH / 2, 400), "HOST", get_font(60), "black", "grey")
    join_button = Button((SCREEN_WIDTH / 2, 525), "JOIN", get_font(60), "black", "grey")
    back_button = Button((SCREEN_WIDTH / 2, 650), "BACK", get_font(75), "black", "grey")
    buttons = [host_button, join_button, back_button]

    while True:
        mouse_position = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if host_button.check_for_input(mouse_position):
                    # Only host if the ip is the same as the current computer's
                    if ip_input_box.text == str(socket.gethostbyname(socket.gethostname())):
                        map = map_selection_screen()
                        if map:  # Only start the game if the play button was pressed
                            try:
                                start_new_thread(server_startup, (ip_input_box.text, int(port_input_box.text), 2, map))
                                multiplayer_client(ip_input_box.text, int(port_input_box.text))
                                return  # Return to main menu
                            except Exception as e:
                                print(e)  # Print why the multiplayer client couldn't start
                        else:
                            pass
                if join_button.check_for_input(mouse_position):
                    try:
                        multiplayer_client(ip_input_box.text, int(port_input_box.text))
                        return  # Return to main menu
                    except Exception as e:
                        print(e)  # Print why the multiplayer client couldn't start
                        pass
                if back_button.check_for_input(mouse_position):
                    return  # Return to main menu
            for input_box in input_boxes:
                input_box.update(event, mouse_position)

        redraw_window(None, [], [], [], [], [], BACKGROUND_IMAGE, text_boxes, buttons, input_boxes)

        pygame.display.update()


def multiplayer_client(server_ip, port):
    network = Network(server_ip, port)
    player, map = network.get_player_and_map()
    clock = pygame.time.Clock()
    pygame.mixer_music.pause()
    pygame.mouse.set_visible(False)

    current_weapon_text = Text((840, 30), f"Current weapon: {player.current_weapon}", get_font(20), "white")
    text_boxes = [current_weapon_text]

    bullets = []

    debugging = False

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                player.health = 0  # Kill own player so opponent wins
                network.send(player, [])
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                player.shooting = True
            if event.type == pygame.MOUSEBUTTONUP:
                player.shooting = False
            if event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()

                player.switch_weapon(keys)
                current_weapon_text.change_text(f"Current weapon: {player.current_weapon}")

                # Toggles debugging mode
                if keys[pygame.K_TAB]:
                    debugging = not debugging

                # Kills the player if '0' key is pressed
                if debugging and keys[pygame.K_0]:
                    player.health = 0

        new_bullets = player.update(map.walls, bullets, [])

        message = network.send(player, new_bullets)
        if message == "win" or message == "lose":
            break
        else:
            player2, enemy_bullets = message

        bullets = bullets + new_bullets + enemy_bullets

        # Deletes bullets if they hit a wall
        for bullet in bullets:
            bullet.update()
            if player2 and bullet.rect.colliderect(
                    player2.rect):  # remove bullets for the client if they hit the enemy player
                bullets.remove(bullet)
            for wall in map.walls:
                if bullet.rect.colliderect(wall):
                    bullets.remove(bullet)
                    break  # Break incase two walls are hit

        redraw_window(player, player2, map.walls, bullets, [], [], FLOOR_IMAGE, text_boxes, [], [])

        # Debugging mode
        if debugging:
            draw_debugging_tools(player, [], bullets, [], map.player_spawns, clock)

        pygame.display.update()

    pygame.mouse.set_visible(True)
    outcome_screen(message)


def outcome_screen(outcome):
    outcome_text = Text((SCREEN_WIDTH / 2, 200), f"You {outcome}", get_font(70), "black")

    main_menu_button = Button((SCREEN_WIDTH / 2, 700), "Main Menu", get_font(50), "black", "grey")

    while True:
        SCREEN.blit(BACKGROUND_IMAGE, (0, 0))

        outcome_text.draw()

        main_menu_button.draw()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if main_menu_button.check_for_input(pygame.mouse.get_pos()):
                    return

        pygame.display.update()


if __name__ == '__main__':
    main_menu()
