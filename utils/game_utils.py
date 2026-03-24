import json
import time
import logging
from typing import Dict, List, Optional, Tuple

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 2-D ASCII matrix helpers
# ---------------------------------------------------------------------------

# Default symbol table – maps VGDL sprite-type keywords to single characters.
# The game engine exposes sprite types via getFullState().  We walk each
# sprite's ``stypes`` list (most-specific first) and pick the first match.
# Add entries here as new games require them.
SPRITE_SYMBOL_MAP = {
    # avatars
    "avatar": "A",
    "flakavatar": "A",
    "movingavatar": "A",
    "orientedavatar": "A",
    "shieldedavatar": "A",
    "birdavatar": "A",
    "landeravatar": "A",
    "noisyavatar": "A",
    # common sprite roles
    "wall": "W",
    "door": "D",
    "key": "K",
    "goal": "G",
    "portal": "P",
    "portalentry": "P",
    "portalexit": "p",
    "sword": "s",
    "diamond": "$",
    "boulder": "B",
    "carcass": "c",
    "dirt": ",",
    # enemy / hazard keywords
    "enemy": "E",
    "ghost": "E",
    "zombie": "E",
    "monster": "E",
    "alien": "E",
    "chaser": "E",
    "randomenemy": "E",
    "randomnpc": "N",
    "bomber": "X",
    # projectiles
    "missile": "*",
    "bullet": "*",
    "fireball": "*",
    "sam": "*",
    "bomb": "o",
    # items / collectables
    "resource": "R",
    "fruit": "F",
    "pellet": ".",
    "butterfly": "b",
    "cocoon": "C",
    # terrain
    "water": "~",
    "lava": "!",
    "base": "#",
    "floor": "_",
    "hole": "O",
    "trap": "T",
    "log": "=",
    # immovable generic
    "immovable": "#",
    # catch-all for anything that moves but isn't matched above
    "sprite": "?",
}


def get_game_dimensions(driver) -> Tuple[int, int]:
    """Return (width, height) of the game grid in cells."""
    try:
        dims = driver.execute_script(
            "return [window.game.width, window.game.height];"
        )
        return int(dims[0]), int(dims[1])
    except Exception as exc:
        logger.error(f"Error getting game dimensions: {exc}")
        return 0, 0


def _symbol_for_sprite(sprite_type_key: str, stypes: Optional[List[str]] = None) -> str:
    """Pick the best single-character symbol for a sprite."""
    # First try the specific stypes list (most-specific first)
    if stypes:
        for stype in stypes:
            lower = stype.lower()
            if lower in SPRITE_SYMBOL_MAP:
                return SPRITE_SYMBOL_MAP[lower]
    # Fall back to the group key itself
    lower_key = sprite_type_key.lower()
    if lower_key in SPRITE_SYMBOL_MAP:
        return SPRITE_SYMBOL_MAP[lower_key]
    # Unknown sprite – use first letter uppercased
    return sprite_type_key[0].upper() if sprite_type_key else "?"


def get_game_state_matrix(driver) -> str:
    """
    Query the JS game engine for full state and return a human-readable
    ASCII grid plus a legend mapping symbols to sprite types.

    Returns a string like:
        Legend: A=avatar W=wall E=enemy G=goal .=empty
        WWWWWWWW
        W..A...W
        W..E.G.W
        WWWWWWWW
    """
    try:
        state = driver.execute_script("return window.game.getFullState();")
        width, height = get_game_dimensions(driver)
        if width == 0 or height == 0:
            return "(unable to read game grid dimensions)"

        block_size = driver.execute_script("return window.game.block_size;") or 1

        # Build empty grid
        grid = [["." for _ in range(width)] for _ in range(height)]

        # Track which symbols we actually use for the legend
        used_symbols: Dict[str, str] = {}  # symbol -> type name

        objects = state.get("objects", {})
        for sprite_type, sprites in objects.items():
            if not sprites:
                continue
            for _sid, sprite_data in sprites.items():
                # Positions may be in pixel coords – convert to grid cells
                raw_x = sprite_data.get("x", sprite_data.get("rect", {}).get("x", -1))
                raw_y = sprite_data.get("y", sprite_data.get("rect", {}).get("y", -1))
                if raw_x < 0 or raw_y < 0:
                    continue
                col = int(raw_x) // block_size
                row = int(raw_y) // block_size
                if 0 <= row < height and 0 <= col < width:
                    stypes = sprite_data.get("stypes", [])
                    sym = _symbol_for_sprite(sprite_type, stypes)
                    # Avatar takes priority over anything else in the cell
                    if sym == "A" or grid[row][col] == ".":
                        grid[row][col] = sym
                    used_symbols[sym] = sprite_type

        # Always include empty cell in legend
        used_symbols["."] = "empty"

        legend_parts = [f"{sym}={name}" for sym, name in sorted(used_symbols.items())]
        legend_line = "Legend: " + " ".join(legend_parts)
        grid_lines = ["".join(row) for row in grid]
        return legend_line + "\n" + "\n".join(grid_lines)
    except Exception as exc:
        logger.error(f"Error building game state matrix: {exc}")
        return "(error reading game state)"

def execute_action(driver, action_code):
    """Execute a single action in the game."""
    if action_code is not None:
        # VGDL games use keydown to set state, usually
        # game.step(action) is defined in the game code for the LLM interface
        try:
            driver.execute_script(f"game.step({action_code})")
        except Exception as e:
            logger.error(f"Error executing action {action_code}: {e}")
    else:
        # NOOP action - just advance a tick without input
        try:
            driver.execute_script("game.step(null)")
        except Exception as e:
            logger.error(f"Error executing NOOP action: {e}")

def get_game_screenshot(driver) -> bytes:
    """Get PNG bytes of the game canvas."""
    try:
        canvas = driver.find_element(By.ID, "gjs-canvas")
        return canvas.screenshot_as_png
    except Exception as e:
        logger.error(f"Error getting screenshot: {e}")
        return b""

def is_game_ended(driver) -> bool:
    """Check if the game has ended."""
    try:
        # Check the 'ended' variable in the game instance
        return driver.execute_script("return window.game.ended")
    except Exception as e:
        # Fallback: check if retry button is visible
        try:
            retry_btn = driver.find_element(By.ID, "retry")
            return retry_btn.is_displayed()
        except:
            return False


def is_game_won(driver) -> bool:
    """Return True if the current game instance reports a win state."""
    try:
        return bool(driver.execute_script("return !!(window.game && window.game.win);"))
    except Exception as exc:
        logger.error(f"Error checking win state: {exc}")
        return False

def click_start_llm(driver, max_retries=3):
    """Click the Start LLM button, retrying with page reload if not found."""
    for attempt in range(max_retries):
        try:
            btn = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, "start-llm"))
            )
            btn.click()
            logger.info("Clicked Start LLM button")
            time.sleep(1)
            return
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Start LLM button not found (attempt {attempt + 1}/{max_retries}), reloading page...")
                driver.refresh()
                time.sleep(3)
            else:
                logger.error(f"Error clicking Start LLM after {max_retries} attempts: {e}")
                raise

def click_retry(driver):
    """Click the Retry button."""
    try:
        btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "retry"))
        )
        btn.click()
        logger.info("Clicked Retry button")
        time.sleep(1) # Wait for reset
        return True
    except Exception as e:
        logger.error(f"Error clicking Retry: {e}")
        return False


def click_next_instance(driver):
    """Click the Next Instance / Next Level button."""
    try:
        btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "next"))
        )
        btn.click()
        logger.info("Clicked Next Instance button")
        time.sleep(1)
        return True
    except Exception as e:
        logger.error(f"Error clicking Next Instance: {e}")
        return False

