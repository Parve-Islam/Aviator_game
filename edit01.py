# Importing necessary OpenGL modules for creating 3D graphics
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
# Mathematical operations and randomization support
import math
import random


# Core game status tracking variables stored in a dictionary structure
player_stats = {
    'points': 0,               # Total points accumulated by player
    'remaining_lives': 3,      # How many attempts player has left
    'flight_velocity': 1.0,    # Current movement speed of aircraft
    'power_mode_time': 0,      # Countdown for special power ability
    'is_game_finished': False, # Game termination status flag
    'current_stage': 1,        # Difficulty progression tracker
    'elapsed_frames': 0,       # Total frames since game start
    'hit_counter': 0,          # Tracks hostile aircraft impacts
    'invincibility_active': False,  # God mode status
    'auto_shoot_counter': 0,   # Automatic weapon firing timer
    'game_started': False,     # Has player started the game from menu
    'is_paused': False,        # Is game currently paused
    'combo_count': 0,          # Current combo multiplier
    'combo_timer': 0,          # Time remaining to maintain combo
    'last_ring_y': -999999,    # Y position of last collected ring
    'enemies_destroyed': 0     # NEW: Track total enemies killed
}


# Aircraft position and physics parameters in 3D coordinate system
aircraft_data = {
    'pos_x': 0, 'pos_y': 0, 'pos_z': 50,      # Spatial coordinates
    'rotation_x': 0, 'rotation_y': 0, 'rotation_z': 0,  # Euler angles
    'forward_speed': 1.0,                      # Thrust in forward direction
    'lateral_speed': 0.0,                      # Sideways drift velocity
    'climb_speed': 0.0,                        # Vertical ascent/descent rate
    'rotor_rotation': 0                        # Propeller spin animation angle
}


# View configuration for rendering perspective
view_settings = {
    'view_type': 0,  # 0: rear chase cam, 1: cockpit perspective, 2: lateral view
    'cam_x': 0, 'cam_y': -200, 'cam_z': 150   # Camera placement in world space
}


# Dynamic object collections for game entities
target_hoops = []       # Scoring rings player flies through
barrier_objects = []    # Environmental hazards to navigate around
hostile_crafts = []     # Enemy aircraft pursuing player
projectile_list = []    # Player-fired ammunition
bonus_items = []        # Collectible enhancement objects
blast_effects = []      # Visual explosion animations


# World boundary and rendering constants
WORLD_BOUNDARY = 2000     # Maximum extent of game world
TERRAIN_DIVISIONS = 40    # Grid line density for ground
VIEW_ANGLE = 60           # Camera field of view in degrees


# Infinite world generation parameters for seamless gameplay
CLEANUP_THRESHOLD = 400   # Distance behind aircraft to remove objects
RESPAWN_RANGE = 1800      # Distance ahead to regenerate objects


# Continuously regenerate game objects to maintain infinite gameplay experience
def regenerate_world_objects():
    """Repositions objects that have moved behind the player to maintain continuous world"""
    # Process scoring hoops - move old ones to new positions ahead
    for hoop in target_hoops:
        if hoop['pos_y'] < aircraft_data['pos_y'] - CLEANUP_THRESHOLD:
            hoop['pos_y'] = aircraft_data['pos_y'] + RESPAWN_RANGE
            hoop['pos_x'] = random.uniform(-500, 500)
            hoop['pos_z'] = random.uniform(100, 300)
            hoop['captured'] = False
    
    # Reposition environmental obstacles for continuous challenge
    for barrier in barrier_objects:
        if barrier['pos_y'] < aircraft_data['pos_y'] - CLEANUP_THRESHOLD:
            barrier['pos_y'] = aircraft_data['pos_y'] + RESPAWN_RANGE
            barrier['pos_x'] = random.uniform(-600, 600)
            barrier['pos_z'] = random.uniform(50, 400)
            barrier['obstacle_type'] = random.choice(['mist', 'boulder', 'blimp'])
    
    # FIXED: Recycle enemy aircraft closer to player for better visibility
    for foe in hostile_crafts:
        if foe['pos_y'] < aircraft_data['pos_y'] - CLEANUP_THRESHOLD or not foe['is_alive']:
            # Place enemies closer - between 300-800 units ahead instead of 1500-3000
            foe['pos_x'] = aircraft_data['pos_x'] + random.uniform(-300, 300)
            foe['pos_y'] = aircraft_data['pos_y'] + random.uniform(300, 800)
            foe['pos_z'] = aircraft_data['pos_z'] + random.uniform(-100, 100)
            foe['is_alive'] = True
    
    # Regenerate power-up items for sustained player engagement
    for enhancement in bonus_items:
        if enhancement['pos_y'] < aircraft_data['pos_y'] - CLEANUP_THRESHOLD or enhancement['captured']:
            enhancement['pos_y'] = aircraft_data['pos_y'] + RESPAWN_RANGE
            enhancement['pos_x'] = random.uniform(-300, 300)
            enhancement['pos_z'] = random.uniform(100, 250)
            enhancement['captured'] = False


# Populate initial game world with all interactive elements
def populate_game_world():
    """Creates initial distribution of game objects across the world space"""
    global target_hoops, barrier_objects, hostile_crafts, bonus_items
    
    # Generate collection hoops distributed along flight path
    for idx in range(5):
        target_hoops.append({
            'pos_x': random.uniform(-500, 500),
            'pos_y': 200 + idx * 300,
            'pos_z': random.uniform(100, 300),
            'captured': False
        })
    
    # Create varied environmental obstacles throughout world
    for idx in range(8):
        barrier_objects.append({
            'pos_x': random.uniform(-600, 600),
            'pos_y': random.uniform(100, 1500),
            'pos_z': random.uniform(50, 400),
            'obstacle_type': random.choice(['mist', 'boulder', 'blimp'])
        })
    
    # FIXED: Deploy enemy aircraft closer to player - visible range
    for idx in range(3):
        hostile_crafts.append({
            'pos_x': aircraft_data['pos_x'] + random.uniform(-300, 300),
            'pos_y': aircraft_data['pos_y'] + 300 + (idx * 200),  # Much closer: 300-700 units
            'pos_z': aircraft_data['pos_z'] + random.uniform(-100, 100),
            'is_alive': True
        })
    
    # Place power-up collectibles in strategic locations
    for idx in range(3):
        bonus_items.append({
            'pos_x': random.uniform(-300, 300),
            'pos_y': random.uniform(200, 1000),
            'pos_z': random.uniform(100, 250),
            'captured': False
        })


def render_player_aircraft():
    """Constructs the player's aircraft model using primitive geometric shapes"""
    glPushMatrix()
    # Transform aircraft to its current position and orientation in world
    glTranslatef(aircraft_data['pos_x'], aircraft_data['pos_y'], aircraft_data['pos_z'])
    glRotatef(aircraft_data['rotation_z'], 0, 0, 1)
    glRotatef(aircraft_data['rotation_y'], 1, 0, 0)
    glRotatef(aircraft_data['rotation_x'], 0, 1, 0)
    
    # Main fuselage body - stretched cube forming aircraft center
    glPushMatrix()
    glColor3f(0.75, 0.75, 0.75)  # Light gray metallic appearance
    glScalef(1, 3, 0.5)
    glutSolidCube(30)
    glPopMatrix()
    
    # Main wing structure extending laterally from fuselage
    glPushMatrix()
    glColor3f(0.85, 0.85, 0.85)  # Slightly brighter wing surface
    glScalef(5, 0.3, 0.2)
    glutSolidCube(30)
    glPopMatrix()
    
    # Vertical stabilizer fin at rear of aircraft
    glPushMatrix()
    glTranslatef(0, -35, 10)
    glColor3f(0.65, 0.65, 0.65)  # Darker tail section
    glScalef(0.2, 0.5, 1.5)
    glutSolidCube(30)
    glPopMatrix()
    
    # Horizontal tail stabilizer for pitch control
    glPushMatrix()
    glTranslatef(0, -35, 5)
    glColor3f(0.65, 0.65, 0.65)
    glScalef(2, 0.3, 0.2)
    glutSolidCube(20)
    glPopMatrix()
    
    # Animated propeller blades at aircraft nose
    glPushMatrix()
    glTranslatef(0, 45, 0)
    glRotatef(aircraft_data['rotor_rotation'], 0, 1, 0)
    glColor3f(0.25, 0.25, 0.25)  # Dark propeller blades
    glScalef(2, 0.1, 0.3)
    glutSolidCube(25)
    glPopMatrix()
    
    # Cockpit canopy where pilot sits
    glPushMatrix()
    glTranslatef(0, 10, 8)
    glColor3f(0.15, 0.15, 0.55)  # Blue-tinted glass cockpit
    glutSolidCube(15)
    glPopMatrix()
    
    glPopMatrix()


def render_collection_hoop(hoop):
    """Draws a cylindrical ring object for player to fly through"""
    # Skip rendering if already collected by player
    if hoop['captured']:
        return
    
    glPushMatrix()
    glTranslatef(hoop['pos_x'], hoop['pos_y'], hoop['pos_z'])
    glRotatef(90, 1, 0, 0)  # Orient ring perpendicular to flight path
    
    # Outer ring cylinder in bright gold color
    glColor3f(1, 0.95, 0)
    gluCylinder(gluNewQuadric(), 80, 80, 20, 20, 5)
    
    # Inner ring creating hollow center for flying through
    glColor3f(0.5, 0.475, 0)
    gluCylinder(gluNewQuadric(), 60, 60, 20, 20, 5)
    
    glPopMatrix()


def render_environmental_hazard(barrier):
    """Generates various obstacle types as navigation challenges"""
    glPushMatrix()
    glTranslatef(barrier['pos_x'], barrier['pos_y'], barrier['pos_z'])
    
    if barrier['obstacle_type'] == 'mist':
        # Cloud formation built from multiple overlapping spheres
        glColor3f(0.95, 0.95, 0.95)  # White puffy cloud
        gluSphere(gluNewQuadric(), 40, 10, 10)
        glTranslatef(30, 0, 0)
        gluSphere(gluNewQuadric(), 35, 10, 10)
        glTranslatef(-60, 0, 0)
        gluSphere(gluNewQuadric(), 35, 10, 10)
    elif barrier['obstacle_type'] == 'boulder':
        # Solid rock obstacle as angular cube
        glColor3f(0.45, 0.35, 0.25)  # Brown rocky texture
        glutSolidCube(50)
    else:  # blimp type obstacle
        # Floating balloon with tether line
        glColor3f(0.95, 0.15, 0.15)  # Bright red balloon
        gluSphere(gluNewQuadric(), 30, 10, 10)
        glTranslatef(0, 0, -40)
        glColor3f(0.75, 0.75, 0.75)  # Gray tether string
        glRotatef(-90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), 5, 2, 20, 10, 10)
    
    glPopMatrix()


def render_hostile_aircraft(foe):
    """Draws enemy aircraft model in red hostile colors"""
    # Don't render destroyed enemies
    if not foe['is_alive']:
        return
    
    glPushMatrix()
    glTranslatef(foe['pos_x'], foe['pos_y'], foe['pos_z'])
    
    # IMPROVED: Larger, more visible enemy aircraft
    # Enemy fuselage in threatening red
    glPushMatrix()
    glColor3f(0.85, 0.15, 0.15)
    glScalef(1, 2, 0.5)
    glutSolidCube(30)
    glPopMatrix()
    
    # Enemy wing structure - wider wings
    glPushMatrix()
    glColor3f(0.65, 0.05, 0.05)  # Darker red wings
    glScalef(4, 0.3, 0.2)
    glutSolidCube(25)
    glPopMatrix()
    
    # Enemy tail fin
    glPushMatrix()
    glTranslatef(0, -25, 8)
    glColor3f(0.55, 0.05, 0.05)
    glScalef(0.2, 0.4, 1.2)
    glutSolidCube(25)
    glPopMatrix()
    
    # NEW: Glowing indicator on enemy for better visibility
    glPushMatrix()
    glTranslatef(0, 0, 15)
    glColor3f(1, 0, 0)  # Bright red beacon
    gluSphere(gluNewQuadric(), 8, 8, 8)
    glPopMatrix()
    
    glPopMatrix()


def render_ammunition(projectile):
    """Visualizes fired projectiles as glowing spheres"""
    glPushMatrix()
    # Position projectile at current trajectory point
    glTranslatef(projectile['pos_x'], projectile['pos_y'], projectile['pos_z'])
    glColor3f(1, 0.95, 0)  # Bright yellow energy bolt
    gluSphere(gluNewQuadric(), 5, 8, 8)
    glPopMatrix()


def render_enhancement_item(enhancement):
    """Creates spinning power-up collectible with pulsing glow effect"""
    # Don't render already collected items
    if enhancement['captured']:
        return
    
    glPushMatrix()
    glTranslatef(enhancement['pos_x'], enhancement['pos_y'], enhancement['pos_z'])
    
    # Animated rotation on multiple axes for attention
    glRotatef(player_stats['elapsed_frames'] * 2, 0, 0, 1)
    glRotatef(player_stats['elapsed_frames'] * 1.5, 1, 0, 0)
    
    # Pulsating scale effect for visual attraction
    throb = 0.8 + 0.4 * math.sin(player_stats['elapsed_frames'] * 0.1)
    glScalef(throb, throb, throb)
    glColor3f(0, 0.95, 0.95)  # Vibrant cyan power-up color
    glutSolidCube(25)
    
    # Glowing white outline emphasizing collectible
    glColor3f(1, 1, 1)
    glutWireCube(30)
    
    glPopMatrix()


def generate_explosion_effect(x_pos, y_pos, z_pos):
    """Spawns animated explosion at specified coordinates"""
    # Add explosion data to active effects list
    blast_effects.append({
        'pos_x': x_pos, 'pos_y': y_pos, 'pos_z': z_pos,
        'lifetime': 30,  # Frames before effect disappears
        'radius': 10
    })


def render_blast_animation(blast):
    """Draws expanding explosion effect with color transition"""
    glPushMatrix()
    glTranslatef(blast['pos_x'], blast['pos_y'], blast['pos_z'])
    
    # Calculate explosion progression from 0 to 1
    advancement = 1.0 - (blast['lifetime'] / 30.0)
    expanding_size = blast['radius'] + advancement * 40
    
    # Multiple spheres create volumetric explosion appearance
    for sphere_idx in range(5):
        glPushMatrix()
        random_shift = random.uniform(-20, 20)
        glTranslatef(random_shift, random_shift, random_shift)
        
        # Transition from bright yellow to deep red
        red_val = 1.0
        green_val = 1.0 - advancement
        blue_val = 0.0
        glColor3f(red_val, green_val, blue_val)
        
        glutSolidSphere(expanding_size * (1.0 - sphere_idx * 0.2), 8, 8)
        glPopMatrix()
    
    glPopMatrix()


def process_explosion_effects():
    """Updates all active explosions and removes finished ones"""
    # Iterate through copy to safely modify list
    for blast in blast_effects[:]:
        blast['lifetime'] -= 1
        if blast['lifetime'] <= 0:
            blast_effects.remove(blast)


def render_ground_surface():
    """Creates textured ground plane with grid pattern"""
    # Main ground quad covering world area
    glBegin(GL_QUADS)
    glColor3f(0.15, 0.55, 0.15)  # Grass green terrain
    glVertex3f(-WORLD_BOUNDARY, -WORLD_BOUNDARY, 0)
    glVertex3f(WORLD_BOUNDARY, -WORLD_BOUNDARY, 0)
    glVertex3f(WORLD_BOUNDARY, WORLD_BOUNDARY, 0)
    glVertex3f(-WORLD_BOUNDARY, WORLD_BOUNDARY, 0)
    glEnd()
    
    # Grid lines providing spatial reference
    glColor3f(0.05, 0.35, 0.05)  # Darker green grid lines
    glLineWidth(1)
    grid_spacing = WORLD_BOUNDARY * 2 / TERRAIN_DIVISIONS
    
    glBegin(GL_LINES)
    for line_idx in range(TERRAIN_DIVISIONS + 1):
        line_position = -WORLD_BOUNDARY + line_idx * grid_spacing
        # Parallel grid lines in Y direction
        glVertex3f(-WORLD_BOUNDARY, line_position, 0)
        glVertex3f(WORLD_BOUNDARY, line_position, 0)
        # Parallel grid lines in X direction
        glVertex3f(line_position, -WORLD_BOUNDARY, 0)
        glVertex3f(line_position, WORLD_BOUNDARY, 0)
    glEnd()
    
    # Distant mountain range for horizon depth
    for mountain_idx in range(5):
        glPushMatrix()
        mountain_x = -800 + mountain_idx * 400
        mountain_y = -800
        glTranslatef(mountain_x, mountain_y, 50)
        glColor3f(0.35, 0.25, 0.15)  # Brown mountain peaks
        glScalef(1, 1, 2)
        glutSolidCube(100)
        glPopMatrix()


def render_sky_backdrop():
    """Draws gradient sky background from horizon to zenith"""
    glDisable(GL_DEPTH_TEST)  # Render as flat background
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Vertical gradient simulating atmospheric scattering
    glBegin(GL_QUADS)
    # Upper sky - deep blue
    glColor3f(0.35, 0.55, 0.85)
    glVertex2f(0, 800)
    glVertex2f(1000, 800)
    # Lower sky - pale blue near horizon
    glColor3f(0.65, 0.75, 0.95)
    glVertex2f(1000, 400)
    glVertex2f(0, 400)
    glEnd()
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)


def render_game_interface():
    """Displays heads-up display with game statistics and status"""
    glDisable(GL_DEPTH_TEST)  # Overlay on top of 3D scene
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # START SCREEN - Show before game begins
    if not player_stats['game_started']:
        # Title
        glColor3f(1, 1, 0)  # Yellow title
        display_text(300, 500, "SKY RACER - FLIGHT SIMULATOR")
        
        # Pulsing "Press SPACE to Start" text
        pulse = 0.5 + 0.5 * math.sin(player_stats['elapsed_frames'] * 0.1)
        glColor3f(pulse, pulse, pulse)
        display_text(350, 400, "Press SPACE to Start")
        
        # Instructions
        glColor3f(0.8, 0.8, 0.8)
        display_text(250, 320, "=== FLIGHT CONTROLS ===")
        display_text(250, 290, "WASD / Arrow Keys: Fly")
        display_text(250, 260, "Q/E: Strafe Left/Right")
        display_text(250, 230, "SPACE: Fire Weapon")
        display_text(250, 200, "C: Change Camera")
        display_text(250, 170, "P: Pause Game")
        display_text(250, 140, "X: Toggle Cheat Mode")
        
        glColor3f(1, 0.5, 0)
        display_text(250, 80, "Fly through GOLD RINGS | Avoid OBSTACLES")
        display_text(250, 50, "Shoot RED ENEMIES | Collect CYAN POWER-UPS")
    
    # PAUSE OVERLAY
    elif player_stats['is_paused']:
        # Semi-transparent dark overlay
        glColor3f(0, 0, 0)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(1000, 0)
        glVertex2f(1000, 800)
        glVertex2f(0, 800)
        glEnd()
        
        # Pause text
        glColor3f(1, 1, 0)
        display_text(420, 450, "== PAUSED ==")
        glColor3f(1, 1, 1)
        display_text(350, 400, "Press P to Resume")
        display_text(350, 370, "Press R to Restart")
        
        # Show current stats during pause
        glColor3f(0.7, 0.7, 0.7)
        display_text(380, 320, f"Current Score: {player_stats['points']}")
        display_text(380, 290, f"Lives Remaining: {player_stats['remaining_lives']}")
        display_text(380, 260, f"Current Stage: {player_stats['current_stage']}")
    
    # NORMAL GAMEPLAY HUD
    elif player_stats['game_started'] and not player_stats['is_game_finished']:
        # Core game statistics display
        glColor3f(1, 1, 1)  # White text for readability
        display_text(10, 770, f"Points: {player_stats['points']}")
        display_text(10, 740, f"Lives: {player_stats['remaining_lives']}")
        display_text(10, 710, f"Stage: {player_stats['current_stage']}")
        display_text(10, 680, f"Velocity: {aircraft_data['forward_speed']:.1f}")
        
        # NEW: Show enemy collision counter more prominently
        if player_stats['hit_counter'] > 0:
            glColor3f(1, 0.5, 0)  # Orange warning color
            display_text(10, 650, f"Enemy Collisions: {player_stats['hit_counter']}/5 - BE CAREFUL!")
        else:
            glColor3f(0.7, 0.7, 0.7)
            display_text(10, 650, f"Enemy Collisions: {player_stats['hit_counter']}/5")
        
        # NEW: Show enemies destroyed counter
        glColor3f(0, 1, 0)  # Green for kills
        display_text(10, 620, f"Enemies Destroyed: {player_stats['enemies_destroyed']}")
        
        # Power mode active indicator with countdown
        if player_stats['power_mode_time'] > 0:
            glColor3f(1, 0.95, 0)  # Golden power mode text
            display_text(10, 590, f"POWER MODE! {player_stats['power_mode_time']//60}s - INVINCIBLE!")
            glColor3f(0, 0.95, 0)  # Green bonus description
            display_text(10, 560, "HYPER VELOCITY! Smashing barriers!")
        
        # Cheat mode status indicator
        if player_stats['invincibility_active']:
            glColor3f(1, 0, 1)  # Magenta cheat mode highlight
            display_text(10, 530, "INVINCIBILITY MODE!")
            glColor3f(0.75, 0, 0.75)  # Purple additional info
            display_text(10, 500, "GODMODE + RAPID FIRE!")
        
        # COMBO DISPLAY - Show combo multiplier
        if player_stats['combo_count'] > 1:
            # Big combo text in center of screen
            glColor3f(1, 1, 0)  # Bright yellow
            display_text(420, 600, f"{player_stats['combo_count']}x COMBO!")
            
            # Combo timer bar
            if player_stats['combo_timer'] > 0:
                timer_percentage = player_stats['combo_timer'] / 180.0
                glColor3f(1 - timer_percentage, timer_percentage, 0)  # Red to green
                display_text(420, 570, f"Chain Timer: {player_stats['combo_timer']//60}s")
        
        # Current camera perspective indicator
        camera_modes = ["Rear Chase View", "Cockpit Perspective", "Side Angle View"]
        glColor3f(1, 0.95, 0)  # Yellow camera label
        display_text(750, 770, camera_modes[view_settings['view_type']])
    
    # GAME OVER SCREEN
    if player_stats['is_game_finished']:
        glColor3f(1, 0, 0)  # Red game over text
        display_text(400, 400, "GAME OVER!")
        display_text(350, 370, f"Final Score: {player_stats['points']}")
        display_text(350, 340, f"Enemies Destroyed: {player_stats['enemies_destroyed']}")
        display_text(350, 310, "Press R to restart")
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)


def display_text(x_coord, y_coord, message):
    """Renders text string at specified screen coordinates"""
    # Set raster position for character drawing
    glRasterPos2f(x_coord, y_coord)
    for character in message:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(character))


def update_aircraft_physics():
    """Processes aircraft movement, rotation, and physical constraints"""
    if player_stats['is_game_finished']:
        return
    
    # Animate propeller rotation continuously
    aircraft_data['rotor_rotation'] += 20
    
    # Keep aircraft aligned forward (no yaw drift)
    aircraft_data['rotation_z'] = 0

    # Forward thrust calculation with power mode multiplier
    if player_stats['power_mode_time'] > 0:
        # Quintupled speed during power boost
        aircraft_data['pos_y'] += player_stats['flight_velocity'] * 5
    else:
        # Standard forward movement rate
        aircraft_data['pos_y'] += player_stats['flight_velocity']
    
    # Apply lateral velocity for side-to-side motion
    aircraft_data['pos_x'] += aircraft_data['lateral_speed']
    
    # Apply vertical velocity for altitude changes
    aircraft_data['pos_z'] += aircraft_data['climb_speed']
    
    # Roll angle influences lateral drift slightly
    roll_radians = math.radians(aircraft_data['rotation_x'])
    aircraft_data['pos_x'] += aircraft_data['forward_speed'] * math.sin(roll_radians) * 0.3
    
    # Pitch angle affects vertical movement
    pitch_radians = math.radians(aircraft_data['rotation_y'])
    aircraft_data['pos_z'] += aircraft_data['forward_speed'] * math.sin(pitch_radians) * 0.5
    
    # Friction reduces velocities over time (air resistance)
    aircraft_data['lateral_speed'] *= 0.85  # Lateral damping
    aircraft_data['climb_speed'] *= 0.90    # Vertical damping
    
    # Auto-centering of roll angle when not actively rolling
    if abs(aircraft_data['rotation_x']) > 1:
        aircraft_data['rotation_x'] *= 0.95
    else:
        aircraft_data['rotation_x'] = 0
    
    # Auto-leveling of pitch angle for stable flight
    if abs(aircraft_data['rotation_y']) > 1:
        aircraft_data['rotation_y'] *= 0.98
    else:
        aircraft_data['rotation_y'] = 0
    
    # Ground collision prevention - minimum altitude enforcement
    if aircraft_data['pos_z'] < 20:
        aircraft_data['pos_z'] = 20
        aircraft_data['rotation_y'] = max(aircraft_data['rotation_y'], 0)
    
    # Ceiling limit - maximum altitude constraint
    if aircraft_data['pos_z'] > 500:
        aircraft_data['pos_z'] = 500
        aircraft_data['rotation_y'] = min(aircraft_data['rotation_y'], 0)
    
    # Left boundary enforcement
    if aircraft_data['pos_x'] < -1000:
        aircraft_data['pos_x'] = -1000
        aircraft_data['rotation_x'] = max(aircraft_data['rotation_x'], 0)
    # Right boundary enforcement
    elif aircraft_data['pos_x'] > 1000:
        aircraft_data['pos_x'] = 1000
        aircraft_data['rotation_x'] = min(aircraft_data['rotation_x'], 0)
    
    # Process power boost timer countdown
    if player_stats['power_mode_time'] > 0:
        player_stats['power_mode_time'] -= 1
        if player_stats['power_mode_time'] == 0:
            aircraft_data['forward_speed'] = player_stats['flight_velocity']
    
    # COMBO TIMER - Decrease and reset combo if expired
    if player_stats['combo_timer'] > 0:
        player_stats['combo_timer'] -= 1
        if player_stats['combo_timer'] == 0:
            player_stats['combo_count'] = 0  # Reset combo when timer expires
            print("Combo broken!")


def update_enemy_behavior():
    """FIXED: Enemy AI - stays visible and near player"""
    # Process each enemy aircraft's movement
    for foe in hostile_crafts:
        if not foe['is_alive']:
            continue
        
        # Vector calculation from enemy to player position
        delta_x = aircraft_data['pos_x'] - foe['pos_x']
        delta_y = aircraft_data['pos_y'] - foe['pos_y']
        delta_z = aircraft_data['pos_z'] - foe['pos_z']
        
        # Euclidean distance to player aircraft
        separation = math.sqrt(delta_x*delta_x + delta_y*delta_y + delta_z*delta_z)
        
        if separation > 0:
            # Normalize direction vector components
            delta_x /= separation
            delta_y /= separation
            delta_z /= separation
            
            # CHANGED: Slower pursuit speed so enemies don't escape too quickly
            pursuit_velocity = 0.5 + (player_stats['current_stage'] * 0.1)
            
            # Move towards player
            foe['pos_x'] += delta_x * pursuit_velocity
            foe['pos_y'] += delta_y * pursuit_velocity
            foe['pos_z'] += delta_z * pursuit_velocity
            
            # Evasive maneuvers for unpredictable flight patterns
            evasion_x = math.sin(player_stats['elapsed_frames'] * 0.05 + foe['pos_y'] * 0.005) * 3
            foe['pos_x'] += evasion_x
            foe['pos_z'] += math.cos(player_stats['elapsed_frames'] * 0.04 + foe['pos_x'] * 0.005) * 2


def update_projectile_motion():
    """Advances projectile positions and handles impact detection"""
    # Process each active projectile
    for projectile in projectile_list[:]:
        # Extract velocity from projectile data
        trajectory_speed = projectile.get('velocity', 20)
        
        # Directional components for movement vector
        movement_x = projectile.get('vector_x', 0)
        movement_y = projectile.get('vector_y', 1)
        movement_z = projectile.get('vector_z', 0)
        
        projectile['pos_x'] += movement_x * trajectory_speed
        projectile['pos_y'] += movement_y * trajectory_speed
        projectile['pos_z'] += movement_z * trajectory_speed
        
        # Remove projectiles that travel beyond effective range
        distance_from_aircraft = math.sqrt((projectile['pos_x'] - aircraft_data['pos_x'])**2 + 
                                          (projectile['pos_y'] - aircraft_data['pos_y'])**2 + 
                                          (projectile['pos_z'] - aircraft_data['pos_z'])**2)
        if distance_from_aircraft > 1000:
            projectile_list.remove(projectile)
            continue
        
        # Collision detection with enemy aircraft
        for foe in hostile_crafts:
            if not foe['is_alive']:
                continue
            
            # FIXED: Increased collision radius for easier hitting
            impact_distance = math.sqrt((projectile['pos_x']-foe['pos_x'])**2 + 
                                       (projectile['pos_y']-foe['pos_y'])**2 + 
                                       (projectile['pos_z']-foe['pos_z'])**2)
            if impact_distance < 40:  # Increased from 30 to 40
                # Explosion effect at impact point
                generate_explosion_effect(foe['pos_x'], foe['pos_y'], foe['pos_z'])
                foe['is_alive'] = False
                if projectile in projectile_list:
                    projectile_list.remove(projectile)
                player_stats['points'] += 100
                player_stats['enemies_destroyed'] += 1  # NEW: Track kills
                print(f"Enemy eliminated! +100 points | Total destroyed: {player_stats['enemies_destroyed']}")
                break


def detect_all_collisions():
    """Checks for intersections between aircraft and world objects"""
    if player_stats['is_game_finished']:
        return
    
    # Hoop collection detection with combo system
    for hoop in target_hoops:
        if hoop['captured']:
            continue
        
        proximity = math.sqrt((aircraft_data['pos_x']-hoop['pos_x'])**2 + 
                             (aircraft_data['pos_y']-hoop['pos_y'])**2 + 
                             (aircraft_data['pos_z']-hoop['pos_z'])**2)
        if proximity < 80:
            hoop['captured'] = True
            
            # COMBO SYSTEM - Check if this ring is ahead of last collected ring
            if hoop['pos_y'] > player_stats['last_ring_y']:
                # Consecutive ring collected - increase combo
                player_stats['combo_count'] += 1
                player_stats['combo_timer'] = 180  # 3 seconds to get next ring
                player_stats['last_ring_y'] = hoop['pos_y']
                
                # Calculate points with combo multiplier
                base_points = 100
                combo_multiplier = player_stats['combo_count']
                earned_points = base_points * combo_multiplier
                player_stats['points'] += earned_points
                
                print(f"{player_stats['combo_count']}x COMBO! +{earned_points} points")
            else:
                # Collected ring out of order - reset combo
                player_stats['combo_count'] = 0
                player_stats['combo_timer'] = 0
                player_stats['points'] += 100
    
    # Obstacle collision evaluation
    for barrier in barrier_objects[:]:
        proximity = math.sqrt((aircraft_data['pos_x']-barrier['pos_x'])**2 + 
                             (aircraft_data['pos_y']-barrier['pos_y'])**2 + 
                             (aircraft_data['pos_z']-barrier['pos_z'])**2)
        
        # Mist clouds are non-solid pass-through objects
        if barrier['obstacle_type'] == 'mist':
            continue
            
        # Solid obstacles check for collision
        collision_radius = 40
        if proximity < collision_radius:
            if player_stats['power_mode_time'] > 0:
                # Power mode allows breaking through obstacles
                barrier_objects.remove(barrier)
                generate_explosion_effect(barrier['pos_x'], barrier['pos_y'], barrier['pos_z'])
                player_stats['points'] += 50
            else:
                # Normal collision triggers crash and resets combo
                player_stats['combo_count'] = 0
                player_stats['combo_timer'] = 0
                trigger_aircraft_crash()
                barrier_objects.remove(barrier)
            break
    
    # Enemy aircraft collision detection
    for foe in hostile_crafts:
        if not foe['is_alive']:
            continue
        
        proximity = math.sqrt((aircraft_data['pos_x']-foe['pos_x'])**2 + 
                             (aircraft_data['pos_y']-foe['pos_y'])**2 + 
                             (aircraft_data['pos_z']-foe['pos_z'])**2)
        if proximity < 35:
            if player_stats['power_mode_time'] > 0 or player_stats['invincibility_active']:
                # Invincible modes destroy enemies on contact
                foe['is_alive'] = False
                generate_explosion_effect(foe['pos_x'], foe['pos_y'], foe['pos_z'])
                player_stats['points'] += 150
                player_stats['enemies_destroyed'] += 1
                print(f"Enemy rammed! +150 points | Total destroyed: {player_stats['enemies_destroyed']}")
            else:
                # Normal collision increments damage counter
                player_stats['hit_counter'] += 1
                foe['is_alive'] = False
                
                # NEW: Better feedback for collision
                generate_explosion_effect(foe['pos_x'], foe['pos_y'], foe['pos_z'])
                print(f"COLLISION! Enemy hit {player_stats['hit_counter']}/5")
                
                # Five hits triggers life loss
                if player_stats['hit_counter'] >= 5:
                    player_stats['combo_count'] = 0  # Reset combo on crash
                    player_stats['combo_timer'] = 0
                    trigger_aircraft_crash()
                    player_stats['hit_counter'] = 0
            break
    
    # Power-up collection detection
    for enhancement in bonus_items:
        if enhancement['captured']:
            continue
        
        proximity = math.sqrt((aircraft_data['pos_x']-enhancement['pos_x'])**2 + 
                             (aircraft_data['pos_y']-enhancement['pos_y'])**2 + 
                             (aircraft_data['pos_z']-enhancement['pos_z'])**2)
        if proximity < 35:
            enhancement['captured'] = True
            player_stats['power_mode_time'] = 420  # 7 second duration
            aircraft_data['forward_speed'] = player_stats['flight_velocity'] * 5
            
            # Visual feedback at collection point
            generate_explosion_effect(enhancement['pos_x'], enhancement['pos_y'], enhancement['pos_z'])
            
            player_stats['points'] += 200
            print("POWER-UP! Super speed and invincibility activated!")


def trigger_aircraft_crash():
    """Processes crash event with life deduction and reset logic"""
    # Decrement life counter
    player_stats['remaining_lives'] -= 1
    print(f"CRASHED! Lives remaining: {player_stats['remaining_lives']}")
    if player_stats['remaining_lives'] <= 0:
        player_stats['is_game_finished'] = True
        print(f"GAME OVER! Final score: {player_stats['points']} | Enemies destroyed: {player_stats['enemies_destroyed']}")
    else:
        # Reset aircraft to starting position and orientation
        aircraft_data['pos_x'] = 0
        aircraft_data['pos_y'] = 0
        aircraft_data['pos_z'] = 50
        aircraft_data['rotation_y'] = 0
        aircraft_data['rotation_x'] = 0
        aircraft_data['rotation_z'] = 0


def advance_difficulty_stage():
    """Increases challenge based on accumulated points"""
    # Calculate stage from total points
    updated_stage = 1 + player_stats['points'] // 500
    if updated_stage > player_stats['current_stage']:
        player_stats['current_stage'] = updated_stage
        player_stats['flight_velocity'] += 0.5
        aircraft_data['forward_speed'] = player_stats['flight_velocity']
        
        # Spawn additional enemy for increased difficulty
        for _ in range(1):
            hostile_crafts.append({
                'pos_x': random.uniform(-400, 400),
                'pos_y': aircraft_data['pos_y'] + random.uniform(300, 600),
                'pos_z': random.uniform(150, 350),
                'is_alive': True
            })
        print(f"STAGE {updated_stage}! Speed increased, more enemies spawned!")


def launch_projectile():
    """Creates new projectile from aircraft current position and aim"""
    # Calculate firing direction based on pitch orientation
    pitch_angle = math.radians(aircraft_data['rotation_y'])
    
    # Decompose forward vector into components
    x_component = 0  # No horizontal deviation
    y_component = math.cos(pitch_angle)  # Forward always positive
    z_component = math.sin(pitch_angle)  # Vertical aim adjustment
    
    # Spawn projectile at nose of aircraft
    projectile_list.append({
        'pos_x': aircraft_data['pos_x'],
        'pos_y': aircraft_data['pos_y'] + 50,
        'pos_z': aircraft_data['pos_z'] + 20,
        'vector_x': x_component,
        'vector_y': y_component,
        'vector_z': z_component,
        'velocity': 30
    })


def handle_key_press(pressed_key, x_pos, y_pos):
    """Processes keyboard input for flight controls and commands"""
    global view_settings
    
    # START SCREEN - Only allow SPACE to start
    if not player_stats['game_started']:
        if pressed_key == b' ':  # Space to start game
            player_stats['game_started'] = True
        return
    
    # PAUSE - Allow pause toggle and restart
    if pressed_key == b'p':
        player_stats['is_paused'] = not player_stats['is_paused']
        return
    
    # If paused, only allow restart
    if player_stats['is_paused']:
        if pressed_key == b'r':
            initialize_new_game()
        return
    
    # Restart allowed only when game finished
    if player_stats['is_game_finished']:
        if pressed_key == b'r':
            initialize_new_game()
        return
    
    # Flight control bindings
    if pressed_key == b'w':  # Climb input
        aircraft_data['rotation_y'] = min(aircraft_data['rotation_y'] + 5, 25)
        aircraft_data['climb_speed'] += 3
    elif pressed_key == b's':  # Dive input
        aircraft_data['rotation_y'] = max(aircraft_data['rotation_y'] - 5, -25)
        aircraft_data['climb_speed'] -= 3
    elif pressed_key == b'a':  # Bank left input
        aircraft_data['rotation_x'] = min(aircraft_data['rotation_x'] + 8, 35)
        aircraft_data['lateral_speed'] -= 4
    elif pressed_key == b'd':  # Bank right input
        aircraft_data['rotation_x'] = max(aircraft_data['rotation_x'] - 8, -35)
        aircraft_data['lateral_speed'] += 4
    elif pressed_key == b'q':  # Direct left strafe
        aircraft_data['lateral_speed'] -= 8
    elif pressed_key == b'e':  # Direct right strafe
        aircraft_data['lateral_speed'] += 8
    
    # Action commands
    if pressed_key == b' ':  # Fire weapon
        launch_projectile()
    elif pressed_key == b'c':  # Cycle camera views
        view_settings['view_type'] = (view_settings['view_type'] + 1) % 3
    elif pressed_key == b'x':  # Toggle invincibility cheat
        player_stats['invincibility_active'] = not player_stats['invincibility_active']
        if player_stats['invincibility_active']:
            print("INVINCIBILITY ENABLED!")
        else:
            print("Invincibility disabled")
    elif pressed_key == b'r':  # Manual restart
        initialize_new_game()


def handle_special_keys(special_key, x_pos, y_pos):
    """Processes arrow key inputs for precise flight adjustments"""
    # Block input when game finished
    if player_stats['is_game_finished']:
        return
    
    # Fine control using arrow keys
    if special_key == GLUT_KEY_UP:
        aircraft_data['rotation_y'] = min(aircraft_data['rotation_y'] + 4, 25)
        aircraft_data['climb_speed'] += 2
    elif special_key == GLUT_KEY_DOWN:
        aircraft_data['rotation_y'] = max(aircraft_data['rotation_y'] - 4, -25)
        aircraft_data['climb_speed'] -= 2
    elif special_key == GLUT_KEY_LEFT:
        aircraft_data['rotation_x'] = min(aircraft_data['rotation_x'] + 6, 35)
        aircraft_data['lateral_speed'] -= 3
    elif special_key == GLUT_KEY_RIGHT:
        aircraft_data['rotation_x'] = max(aircraft_data['rotation_x'] - 6, -35)
        aircraft_data['lateral_speed'] += 3


def handle_mouse_input(button_id, button_state, x_pos, y_pos):
    """Processes mouse button events for alternative controls"""
    # Left click fires weapon when game active
    if button_id == GLUT_LEFT_BUTTON and button_state == GLUT_DOWN:
        if not player_stats['is_game_finished']:
            launch_projectile()
    # Right click cycles camera views
    elif button_id == GLUT_RIGHT_BUTTON and button_state == GLUT_DOWN:
        view_settings['view_type'] = (view_settings['view_type'] + 1) % 3


def configure_view_camera():
    """Sets up camera projection and position based on selected mode"""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(VIEW_ANGLE, 1.25, 0.1, 5000)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    # Camera positioning based on current view mode
    if view_settings['view_type'] == 0:  # Rear chase camera
        chase_offset = 300
        elevation_offset = 150
        
        # Position behind and above aircraft
        camera_x = aircraft_data['pos_x'] + 50
        camera_y = aircraft_data['pos_y'] - chase_offset
        camera_z = aircraft_data['pos_z'] + elevation_offset
        
        gluLookAt(camera_x, camera_y, camera_z,
                 aircraft_data['pos_x'], aircraft_data['pos_y'], aircraft_data['pos_z'],
                 0, 0, 1)
    
    elif view_settings['view_type'] == 1:  # Cockpit first-person
        # Camera at pilot eye position
        camera_x = aircraft_data['pos_x']
        camera_y = aircraft_data['pos_y'] - 20
        camera_z = aircraft_data['pos_z'] + 15
        
        # Calculate forward look point with orientation
        pitch_angle = math.radians(aircraft_data['rotation_y'])
        yaw_angle = math.radians(aircraft_data['rotation_z'])
        
        view_range = 500
        target_x = aircraft_data['pos_x'] + view_range * math.sin(yaw_angle) * math.cos(pitch_angle)
        target_y = aircraft_data['pos_y'] + view_range * math.cos(yaw_angle) * math.cos(pitch_angle)
        target_z = aircraft_data['pos_z'] + view_range * math.sin(pitch_angle)
        
        # Up vector adjusted for aircraft roll
        roll_angle = math.radians(aircraft_data['rotation_x'])
        up_x = math.sin(roll_angle)
        up_y = 0
        up_z = math.cos(roll_angle)
        
        gluLookAt(camera_x, camera_y, camera_z,
                 target_x, target_y, target_z,
                 up_x, up_y, up_z)
    
    elif view_settings['view_type'] == 2:  # Lateral side view
        side_offset = 400
        
        camera_x = aircraft_data['pos_x'] + side_offset
        camera_y = aircraft_data['pos_y'] - 100
        camera_z = aircraft_data['pos_z'] + 200
        
        gluLookAt(camera_x, camera_y, camera_z,
                 aircraft_data['pos_x'], aircraft_data['pos_y'], aircraft_data['pos_z'],
                 0, 0, 1)


def initialize_new_game():
    """Resets all game variables to starting state for fresh game"""
    global player_stats, aircraft_data, target_hoops, barrier_objects, hostile_crafts, projectile_list, bonus_items
    
    # Reset player statistics
    player_stats = {
        'points': 0,
        'remaining_lives': 3,
        'flight_velocity': 1.0,
        'power_mode_time': 0,
        'is_game_finished': False,
        'current_stage': 1,
        'elapsed_frames': 0,
        'hit_counter': 0,
        'invincibility_active': False,
        'auto_shoot_counter': 0,
        'game_started': True,  # Start directly when restarting
        'is_paused': False,
        'combo_count': 0,
        'combo_timer': 0,
        'last_ring_y': -999999,
        'enemies_destroyed': 0
    }
    
    # Reset aircraft state
    aircraft_data = {
        'pos_x': 0, 'pos_y': 0, 'pos_z': 50,
        'rotation_x': 0, 'rotation_y': 0, 'rotation_z': 0,
        'forward_speed': 1.0,
        'lateral_speed': 0.0,
        'climb_speed': 0.0,
        'rotor_rotation': 0
    }
    
    # Clear all object lists
    target_hoops = []
    barrier_objects = []
    hostile_crafts = []
    projectile_list = []
    bonus_items = []
    
    # Regenerate world objects
    populate_game_world()


def continuous_game_update():
    """Main game loop function called repeatedly for updates"""
    # Increment frame counter (runs even on start screen for animations)
    player_stats['elapsed_frames'] += 1
    
    # Don't update game if not started or paused
    if not player_stats['game_started'] or player_stats['is_paused']:
        glutPostRedisplay()
        return
    
    if not player_stats['is_game_finished']:
        # Auto-fire weapon when invincibility active
        if player_stats['invincibility_active']:
            player_stats['auto_shoot_counter'] += 1
            if player_stats['auto_shoot_counter'] >= 5:
                launch_projectile()
                player_stats['auto_shoot_counter'] = 0
        
        # Update all game systems
        update_aircraft_physics()
        update_enemy_behavior()
        update_projectile_motion()
        process_explosion_effects()
        detect_all_collisions()
        regenerate_world_objects()
        advance_difficulty_stage()
    
    # Trigger redraw
    glutPostRedisplay()


def render_complete_scene():
    """Main rendering function that draws entire game world"""
    # Clear both color and depth buffers
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)
    
    configure_view_camera()
    
    # Render background sky first
    render_sky_backdrop()
    
    # Enable depth testing for proper 3D layering
    glEnable(GL_DEPTH_TEST)
    
    # Draw environment
    render_ground_surface()
    
    # Hide aircraft in first-person view
    if view_settings['view_type'] != 1:
        render_player_aircraft()
    
    # Render all game objects
    for hoop in target_hoops:
        render_collection_hoop(hoop)
    
    for barrier in barrier_objects:
        render_environmental_hazard(barrier)
    
    for foe in hostile_crafts:
        render_hostile_aircraft(foe)
    
    for projectile in projectile_list:
        render_ammunition(projectile)
    
    for enhancement in bonus_items:
        render_enhancement_item(enhancement)
    
    for blast in blast_effects:
        render_blast_animation(blast)
    
    # Overlay interface last
    render_game_interface()
    
    glutSwapBuffers()


def main():
    """Entry point - initializes OpenGL and starts game loop"""
    # Initialize GLUT system
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Sky Racer - Flight Simulator")
    
    # Enable depth testing and set sky color
    glEnable(GL_DEPTH_TEST)
    glClearColor(0.45, 0.65, 0.95, 1.0)
    
    # Create initial game world
    populate_game_world()
    
    # Register callback functions
    glutDisplayFunc(render_complete_scene)
    glutKeyboardFunc(handle_key_press)
    glutSpecialFunc(handle_special_keys)
    glutMouseFunc(handle_mouse_input)
    glutIdleFunc(continuous_game_update)
    
    glutMainLoop()


if __name__ == "__main__":
    main()