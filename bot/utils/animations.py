"""
Animation & GIF Engine for Kingdom Conquest Bot.
Creates animated GIFs for battles, level-ups, victories, and other game events.
Uses PIL for frame generation and imageio/gif stitching.

Dependencies: Pillow, imageio[ffmpeg] (optional), numpy
"""
import os
import io
import math
import random
from typing import List, Tuple, Optional, Dict
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

try:
    import imageio
    IMAGEIO_AVAILABLE = True
except ImportError:
    IMAGEIO_AVAILABLE = False

import numpy as np

ANIMATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'animations')
os.makedirs(ANIMATIONS_DIR, exist_ok=True)

# Color palette
COLORS = {
    'bg_dark': (26, 26, 46),
    'bg_card': (22, 33, 62),
    'primary': (233, 69, 96),
    'secondary': (15, 52, 96),
    'accent': (83, 52, 131),
    'gold': (255, 215, 0),
    'gold_light': (255, 237, 74),
    'food': (78, 204, 163),
    'white': (224, 224, 224),
    'red': (255, 107, 107),
    'green': (78, 204, 163),
    'blue': (78, 205, 196),
    'yellow': (255, 230, 109),
    'purple': (147, 51, 234),
    'orange': (251, 146, 60),
    'silver': (192, 192, 192),
    'bronze': (205, 127, 50),
}


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def create_gradient_background(width: int, height: int, color1: Tuple[int, int, int],
                                color2: Tuple[int, int, int], direction: str = 'vertical') -> Image.Image:
    """Create a gradient background image."""
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    for i in range(height if direction == 'vertical' else width):
        ratio = i / (height if direction == 'vertical' else width)
        r = int(color1[0] + (color2[0] - color1[0]) * ratio)
        g = int(color1[1] + (color2[1] - color1[1]) * ratio)
        b = int(color1[2] + (color2[2] - color1[2]) * ratio)
        if direction == 'vertical':
            draw.line([(0, i), (width, i)], fill=(r, g, b))
        else:
            draw.line([(i, 0), (i, height)], fill=(r, g, b))
    return img


def add_glow_effect(draw, x: int, y: int, radius: int, color: Tuple[int, int, int], intensity: float = 0.5):
    """Add a glow effect at position."""
    for r in range(radius, 0, -2):
        alpha = int(255 * intensity * (r / radius))
        glow_color = (*color, alpha)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=glow_color)


def draw_rounded_rectangle(draw, xy, radius, fill, outline=None, width=1):
    """Draw a rounded rectangle."""
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def save_gif(frames: List[Image.Image], filename: str, duration: int = 100) -> str:
    """Save frames as animated GIF."""
    filepath = os.path.join(ANIMATIONS_DIR, filename)
    if len(frames) > 0:
        frames[0].save(
            filepath,
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=0,
            optimize=True
        )
    return filepath


# ============================================================================
# 1. BATTLE ANIMATION GIF
# ============================================================================

def generate_battle_animation(attacker_name: str, defender_name: str,
                               attacker_army: int, defender_army: int,
                               result: str = "victory") -> str:
    """
    Generate an animated battle GIF showing clash between two armies.
    result: 'victory' | 'defeat' | 'draw'
    """
    W, H = 600, 350
    frames = []
    num_frames = 20

    # Background colors based on result
    if result == "victory":
        bg1, bg2 = COLORS['bg_dark'], (20, 40, 30)
        result_color = COLORS['green']
        result_text = "VICTORY!"
    elif result == "defeat":
        bg1, bg2 = COLORS['bg_dark'], (40, 20, 20)
        result_color = COLORS['red']
        result_text = "DEFEAT!"
    else:
        bg1, bg2 = COLORS['bg_dark'], (30, 30, 30)
        result_color = COLORS['gold']
        result_text = "DRAW!"

    for frame_idx in range(num_frames):
        img = create_gradient_background(W, H, bg1, bg2)
        draw = ImageDraw.Draw(img)
        progress = frame_idx / (num_frames - 1)

        # Draw battlefield ground
        draw.rectangle([0, H-60, W, H], fill=(15, 25, 45))
        draw.line([(0, H-60), (W, H-60)], fill=COLORS['secondary'], width=2)

        # Draw army bars at top
        atk_bar_width = int((attacker_army / max(attacker_army + defender_army, 1)) * 250)
        def_bar_width = int((defender_army / max(attacker_army + defender_army, 1)) * 250)

        # Attacker bar (left)
        draw.rectangle([30, 20, 30 + atk_bar_width, 40], fill=COLORS['primary'])
        draw.text((30, 45), f"{attacker_name}", fill=COLORS['white'])
        draw.text((30, 60), f"Army: {attacker_army:,}", fill=COLORS['gold'])

        # VS text
        draw.text((W//2 - 20, 25), "VS", fill=COLORS['gold'], font=None)

        # Defender bar (right)
        draw.rectangle([W - 30 - def_bar_width, 20, W - 30, 40], fill=COLORS['secondary'])
        draw.text((W - 30 - def_bar_width, 45), f"{defender_name}", fill=COLORS['white'])
        draw.text((W - 30 - def_bar_width, 60), f"Army: {defender_army:,}", fill=COLORS['gold'])

        # Animated soldiers
        # Attackers moving right
        atk_start_x = 50
        atk_end_x = W//2 - 50
        atk_x = int(atk_start_x + (atk_end_x - atk_start_x) * min(progress * 1.5, 1))
        # Bouncing effect
        bounce = abs(math.sin(progress * 10)) * 5

        for i in range(5):
            sx = atk_x + i * 25
            sy = H - 80 - bounce - (i % 2) * 5
            # Soldier body
            draw.ellipse([sx-8, sy-8, sx+8, sy+8], fill=COLORS['primary'])
            # Sword
            sword_progress = max(0, (progress - 0.5) * 2)
            if sword_progress > 0:
                draw.line([sx+8, sy-5, sx+20, sy-15], fill=COLORS['silver'], width=2)

        # Defenders moving left
        def_start_x = W - 50
        def_end_x = W//2 + 50
        def_x = int(def_start_x + (def_end_x - def_start_x) * min(progress * 1.5, 1))
        def_bounce = abs(math.cos(progress * 10)) * 5

        for i in range(5):
            sx = def_x - i * 25
            sy = H - 80 - def_bounce - (i % 2) * 5
            draw.ellipse([sx-8, sy-8, sx+8, sy+8], fill=COLORS['secondary'])
            # Shield
            shield_progress = max(0, (progress - 0.5) * 2)
            if shield_progress > 0:
                draw.ellipse([sx-12, sy-12, sx+2, sy+2], outline=COLORS['gold'], width=2)

        # Clash effects
        if progress > 0.5:
            clash_intensity = min(1, (progress - 0.5) * 3)
            # Flash effect
            for _ in range(int(clash_intensity * 8)):
                cx = W//2 + random.randint(-40, 40)
                cy = H - 90 + random.randint(-30, 30)
                size = random.randint(3, 12)
                color = random.choice([COLORS['gold'], COLORS['red'], COLORS['yellow'], COLORS['orange']])
                draw.ellipse([cx-size, cy-size, cx+size, cy+size], fill=color)

        # Result text at end
        if progress > 0.7:
            text_alpha = int(255 * min(1, (progress - 0.7) * 5))
            # Semi-transparent overlay
            overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle([0, 0, W, H], fill=(0, 0, 0, text_alpha // 3))
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
            draw = ImageDraw.Draw(img)
            # Result text with glow
            text_x = W//2 - 80
            text_y = H//2 - 30
            for offset in range(3, 0, -1):
                glow_alpha = text_alpha // (offset + 1)
                glow_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
                glow_draw = ImageDraw.Draw(glow_layer)
                glow_draw.text((text_x, text_y), result_text, fill=(*result_color, glow_alpha))
                img = Image.alpha_composite(img.convert('RGBA'), glow_layer).convert('RGB')
                draw = ImageDraw.Draw(img)
            draw.text((text_x, text_y), result_text, fill=result_color)

        frames.append(img)

    filename = f'battle_{result}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.gif'
    return save_gif(frames, filename, duration=120)


# ============================================================================
# 2. LEVEL-UP ANIMATION
# ============================================================================

def generate_levelup_animation(entity_name: str, entity_type: str = "building",
                                old_level: int = 1, new_level: int = 2) -> str:
    """
    Generate level-up celebration animation.
    entity_type: 'building' | 'hero' | 'kingdom'
    """
    W, H = 500, 300
    frames = []
    num_frames = 24

    type_colors = {
        'building': COLORS['gold'],
        'hero': COLORS['purple'],
        'kingdom': COLORS['green']
    }
    type_emojis = {
        'building': '',
        'hero': '',
        'kingdom': ''
    }
    accent_color = type_colors.get(entity_type, COLORS['gold'])
    emoji = type_emojis.get(entity_type, '')

    for frame_idx in range(num_frames):
        progress = frame_idx / (num_frames - 1)
        img = create_gradient_background(W, H, COLORS['bg_dark'], (30, 30, 20))
        draw = ImageDraw.Draw(img)

        # Background particles
        random.seed(42)  # Consistent particles
        for i in range(30):
            px = random.randint(0, W)
            py = random.randint(0, H)
            size = random.randint(1, 4)
            brightness = abs(math.sin(progress * 6 + i))
            if brightness > 0.3:
                color = tuple(int(c * brightness) for c in accent_color)
                draw.ellipse([px-size, py-size, px+size, py+size], fill=color)

        # Central glow pulsing
        pulse = abs(math.sin(progress * 8))
        glow_radius = int(60 + pulse * 40)
        glow_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_layer)
        for r in range(glow_radius, 0, -3):
            alpha = int(50 * pulse * (r / glow_radius))
            glow_draw.ellipse([W//2-r, H//2-r-20, W//2+r, H//2+r-20],
                              fill=(*accent_color, alpha))
        img = Image.alpha_composite(img.convert('RGBA'), glow_layer).convert('RGB')
        draw = ImageDraw.Draw(img)

        # Level text
        level_bounce = abs(math.sin(progress * 12)) * 10
        # Old level
        old_alpha = max(0, int(255 * (1 - progress * 2)))
        if old_alpha > 0:
            draw.text((W//2 - 80, H//2 - 60 - level_bounce), f"Lv.{old_level}",
                     fill=tuple(int(c * old_alpha / 255) for c in COLORS['white']))

        # Arrow
        if 0.3 < progress < 0.8:
            arrow_alpha = int(255 * (1 - abs(progress - 0.55) * 3))
            arrow_color = tuple(int(c * arrow_alpha / 255) for c in COLORS['gold'])
            draw.text((W//2 - 15, H//2 - 70), "->", fill=arrow_color)

        # New level
        new_alpha = int(255 * min(1, max(0, (progress - 0.4) * 3)))
        scale = 1 + pulse * 0.3
        new_color = tuple(int(c * new_alpha / 255) for c in accent_color)
        draw.text((W//2 - 10, H//2 - 60 - level_bounce), f"Lv.{new_level}", fill=new_color)

        # Entity name
        draw.text((W//2 - 100, H//2 + 10), f"{entity_name}", fill=COLORS['white'])
        draw.text((W//2 - 80, H//2 + 35), "LEVELED UP!", fill=accent_color)

        # Stars bursting
        if progress > 0.5:
            star_count = int((progress - 0.5) * 2 * 12)
            for i in range(star_count):
                angle = (i / 12) * 2 * math.pi
                distance = int((progress - 0.5) * 2 * 150)
                sx = W//2 + int(math.cos(angle) * distance)
                sy = H//2 - 20 + int(math.sin(angle) * distance)
                size = max(2, int(8 * (1 - progress)))
                draw.ellipse([sx-size, sy-size, sx+size, sy+size], fill=COLORS['gold'])

        frames.append(img)

    filename = f'levelup_{entity_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.gif'
    return save_gif(frames, filename, duration=100)


# ============================================================================
# 3. VICTORY/REWARD ANIMATION
# ============================================================================

def generate_reward_animation(reward_type: str, amount: int, bonus_text: str = "") -> str:
    """
    Generate reward collection animation.
    reward_type: 'gold' | 'food' | 'gems' | 'trophy' | 'chest'
    """
    W, H = 500, 350
    frames = []
    num_frames = 20

    reward_colors = {
        'gold': COLORS['gold'],
        'food': COLORS['food'],
        'gems': COLORS['blue'],
        'trophy': COLORS['gold'],
        'chest': COLORS['orange']
    }
    reward_labels = {
        'gold': 'GOLD',
        'food': 'FOOD',
        'gems': 'GEMS',
        'trophy': 'TROPHY',
        'chest': 'CHEST'
    }
    color = reward_colors.get(reward_type, COLORS['gold'])
    label = reward_labels.get(reward_type, 'REWARD')

    for frame_idx in range(num_frames):
        progress = frame_idx / (num_frames - 1)
        img = create_gradient_background(W, H, COLORS['bg_dark'], (25, 35, 25))
        draw = ImageDraw.Draw(img)

        # Floating particles
        random.seed(123)
        for i in range(25):
            fx = random.randint(0, W)
            base_fy = random.randint(0, H)
            fy = int(base_fy - progress * 100) % H
            size = random.randint(1, 3)
            brightness = random.random()
            if brightness > 0.4:
                c = tuple(int(ch * brightness) for ch in color)
                draw.ellipse([fx-size, fy-size, fx+size, fy+size], fill=c)

        # Central reward icon (pulsing circle)
        pulse = 1 + abs(math.sin(progress * 10)) * 0.2
        radius = int(50 * pulse)

        # Outer glow rings
        for ring in range(3):
            ring_radius = radius + ring * 20 + int(progress * 50)
            ring_alpha = max(0, int(100 - ring * 30 - progress * 50))
            ring_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            ring_draw = ImageDraw.Draw(ring_layer)
            ring_draw.ellipse([W//2-ring_radius, H//2-20-ring_radius,
                               W//2+ring_radius, H//2-20+ring_radius],
                              outline=(*color, ring_alpha), width=2)
            img = Image.alpha_composite(img.convert('RGBA'), ring_layer).convert('RGB')
            draw = ImageDraw.Draw(img)

        # Main reward circle
        draw.ellipse([W//2-radius, H//2-20-radius, W//2+radius, H//2-20+radius],
                     fill=color, outline=tuple(min(255, c+50) for c in color), width=3)

        # Label text
        draw.text((W//2 - 40, H//2 - 30), label, fill=COLORS['white'])

        # Amount with counting animation
        display_amount = int(amount * min(1, progress * 1.5))
        amount_text = f"+{display_amount:,}"
        draw.text((W//2 - 60, H//2 + 10), amount_text, fill=COLORS['white'])

        # Bonus text
        if bonus_text and progress > 0.6:
            alpha = int(255 * min(1, (progress - 0.6) * 3))
            bonus_c = tuple(int(c * alpha / 255) for c in COLORS['green'])
            draw.text((W//2 - 80, H//2 + 50), bonus_text, fill=bonus_c)

        # Celebration burst at end
        if progress > 0.8:
            burst_count = int((progress - 0.8) * 5 * 20)
            for i in range(burst_count):
                angle = random.uniform(0, 2 * math.pi)
                distance = random.randint(80, 200)
                bx = W//2 + int(math.cos(angle) * distance)
                by = H//2 - 20 + int(math.sin(angle) * distance)
                bsize = random.randint(2, 6)
                burst_color = random.choice([color, COLORS['gold'], COLORS['yellow']])
                draw.ellipse([bx-bsize, by-bsize, bx+bsize, by+bsize], fill=burst_color)

        frames.append(img)

    filename = f'reward_{reward_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.gif'
    return save_gif(frames, filename, duration=100)


# ============================================================================
# 4. SPIN WHEEL ANIMATION
# ============================================================================

def generate_spin_animation(items: List[str], win_index: int, colors: Optional[List] = None) -> str:
    """
    Generate lucky spin wheel animation.
    items: List of prize names
    win_index: Index of winning item
    """
    W, H = 400, 400
    frames = []
    num_frames = 30

    if colors is None:
        colors = [COLORS['primary'], COLORS['secondary'], COLORS['accent'],
                  COLORS['gold'], COLORS['food'], COLORS['red'], COLORS['blue'], COLORS['purple']]

    wheel_radius = 150
    center_x, center_y = W // 2, H // 2
    num_items = len(items)
    angle_per_item = 360 / num_items

    # Spin with deceleration
    total_rotation = 360 * 5 + win_index * angle_per_item  # 5 full spins + land on winner

    for frame_idx in range(num_frames):
        progress = frame_idx / (num_frames - 1)
        # Ease out cubic
        eased = 1 - (1 - progress) ** 3
        current_rotation = total_rotation * eased

        img = create_gradient_background(W, H, COLORS['bg_dark'], (25, 25, 45))
        draw = ImageDraw.Draw(img)

        # Draw wheel
        for i in range(num_items):
            start_angle = math.radians(i * angle_per_item + current_rotation - 90)
            end_angle = math.radians((i + 1) * angle_per_item + current_rotation - 90)
            item_color = colors[i % len(colors)]

            # Draw wedge as polygon
            points = [(center_x, center_y)]
            steps = 20
            for step in range(steps + 1):
                angle = start_angle + (end_angle - start_angle) * step / steps
                x = center_x + int(wheel_radius * math.cos(angle))
                y = center_y + int(wheel_radius * math.sin(angle))
                points.append((x, y))

            draw.polygon(points, fill=item_color, outline=COLORS['bg_dark'])

            # Draw text
            mid_angle = (start_angle + end_angle) / 2
            text_radius = wheel_radius * 0.65
            tx = center_x + int(text_radius * math.cos(mid_angle))
            ty = center_y + int(text_radius * math.sin(mid_angle))
            item_text = items[i][:8]
            draw.text((tx - 20, ty - 5), item_text, fill=COLORS['white'])

        # Draw center circle
        draw.ellipse([center_x-20, center_y-20, center_x+20, center_y+20],
                     fill=COLORS['gold'], outline=COLORS['bg_dark'], width=3)

        # Draw pointer at top
        draw.polygon([(center_x, center_y - wheel_radius - 15),
                      (center_x - 10, center_y - wheel_radius),
                      (center_x + 10, center_y - wheel_radius)],
                     fill=COLORS['red'])

        # Flash effect at end
        if progress > 0.9:
            flash = Image.new('RGBA', (W, H), (*COLORS['gold'], int(100 * (progress - 0.9) * 10)))
            img = Image.alpha_composite(img.convert('RGBA'), flash).convert('RGB')

        frames.append(img)

    filename = f'spin_wheel_{datetime.now().strftime("%Y%m%d_%H%M%S")}.gif'
    return save_gif(frames, filename, duration=80)


# ============================================================================
# 5. TRAINING ANIMATION
# ============================================================================

def generate_training_animation(unit_type: str, count: int) -> str:
    """
    Generate army training animation.
    unit_type: 'infantry' | 'archers' | 'cavalry'
    """
    W, H = 500, 280
    frames = []
    num_frames = 18

    unit_colors = {
        'infantry': COLORS['red'],
        'archers': COLORS['blue'],
        'cavalry': COLORS['yellow']
    }
    unit_names = {
        'infantry': 'INFANTRY',
        'archers': 'ARCHERS',
        'cavalry': 'CAVALRY'
    }
    color = unit_colors.get(unit_type, COLORS['red'])
    name = unit_names.get(unit_type, 'UNITS')

    for frame_idx in range(num_frames):
        progress = frame_idx / (num_frames - 1)
        img = create_gradient_background(W, H, COLORS['bg_dark'], (25, 30, 25))
        draw = ImageDraw.Draw(img)

        # Training ground
        draw.rectangle([0, H-50, W, H], fill=(40, 35, 30))
        draw.line([(0, H-50), (W, H-50)], fill=COLORS['gold'], width=2)

        # Animated units forming up
        units_per_row = 8
        unit_size = 12
        spacing = 50
        start_x = 50
        start_y = H - 100

        visible_units = int(count * min(1, progress * 1.5))
        for i in range(min(visible_units, 24)):  # Show max 24 units
            col = i % units_per_row
            row = i // units_per_row
            ux = start_x + col * spacing
            uy = start_y - row * 30

            # Marching animation
            march_offset = int(math.sin(progress * 8 + i * 0.5) * 3)
            draw.ellipse([ux-unit_size, uy-unit_size+march_offset,
                          ux+unit_size, uy+unit_size+march_offset], fill=color)
            # Weapon/symbol
            draw.rectangle([ux-3, uy-15+march_offset, ux+3, uy-5+march_offset],
                          fill=COLORS['silver'])

        # Title
        draw.text((W//2 - 80, 20), f"TRAINING {name}", fill=COLORS['white'])
        draw.text((W//2 - 60, 45), f"Count: {visible_units}/{count}", fill=color)

        # Progress bar
        bar_width = 300
        bar_x = W//2 - bar_width//2
        bar_y = 80
        draw.rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + 20],
                      outline=COLORS['white'], width=1)
        fill_width = int(bar_width * progress)
        draw.rectangle([bar_x, bar_y, bar_x + fill_width, bar_y + 20], fill=color)
        draw.text((bar_x + bar_width//2 - 30, bar_y + 22), f"{int(progress*100)}%", fill=COLORS['white'])

        frames.append(img)

    filename = f'training_{unit_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.gif'
    return save_gif(frames, filename, duration=120)


# ============================================================================
# 6. ACHIEVEMENT UNLOCK ANIMATION
# ============================================================================

def generate_achievement_animation(achievement_name: str, rarity: str = "common") -> str:
    """
    Generate achievement unlock animation.
    rarity: 'common' | 'rare' | 'epic' | 'legendary'
    """
    W, H = 500, 300
    frames = []
    num_frames = 22

    rarity_colors = {
        'common': COLORS['silver'],
        'rare': COLORS['blue'],
        'epic': COLORS['purple'],
        'legendary': COLORS['gold']
    }
    color = rarity_colors.get(rarity, COLORS['gold'])

    for frame_idx in range(num_frames):
        progress = frame_idx / (num_frames - 1)
        img = create_gradient_background(W, H, COLORS['bg_dark'], (30, 25, 20))
        draw = ImageDraw.Draw(img)

        # Trophy glow
        pulse = 1 + abs(math.sin(progress * 8)) * 0.3
        glow_r = int(60 * pulse)
        glow_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_layer)
        for r in range(glow_r, 0, -4):
            alpha = int(80 * (r / glow_r) * (1 - progress * 0.5))
            glow_draw.ellipse([W//2-r, H//2-30-r, W//2+r, H//2-30+r],
                              fill=(*color, alpha))
        img = Image.alpha_composite(img.convert('RGBA'), glow_layer).convert('RGB')
        draw = ImageDraw.Draw(img)

        # Trophy shape (simplified)
        trophy_y = H // 2 - 40
        # Trophy cup
        draw.ellipse([W//2-30, trophy_y-20, W//2+30, trophy_y+20],
                     fill=color, outline=tuple(min(255, c+60) for c in color), width=2)
        # Trophy base
        draw.rectangle([W//2-15, trophy_y+20, W//2+15, trophy_y+45],
                      fill=color, outline=tuple(min(255, c+60) for c in color), width=2)
        # Handles
        draw.arc([W//2-40, trophy_y-15, W//2-20, trophy_y+15], 90, 270,
                 fill=tuple(min(255, c+60) for c in color), width=3)
        draw.arc([W//2+20, trophy_y-15, W//2+40, trophy_y+15], 270, 90,
                 fill=tuple(min(255, c+60) for c in color), width=3)

        # Text animations
        if progress > 0.2:
            alpha = int(255 * min(1, (progress - 0.2) * 3))
            c = tuple(int(ch * alpha / 255) for ch in COLORS['white'])
            draw.text((W//2 - 80, trophy_y + 60), "ACHIEVEMENT UNLOCKED!", fill=c)

        if progress > 0.4:
            alpha2 = int(255 * min(1, (progress - 0.4) * 3))
            name_c = tuple(int(ch * alpha2 / 255) for ch in color)
            draw.text((W//2 - len(achievement_name)*4, trophy_y + 85), achievement_name, fill=name_c)

        if progress > 0.6:
            alpha3 = int(255 * min(1, (progress - 0.6) * 3))
            rarity_c = tuple(int(ch * alpha3 / 255) for ch in color)
            draw.text((W//2 - 40, trophy_y + 110), f"[{rarity.upper()}]", fill=rarity_c)

        # Sparkle particles
        if progress > 0.3:
            random.seed(456)
            sparkle_count = int((progress - 0.3) * 15)
            for i in range(sparkle_count):
                sx = random.randint(0, W)
                sy = random.randint(0, H)
                size = random.randint(1, 4)
                sparkle_alpha = random.random()
                if sparkle_alpha > 0.3:
                    sc = tuple(int(ch * sparkle_alpha) for ch in color)
                    draw.ellipse([sx-size, sy-size, sx+size, sy+size], fill=sc)

        frames.append(img)

    filename = f'achievement_{rarity}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.gif'
    return save_gif(frames, filename, duration=100)


# ============================================================================
# 7. ATTACK ALERT ANIMATION
# ============================================================================

def generate_attack_alert_animation(attacker_name: str, attack_power: int) -> str:
    """
    Generate attack warning/alert animation.
    """
    W, H = 500, 280
    frames = []
    num_frames = 16

    for frame_idx in range(num_frames):
        progress = frame_idx / (num_frames - 1)
        img = create_gradient_background(W, H, COLORS['bg_dark'], (40, 20, 20))
        draw = ImageDraw.Draw(img)

        # Pulsing red warning overlay
        pulse = abs(math.sin(progress * 12))
        warning_layer = Image.new('RGBA', (W, H), (255, 0, 0, int(30 * pulse)))
        img = Image.alpha_composite(img.convert('RGBA'), warning_layer).convert('RGB')
        draw = ImageDraw.Draw(img)

        # Warning border
        border_width = int(5 * pulse)
        draw.rectangle([border_width, border_width, W-border_width, H-border_width],
                      outline=COLORS['red'], width=border_width)

        # Warning icon (triangle)
        tri_y = 60
        draw.polygon([(W//2, tri_y-30), (W//2-25, tri_y+15), (W//2+25, tri_y+15)],
                     fill=COLORS['red'], outline=COLORS['yellow'], width=2)
        draw.text((W//2-3, tri_y-5), "!", fill=COLORS['yellow'])

        # Alert text
        draw.text((W//2-100, tri_y+30), "UNDER ATTACK!", fill=COLORS['red'])
        draw.text((W//2-120, tri_y+55), f"Attacker: {attacker_name}", fill=COLORS['white'])
        draw.text((W//2-100, tri_y+75), f"Power: {attack_power:,}", fill=COLORS['gold'])

        # Animated swords
        sword_x = W//2 - 50 + int(progress * 100)
        draw.line([(sword_x-20, tri_y+100), (sword_x+20, tri_y+120)], fill=COLORS['silver'], width=3)
        draw.line([(W-sword_x-20, tri_y+100), (W-sword_x+20, tri_y+120)], fill=COLORS['silver'], width=3)

        frames.append(img)

    filename = f'attack_alert_{datetime.now().strftime("%Y%m%d_%H%M%S")}.gif'
    return save_gif(frames, filename, duration=100)


# ============================================================================
# 8. DAILY LOGIN STREAK ANIMATION
# ============================================================================

def generate_login_streak_animation(streak_days: int, bonus_reward: int = 0) -> str:
    """
    Generate daily login streak celebration animation.
    """
    W, H = 500, 300
    frames = []
    num_frames = 20

    for frame_idx in range(num_frames):
        progress = frame_idx / (num_frames - 1)
        img = create_gradient_background(W, H, COLORS['bg_dark'], (25, 25, 35))
        draw = ImageDraw.Draw(img)

        # Day counters
        day_size = 35
        start_x = 50
        y_pos = H // 2 - 30
        spacing = 55

        for day in range(1, min(streak_days + 3, 8)):
            dx = start_x + (day - 1) * spacing
            is_completed = day <= streak_days
            is_today = day == streak_days

            if is_completed:
                fill_c = COLORS['green'] if not is_today else COLORS['gold']
                text_c = COLORS['bg_dark']
            else:
                fill_c = COLORS['bg_card']
                text_c = COLORS['white']

            # Pulsing today
            if is_today:
                scale = 1 + abs(math.sin(progress * 10)) * 0.2
                dsize = int(day_size * scale)
            else:
                dsize = day_size

            draw.ellipse([dx-dsize, y_pos-dsize, dx+dsize, y_pos+dsize],
                        fill=fill_c, outline=COLORS['gold'] if is_today else COLORS['secondary'], width=2)
            draw.text((dx-8, y_pos-8), str(day), fill=text_c)

            # Checkmark for completed
            if is_completed and not is_today:
                draw.text((dx-5, y_pos+20), "OK", fill=COLORS['green'])

        # Streak text
        draw.text((W//2 - 100, y_pos - 70), f"{streak_days} DAY STREAK!", fill=COLORS['gold'])

        # Bonus animation
        if bonus_reward > 0 and progress > 0.5:
            bonus_alpha = int(255 * min(1, (progress - 0.5) * 3))
            bonus_c = tuple(int(c * bonus_alpha / 255) for c in COLORS['green'])
            draw.text((W//2 - 80, y_pos + 60), f"Bonus: +{bonus_reward:,} Gold", fill=bonus_c)

        # Confetti
        if progress > 0.3:
            random.seed(789)
            for i in range(int(progress * 20)):
                cx = random.randint(0, W)
                cy = int(random.randint(0, H//2) - progress * 50)
                size = random.randint(2, 5)
                confetti_c = random.choice([COLORS['gold'], COLORS['green'], COLORS['red'],
                                           COLORS['blue'], COLORS['yellow']])
                draw.rectangle([cx-size, cy-size, cx+size, cy+size], fill=confetti_c)

        frames.append(img)

    filename = f'login_streak_{datetime.now().strftime("%Y%m%d_%H%M%S")}.gif'
    return save_gif(frames, filename, duration=100)


# ============================================================================
# UTILITY: Cleanup old animations
# ============================================================================

def cleanup_old_animations(max_age_hours: int = 24):
    """Remove animation GIFs older than specified hours."""
    if not os.path.exists(ANIMATIONS_DIR):
        return
    cutoff = datetime.now() - __import__('datetime').timedelta(hours=max_age_hours)
    for filename in os.listdir(ANIMATIONS_DIR):
        filepath = os.path.join(ANIMATIONS_DIR, filename)
        if os.path.isfile(filepath):
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            if mtime < cutoff:
                try:
                    os.remove(filepath)
                except OSError:
                    pass
