# -------------------
# CONFIG
# -------------------
SCALE = 1# <-- Global scale multiplier; increase/decrease to resize the entire UI
BASE_WIDTH = 1024  # Base resolution width before scaling
BASE_HEIGHT = 600  # Base resolution height before scaling

# Apply scaling to get the actual screen resolution
SCREEN_WIDTH = int(BASE_WIDTH*SCALE)
SCREEN_HEIGHT = int(BASE_HEIGHT*SCALE)

# Background ["black_fade", "carbon_fiber", "metal", "pattern1", "pattern2", "pattern4", "pattern5",
# "pattern7", "pattern9","pattern10", "pattern11", "pattern12", "pattern13", "pattern15", "pattern16"
background_image =  "pattern12"