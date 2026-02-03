# Kitchen Companion

A Python/FastAPI web application for managing recipes, generating shopping lists, and timing your cooking.

## Features

- **Recipe Management**: Store recipes in markdown format with automatic parsing
- **Auto-Refresh**: Recipes automatically reload when files change (no manual refresh needed)
- **Shopping List Generation**: Combine ingredients from multiple recipes with automatic unit conversion
- **Smart Ingredient Combining**: Automatically combines duplicate ingredients (e.g., 500g + 500g = 1kg)
- **Pantry Filtering**: Filter out pantry staples from your shopping list
- **Recipe Scaling**: Scale recipes to different serving sizes
- **Kitchen Timers**: Interactive timers with auto-detection from recipe text
- **Dark Theme UI**: Mobile-responsive interface optimized for cooking
- **Recipe Sharing**: Export recipes to email-friendly HTML

## Kitchen Timer Features

- Auto-detects time references: "cook for 15 minutes" automatically becomes a timer button
- Explicit timer syntax: `[15m]` or `[timer:15m:Label]`
- Multiple simultaneous timers
- Play, pause, stop, and reset controls
- Browser notifications when timers complete
- Sound alerts
- Custom timer creation
- Floating panel for managing active timers

## Tech Stack

- **Backend**: Python 3.11+, FastAPI
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Database**: SQLite
- **Containerization**: Docker, Docker Compose
- **Libraries**: 
  - `pint` for unit conversion
  - `markdown` for recipe parsing
  - `uvicorn` for ASGI server

## Quick Start

### Using Docker (Recommended)

```bash
docker-compose up --build
```

Access the app at `http://localhost:8080`

### Manual Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
uvicorn src.main:app --reload --port 8080
```

## Project Structure

```
kitchen-companion/
├── src/
│   ├── api/          # FastAPI routes
│   ├── models/       # Database models
│   ├── services/     # Business logic
│   └── static/       # Frontend files
├── recipes/          # Recipe markdown files
├── data/             # SQLite database (auto-created)
├── pantry.txt        # Pantry items configuration
├── categories.txt    # Ingredient categories (optional)
└── docker-compose.yml
```

## Recipe Format

Recipes are stored as markdown files in the `recipes/` folder:

```markdown
# Recipe Name

Servings: 4

## Ingredients

- 500g chicken breast
- 2 tbsp olive oil
- 1 onion, diced
- salt to taste

## Instructions

1. Prepare all ingredients
1. Cook for 15 minutes [15m]
1. Let rest for 5 minutes
1. Serve and enjoy
```

### Timer Syntax

- **Auto-detection**: "cook for 15 minutes" → creates timer automatically
- **Explicit short**: `[15m]` → 15 minute timer
- **Explicit with label**: `[timer:15m:Chicken]` → labeled timer
- **Formats**: `15m`, `1h30m`, `45s`, `1h`

## Configuration

### Pantry Items (`pantry.txt`)

List items you always have on hand (one per line):

```
salt
pepper
olive oil
garlic
onion
```

### Store Zones (`categories.txt`)

Organize shopping lists by your store's actual layout using numbered zones:

```
# Map items to zones in the order you encounter them in your store
zone1: lettuce, spinach, herbs
zone2: bell pepper, onion, garlic, tomato
zone3: chicken, beef, pork
zone4: milk, cheese, butter
zone5: bread, rolls
# ... continue matching your store layout
```

**How it works:**
- Zone numbers can be anything: `zone1`, `zone2`, or `A`, `B`, `Front`, `Back`, etc.
- Items are sorted by zone order (as listed in file), then alphabetically within each zone
- Case-insensitive partial matching (e.g., "olive oil" matches "oil")
- First matching zone wins
- Unmatched items appear last in an "unzoned" group

**Why zones instead of categories?**
- Stores don't follow logical category layouts
- Multiple produce sections? Map them to `zone1` and `zone8`
- Dairy split across the store? Use `zone4` and `zone12`
- Flexible to any store layout - number zones in the order you shop

## API Endpoints

- `GET /api/recipes` - List all recipes
- `GET /api/recipes/{id}` - Get recipe details with timers
- `POST /api/shopping-list` - Generate combined shopping list
- `POST /api/recipes/upload` - Upload new recipe
- `POST /api/refresh` - Rescan recipes folder

## Development

The application hot-reloads when files change. Recipe files are **automatically detected and refreshed** in real-time - no manual refresh needed!

### Auto-Refresh Feature

- Uses file system watching (watchdog) to detect recipe changes
- Server-Sent Events (SSE) push updates to connected clients
- Recipes automatically reload when you:
  - Add new recipe files
  - Edit existing recipes
  - Delete recipes
- Subtle notification appears when recipes update

### Adding New Recipes

1. Create a `.md` file in the `recipes/` folder
2. Follow the recipe format above
3. Save the file - it will automatically appear in the UI!

No restart or manual refresh required.

## Zone Management CLI

Use the `zones.py` CLI tool to maintain your zone configuration:

### Analyze Unzoned Items

```bash
python zones.py
```

**Output:**
- Zone distribution (how many ingredients in each zone)
- List of unzoned items sorted by frequency
- Coverage percentage
- Suggestions for which items to add to zones

**Example output:**
```
📊 Zone Distribution:
------------------------------------------------------------
  zone1                  12 ingredients
  zone2                  45 ingredients
  zone3                  23 ingredients
  ...
  Unzoned                 8 (5.2%)

⚠️  Unzoned Items (add these to categories.txt):
------------------------------------------------------------
  • paprika                                  (in 5 recipes)
  • cumin                                    (in 3 recipes)
  • bay leaves                               (in 2 recipes)
```

### Show Current Zones

```bash
python zones.py --show-zones
```

Shows all configured zones and their pattern lists.

### Workflow

1. Add new recipes
2. Run `python zones.py` to see unzoned ingredients
3. Edit `categories.txt` to add missing items to appropriate zones
4. Repeat as needed

## License

MIT
