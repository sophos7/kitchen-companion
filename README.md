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

### Categories (`categories.txt`)

Organize shopping lists by store sections:

```
produce: bell pepper, onion, garlic, tomato
dairy: milk, cheese, butter, yogurt
meat: chicken, beef, pork
```

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

## License

MIT
