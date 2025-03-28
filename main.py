import pygame
import random
import math

pygame.init()

# --- Screen & Simulation Parameters ---
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Disease Spread Simulation")

POPULATION_SIZE = 100
INITIAL_INFECTED = 5
INFECTION_RADIUS = 10
INFECTION_RATE = 0.9
RECOVERY_RATE = 0.01
MORTALITY_RATE = 0.002

FPS = 30
STUCK_TIME_SECONDS = 1.5
STUCK_FRAMES_THRESHOLD = STUCK_TIME_SECONDS * FPS  # 5s * 30fps = 150

# --- Reinfection Toggle ---
ALLOW_REINFECTION = True  # Change to True if recovered people can be reinfected

# --- River & Bridge Properties ---
RIVER_X = WIDTH // 2 - 50
RIVER_WIDTH = 100
BRIDGE_Y = 250
BRIDGE_HEIGHT = 100
BRIDGE_RECT = (RIVER_X, BRIDGE_Y, RIVER_WIDTH, BRIDGE_HEIGHT)

# --- Food Properties ---
NUM_FOOD_ITEMS = 5
FOOD_RADIUS = 5
FOOD_INFECTION_PROBABILITY = 0.15

# --- Colors ---
WHITE = (255, 255, 255)
RED = (255, 0, 0)       # Infected
GREEN = (0, 255, 0)     # Healthy
BLUE = (0, 0, 255)      # Recovered
BLACK = (0, 0, 0)       # Dead
BROWN = (139, 69, 19)   # Food
CYAN = (0, 255, 255)    # River
GRAY = (160, 160, 160)  # Bridge

# --- Helper: Spawn outside river (or on the bridge) ---
def random_position_outside_river():
    """
    Returns (x, y) coordinates that are NOT inside the river,
    unless it's on the bridge rectangle.
    """
    while True:
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        in_river = (RIVER_X <= x <= RIVER_X + RIVER_WIDTH)
        in_bridge = (BRIDGE_RECT[0] <= x <= BRIDGE_RECT[0] + BRIDGE_RECT[2] and
                     BRIDGE_RECT[1] <= y <= BRIDGE_RECT[1] + BRIDGE_RECT[3])

        # Valid if outside river OR inside the bridge
        if not in_river or in_bridge:
            return x, y

# --- Person Class ---
class Person:
    def __init__(self):
        self.x, self.y = random_position_outside_river()
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.status = "healthy"  # healthy, infected, recovered, dead
        self.time_infected = 0
        self.target_food = None
        self.stuck_frames = 0  # how many frames they've been "stuck"

    def move(self):
        if self.status == "dead":
            return

        old_x, old_y = self.x, self.y

        # Move toward food if assigned
        if self.target_food:
            fx, fy = self.target_food
            dx, dy = fx - self.x, fy - self.y
            dist = math.hypot(dx, dy)
            if dist < 2:
                # Reached the food
                self.target_food = None
                # Possibly infected by food
                if self.status == "healthy" and random.random() < FOOD_INFECTION_PROBABILITY:
                    self.status = "infected"
            else:
                self.x += (dx / dist) * 1.5
                self.y += (dy / dist) * 1.5
        else:
            # Random movement
            self.x += self.vx
            self.y += self.vy

        # Bounce off screen edges
        if self.x <= 0 or self.x >= WIDTH:
            self.vx *= -1
        if self.y <= 0 or self.y >= HEIGHT:
            self.vy *= -1

        # Check if inside the river region
        in_river = (RIVER_X <= self.x <= RIVER_X + RIVER_WIDTH)
        # Check if inside the bridge
        in_bridge = (BRIDGE_RECT[0] <= self.x <= BRIDGE_RECT[0] + BRIDGE_RECT[2] and
                     BRIDGE_RECT[1] <= self.y <= BRIDGE_RECT[1] + BRIDGE_RECT[3])

        # If in the river but not in the bridge, revert and randomize
        if in_river and not in_bridge:
            self.x, self.y = old_x, old_y
            self.vx = random.uniform(-2, 2)
            self.vy = random.uniform(-2, 2)

        # Check how far we've moved this frame
        dist_moved = math.hypot(self.x - old_x, self.y - old_y)
        if dist_moved < 0.1:
            self.stuck_frames += 1
        else:
            self.stuck_frames = 0

        # If stuck for too long, respawn
        if self.stuck_frames > STUCK_FRAMES_THRESHOLD:
            self.respawn()

    def respawn(self):
        """
        Respawn at a new random location (outside the river or on the bridge),
        preserving infection status but resetting movement.
        """
        self.x, self.y = random_position_outside_river()
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.stuck_frames = 0  # reset stuck timer

    def infect(self):
        """
        Infect this person if:
          - They are healthy, OR
          - They are recovered AND ALLOW_REINFECTION is True
        """
        if self.status == "healthy":
            self.status = "infected"
            self.time_infected = 0
        elif ALLOW_REINFECTION and self.status == "recovered":
            self.status = "infected"
            self.time_infected = 0

    def update_status(self):
        if self.status == "infected":
            self.time_infected += 1
            # Chance to recover
            if random.random() < RECOVERY_RATE:
                self.status = "recovered"
            # Chance to die
            elif random.random() < MORTALITY_RATE:
                self.status = "dead"

# --- Create Population ---
population = [Person() for _ in range(POPULATION_SIZE)]
for i in range(INITIAL_INFECTED):
    population[i].infect()

# --- Generate Food Items ---
food_items = [
    (random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50))
    for _ in range(NUM_FOOD_ITEMS)
]

# --- Main Simulation Loop ---
running = True
clock = pygame.time.Clock()

while running:
    screen.fill(WHITE)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Draw the river (cyan)
    pygame.draw.rect(screen, CYAN, (RIVER_X, 0, RIVER_WIDTH, HEIGHT))

    # Draw the "full" bridge (gray rectangle)
    pygame.draw.rect(screen, GRAY, BRIDGE_RECT)

    # Draw food
    for food in food_items:
        pygame.draw.circle(screen, BROWN, food, FOOD_RADIUS)

    # Track stats
    healthy_count = 0
    infected_count = 0
    recovered_count = 0
    dead_count = 0

    # Update and draw each person
    for person in population:
        person.move()
        person.update_status()

        # Randomly pick a food target sometimes
        if random.random() < 0.002 and person.target_food is None:
            person.target_food = random.choice(food_items)

        # Determine color based on status
        if person.status == "dead":
            color = BLACK
            dead_count += 1
        elif person.status == "infected":
            color = RED
            infected_count += 1
        elif person.status == "recovered":
            color = BLUE
            recovered_count += 1
        else:
            color = GREEN
            healthy_count += 1

        pygame.draw.circle(screen, color, (int(person.x), int(person.y)), 5)

    # Infection checks
    for i in range(POPULATION_SIZE):
        for j in range(i + 1, POPULATION_SIZE):
            p1, p2 = population[i], population[j]
            # If they are close enough
            dist = math.hypot(p1.x - p2.x, p1.y - p2.y)
            if dist < INFECTION_RADIUS and random.random() < INFECTION_RATE:
                # Infect the other if one is infected
                if p1.status == "infected":
                    p2.infect()
                if p2.status == "infected":
                    p1.infect()

    # Display stats (bottom-right)
    font = pygame.font.Font(None, 24)
    stats_text = [
        f"Healthy: {healthy_count}",
        f"Infected: {infected_count}",
        f"Recovered: {recovered_count}",
        f"Dead: {dead_count}"
    ]
    y_offset = HEIGHT - 80
    for text in stats_text:
        render = font.render(text, True, BLACK)
        screen.blit(render, (WIDTH - 150, y_offset))
        y_offset += 20

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()