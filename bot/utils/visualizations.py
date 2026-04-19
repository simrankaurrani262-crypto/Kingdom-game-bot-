"""
Advanced Visualization Engine for Kingdom Conquest Bot.
Generates high-quality charts, graphs, and visual data representations.
Supports: Bar charts, Pie charts, Line graphs, Radar charts, Heatmaps, Progress bars.

Dependencies: matplotlib, seaborn, numpy, Pillow
"""
import os
import io
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for server use
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyBboxPatch, Circle, Wedge
    from matplotlib.gridspec import GridSpec
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# Configure seaborn style
if MATPLOTLIB_AVAILABLE:
    sns.set_style("darkgrid")
    plt.rcParams['figure.facecolor'] = '#1a1a2e'
    plt.rcParams['axes.facecolor'] = '#16213e'
    plt.rcParams['text.color'] = '#e0e0e0'
    plt.rcParams['axes.labelcolor'] = '#e0e0e0'
    plt.rcParams['xtick.color'] = '#e0e0e0'
    plt.rcParams['ytick.color'] = '#e0e0e0'
    plt.rcParams['axes.edgecolor'] = '#0f3460'
    plt.rcParams['grid.color'] = '#0f3460'
    plt.rcParams['figure.dpi'] = 150

CHARTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'charts')
os.makedirs(CHARTS_DIR, exist_ok=True)

# Color schemes
KINGDOM_COLORS = {
    'primary': '#e94560',
    'secondary': '#0f3460',
    'accent': '#533483',
    'gold': '#ffd700',
    'food': '#4ecca3',
    'infantry': '#ff6b6b',
    'archers': '#4ecdc4',
    'cavalry': '#ffe66d',
    'bg_dark': '#1a1a2e',
    'bg_card': '#16213e',
    'text': '#e0e0e0'
}

ARMY_COLORS = {
    'infantry': '#ff6b6b',
    'archers': '#4ecdc4',
    'cavalry': '#ffe66d'
}

BUILDING_COLORS = {
    'town_hall': '#e94560',
    'gold_mine': '#ffd700',
    'farm': '#4ecca3',
    'barracks': '#ff6b6b',
    'wall': '#a8a8a8'
}


def ensure_matplotlib():
    """Check if matplotlib is available."""
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError("matplotlib and seaborn required. Install: pip install matplotlib seaborn numpy")


def save_chart(fig, filename: str) -> str:
    """Save matplotlib figure and return file path."""
    filepath = os.path.join(CHARTS_DIR, filename)
    fig.savefig(filepath, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none', pad_inches=0.2)
    plt.close(fig)
    return filepath


# ============================================================================
# 1. ARMY COMPOSITION CHART (Pie + Bar)
# ============================================================================

def generate_army_chart(infantry: int, archers: int, cavalry: int, kingdom_name: str = "Your Kingdom") -> str:
    """
    Generate a visual army composition chart.
    Returns: filepath to generated image
    """
    ensure_matplotlib()
    fig = plt.figure(figsize=(10, 5), facecolor=KINGDOM_COLORS['bg_dark'])
    gs = GridSpec(1, 2, figure=fig, width_ratios=[1, 1.2])

    # Pie Chart
    ax1 = fig.add_subplot(gs[0])
    labels = ['Infantry', 'Archers', 'Cavalry']
    sizes = [infantry, archers, cavalry]
    colors = [ARMY_COLORS['infantry'], ARMY_COLORS['archers'], ARMY_COLORS['cavalry']]
    explode = (0.02, 0.02, 0.02)
    wedges, texts, autotexts = ax1.pie(sizes, explode=explode, labels=labels, colors=colors,
                                        autopct='%1.1f%%', startangle=90,
                                        textprops={'color': '#e0e0e0', 'fontsize': 10},
                                        wedgeprops={'edgecolor': '#1a1a2e', 'linewidth': 2})
    for autotext in autotexts:
        autotext.set_fontweight('bold')
        autotext.set_fontsize(11)
    ax1.set_title('Army Composition', fontsize=14, fontweight='bold', color='#e0e0e0', pad=15)

    # Bar Chart
    ax2 = fig.add_subplot(gs[1])
    units = ['Infantry', 'Archers', 'Cavalry']
    counts = [infantry, archers, cavalry]
    bars = ax2.bar(units, counts, color=colors, edgecolor='#1a1a2e', linewidth=2, width=0.6)
    ax2.set_ylabel('Count', fontsize=11, fontweight='bold')
    ax2.set_title('Army Strength', fontsize=14, fontweight='bold', color='#e0e0e0', pad=15)
    ax2.tick_params(axis='x', labelsize=10)
    ax2.tick_params(axis='y', labelsize=9)

    # Add value labels on bars
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{count:,}', ha='center', va='bottom', fontsize=11, fontweight='bold', color='#e0e0e0')

    fig.suptitle(f'Army Report - {kingdom_name}', fontsize=16, fontweight='bold', color='#e94560', y=1.02)
    plt.tight_layout()
    return save_chart(fig, f'army_chart_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')


# ============================================================================
# 2. RESOURCE HISTORY LINE CHART
# ============================================================================

def generate_resource_chart(gold_history: List[int], food_history: List[int],
                            labels: Optional[List[str]] = None,
                            kingdom_name: str = "Your Kingdom") -> str:
    """
    Generate a line chart showing resource history over time.
    gold_history: List of gold values over time
    food_history: List of food values over time
    labels: Optional x-axis labels (dates/times)
    """
    ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(10, 5), facecolor=KINGDOM_COLORS['bg_dark'])
    ax.set_facecolor(KINGDOM_COLORS['bg_card'])

    x = range(len(gold_history))
    if labels is None:
        labels = [f'Day {i+1}' for i in x]

    ax.plot(x, gold_history, color=KINGDOM_COLORS['gold'], linewidth=2.5, marker='o',
            markersize=6, label='Gold', markerfacecolor='#ffed4a', markeredgecolor='#b8860b')
    ax.plot(x, food_history, color=KINGDOM_COLORS['food'], linewidth=2.5, marker='s',
            markersize=6, label='Food', markerfacecolor='#7ef9c1', markeredgecolor='#2e8b57')

    ax.fill_between(x, gold_history, alpha=0.15, color=KINGDOM_COLORS['gold'])
    ax.fill_between(x, food_history, alpha=0.15, color=KINGDOM_COLORS['food'])

    ax.set_xlabel('Time Period', fontsize=11, fontweight='bold')
    ax.set_ylabel('Resources', fontsize=11, fontweight='bold')
    ax.set_title(f'Resource Trends - {kingdom_name}', fontsize=14, fontweight='bold', color='#e0e0e0', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
    ax.legend(loc='upper left', framealpha=0.9, facecolor='#16213e', edgecolor='#0f3460', fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--')

    plt.tight_layout()
    return save_chart(fig, f'resource_chart_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')


# ============================================================================
# 3. BATTLE ANALYTICS CHART
# ============================================================================

def generate_battle_analytics(wins: int, losses: int, raids_won: int, raids_lost: int,
                              total_damage_dealt: int, total_damage_taken: int,
                              kingdom_name: str = "Your Kingdom") -> str:
    """
    Generate comprehensive battle analytics visualization.
    """
    ensure_matplotlib()
    fig = plt.figure(figsize=(12, 5), facecolor=KINGDOM_COLORS['bg_dark'])
    gs = GridSpec(1, 3, figure=fig, width_ratios=[1, 1, 1.2])

    # Win/Loss Pie
    ax1 = fig.add_subplot(gs[0])
    battle_labels = ['Wins', 'Losses']
    battle_sizes = [wins, losses]
    battle_colors = ['#4ecca3', '#e94560']
    wedges1, texts1, autotexts1 = ax1.pie(battle_sizes, labels=battle_labels, colors=battle_colors,
                                           autopct='%1.1f%%', startangle=90,
                                           textprops={'color': '#e0e0e0', 'fontsize': 10},
                                           wedgeprops={'edgecolor': '#1a1a2e', 'linewidth': 2})
    for autotext in autotexts1:
        autotext.set_fontweight('bold')
    ax1.set_title('PvP Record', fontsize=12, fontweight='bold', color='#e0e0e0', pad=10)

    # Raid Stats Pie
    ax2 = fig.add_subplot(gs[1])
    raid_labels = ['Raids Won', 'Raids Lost']
    raid_sizes = [raids_won, raids_lost]
    raid_colors = ['#533483', '#ff6b6b']
    wedges2, texts2, autotexts2 = ax2.pie(raid_sizes, labels=raid_labels, colors=raid_colors,
                                           autopct='%1.1f%%', startangle=90,
                                           textprops={'color': '#e0e0e0', 'fontsize': 10},
                                           wedgeprops={'edgecolor': '#1a1a2e', 'linewidth': 2})
    for autotext in autotexts2:
        autotext.set_fontweight('bold')
    ax2.set_title('Raid Record', fontsize=12, fontweight='bold', color='#e0e0e0', pad=10)

    # Damage Comparison Bar
    ax3 = fig.add_subplot(gs[2])
    dmg_categories = ['Damage\nDealt', 'Damage\nTaken']
    dmg_values = [total_damage_dealt, total_damage_taken]
    dmg_colors = ['#e94560', '#0f3460']
    bars = ax3.bar(dmg_categories, dmg_values, color=dmg_colors, edgecolor='#1a1a2e',
                   linewidth=2, width=0.5)
    ax3.set_ylabel('Damage Points', fontsize=10, fontweight='bold')
    ax3.set_title('Damage Stats', fontsize=12, fontweight='bold', color='#e0e0e0', pad=10)
    for bar, val in zip(bars, dmg_values):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:,}', ha='center', va='bottom', fontsize=10, fontweight='bold', color='#e0e0e0')

    fig.suptitle(f'Battle Analytics - {kingdom_name}', fontsize=15, fontweight='bold',
                 color='#e94560', y=1.02)
    plt.tight_layout()
    return save_chart(fig, f'battle_analytics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')


# ============================================================================
# 4. BUILDING PROGRESS CHART
# ============================================================================

def generate_building_progress(building_levels: Dict[str, int], max_level: int = 25,
                               kingdom_name: str = "Your Kingdom") -> str:
    """
    Generate horizontal bar chart showing building progress.
    building_levels: {'town_hall': 10, 'gold_mine': 8, ...}
    """
    ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(10, 5), facecolor=KINGDOM_COLORS['bg_dark'])
    ax.set_facecolor(KINGDOM_COLORS['bg_card'])

    buildings = list(building_levels.keys())
    levels = list(building_levels.values())
    colors = [BUILDING_COLORS.get(b, '#e94560') for b in buildings]
    building_labels = [b.replace('_', ' ').title() for b in buildings]

    # Progress bars
    bars = ax.barh(building_labels, levels, color=colors, edgecolor='#1a1a2e',
                   linewidth=2, height=0.6)

    # Background bars showing max
    ax.barh(building_labels, [max_level]*len(buildings), color='#0f3460', alpha=0.3,
            height=0.6, zorder=0)

    # Add level labels
    for bar, level in zip(bars, levels):
        width = bar.get_width()
        ax.text(width + 0.5, bar.get_y() + bar.get_height()/2.,
                f'Lv.{level}/{max_level}', ha='left', va='center',
                fontsize=10, fontweight='bold', color='#e0e0e0')

    ax.set_xlabel('Level', fontsize=11, fontweight='bold')
    ax.set_title(f'Building Progress - {kingdom_name}', fontsize=14, fontweight='bold',
                 color='#e0e0e0', pad=15)
    ax.set_xlim(0, max_level + 3)
    ax.invert_yaxis()
    ax.grid(True, axis='x', alpha=0.3, linestyle='--')

    plt.tight_layout()
    return save_chart(fig, f'building_progress_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')


# ============================================================================
# 5. LEADERBOARD VISUAL CHART
# ============================================================================

def generate_leaderboard_chart(players: List[Dict], chart_type: str = 'power',
                               title: str = "Kingdom Leaderboard") -> str:
    """
    Generate a visual leaderboard chart.
    players: [{'name': 'Player1', 'power': 5000, 'gold': 10000, 'wins': 50}, ...]
    chart_type: 'power' | 'gold' | 'wins'
    """
    ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(10, 6), facecolor=KINGDOM_COLORS['bg_dark'])
    ax.set_facecolor(KINGDOM_COLORS['bg_card'])

    names = [p['name'][:15] for p in players[:10]]  # Top 10
    values = [p.get(chart_type, 0) for p in players[:10]]

    # Gradient colors based on rank
    colors = plt.cm.RdYlGn(np.linspace(0.3, 0.9, len(names)))[::-1]

    bars = ax.barh(range(len(names)), values, color=colors, edgecolor='#1a1a2e',
                   linewidth=1.5, height=0.7)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels([f"#{i+1} {n}" for i, n in enumerate(names)], fontsize=9)
    ax.invert_yaxis()

    # Add value labels
    for bar, val in zip(bars, values):
        width = bar.get_width()
        ax.text(width + max(values)*0.01, bar.get_y() + bar.get_height()/2.,
                f'{val:,}', ha='left', va='center', fontsize=9, fontweight='bold', color='#e0e0e0')

    ax.set_xlabel(chart_type.title(), fontsize=11, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold', color='#e0e0e0', pad=15)
    ax.grid(True, axis='x', alpha=0.3, linestyle='--')

    plt.tight_layout()
    return save_chart(fig, f'leaderboard_{chart_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')


# ============================================================================
# 6. POWER RADAR CHART (Player Stats)
# ============================================================================

def generate_power_radar(attack: int, defense: int, economy: int, strategy: int,
                         speed: int, kingdom_name: str = "Your Kingdom") -> str:
    """
    Generate a radar/spider chart for player power breakdown.
    All values should be 0-100 scale.
    """
    ensure_matplotlib()
    categories = ['Attack', 'Defense', 'Economy', 'Strategy', 'Speed']
    values = [attack, defense, economy, strategy, speed]
    values += values[:1]  # Complete the circle

    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True),
                           facecolor=KINGDOM_COLORS['bg_dark'])
    ax.set_facecolor(KINGDOM_COLORS['bg_card'])

    ax.fill(angles, values, color='#e94560', alpha=0.25)
    ax.plot(angles, values, color='#e94560', linewidth=2.5, marker='o', markersize=8)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=12, fontweight='bold', color='#e0e0e0')
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'], color='#888888', fontsize=8)
    ax.grid(True, alpha=0.3, color='#0f3460')

    ax.set_title(f'Power Profile - {kingdom_name}', fontsize=14, fontweight='bold',
                 color='#e94560', pad=25)

    plt.tight_layout()
    return save_chart(fig, f'power_radar_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')


# ============================================================================
# 7. ECONOMY TREND CHART
# ============================================================================

def generate_economy_chart(production_history: List[int], consumption_history: List[int],
                           net_history: List[int], labels: Optional[List[str]] = None,
                           kingdom_name: str = "Your Kingdom") -> str:
    """
    Generate economy trend chart with production, consumption, and net.
    """
    ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(10, 5), facecolor=KINGDOM_COLORS['bg_dark'])
    ax.set_facecolor(KINGDOM_COLORS['bg_card'])

    x = range(len(production_history))
    if labels is None:
        labels = [f'Day {i+1}' for i in x]

    ax.plot(x, production_history, color='#4ecca3', linewidth=2, marker='o',
            markersize=5, label='Production')
    ax.plot(x, consumption_history, color='#e94560', linewidth=2, marker='s',
            markersize=5, label='Consumption')
    ax.plot(x, net_history, color='#ffd700', linewidth=2.5, marker='D',
            markersize=6, label='Net Income')

    ax.fill_between(x, net_history, alpha=0.2, color='#ffd700')

    ax.axhline(y=0, color='#ffffff', linewidth=1, linestyle='-', alpha=0.3)

    ax.set_xlabel('Time Period', fontsize=11, fontweight='bold')
    ax.set_ylabel('Gold', fontsize=11, fontweight='bold')
    ax.set_title(f'Economy Overview - {kingdom_name}', fontsize=14, fontweight='bold',
                 color='#e0e0e0', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
    ax.legend(loc='upper left', framealpha=0.9, facecolor='#16213e',
              edgecolor='#0f3460', fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--')

    plt.tight_layout()
    return save_chart(fig, f'economy_chart_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')


# ============================================================================
# 8. ACTIVITY HEATMAP
# ============================================================================

def generate_activity_heatmap(activity_data: List[List[int]],
                              kingdom_name: str = "Your Kingdom") -> str:
    """
    Generate activity heatmap (7 days x 24 hours).
    activity_data: 7x24 matrix of activity counts
    """
    ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(14, 4), facecolor=KINGDOM_COLORS['bg_dark'])
    ax.set_facecolor(KINGDOM_COLORS['bg_card'])

    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    hours = [f'{h:02d}:00' for h in range(0, 24, 3)]

    sns.heatmap(activity_data, cmap='YlOrRd', ax=ax, cbar_kws={'label': 'Activity Level'},
                linewidths=0.5, linecolor='#1a1a2e', alpha=0.9)

    ax.set_xticks(range(0, 24, 3))
    ax.set_xticklabels(hours, rotation=45, ha='right', fontsize=8)
    ax.set_yticklabels(days, rotation=0, fontsize=10, fontweight='bold')
    ax.set_xlabel('Hour of Day', fontsize=11, fontweight='bold')
    ax.set_ylabel('Day of Week', fontsize=11, fontweight='bold')
    ax.set_title(f'Activity Heatmap - {kingdom_name}', fontsize=14, fontweight='bold',
                 color='#e0e0e0', pad=15)

    # Style the colorbar
    cbar = ax.collections[0].colorbar
    cbar.ax.yaxis.label.set_color('#e0e0e0')
    cbar.ax.tick_params(colors='#e0e0e0')

    plt.tight_layout()
    return save_chart(fig, f'activity_heatmap_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')


# ============================================================================
# 9. COMPARISON CHART (Player vs Player)
# ============================================================================

def generate_comparison_chart(player1_name: str, player1_stats: Dict[str, int],
                              player2_name: str, player2_stats: Dict[str, int]) -> str:
    """
    Generate side-by-side comparison chart between two players.
    """
    ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(10, 6), facecolor=KINGDOM_COLORS['bg_dark'])
    ax.set_facecolor(KINGDOM_COLORS['bg_card'])

    categories = list(player1_stats.keys())
    p1_values = list(player1_stats.values())
    p2_values = list(player2_stats.values())

    x = np.arange(len(categories))
    width = 0.35

    bars1 = ax.bar(x - width/2, p1_values, width, label=player1_name,
                   color='#e94560', edgecolor='#1a1a2e', linewidth=1.5)
    bars2 = ax.bar(x + width/2, p2_values, width, label=player2_name,
                   color='#0f3460', edgecolor='#1a1a2e', linewidth=1.5)

    # Add value labels
    for bar in bars1:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height, f'{int(height):,}',
                ha='center', va='bottom', fontsize=8, color='#e94560', fontweight='bold')
    for bar in bars2:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height, f'{int(height):,}',
                ha='center', va='bottom', fontsize=8, color='#4ecdc4', fontweight='bold')

    ax.set_ylabel('Value', fontsize=11, fontweight='bold')
    ax.set_title(f'{player1_name} vs {player2_name}', fontsize=14, fontweight='bold',
                 color='#e0e0e0', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels([c.replace('_', ' ').title() for c in categories],
                       rotation=30, ha='right', fontsize=9)
    ax.legend(framealpha=0.9, facecolor='#16213e', edgecolor='#0f3460', fontsize=10)
    ax.grid(True, axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()
    return save_chart(fig, f'comparison_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')


# ============================================================================
# 10. ACHIEVEMENT PROGRESS CHART
# ============================================================================

def generate_achievement_progress(achievements: List[Dict], kingdom_name: str = "Your Kingdom") -> str:
    """
    Generate achievement progress bars.
    achievements: [{'name': 'First Blood', 'current': 5, 'target': 10, 'completed': False}, ...]
    """
    ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(10, max(4, len(achievements) * 0.6)),
                           facecolor=KINGDOM_COLORS['bg_dark'])
    ax.set_facecolor(KINGDOM_COLORS['bg_card'])

    names = [a['name'] for a in achievements]
    progresses = [(a['current'] / a['target']) * 100 for a in achievements]
    colors = ['#4ecca3' if a['completed'] else '#e94560' for a in achievements]

    y_pos = range(len(names))
    bars = ax.barh(y_pos, progresses, color=colors, edgecolor='#1a1a2e',
                   linewidth=1.5, height=0.6)

    # Background bars at 100%
    ax.barh(y_pos, [100]*len(names), color='#0f3460', alpha=0.3, height=0.6, zorder=0)

    # Add percentage labels
    for bar, pct, ach in zip(bars, progresses, achievements):
        width = bar.get_width()
        label = f"{ach['current']}/{ach['target']} ({pct:.0f}%)"
        ax.text(min(width + 2, 95), bar.get_y() + bar.get_height()/2.,
                label, ha='left', va='center', fontsize=9, fontweight='bold', color='#e0e0e0')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=9)
    ax.set_xlabel('Progress (%)', fontsize=11, fontweight='bold')
    ax.set_title(f'Achievement Progress - {kingdom_name}', fontsize=14, fontweight='bold',
                 color='#e0e0e0', pad=15)
    ax.set_xlim(0, 110)
    ax.invert_yaxis()
    ax.grid(True, axis='x', alpha=0.3, linestyle='--')

    plt.tight_layout()
    return save_chart(fig, f'achievements_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')


# ============================================================================
# 11. QUICK STATUS CARD (Mini Chart)
# ============================================================================

def generate_quick_status(gold: int, food: int, energy: int, army: int,
                          power: int, kingdom_name: str = "Your Kingdom") -> str:
    """
    Generate a compact status card image with mini charts.
    """
    ensure_matplotlib()
    fig = plt.figure(figsize=(8, 4), facecolor=KINGDOM_COLORS['bg_dark'])

    # Main metrics as big numbers with icons
    gs = GridSpec(2, 3, figure=fig, hspace=0.4, wspace=0.3)
    metrics = [
        ('GOLD', gold, '#ffd700', gs[0, 0]),
        ('FOOD', food, '#4ecca3', gs[0, 1]),
        ('ENERGY', energy, '#e94560', gs[0, 2]),
        ('ARMY', army, '#ff6b6b', gs[1, 0]),
        ('POWER', power, '#533483', gs[1, 1]),
    ]

    for label, value, color, subplot in metrics:
        ax = fig.add_subplot(subplot)
        ax.set_facecolor(KINGDOM_COLORS['bg_card'])
        ax.text(0.5, 0.6, f'{value:,}', ha='center', va='center',
                fontsize=22, fontweight='bold', color=color, transform=ax.transAxes)
        ax.text(0.5, 0.2, label, ha='center', va='center',
                fontsize=10, color='#888888', transform=ax.transAxes)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        # Rounded rectangle border
        rect = FancyBboxPatch((0.05, 0.05), 0.9, 0.9, boxstyle="round,pad=0.05",
                               facecolor='#16213e', edgecolor=color, linewidth=2,
                               transform=ax.transAxes)
        ax.add_patch(rect)

    # Mini pie in last slot
    ax_pie = fig.add_subplot(gs[1, 2])
    ax_pie.set_facecolor(KINGDOM_COLORS['bg_card'])
    ax_pie.pie([gold, food, army], colors=['#ffd700', '#4ecca3', '#ff6b6b'],
               startangle=90, wedgeprops={'edgecolor': '#1a1a2e', 'linewidth': 1})
    ax_pie.set_title('Resources', fontsize=10, color='#e0e0e0', pad=5)

    fig.suptitle(f'{kingdom_name}', fontsize=14, fontweight='bold',
                 color='#e94560', y=0.98)
    plt.tight_layout()
    return save_chart(fig, f'status_card_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')


# ============================================================================
# UTILITY: Cleanup old charts
# ============================================================================

def cleanup_old_charts(max_age_hours: int = 24):
    """Remove chart images older than specified hours."""
    if not os.path.exists(CHARTS_DIR):
        return
    cutoff = datetime.now() - timedelta(hours=max_age_hours)
    for filename in os.listdir(CHARTS_DIR):
        filepath = os.path.join(CHARTS_DIR, filename)
        if os.path.isfile(filepath):
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            if mtime < cutoff:
                try:
                    os.remove(filepath)
                except OSError:
                    pass
