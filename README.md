# Kingdom Conquest - Telegram Bot

A fully-featured **multiplayer strategy kingdom builder** Telegram bot with PvP combat, alliances, quests, heroes, and more!

## Features

### Core Gameplay
- **Kingdom Creation** - Custom name, flag emoji, and trait selection
- **Building System** - 5 building types (Town Hall, Gold Mine, Farm, Barracks, Wall) with 25 levels each
- **Army Management** - 3 unit types (Infantry, Archers, Cavalry) with training and food consumption
- **PvP Combat** - Full battle engine with round-by-round simulation, RNG, hero bonuses, and wall defense
- **Resource Economy** - Gold and Food production with collection mechanics

### Social & Competitive
- **Alliance System** - Create/join alliances, team wars, shared treasury
- **Leaderboard** - Player and alliance rankings by power
- **Bounty System** - Place bounties on other players
- **Revenge System** - 1-hour revenge window after being attacked

### Exploration & Intel
- **10x10 World Map** - Visual grid with kingdom positions
- **Spy System** - Gather intel on enemies (basic/detailed/full reports)
- **Raid System** - Quick loot attacks with reduced risk

### Heroes & Progression
- **5 Unique Heroes** - Sir Aldric, Lyra, Kael, Morgana, Shadow
- **Skill Tree** - Attack, Defense, and Economy branches
- **Achievement System** - 8 achievements with titles
- **Quest System** - 5 daily quests + milestone quests

### Mini-Games
- **Dice Game** - Bet gold, roll for multipliers (4h cooldown)
- **Lucky Spin** - Wheel with gems, gold, food, energy, shields (8h cooldown)
- **Kingdom Quiz** - Trivia questions for rewards (6h cooldown)

### Premium & Events
- **Black Market** - Gems-based shop with instant builds, energy refills, shields
- **Decision Events** - Random choose-your-path encounters
- **World Events** - Global events affecting all players
- **Survival Mode** - Wave-based PvE with escalating rewards

### Admin Features
- **Warning System** - 3-tier warning escalation
- **Ban/Unban** - Temporary and permanent bans
- **Resource Giving** - Admin can give gold/gems/food
- **Broadcast** - Message all users
- **Statistics** - Bot analytics dashboard

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Bot Framework | python-telegram-bot v20+ (async) |
| Database | SQLite (thread-safe, can swap to PostgreSQL) |
| Language | Python 3.11+ |
| Deployment | Polling or Webhook |

## Installation

1. **Clone/download** the project:
```bash
cd kingdom_conquest
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your bot token from @BotFather
```

4. **Run the bot**:
```bash
cd bot
python main.py
```

## Bot Commands

### User Commands
| Command | Description |
|---------|-------------|
| `/start` | Begin game / Show dashboard |
| `/dashboard` | Open main HUD |
| `/attack` | Quick attack menu |
| `/build` | Building management |
| `/army` | Army overview |
| `/map` | Show world map |
| `/alliance` | Alliance hub |
| `/quests` | Quest board |
| `/hero` | Hero management |
| `/spy` | Send spy mission |
| `/raid` | Quick raid |
| `/market` | Black market |
| `/leaderboard` | Rankings |
| `/gems` | Premium shop |
| `/settings` | Preferences |
| `/help` | Game guide |
| `/scout x y` | Scout map tile |
| `/bounty @user amount` | Place bounty |
| `/bounties` | List bounties |

### Admin Commands
| Command | Description |
|---------|-------------|
| `/admin warn @user reason` | Warn user |
| `/admin ban @user days reason` | Ban user |
| `/admin unban @user` | Unban user |
| `/admin give @user resource amount` | Give resources |
| `/admin broadcast message` | Global message |
| `/admin stats` | Bot statistics |
| `/admin maintenance on/off` | Maintenance mode |

## Game Balance

### Starting Resources
- Gold: 1,000
- Food: 500
- Energy: 10/10
- Infantry: 50

### Energy System
- Max: 10
- Regen: 1 per 30 minutes
- Attack cost: 1

### New Player Protection
- 24-hour newbie shield
- Shield breaks on attack

### Combat
- ±15% RNG factor
- Wall damage reduction: 3% per level (max 75%)
- Proximity bonus: +10% for nearby targets
- Loot: 20% of defender's gold

## Project Structure

```
kingdom_conquest/
├── bot/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── config.py               # All game constants
│   ├── handlers/               # Telegram handlers
│   │   ├── start.py            # Onboarding & tutorial
│   │   ├── dashboard.py        # Main HUD
│   │   ├── build.py            # Building system
│   │   ├── army.py             # Army management
│   │   ├── attack.py           # PvP & combat
│   │   ├── map_system.py       # 10x10 grid
│   │   ├── alliance.py         # Alliances
│   │   ├── quests.py           # Quests
│   │   ├── heroes.py           # Heroes & skills
│   │   ├── spy.py              # Spy missions
│   │   ├── black_market.py     # Premium shop
│   │   ├── games.py            # Mini-games
│   │   ├── leaderboard.py      # Rankings
│   │   ├── settings.py         # Preferences
│   │   ├── admin.py            # Moderation
│   │   ├── bounty.py           # Bounty system
│   │   ├── survival.py         # PvE survival
│   │   └── events.py           # World events
│   ├── services/               # Game logic
│   │   ├── combat_engine.py    # Battle simulation
│   │   ├── economy.py          # Resource formulas
│   │   ├── energy_service.py   # Energy regen
│   │   ├── matchmaking.py      # Opponent finding
│   │   ├── notification.py     # Push notifications
│   │   └── ai_bot.py           # NPC & world events
│   ├── models/
│   │   └── database.py         # SQLite ORM
│   └── utils/
│       ├── keyboards.py        # All inline keyboards
│       ├── formatters.py       # Display formatting
│       └── constants.py        # Game data
├── requirements.txt
├── .env.example
└── README.md
```

## License

MIT License - Free to use and modify!

## Credits

Built with python-telegram-bot framework. Game design by Kingdom Conquest team.
