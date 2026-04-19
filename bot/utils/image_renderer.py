"""
Dynamic Image Rendering Engine for Kingdom Conquest Bot.
Creates rich visual cards and HUD elements using PIL.
Generates: Hero cards, Battle reports, Kingdom banners, Spy reports, Stat cards.

Dependencies: Pillow, numpy (optional)
"""
import os
import io
import math
import random
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

CARDS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'cards')
os.makedirs(CARDS_DIR, exist_ok=True)

# =============================================================================
# COLOR SCHEMES
# =============================================================================

THEMES = {
    'dark_kingdom': {
        'bg': (26, 26, 46),
        'card': (22, 33, 62),
        'accent': (233, 69, 96),
        'text': (224, 224, 224),
        'muted': (136, 136, 136),
        'border': (15, 52, 96),
        'success': (78, 204, 163),
        'warning': (255, 215, 0),
        'danger': (255, 107, 107),
    },
    'golden_empire': {
        'bg': (25, 20, 10),
        'card': (45, 35, 15),
        'accent': (255, 215, 0),
        'text': (255, 248, 220),
        'muted': (180, 160, 120),
        'border': (180, 140, 60),
        'success': (200, 180, 80),
        'warning': (255, 180, 0),
        'danger': (200, 80, 60),
    },
    'frost_guardian': {
        'bg': (10, 20, 30),
        'card': (15, 30, 50),
        'accent': (100, 200, 255),
        'text': (220, 240, 255),
        'muted': (100, 140, 180),
        'border': (50, 100, 150),
        'success': (80, 200, 160),
        'warning': (100, 220, 255),
        'danger': (255, 100, 100),
    }
}

RARITY_COLORS = {
    'common': (192, 192, 192),
    'uncommon': (100, 200, 100),
    'rare': (100, 150, 255),
    'epic': (180, 100, 255),
    'legendary': (255, 180, 50),
    'mythic': (255, 80, 80),
}


def get_theme(name: str = 'dark_kingdom') -> Dict:
    """Get color theme by name."""
    return THEMES.get(name, THEMES['dark_kingdom'])


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def create_gradient(width: int, height: int, color1: Tuple[int, int, int],
                    color2: Tuple[int, int, int], direction: str = 'vertical') -> Image.Image:
    """Create gradient background."""
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    max_dim = height if direction == 'vertical' else width
    for i in range(max_dim):
        ratio = i / max_dim
        r = int(color1[0] + (color2[0] - color1[0]) * ratio)
        g = int(color1[1] + (color2[1] - color1[1]) * ratio)
        b = int(color1[2] + (color2[2] - color1[2]) * ratio)
        if direction == 'vertical':
            draw.line([(0, i), (width, i)], fill=(r, g, b))
        else:
            draw.line([(i, 0), (i, height)], fill=(r, g, b))
    return img


def add_rounded_rect(img: Image.Image, xy, radius: int, fill, outline=None, width=1):
    """Add rounded rectangle to image."""
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)
    return img


def add_glow(img: Image.Image, center: Tuple[int, int], radius: int,
             color: Tuple[int, int, int], intensity: float = 0.4) -> Image.Image:
    """Add radial glow effect."""
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for r in range(radius, 0, -3):
        alpha = int(255 * intensity * (r / radius))
        draw.ellipse([center[0]-r, center[1]-r, center[0]+r, center[1]+r],
                     fill=(*color, alpha))
    return Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')


def add_text_shadow(draw, text: str, pos: Tuple[int, int], fill, shadow_color=(0, 0, 0),
                    offset: int = 2):
    """Draw text with shadow."""
    x, y = pos
    draw.text((x + offset, y + offset), text, fill=shadow_color)
    draw.text((x, y), text, fill=fill)


# =============================================================================
# 1. HERO STAT CARD
# =============================================================================

def render_hero_card(hero_name: str, hero_title: str, level: int, rarity: str,
                     stats: Dict[str, int], skill_tree: Dict, experience: int,
                     exp_to_next: int, image_path: Optional[str] = None,
                     theme_name: str = 'dark_kingdom') -> str:
    """
    Generate a beautiful hero stat card image.
    stats: {'attack': 85, 'defense': 70, 'hp': 1200, 'speed': 60}
    skill_tree: {'attack': 3, 'defense': 2, 'economy': 1}
    """
    theme = get_theme(theme_name)
    W, H = 500, 700
    rarity_color = RARITY_COLORS.get(rarity, RARITY_COLORS['common'])

    # Background with rarity glow
    img = create_gradient(W, H, theme['bg'], tuple(max(0, c - 10) for c in theme['bg']))
    img = add_glow(img, (W // 2, H // 2), 250, rarity_color, intensity=0.15)

    draw = ImageDraw.Draw(img)

    # Card border with rarity color
    border_padding = 15
    add_rounded_rect(img, (border_padding, border_padding, W - border_padding, H - border_padding),
                     20, None, rarity_color, 3)

    # Inner card
    inner_padding = 25
    add_rounded_rect(img, (inner_padding, inner_padding, W - inner_padding, H - inner_padding),
                     15, theme['card'], theme['border'], 2)

    # Hero portrait area
    portrait_y = 60
    portrait_size = 120

    # Portrait circle background
    draw.ellipse([W // 2 - portrait_size, portrait_y - portrait_size // 2,
                  W // 2 + portrait_size, portrait_y + portrait_size * 1.5],
                 fill=theme['bg'], outline=rarity_color, width=4)

    # Try to load hero image
    if image_path and os.path.exists(image_path):
        try:
            hero_img = Image.open(image_path).convert('RGBA')
            hero_img = hero_img.resize((portrait_size * 2 - 20, portrait_size * 2 - 20),
                                       Image.LANCZOS)
            # Create circular mask
            mask = Image.new('L', hero_img.size, 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse([0, 0, hero_img.size[0], hero_img.size[1]], fill=255)
            hero_img.putalpha(mask)
            img.paste(hero_img, (W // 2 - portrait_size + 10, portrait_y - portrait_size // 2 + 10),
                     hero_img)
        except Exception:
            draw.ellipse([W // 2 - portrait_size + 10, portrait_y - portrait_size // 2 + 10,
                          W // 2 + portrait_size - 10, portrait_y + portrait_size * 1.5 - 10],
                         fill=rarity_color)
    else:
        # Placeholder with initial
        draw.ellipse([W // 2 - portrait_size + 10, portrait_y - portrait_size // 2 + 10,
                      W // 2 + portrait_size - 10, portrait_y + portrait_size * 1.5 - 10],
                     fill=rarity_color)
        draw.text((W // 2 - 15, portrait_y + 20), hero_name[0].upper(),
                 fill=(255, 255, 255))

    # Rarity badge
    badge_y = portrait_y + portrait_size * 1.5 + 10
    add_rounded_rect(img, (W // 2 - 50, badge_y, W // 2 + 50, badge_y + 25), 12, rarity_color)
    draw.text((W // 2 - 30, badge_y + 5), rarity.upper(), fill=theme['bg'])

    # Hero name
    name_y = badge_y + 40
    draw.text((W // 2 - len(hero_name) * 6, name_y), hero_name, fill=theme['text'])
    draw.text((W // 2 - len(hero_title) * 5, name_y + 25), hero_title, fill=theme['muted'])

    # Level
    level_y = name_y + 55
    draw.text((50, level_y), f"Level: {level}", fill=theme['accent'])

    # EXP bar
    exp_y = level_y + 25
    exp_width = 400
    exp_fill = int((experience / max(exp_to_next, 1)) * exp_width)
    add_rounded_rect(img, (50, exp_y, 50 + exp_width, exp_y + 18), 9, theme['bg'],
                     theme['border'], 1)
    if exp_fill > 0:
        add_rounded_rect(img, (50, exp_y, 50 + exp_fill, exp_y + 18), 9, theme['warning'])
    draw.text((55, exp_y + 1), f"EXP: {experience:,}/{exp_to_next:,}", fill=theme['text'])

    # Stats section
    stats_y = exp_y + 45
    draw.text((50, stats_y), "STATS", fill=theme['accent'])
    add_rounded_rect(img, (45, stats_y + 20, W - 45, stats_y + 200), 10, theme['bg'],
                     theme['border'], 1)

    stat_items = list(stats.items())
    for i, (stat_name, stat_value) in enumerate(stat_items):
        row = i // 2
        col = i % 2
        sx = 65 + col * 210
        sy = stats_y + 35 + row * 55

        # Stat icon background
        stat_colors = {'attack': theme['danger'], 'defense': theme['success'],
                      'hp': theme['warning'], 'speed': theme['accent']}
        stat_color = stat_colors.get(stat_name.lower(), theme['muted'])

        add_rounded_rect(img, (sx, sy, sx + 30, sy + 30), 8, stat_color)
        draw.text((sx + 5, sy + 5), stat_name[0].upper(), fill=(255, 255, 255))
        draw.text((sx + 35, sy + 2), stat_name.upper(), fill=theme['muted'])
        draw.text((sx + 35, sy + 15), str(stat_value), fill=theme['text'])

    # Skill tree section
    skill_y = stats_y + 210
    draw.text((50, skill_y), "SKILL TREE", fill=theme['accent'])
    add_rounded_rect(img, (45, skill_y + 20, W - 45, skill_y + 110), 10, theme['bg'],
                     theme['border'], 1)

    skill_colors = {'attack': theme['danger'], 'defense': theme['success'],
                   'economy': theme['warning']}
    for i, (skill, points) in enumerate(skill_tree.items()):
        sx = 65 + i * 150
        sy = skill_y + 40
        sc = skill_colors.get(skill.lower(), theme['accent'])
        add_rounded_rect(img, (sx, sy, sx + 30, sy + 30), 8, sc)
        draw.text((sx + 5, sy + 5), skill[0].upper(), fill=(255, 255, 255))
        draw.text((sx + 35, sy + 2), skill.upper(), fill=theme['muted'])
        # Skill points dots
        for p in range(5):
            dot_color = sc if p < points else theme['border']
            draw.ellipse([sx + 35 + p * 15, sy + 18, sx + 45 + p * 15, sy + 28], fill=dot_color)

    # Footer
    footer_y = H - 50
    draw.text((W // 2 - 80, footer_y), "KINGDOM CONQUEST", fill=theme['muted'])

    # Save
    filepath = os.path.join(CARDS_DIR, f'hero_card_{hero_name.lower()}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
    img.save(filepath, quality=95)
    return filepath


# =============================================================================
# 2. BATTLE REPORT CARD
# =============================================================================

def render_battle_report(attacker_name: str, defender_name: str,
                         attacker_losses: Dict[str, int], defender_losses: Dict[str, int],
                         loot_gold: int, loot_food: int, result: str,
                         battle_rounds: int, total_damage: int,
                         theme_name: str = 'dark_kingdom') -> str:
    """
    Generate a visual battle report card.
    """
    theme = get_theme(theme_name)
    W, H = 550, 650

    result_colors = {'victory': theme['success'], 'defeat': theme['danger'], 'draw': theme['warning']}
    result_color = result_colors.get(result.lower(), theme['warning'])

    # Background
    img = create_gradient(W, H, theme['bg'], tuple(max(0, c - 15) for c in theme['bg']))
    img = add_glow(img, (W // 2, 100), 200, result_color, intensity=0.2)
    draw = ImageDraw.Draw(img)

    # Header
    add_rounded_rect(img, (20, 20, W - 20, 100), 15, theme['card'], result_color, 3)
    draw.text((W // 2 - 70, 35), "BATTLE REPORT", fill=result_color)
    draw.text((W // 2 - 40, 65), result.upper(), fill=theme['text'])

    # Attacker vs Defender
    add_rounded_rect(img, (20, 110, W - 20, 200), 10, theme['card'], theme['border'], 1)
    draw.text((40, 120), f"ATTACKER: {attacker_name}", fill=theme['danger'])
    draw.text((W - 200, 120), f"DEFENDER: {defender_name}", fill=theme['success'])
    draw.text((W // 2 - 15, 145), "VS", fill=theme['warning'])

    # Army comparison bars
    max_units = max(sum(attacker_losses.values()), sum(defender_losses.values()), 1)
    bar_width = 200

    y_offset = 170
    for side, losses, color, x_pos in [('ATK', attacker_losses, theme['danger'], 40),
                                        ('DEF', defender_losses, theme['success'], W - 250)]:
        total = sum(losses.values())
        bar_fill = int((total / max_units) * bar_width) if max_units > 0 else 0
        draw.text((x_pos, y_offset), f"{side}: {total:,} lost", fill=color)
        add_rounded_rect(img, (x_pos, y_offset + 18, x_pos + bar_width, y_offset + 30), 6,
                        theme['bg'], theme['border'], 1)
        if bar_fill > 0:
            add_rounded_rect(img, (x_pos, y_offset + 18, x_pos + bar_fill, y_offset + 30), 6, color)

    # Loot section
    loot_y = 220
    add_rounded_rect(img, (20, loot_y, W - 20, loot_y + 80), 10, theme['card'],
                     theme['border'], 1)
    draw.text((40, loot_y + 10), "LOOT GAINED", fill=theme['warning'])
    draw.text((40, loot_y + 35), f"Gold: +{loot_gold:,}", fill=theme['warning'])
    draw.text((W // 2, loot_y + 35), f"Food: +{loot_food:,}", fill=theme['success'])

    # Detailed losses
    detail_y = 320
    add_rounded_rect(img, (20, detail_y, W - 20, detail_y + 200), 10, theme['card'],
                     theme['border'], 1)
    draw.text((40, detail_y + 10), "CASUALTY REPORT", fill=theme['accent'])

    unit_types = ['infantry', 'archers', 'cavalry']
    for i, unit in enumerate(unit_types):
        row_y = detail_y + 40 + i * 45
        atk_loss = attacker_losses.get(unit, 0)
        def_loss = defender_losses.get(unit, 0)

        unit_colors = {'infantry': theme['danger'], 'archers': theme['success'],
                      'cavalry': theme['warning']}
        uc = unit_colors.get(unit, theme['muted'])

        draw.text((40, row_y), unit.upper(), fill=uc)
        draw.text((150, row_y), f"ATK: -{atk_loss:,}", fill=theme['danger'])
        draw.text((300, row_y), f"DEF: -{def_loss:,}", fill=theme['success'])

        # Mini progress bar
        total_unit_loss = atk_loss + def_loss
        if total_unit_loss > 0:
            atk_ratio = int((atk_loss / total_unit_loss) * 150)
            add_rounded_rect(img, (150, row_y + 18, 300, row_y + 28), 5, theme['bg'])
            add_rounded_rect(img, (150, row_y + 18, 150 + atk_ratio, row_y + 28), 5,
                           theme['danger'])
            add_rounded_rect(img, (150 + atk_ratio, row_y + 18, 300, row_y + 28), 5,
                           theme['success'])

    # Battle stats
    stats_y = detail_y + 210
    add_rounded_rect(img, (20, stats_y, W - 20, stats_y + 60), 10, theme['card'],
                     theme['border'], 1)
    draw.text((40, stats_y + 10), f"Rounds: {battle_rounds}", fill=theme['text'])
    draw.text((200, stats_y + 10), f"Total Damage: {total_damage:,}", fill=theme['danger'])
    draw.text((400, stats_y + 10), f"Efficiency: {(loot_gold/max(total_damage,1)*100):.1f}%",
             fill=theme['warning'])

    # Footer timestamp
    draw.text((W // 2 - 80, H - 40), f"Report ID: {datetime.now().strftime('%Y%m%d%H%M')}",
             fill=theme['muted'])

    filepath = os.path.join(CARDS_DIR, f'battle_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
    img.save(filepath, quality=95)
    return filepath


# =============================================================================
# 3. KINGDOM BANNER
# =============================================================================

def render_kingdom_banner(kingdom_name: str, king_name: str, flag_emoji: str,
                          power: int, gold: int, food: int, army: int,
                          buildings: int, wins: int, rank: int,
                          theme_name: str = 'dark_kingdom') -> str:
    """
    Generate a kingdom banner/header image.
    """
    theme = get_theme(theme_name)
    W, H = 800, 400

    # Rich gradient background
    img = create_gradient(W, H, theme['bg'], (theme['bg'][0] + 10, theme['bg'][1] + 5, theme['bg'][2] + 15))
    img = add_glow(img, (W // 2, H // 2), 300, theme['accent'], intensity=0.1)
    draw = ImageDraw.Draw(img)

    # Top accent bar
    add_rounded_rect(img, (0, 0, W, 8), 0, theme['accent'])

    # Kingdom name area
    draw.text((60, 40), flag_emoji, fill=theme['text'])
    draw.text((100, 40), kingdom_name.upper(), fill=theme['accent'])
    draw.text((100, 70), f"Ruler: {king_name}", fill=theme['muted'])

    # Rank badge
    rank_colors = {1: (255, 215, 0), 2: (192, 192, 192), 3: (205, 127, 50)}
    rank_color = rank_colors.get(rank, theme['muted'])
    add_rounded_rect(img, (W - 120, 40, W - 40, 90), 25, rank_color)
    draw.text((W - 95, 50), f"#{rank}", fill=theme['bg'])

    # Power display
    power_y = 120
    add_rounded_rect(img, (40, power_y, W - 40, power_y + 60), 15, theme['card'],
                     theme['border'], 2)
    draw.text((60, power_y + 5), "TOTAL POWER", fill=theme['muted'])
    draw.text((60, power_y + 25), f"{power:,}", fill=theme['accent'])

    # Stats grid
    grid_y = 200
    stats = [
        ('GOLD', gold, theme['warning']),
        ('FOOD', food, theme['success']),
        ('ARMY', army, theme['danger']),
        ('BUILDINGS', buildings, theme['accent']),
        ('WINS', wins, theme['warning']),
    ]

    for i, (label, value, color) in enumerate(stats):
        x_pos = 40 + i * 155
        add_rounded_rect(img, (x_pos, grid_y, x_pos + 145, grid_y + 80), 12, theme['card'],
                        color, 1)
        draw.text((x_pos + 10, grid_y + 5), label, fill=theme['muted'])
        draw.text((x_pos + 10, grid_y + 30), f"{value:,}", fill=color)

    # Progress section
    prog_y = 310
    add_rounded_rect(img, (40, prog_y, W - 40, prog_y + 60), 12, theme['card'],
                     theme['border'], 1)
    draw.text((60, prog_y + 5), "KINGDOM PROGRESS", fill=theme['muted'])
    # Overall progress bar
    progress_fill = int(min(1, (buildings / 125)) * (W - 100))  # 5 buildings * 25 max level
    add_rounded_rect(img, (60, prog_y + 30, W - 60, prog_y + 48), 9, theme['bg'],
                     theme['border'], 1)
    if progress_fill > 0:
        add_rounded_rect(img, (60, prog_y + 30, 60 + progress_fill, prog_y + 48), 9,
                        theme['accent'])
    draw.text((W // 2 - 30, prog_y + 50), f"{int(min(1, buildings/125)*100)}% Complete",
             fill=theme['muted'])

    filepath = os.path.join(CARDS_DIR, f'kingdom_banner_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
    img.save(filepath, quality=95)
    return filepath


# =============================================================================
# 4. SPY REPORT CARD
# =============================================================================

def render_spy_report(target_name: str, intel_level: str,  # basic/detailed/full
                      resources: Dict, army: Dict, buildings: Dict,
                      defense_rating: int, risk_level: str,  # low/medium/high/extreme
                      theme_name: str = 'dark_kingdom') -> str:
    """
    Generate a visual spy/intel report card.
    """
    theme = get_theme(theme_name)
    W, H = 500, 600

    risk_colors = {'low': theme['success'], 'medium': theme['warning'],
                   'high': theme['danger'], 'extreme': (200, 50, 50)}
    risk_color = risk_colors.get(risk_level, theme['warning'])
    intel_colors = {'basic': theme['muted'], 'detailed': theme['warning'], 'full': theme['success']}
    intel_color = intel_colors.get(intel_level, theme['muted'])

    # Background with risk tint
    img = create_gradient(W, H, theme['bg'], tuple(max(0, c - 5) for c in theme['bg']))
    img = add_glow(img, (W // 2, 80), 150, risk_color, intensity=0.1)
    draw = ImageDraw.Draw(img)

    # Header - Classified
    add_rounded_rect(img, (20, 20, W - 20, 90), 15, theme['card'], risk_color, 3)
    draw.text((W // 2 - 70, 30), "CLASSIFIED INTEL", fill=risk_color)
    draw.text((W // 2 - 60, 55), f"Target: {target_name}", fill=theme['text'])

    # Intel level badge
    add_rounded_rect(img, (W - 130, 30, W - 30, 55), 10, intel_color)
    draw.text((W - 120, 33), intel_level.upper(), fill=theme['bg'])

    # Risk indicator
    risk_y = 100
    add_rounded_rect(img, (20, risk_y, W - 20, risk_y + 50), 10, theme['card'],
                     theme['border'], 1)
    draw.text((40, risk_y + 5), "THREAT LEVEL", fill=theme['muted'])
    # Risk bar
    risk_width = 300
    risk_fill = {'low': 0.25, 'medium': 0.5, 'high': 0.75, 'extreme': 1.0}.get(risk_level, 0.5)
    add_rounded_rect(img, (150, risk_y + 5, 150 + risk_width, risk_y + 20), 8, theme['bg'],
                     theme['border'], 1)
    add_rounded_rect(img, (150, risk_y + 5, 150 + int(risk_width * risk_fill), risk_y + 20),
                     8, risk_color)
    draw.text((150 + risk_width + 10, risk_y + 3), risk_level.upper(), fill=risk_color)

    # Resources section
    res_y = risk_y + 60
    add_rounded_rect(img, (20, res_y, W - 20, res_y + 100), 10, theme['card'],
                     theme['border'], 1)
    draw.text((40, res_y + 5), "RESOURCES", fill=theme['warning'])
    if intel_level in ['detailed', 'full']:
        draw.text((40, res_y + 30), f"Gold: {resources.get('gold', '???'):,}", fill=theme['warning'])
        draw.text((250, res_y + 30), f"Food: {resources.get('food', '???'):,}", fill=theme['success'])
    else:
        draw.text((40, res_y + 30), f"Gold: {'~' + str(resources.get('gold', 0) // 1000) + 'K' if resources.get('gold') else '???'}", fill=theme['warning'])
        draw.text((250, res_y + 30), f"Food: {'~' + str(resources.get('food', 0) // 1000) + 'K' if resources.get('food') else '???'}", fill=theme['success'])

    # Army section
    army_y = res_y + 110
    add_rounded_rect(img, (20, army_y, W - 20, army_y + 130), 10, theme['card'],
                     theme['border'], 1)
    draw.text((40, army_y + 5), "ARMY COMPOSITION", fill=theme['danger'])

    unit_types = ['infantry', 'archers', 'cavalry']
    unit_colors = [theme['danger'], theme['success'], theme['warning']]
    for i, (unit, color) in enumerate(zip(unit_types, unit_colors)):
        uy = army_y + 35 + i * 28
        count = army.get(unit, 0) if intel_level in ['detailed', 'full'] else '???'
        draw.text((40, uy), f"{unit.upper()}: {count}", fill=color)

        # Mini bar
        if intel_level == 'full' and count != '???':
            max_count = max(army.values()) if army else 1
            bar_fill = int((count / max(max_count, 1)) * 200)
            add_rounded_rect(img, (200, uy + 2, 400, uy + 15), 6, theme['bg'])
            add_rounded_rect(img, (200, uy + 2, 200 + bar_fill, uy + 15), 6, color)

    # Buildings section
    build_y = army_y + 140
    add_rounded_rect(img, (20, build_y, W - 20, build_y + 100), 10, theme['card'],
                     theme['border'], 1)
    draw.text((40, build_y + 5), "BUILDINGS", fill=theme['accent'])

    if intel_level == 'full':
        for i, (btype, blevel) in enumerate(buildings.items()):
            by = build_y + 30 + i * 20
            draw.text((40 + (i % 3) * 160, by), f"{btype.replace('_', ' ').title()}: Lv.{blevel}",
                     fill=theme['text'])
    else:
        draw.text((40, build_y + 30), f"Building Count: {len(buildings)}", fill=theme['muted'])

    # Defense rating
    def_y = build_y + 110
    add_rounded_rect(img, (20, def_y, W - 20, def_y + 50), 10, theme['card'],
                     theme['border'], 1)
    draw.text((40, def_y + 5), "DEFENSE RATING", fill=theme['success'])
    def_fill = min(int((defense_rating / 1000) * 300), 300)
    add_rounded_rect(img, (180, def_y + 5, 480, def_y + 20), 8, theme['bg'])
    add_rounded_rect(img, (180, def_y + 5, 180 + def_fill, def_y + 20), 8, theme['success'])
    draw.text((490, def_y + 3), str(defense_rating), fill=theme['text'])

    filepath = os.path.join(CARDS_DIR, f'spy_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
    img.save(filepath, quality=95)
    return filepath


# =============================================================================
# 5. NOTIFICATION CARD
# =============================================================================

def render_notification_card(title: str, message: str, notif_type: str = "info",
                              action_text: str = "", theme_name: str = 'dark_kingdom') -> str:
    """
    Generate a notification card image.
    notif_type: 'info' | 'warning' | 'danger' | 'success' | 'event'
    """
    theme = get_theme(theme_name)
    W, H = 500, 250

    type_colors = {
        'info': theme['accent'],
        'warning': theme['warning'],
        'danger': theme['danger'],
        'success': theme['success'],
        'event': (180, 100, 255)
    }
    type_color = type_colors.get(notif_type, theme['accent'])

    type_emojis = {'info': '', 'warning': 'WARNING', 'danger': 'ALERT',
                  'success': 'SUCCESS', 'event': 'EVENT'}
    type_emoji = type_emojis.get(notif_type, '')

    img = create_gradient(W, H, theme['bg'], (theme['bg'][0] + 5, theme['bg'][1] + 5, theme['bg'][2] + 10))
    img = add_glow(img, (W // 2, H // 2), 180, type_color, intensity=0.15)
    draw = ImageDraw.Draw(img)

    # Left accent bar
    draw.rectangle([0, 0, 8, H], fill=type_color)

    # Type badge
    add_rounded_rect(img, (30, 25, 130, 50), 12, type_color)
    draw.text((40, 30), type_emoji, fill=theme['bg'])

    # Title
    draw.text((30, 65), title, fill=theme['text'])

    # Message
    draw.text((30, 100), message, fill=theme['muted'])

    # Action button
    if action_text:
        add_rounded_rect(img, (30, 160, 200, 195), 15, type_color)
        draw.text((50, 167), action_text, fill=theme['bg'])

    filepath = os.path.join(CARDS_DIR, f'notification_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
    img.save(filepath, quality=95)
    return filepath


# =============================================================================
# 6. LEADERBOARD PODIUM CARD
# =============================================================================

def render_leaderboard_podium(top_players: List[Dict], category: str = "power") -> str:
    """
    Generate a visual leaderboard podium image.
    top_players: [{'name': 'Player1', 'power': 10000, 'alliance': 'TeamA'}, ...] (top 3)
    """
    theme = get_theme('golden_empire')
    W, H = 600, 450

    podium_heights = [180, 220, 160]  # 1st, 2nd, 3rd
    podium_colors = [(255, 215, 0), (192, 192, 192), (205, 127, 50)]
    x_positions = [200, 50, 350]

    img = create_gradient(W, H, theme['bg'], (30, 25, 15))
    draw = ImageDraw.Draw(img)

    # Title
    draw.text((W // 2 - 80, 20), f"TOP {category.upper()}", fill=theme['accent'])

    # Draw podium blocks
    for i in range(min(3, len(top_players))):
        player = top_players[i]
        x = x_positions[i]
        h = podium_heights[i]
        y = H - h - 50
        color = podium_colors[i]

        # Podium block
        add_rounded_rect(img, (x, y, x + 150, y + h), 10, theme['card'], color, 2)

        # Rank
        draw.text((x + 55, y + 10), f"#{i+1}", fill=color)

        # Name
        name = player['name'][:12]
        draw.text((x + 10, y + 40), name, fill=theme['text'])

        # Value
        value = player.get(category, 0)
        draw.text((x + 10, y + 60), f"{value:,}", fill=color)

        # Alliance
        alliance = player.get('alliance', '')
        if alliance:
            draw.text((x + 10, y + 85), f"[{alliance}]", fill=theme['muted'])

        # Crown for 1st
        if i == 0:
            draw.text((x + 55, y - 30), "KING", fill=theme['accent'])

    filepath = os.path.join(CARDS_DIR, f'leaderboard_podium_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
    img.save(filepath, quality=95)
    return filepath
