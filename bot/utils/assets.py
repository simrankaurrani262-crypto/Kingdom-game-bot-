"""
Asset registry for Kingdom Conquest.
Maps game elements to their visual asset files.
"""
import os

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets')

# Hero portraits
HERO_IMAGES = {
    'sir_aldric': os.path.join(ASSETS_DIR, 'hero_sir_aldric.png'),
    'lyra': os.path.join(ASSETS_DIR, 'hero_lyra.png'),
    'kael': os.path.join(ASSETS_DIR, 'hero_kael.png'),
    'morgana': os.path.join(ASSETS_DIR, 'hero_morgana.png'),
    'shadow': os.path.join(ASSETS_DIR, 'hero_shadow.png'),
}

# Building images
BUILDING_IMAGES = {
    'town_hall': os.path.join(ASSETS_DIR, 'building_townhall.png'),
    'gold_mine': os.path.join(ASSETS_DIR, 'building_goldmine.png'),
    'farm': os.path.join(ASSETS_DIR, 'building_farm.png'),
    'barracks': os.path.join(ASSETS_DIR, 'building_barracks.png'),
    'wall': os.path.join(ASSETS_DIR, 'building_wall.png'),
}

# Scene images
SCENE_IMAGES = {
    'welcome': os.path.join(ASSETS_DIR, 'welcome_banner.png'),
    'battle': os.path.join(ASSETS_DIR, 'battle_scene.png'),
    'spy': os.path.join(ASSETS_DIR, 'spy_scene.png'),
    'alliance': os.path.join(ASSETS_DIR, 'alliance_banner.png'),
    'black_market': os.path.join(ASSETS_DIR, 'black_market.png'),
    'victory': os.path.join(ASSETS_DIR, 'victory.png'),
}

def get_hero_image(hero_key: str) -> str:
    """Get path to hero portrait."""
    return HERO_IMAGES.get(hero_key, '')

def get_building_image(building_type: str) -> str:
    """Get path to building image."""
    return BUILDING_IMAGES.get(building_type, '')

def get_scene_image(scene: str) -> str:
    """Get path to scene image."""
    return SCENE_IMAGES.get(scene, '')

def asset_exists(path: str) -> bool:
    """Check if an asset file exists."""
    return path and os.path.isfile(path)

def get_all_assets() -> dict:
    """Get all available assets."""
    return {
        'heroes': {k: v for k, v in HERO_IMAGES.items() if asset_exists(v)},
        'buildings': {k: v for k, v in BUILDING_IMAGES.items() if asset_exists(v)},
        'scenes': {k: v for k, v in SCENE_IMAGES.items() if asset_exists(v)},
    }
