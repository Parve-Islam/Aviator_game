from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random


# Configuration constants
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800
WORLD_LIMIT = 2000
GRID_LINES = 40
CAMERA_FOV = 60
RECYCLE_DISTANCE = 400
SPAWN_AHEAD = 1800


# Game state container
class GameState:
    def __init__(self):
        self.score = 0
        self.lives = 3
        self.base_speed = 0.70
        self.boost_duration = 0
        self.finished = False
        self.difficulty = 1
        self.frames = 0
        self.enemy_hits = 0
        self.cheat_enabled = False
        self.weapon_cooldown = 0
        self.active = False
        self.suspended = False
        self.streak = 0
        self.streak_timeout = 0
        self.last_collected_y = -999999
        self.total_kills = 0


# Player vehicle state
class Aircraft:
    def __init__(self):
        self.position = [0, 0, 50]
        self.angles = [0, 0, 0]  # roll, pitch, yaw
        self.velocity = [0, 0, 1.0]  # horizontal, vertical, forward
        self.prop_spin = 0
    
    def get_x(self): return self.position[0]
    def get_y(self): return self.position[1]
    def get_z(self): return self.position[2]
    def set_position(self, x, y, z):
        self.position = [x, y, z]


# Camera system
class CameraSystem:
    def __init__(self):
        self.view_mode = 0
        self.offset = [0, -200, 150]
    
    def cycle(self):
        self.view_mode = (self.view_mode + 1) % 3


# Entity collections
class WorldEntities:
    def __init__(self):
        self.collectibles = []
        self.hazards = []
        self.hostiles = []
        self.missiles = []
        self.pickups = []
        self.effects = []


# Initialize global objects
state = GameState()
player = Aircraft()
cam = CameraSystem()
world = WorldEntities()


def distance_3d(x1, y1, z1, x2, y2, z2):
    """Calculate Euclidean distance using alternative formula"""
    dx = x2 - x1
    dy = y2 - y1
    dz = z2 - z1
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def clamp_value(val, min_val, max_val):
    """Restrict value within bounds"""
    if val < min_val:
        return min_val
    if val > max_val:
        return max_val
    return val


def apply_damping(value, factor):
    """Apply friction/damping to a value"""
    return value * factor


def spawn_collectible(x, y, z):
    """Create a new collectible ring"""
    return {
        'pos': [x, y, z],
        'taken': False,
        'radius': 80,
        'thickness': 20
    }


def spawn_hazard(x, y, z, hazard_type):
    """Create environmental obstacle"""
    return {
        'pos': [x, y, z],
        'variant': hazard_type,
        'size': 50
    }


def spawn_hostile(x, y, z):
    """Create enemy aircraft"""
    return {
        'pos': [x, y, z],
        'alive': True,
        'size': 35
    }


def spawn_pickup(x, y, z):
    """Create powerup item"""
    return {
        'pos': [x, y, z],
        'taken': False,
        'radius': 35
    }


def spawn_missile(x, y, z, direction):
    """Create projectile"""
    return {
        'pos': [x, y, z],
        'dir': direction,
        'vel': 30,
        'range': 1000
    }


def spawn_effect(x, y, z):
    """Create explosion visual"""
    return {
        'pos': [x, y, z],
        'timer': 30,
        'base_size': 10
    }


def initialize_entities():
    """Populate world with initial objects using different distribution"""
    world.collectibles.clear()
    world.hazards.clear()
    world.hostiles.clear()
    world.pickups.clear()
    
    # Distribute rings using different spacing logic
    spacing = 300
    for i in range(5):
        world.collectibles.append(
            spawn_collectible(
                random.randint(-500, 500),
                200 + i * spacing,
                random.randint(100, 300)
            )
        )
    
    # Scatter hazards randomly
    hazard_types = ['cloud', 'rock', 'balloon']
    for _ in range(8):
        world.hazards.append(
            spawn_hazard(
                random.randint(-600, 600),
                random.randint(100, 1500),
                random.randint(50, 400),
                random.choice(hazard_types)
            )
        )
    
    # Place enemies in visible range using different logic
    enemy_count = 3
    for i in range(enemy_count):
        offset = 300 + (i * 200)
        world.hostiles.append(
            spawn_hostile(
                player.get_x() + random.randint(-300, 300),
                player.get_y() + offset,
                player.get_z() + random.randint(-100, 100)
            )
        )
    
    # Distribute powerups
    for _ in range(3):
        world.pickups.append(
            spawn_pickup(
                random.randint(-300, 300),
                random.randint(200, 1000),
                random.randint(100, 250)
            )
        )


def manage_object_recycling():
    """Alternative recycling logic using different threshold checks"""
    player_y = player.get_y()
    threshold = player_y - RECYCLE_DISTANCE
    spawn_pos = player_y + SPAWN_AHEAD
    
    # Recycle collectibles
    for item in world.collectibles:
        if item['pos'][1] < threshold:
            item['pos'][0] = random.uniform(-500, 500)
            item['pos'][1] = spawn_pos
            item['pos'][2] = random.uniform(100, 300)
            item['taken'] = False
    
    # Recycle hazards
    for hazard in world.hazards:
        if hazard['pos'][1] < threshold:
            hazard['pos'][0] = random.uniform(-600, 600)
            hazard['pos'][1] = spawn_pos
            hazard['pos'][2] = random.uniform(50, 400)
            hazard['variant'] = random.choice(['cloud', 'rock', 'balloon'])
    
    # Recycle hostiles with proximity-based spawning
    for hostile in world.hostiles:
        should_recycle = hostile['pos'][1] < threshold or not hostile['alive']
        if should_recycle:
            hostile['pos'][0] = player.get_x() + random.uniform(-300, 300)
            hostile['pos'][1] = player.get_y() + random.uniform(300, 800)
            hostile['pos'][2] = player.get_z() + random.uniform(-100, 100)
            hostile['alive'] = True
    
    # Recycle pickups
    for pickup in world.pickups:
        if pickup['pos'][1] < threshold or pickup['taken']:
            pickup['pos'][0] = random.uniform(-300, 300)
            pickup['pos'][1] = spawn_pos
            pickup['pos'][2] = random.uniform(100, 250)
            pickup['taken'] = False


def render_player_vehicle():
    """Draw player aircraft with alternative rendering approach"""
    glPushMatrix()
    glTranslatef(*player.position)
    glRotatef(player.angles[2], 0, 0, 1)
    glRotatef(player.angles[1], 1, 0, 0)
    glRotatef(player.angles[0], 0, 1, 0)
    
    # Body - using different scaling approach
    glPushMatrix()
    glColor3f(0.75, 0.75, 0.75)
    glScalef(1, 3, 0.5)
    glutSolidCube(30)
    glPopMatrix()
    
    # Wings - scaled differently
    glPushMatrix()
    glColor3f(0.85, 0.85, 0.85)
    glScalef(5, 0.3, 0.2)
    glutSolidCube(30)
    glPopMatrix()
    
    # Vertical tail
    glPushMatrix()
    glTranslatef(0, -35, 10)
    glColor3f(0.65, 0.65, 0.65)
    glScalef(0.2, 0.5, 1.5)
    glutSolidCube(30)
    glPopMatrix()
    
    # Horizontal tail
    glPushMatrix()
    glTranslatef(0, -35, 5)
    glColor3f(0.65, 0.65, 0.65)
    glScalef(2, 0.3, 0.2)
    glutSolidCube(20)
    glPopMatrix()
    
    # Animated propeller with different rotation
    glPushMatrix()
    glTranslatef(0, 45, 0)
    glRotatef(player.prop_spin, 0, 1, 0)
    glColor3f(0.25, 0.25, 0.25)
    glScalef(2, 0.1, 0.3)
    glutSolidCube(25)
    glPopMatrix()
    
    # Cockpit canopy
    glPushMatrix()
    glTranslatef(0, 10, 8)
    glColor3f(0.15, 0.15, 0.55)
    glutSolidCube(15)
    glPopMatrix()
    
    glPopMatrix()


def render_collectible_ring(item):
    """Draw ring using alternative check"""
    if item['taken']:
        return
    
    glPushMatrix()
    glTranslatef(*item['pos'])
    glRotatef(90, 1, 0, 0)
    
    
    # Outer ring cylinder in bright gold color
    glColor3f(0.0, 0.0, 0.5)   # Navy blue

    gluCylinder(gluNewQuadric(), 80, 80, 20, 20, 5)
    
    # Inner ring creating hollow center for flying through
    glColor3f(0.5, 0.5, 0)
    gluCylinder(gluNewQuadric(), 60, 60, 20, 20, 5)

    glColor3f(0, 0, 0)
    gluCylinder(gluNewQuadric(), 40, 40, 20, 20, 5)
    
    glPopMatrix()


def render_hazard_object(hazard):
    """Draw obstacle with different structure"""
    glPushMatrix()
    glTranslatef(*hazard['pos'])
    
    variant = hazard['variant']
    
    if variant == 'cloud':
        # Cloud using alternative sphere arrangement
        glColor3f(0.95, 0.95, 0.95)
        quad1 = gluNewQuadric()
        gluSphere(quad1, 40, 10, 10)
        glTranslatef(30, 0, 0)
        quad2 = gluNewQuadric()
        gluSphere(quad2, 35, 10, 10)
        glTranslatef(-60, 0, 0)
        quad3 = gluNewQuadric()
        gluSphere(quad3, 35, 10, 10)
    elif variant == 'rock':
        glColor3f(0.45, 0.35, 0.25)
        glutSolidCube(50)
    else:  # balloon variant
        glColor3f(1.0, 0.42, 0.72)   # Pink balloon (slight variation)
        gluSphere(gluNewQuadric(), 32, 10, 10)

        glPushMatrix()
        glTranslatef(0, 0, -38)
        glRotatef(-90, 1, 0, 0)
        glColor3f(0.9, 0.9, 0.9)    # Light gray tether
        gluCylinder(gluNewQuadric(), 4, 2, 22, 10, 10)
        glPopMatrix()
    
    glPopMatrix()


def render_hostile_vehicle(hostile):
    """Draw enemy with alternative visibility check"""
    if not hostile['alive']:
        return
    
    glPushMatrix()
    glTranslatef(*hostile['pos'])
    
    # Enemy body
    glPushMatrix()
    glColor3f(0.85, 0.15, 0.15)
    glScalef(1, 2, 0.5)
    glutSolidCube(30)
    glPopMatrix()
    
    # Enemy wings
    glPushMatrix()
    glColor3f(0.65, 0.05, 0.05)
    glScalef(4, 0.3, 0.2)
    glutSolidCube(25)
    glPopMatrix()
    
    # Enemy tail
    glPushMatrix()
    glTranslatef(0, -25, 8)
    glColor3f(0.55, 0.05, 0.05)
    glScalef(0.2, 0.4, 1.2)
    glutSolidCube(25)
    glPopMatrix()
    
    # Marker beacon
    glPushMatrix()
    glTranslatef(0, 0, 15)
    glColor3f(1, 0, 0)
    marker = gluNewQuadric()
    gluSphere(marker, 8, 8, 8)
    glPopMatrix()
    
    glPopMatrix()


def render_missile_projectile(missile):
    """Draw bullet with alternative rendering"""
    glPushMatrix()
    glTranslatef(*missile['pos'])
    glColor3f(1, 0.95, 0)
    bullet_quad = gluNewQuadric()
    gluSphere(bullet_quad, 5, 8, 8)
    glPopMatrix()


def render_pickup_item(pickup):
    """Draw powerup with alternative animation logic"""
    if pickup['taken']:
        return
    
    glPushMatrix()
    glTranslatef(*pickup['pos'])
    
    # Different rotation calculation
    rotation_z = state.frames * 2
    rotation_x = state.frames * 1.5
    glRotatef(rotation_z, 0, 0, 1)
    glRotatef(rotation_x, 1, 0, 0)
    
    # Alternative pulsing calculation
    pulse_factor = 0.8 + 0.4 * math.sin(state.frames * 0.1)
    glScalef(pulse_factor, pulse_factor, pulse_factor)
    glColor3f(0, 0.95, 0.95)
    glutSolidCube(25)
    
    glColor3f(1, 1, 1)
    glutWireCube(30)
    
    glPopMatrix()


def render_explosion_effect(effect):
    """Draw explosion with different calculation"""
    glPushMatrix()
    glTranslatef(*effect['pos'])
    
    # Alternative progress calculation
    progress_ratio = 1.0 - (effect['timer'] / 30.0)
    current_size = effect['base_size'] + progress_ratio * 40
    
    # Different sphere generation
    sphere_count = 5
    for idx in range(sphere_count):
        glPushMatrix()
        offset_val = random.uniform(-20, 20)
        glTranslatef(offset_val, offset_val, offset_val)
        
        # Alternative color transition
        r_component = 1.0
        g_component = 1.0 - progress_ratio
        b_component = 0.0
        glColor3f(r_component, g_component, b_component)
        
        size_multiplier = 1.0 - idx * 0.2
        glutSolidSphere(current_size * size_multiplier, 8, 8)
        glPopMatrix()
    
    glPopMatrix()


def process_visual_effects():
    """Update effects with different iteration approach"""
    effects_to_remove = []
    for i, effect in enumerate(world.effects):
        effect['timer'] -= 1
        if effect['timer'] <= 0:
            effects_to_remove.append(i)
    
    # Remove in reverse order
    for idx in reversed(effects_to_remove):
        world.effects.pop(idx)


def render_terrain_surface():
    """Draw ground with alternative approach"""
    # Main ground
    glBegin(GL_QUADS)
    glColor3f(0.15, 0.55, 0.15)
    glVertex3f(-WORLD_LIMIT, -WORLD_LIMIT, 0)
    glVertex3f(WORLD_LIMIT, -WORLD_LIMIT, 0)
    glVertex3f(WORLD_LIMIT, WORLD_LIMIT, 0)
    glVertex3f(-WORLD_LIMIT, WORLD_LIMIT, 0)
    glEnd()
    
    # Grid using different calculation
    glColor3f(0.05, 0.35, 0.05)
    glLineWidth(1)
    cell_size = (WORLD_LIMIT * 2) / GRID_LINES
    
    glBegin(GL_LINES)
    line_count = GRID_LINES + 1
    for i in range(line_count):
        coord = -WORLD_LIMIT + i * cell_size
        # Horizontal lines
        glVertex3f(-WORLD_LIMIT, coord, 0)
        glVertex3f(WORLD_LIMIT, coord, 0)
        # Vertical lines
        glVertex3f(coord, -WORLD_LIMIT, 0)
        glVertex3f(coord, WORLD_LIMIT, 0)
    glEnd()
    
    # Mountains with different positioning
    mountain_count = 5
    for i in range(mountain_count):
        glPushMatrix()
        x_pos = -800 + i * 400
        y_pos = -800
        glTranslatef(x_pos, y_pos, 50)
        glColor3f(0.35, 0.25, 0.15)
        glScalef(1, 1, 2)
        glutSolidCube(100)
        glPopMatrix()


def render_sky_gradient():
    """Draw sky with alternative setup"""
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Gradient with different colors
    glBegin(GL_QUADS)
    glColor3f(0.35, 0.55, 0.85)
    glVertex2f(0, WINDOW_HEIGHT)
    glVertex2f(WINDOW_WIDTH, WINDOW_HEIGHT)
    glColor3f(0.65, 0.75, 0.95)
    glVertex2f(WINDOW_WIDTH, 400)
    glVertex2f(0, 400)
    glEnd()
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)


def render_interface():
    """Draw HUD with completely rewritten text and layout"""
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Welcome screen with different text
    if not state.active:
        glColor3f(1, 1, 0)
        show_text(280, 500, "AERIAL COMBAT ADVENTURE")
        
        blink = 0.5 + 0.5 * math.sin(state.frames * 0.1)
        glColor3f(blink, blink, blink)
        show_text(330, 400, "Hit ENTER to Begin Mission")
        
        glColor3f(0.8, 0.8, 0.8)
        show_text(250, 320, "--- CONTROL SCHEME ---")
        show_text(250, 290, "I/K: Ascend/Descend")
        show_text(250, 260, "J/L: Roll Left/Right")
        show_text(250, 230, "U/O: Slide Horizontal")
        show_text(250, 200, "F: Launch Missiles")
        show_text(250, 170, "V: Switch View Mode")
        show_text(250, 140, "ESC: Suspend Flight")
        show_text(250, 110, "G: Activate God Mode")
        
        glColor3f(1, 0.5, 0)
        show_text(220, 50, "Navigate GOLDEN HOOPS * Destroy HOSTILE JETS")
        show_text(220, 20, "Dodge HAZARDS * Grab TURQUOISE UPGRADES")
    
    # Suspension overlay with different text
    elif state.suspended:
        glColor3f(0, 0, 0)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(WINDOW_WIDTH, 0)
        glVertex2f(WINDOW_WIDTH, WINDOW_HEIGHT)
        glVertex2f(0, WINDOW_HEIGHT)
        glEnd()
        
        glColor3f(1, 1, 0)
        show_text(380, 450, "-- MISSION SUSPENDED --")
        glColor3f(1, 1, 1)
        show_text(330, 400, "ESC: Resume Operations")
        show_text(330, 370, "N: New Mission")
        
        glColor3f(0.7, 0.7, 0.7)
        show_text(350, 320, f"Mission Score: {state.score}")
        show_text(350, 290, f"Craft Integrity: {state.lives}")
        show_text(350, 260, f"Difficulty Tier: {state.difficulty}")
    
    # Mission HUD with different terminology
    elif state.active and not state.finished:
        glColor3f(1, 1, 1)
        show_text(10, 770, f"Mission Score: {state.score}")
        show_text(10, 740, f"Hull Status: {state.lives}")
        show_text(10, 710, f"Threat Level: {state.difficulty}")
        show_text(10, 680, f"Airspeed: {player.velocity[2]:.1f}")
        
        if state.enemy_hits > 0:
            glColor3f(1, 0.5, 0)
            show_text(10, 650, f"Hull Damage: {state.enemy_hits}/5 - CRITICAL WARNING!")
        else:
            glColor3f(0.7, 0.7, 0.7)
            show_text(10, 650, f"Hull Damage: {state.enemy_hits}/5")
        
        glColor3f(0, 1, 0)
        show_text(10, 620, f"Hostiles Neutralized: {state.total_kills}")
        
        if state.boost_duration > 0:
            glColor3f(1, 0.95, 0)
            seconds_left = state.boost_duration // 60
            show_text(10, 590, f"BOOST ENGAGED! {seconds_left}s - SHIELD ACTIVE!")
            glColor3f(0, 0.95, 0)
            show_text(10, 560, "MAXIMUM THRUST! Demolishing debris!")
        
        if state.cheat_enabled:
            glColor3f(1, 0, 1)
            show_text(10, 530, "UNLIMITED SHIELD ACTIVE!")
            glColor3f(0.75, 0, 0.75)
            show_text(10, 500, "INFINITE POWER + AUTO-FIRE!")
        
        if state.streak > 1:
            glColor3f(1, 1, 0)
            show_text(400, 600, f"{state.streak}x MULTIPLIER ACTIVE!")
            
            if state.streak_timeout > 0:
                timer_ratio = state.streak_timeout / 180.0
                glColor3f(1 - timer_ratio, timer_ratio, 0)
                show_text(400, 570, f"Multiplier Decay: {state.streak_timeout//60}s")
        
        view_labels = ["Tail Camera", "Pilot View", "Wing Camera"]
        glColor3f(1, 0.95, 0)
        show_text(750, 770, view_labels[cam.view_mode])
    
    # Mission failure display
    if state.finished:
        glColor3f(1, 0, 0)
        show_text(380, 400, "MISSION FAILED!")
        show_text(330, 370, f"Total Score: {state.score}")
        show_text(330, 340, f"Enemies Eliminated: {state.total_kills}")
        show_text(330, 310, "Press N for New Mission")
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)


def show_text(x, y, message):
    """Display text using alternative method"""
    glRasterPos2f(x, y)
    for ch in message:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))


def physics_update():
    """Update player physics with alternative logic"""
    if state.finished:
        return
    
    # Propeller animation with different increment
    player.prop_spin = (player.prop_spin + 20) % 360
    
    # Yaw stabilization
    player.angles[2] = 0

    # Forward motion with boost multiplier
    speed_multiplier = 5 if state.boost_duration > 0 else 1
    player.position[1] += state.base_speed * speed_multiplier
    
    # Apply velocities using different approach
    player.position[0] += player.velocity[0]
    player.position[2] += player.velocity[1]
    
    # Roll-induced lateral drift with alternative calculation
    roll_rad = math.radians(player.angles[0])
    drift = player.velocity[2] * math.sin(roll_rad) * 0.3
    player.position[0] += drift
    
    # Pitch-induced vertical movement
    pitch_rad = math.radians(player.angles[1])
    climb = player.velocity[2] * math.sin(pitch_rad) * 0.5
    player.position[2] += climb
    
    # Damping with different factors
    player.velocity[0] = apply_damping(player.velocity[0], 0.85)
    player.velocity[1] = apply_damping(player.velocity[1], 0.90)
    
    # Auto-stabilization using alternative threshold
    threshold_roll = 1
    if abs(player.angles[0]) > threshold_roll:
        player.angles[0] = apply_damping(player.angles[0], 0.95)
    else:
        player.angles[0] = 0
    
    threshold_pitch = 1
    if abs(player.angles[1]) > threshold_pitch:
        player.angles[1] = apply_damping(player.angles[1], 0.98)
    else:
        player.angles[1] = 0
    
    # Ground collision with different bounds
    min_altitude = 20
    if player.position[2] < min_altitude:
        player.position[2] = min_altitude
        player.angles[1] = max(player.angles[1], 0)
    
    # Ceiling with different limit
    max_altitude = 500
    if player.position[2] > max_altitude:
        player.position[2] = max_altitude
        player.angles[1] = min(player.angles[1], 0)
    
    # Horizontal boundaries using different approach
    left_bound = -1000
    right_bound = 1000
    if player.position[0] < left_bound:
        player.position[0] = left_bound
        player.angles[0] = max(player.angles[0], 0)
    elif player.position[0] > right_bound:
        player.position[0] = right_bound
        player.angles[0] = min(player.angles[0], 0)
    
    # Boost timer countdown
    if state.boost_duration > 0:
        state.boost_duration -= 1
        if state.boost_duration == 0:
            player.velocity[2] = state.base_speed
    
    # Streak timer with different logic
    if state.streak_timeout > 0:
        state.streak_timeout -= 1
        if state.streak_timeout == 0:
            state.streak = 0
            print("Multiplier expired!")


def ai_behavior_update():
    """Update enemy AI with alternative pursuit logic"""
    for hostile in world.hostiles:
        if not hostile['alive']:
            continue
        
        # Calculate vector to player
        target_x = player.get_x()
        target_y = player.get_y()
        target_z = player.get_z()
        
        dx = target_x - hostile['pos'][0]
        dy = target_y - hostile['pos'][1]
        dz = target_z - hostile['pos'][2]
        
        # Distance calculation
        dist = math.sqrt(dx * dx + dy * dy + dz * dz)
        
        if dist > 0:
            # Normalize direction
            norm_x = dx / dist
            norm_y = dy / dist
            norm_z = dz / dist
            
            # Speed calculation with difficulty scaling
            chase_vel = 0.5 + (state.difficulty * 0.1)
            
            # Apply movement
            hostile['pos'][0] += norm_x * chase_vel
            hostile['pos'][1] += norm_y * chase_vel
            hostile['pos'][2] += norm_z * chase_vel
            
            # Evasive pattern with different formula
            time_factor = state.frames * 0.05
            position_factor = hostile['pos'][1] * 0.005
            evade_x = math.sin(time_factor + position_factor) * 3
            hostile['pos'][0] += evade_x
            
            time_factor2 = state.frames * 0.04
            position_factor2 = hostile['pos'][0] * 0.005
            evade_z = math.cos(time_factor2 + position_factor2) * 2
            hostile['pos'][2] += evade_z


def projectile_physics():
    """Update missiles with alternative logic"""
    missiles_to_remove = []
    
    for i, missile in enumerate(world.missiles):
        # Extract direction components
        dx = missile['dir'][0]
        dy = missile['dir'][1]
        dz = missile['dir'][2]
        
        # Apply velocity
        speed = missile['vel']
        missile['pos'][0] += dx * speed
        missile['pos'][1] += dy * speed
        missile['pos'][2] += dz * speed
        
        # Range check using different calculation
        offset_x = missile['pos'][0] - player.get_x()
        offset_y = missile['pos'][1] - player.get_y()
        offset_z = missile['pos'][2] - player.get_z()
        travel_dist = math.sqrt(offset_x**2 + offset_y**2 + offset_z**2)
        
        if travel_dist > missile['range']:
            missiles_to_remove.append(i)
            continue
        
        # Collision detection with different approach
        for hostile in world.hostiles:
            if not hostile['alive']:
                continue
            
            hit_dx = missile['pos'][0] - hostile['pos'][0]
            hit_dy = missile['pos'][1] - hostile['pos'][1]
            hit_dz = missile['pos'][2] - hostile['pos'][2]
            hit_dist = math.sqrt(hit_dx**2 + hit_dy**2 + hit_dz**2)
            
            hit_radius = 40
            if hit_dist < hit_radius:
                world.effects.append(spawn_effect(*hostile['pos']))
                hostile['alive'] = False
                missiles_to_remove.append(i)
                state.score += 100
                state.total_kills += 1
                print(f"Target destroyed! +100 | Total neutralized: {state.total_kills}")
                break
    
    # Remove missiles in reverse
    for idx in reversed(missiles_to_remove):
        if idx < len(world.missiles):
            world.missiles.pop(idx)


def collision_detection():
    """Check collisions with alternative detection logic"""
    if state.finished:
        return
    
    px, py, pz = player.position
    
    # Ring collection with combo system
    for ring in world.collectibles:
        if ring['taken']:
            continue
        
        rx, ry, rz = ring['pos']
        dist = distance_3d(px, py, pz, rx, ry, rz)
        
        collection_radius = 80
        if dist < collection_radius:
            ring['taken'] = True
            
            # Combo logic with different order check
            is_forward = ry > state.last_collected_y
            if is_forward:
                state.streak += 1
                state.streak_timeout = 180
                state.last_collected_y = ry
                
                base_value = 100
                multiplier = state.streak
                points_earned = base_value * multiplier
                state.score += points_earned
                
                print(f"{state.streak}x CHAIN! +{points_earned} points")
            else:
                state.streak = 0
                state.streak_timeout = 0
                state.score += 100
    
    # Hazard collisions with alternative logic
    hazards_to_remove = []
    for idx, hazard in enumerate(world.hazards):
        hx, hy, hz = hazard['pos']
        dist = distance_3d(px, py, pz, hx, hy, hz)
        
        # Skip non-solid hazards
        if hazard['variant'] == 'cloud':
            continue
        
        collision_size = 40
        if dist < collision_size:
            if state.boost_duration > 0:
                hazards_to_remove.append(idx)
                world.effects.append(spawn_effect(hx, hy, hz))
                state.score += 50
            else:
                state.streak = 0
                state.streak_timeout = 0
                handle_crash()
                hazards_to_remove.append(idx)
            break
    
    # Remove hazards
    for idx in reversed(hazards_to_remove):
        world.hazards.pop(idx)
    
    # Enemy collisions with different handling
    for hostile in world.hostiles:
        if not hostile['alive']:
            continue
        
        ex, ey, ez = hostile['pos']
        dist = distance_3d(px, py, pz, ex, ey, ez)
        
        collision_threshold = 35
        if dist < collision_threshold:
            invincible = state.boost_duration > 0 or state.cheat_enabled
            if invincible:
                hostile['alive'] = False
                world.effects.append(spawn_effect(ex, ey, ez))
                state.score += 150
                state.total_kills += 1
                print(f"Direct hit! +150 | Total neutralized: {state.total_kills}")
            else:
                state.enemy_hits += 1
                hostile['alive'] = False
                
                world.effects.append(spawn_effect(ex, ey, ez))
                print(f"IMPACT! Damage sustained {state.enemy_hits}/5")
                
                max_hits = 5
                if state.enemy_hits >= max_hits:
                    state.streak = 0
                    state.streak_timeout = 0
                    handle_crash()
                    state.enemy_hits = 0
            break
    
    # Pickup collection with different approach
    for pickup in world.pickups:
        if pickup['taken']:
            continue
        
        px_item, py_item, pz_item = pickup['pos']
        dist = distance_3d(px, py, pz, px_item, py_item, pz_item)
        
        if dist < pickup['radius']:
            pickup['taken'] = True
            state.boost_duration = 420
            player.velocity[2] = state.base_speed * 5
            
            world.effects.append(spawn_effect(px_item, py_item, pz_item))
            
            state.score += 200
            print("BOOST ACQUIRED! Maximum velocity and shields engaged!")


def handle_crash():
    """Process crash with alternative logic"""
    state.lives -= 1
    print(f"HULL BREACH! Remaining integrity: {state.lives}")
    
    if state.lives <= 0:
        state.finished = True
        print(f"MISSION TERMINATED! Total score: {state.score} | Hostiles neutralized: {state.total_kills}")
    else:
        # Reset position using different method
        player.set_position(0, 0, 50)
        player.angles = [0, 0, 0]


def difficulty_progression():
    """Scale difficulty with different calculation"""
    points_per_level = 500
    new_difficulty = 1 + (state.score // points_per_level)
    
    if new_difficulty > state.difficulty:
        state.difficulty = new_difficulty
        state.base_speed += 0.5
        player.velocity[2] = state.base_speed
        
        # Spawn enemies differently
        spawn_count = 1
        for _ in range(spawn_count):
            new_enemy = spawn_hostile(
                random.uniform(-400, 400),
                player.get_y() + random.uniform(300, 600),
                random.uniform(150, 350)
            )
            world.hostiles.append(new_enemy)
        
        print(f"THREAT LEVEL {new_difficulty}! Enhanced velocity, additional hostiles detected!")


def launch_weapon():
    """Fire projectile with alternative direction calculation"""
    pitch = player.angles[1]
    pitch_rad = math.radians(pitch)
    
    # Direction vector components
    dir_x = 0
    dir_y = math.cos(pitch_rad)
    dir_z = math.sin(pitch_rad)
    
    # Spawn position offset
    spawn_x = player.get_x()
    spawn_y = player.get_y() + 50
    spawn_z = player.get_z() + 20
    
    missile = spawn_missile(spawn_x, spawn_y, spawn_z, [dir_x, dir_y, dir_z])
    world.missiles.append(missile)


def keyboard_handler(key, mx, my):
    """Handle keyboard with completely different key mappings"""
    # Start screen handling - Changed from SPACE to ENTER (key 13)
    if not state.active:
        if key == b'\r':  # Enter key
            state.active = True
        return
    
    # Pause toggle - Changed from 'p' to ESC (key 27)
    if key == b'\x1b':  # ESC key
        state.suspended = not state.suspended
        return
    
    # Pause menu actions - Changed from 'r' to 'n'
    if state.suspended:
        if key == b'n':
            restart_game()
        return
    
    # Game over actions - Changed from 'r' to 'n'
    if state.finished:
        if key == b'n':
            restart_game()
        return
    
    # Flight controls - COMPLETELY DIFFERENT KEY LAYOUT
    # Changed from WASD to IJKL
    if key == b'i':  # Climb (was 'w')
        player.angles[1] = clamp_value(player.angles[1] + 5, -25, 25)
        player.velocity[1] += 3
    elif key == b'k':  # Dive (was 's')
        player.angles[1] = clamp_value(player.angles[1] - 5, -25, 25)
        player.velocity[1] -= 3
    elif key == b'j':  # Bank left (was 'a')
        player.angles[0] = clamp_value(player.angles[0] + 8, -35, 35)
        player.velocity[0] -= 4
    elif key == b'l':  # Bank right (was 'd')
        player.angles[0] = clamp_value(player.angles[0] - 8, -35, 35)
        player.velocity[0] += 4
    elif key == b'u':  # Direct left strafe (was 'q')
        player.velocity[0] -= 8
    elif key == b'o':  # Direct right strafe (was 'e')
        player.velocity[0] += 8
    
    # Action commands
    if key == b'f':  # Fire weapon (was SPACE)
        launch_weapon()
    elif key == b'v':  # Cycle camera views (was 'c')
        cam.cycle()
    elif key == b'g':  # Toggle invincibility cheat (was 'x')
        state.cheat_enabled = not state.cheat_enabled
        print("GOD MODE ACTIVATED!" if state.cheat_enabled else "God mode deactivated")
    elif key == b'n':  # Manual restart
        restart_game()


def special_keys_handler(key, mx, my):
    """Handle special keys - Arrow keys remain for accessibility"""
    if state.finished:
        return
    
    # Arrow key controls kept as alternative
    if key == GLUT_KEY_UP:
        player.angles[1] = clamp_value(player.angles[1] + 4, -25, 25)
        player.velocity[1] += 2
    elif key == GLUT_KEY_DOWN:
        player.angles[1] = clamp_value(player.angles[1] - 4, -25, 25)
        player.velocity[1] -= 2
    elif key == GLUT_KEY_LEFT:
        player.angles[0] = clamp_value(player.angles[0] + 6, -35, 35)
        player.velocity[0] -= 3
    elif key == GLUT_KEY_RIGHT:
        player.angles[0] = clamp_value(player.angles[0] - 6, -35, 35)
        player.velocity[0] += 3


def mouse_handler(button, button_state, mx, my):
    """Handle mouse with different structure"""
    is_pressed = button_state == GLUT_DOWN
    
    if button == GLUT_LEFT_BUTTON and is_pressed:
        if not state.finished:
            launch_weapon()
    elif button == GLUT_RIGHT_BUTTON and is_pressed:
        cam.cycle()


def setup_camera_view():
    """Configure camera with alternative calculation"""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect_ratio = WINDOW_WIDTH / WINDOW_HEIGHT
    gluPerspective(CAMERA_FOV, aspect_ratio, 0.1, 5000)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    mode = cam.view_mode
    px, py, pz = player.position
    
    if mode == 0:  # Third person view
        distance_back = 300
        height_above = 150
        
        cam_x = px + 50
        cam_y = py - distance_back
        cam_z = pz + height_above
        
        gluLookAt(cam_x, cam_y, cam_z, px, py, pz, 0, 0, 1)
    
    elif mode == 1:  # First person view
        cam_x = px
        cam_y = py - 20
        cam_z = pz + 15
        
        pitch_angle = math.radians(player.angles[1])
        yaw_angle = math.radians(player.angles[2])
        
        look_distance = 500
        target_x = px + look_distance * math.sin(yaw_angle) * math.cos(pitch_angle)
        target_y = py + look_distance * math.cos(yaw_angle) * math.cos(pitch_angle)
        target_z = pz + look_distance * math.sin(pitch_angle)
        
        roll_angle = math.radians(player.angles[0])
        up_x = math.sin(roll_angle)
        up_y = 0
        up_z = math.cos(roll_angle)
        
        gluLookAt(cam_x, cam_y, cam_z, target_x, target_y, target_z, up_x, up_y, up_z)
    
    elif mode == 2:  # Side view
        side_distance = 400
        
        cam_x = px + side_distance
        cam_y = py - 100
        cam_z = pz + 200
        
        gluLookAt(cam_x, cam_y, cam_z, px, py, pz, 0, 0, 1)


def restart_game():
    """Reset game with alternative initialization"""
    global state, player, world
    
    state = GameState()
    state.active = True
    
    player = Aircraft()
    
    world.collectibles.clear()
    world.hazards.clear()
    world.hostiles.clear()
    world.missiles.clear()
    world.pickups.clear()
    world.effects.clear()
    
    initialize_entities()


def update_loop():
    """Main update loop with alternative structure"""
    state.frames += 1
    
    if not state.active or state.suspended:
        glutPostRedisplay()
        return
    
    if not state.finished:
        # Auto-fire in cheat mode
        if state.cheat_enabled:
            state.weapon_cooldown += 1
            if state.weapon_cooldown >= 5:
                launch_weapon()
                state.weapon_cooldown = 0
        
        # Update all systems
        physics_update()
        ai_behavior_update()
        projectile_physics()
        process_visual_effects()
        collision_detection()
        manage_object_recycling()
        difficulty_progression()
    
    glutPostRedisplay()


def render_scene():
    """Main render with alternative order"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    
    setup_camera_view()
    
    render_sky_gradient()
    
    glEnable(GL_DEPTH_TEST)
    
    render_terrain_surface()
    
    # Don't render player in first person
    if cam.view_mode != 1:
        render_player_vehicle()
    
    # Render all entities
    for ring in world.collectibles:
        render_collectible_ring(ring)
    
    for hazard in world.hazards:
        render_hazard_object(hazard)
    
    for hostile in world.hostiles:
        render_hostile_vehicle(hostile)
    
    for missile in world.missiles:
        render_missile_projectile(missile)
    
    for pickup in world.pickups:
        render_pickup_item(pickup)
    
    for effect in world.effects:
        render_explosion_effect(effect)
    
    render_interface()
    
    glutSwapBuffers()


def main():
    """Entry point with alternative initialization"""
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Sky Racer - Flight Simulator")
    
    glEnable(GL_DEPTH_TEST)
    glClearColor(0.45, 0.65, 0.95, 1.0)
    
    initialize_entities()
    
    glutDisplayFunc(render_scene)
    glutKeyboardFunc(keyboard_handler)
    glutSpecialFunc(special_keys_handler)
    glutMouseFunc(mouse_handler)
    glutIdleFunc(update_loop)
    
    glutMainLoop()


if __name__ == "__main__":
    main()