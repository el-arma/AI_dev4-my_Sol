import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from pathlib import Path

def _extract_grid(image_path: str, output_path: str, output_size: int = 900) -> np.ndarray:
    """
    Detect and crop the largest rectangular grid from an image.

    Args:
        image_path:  Path to the input image.
        output_path: Where to save the cropped result.
        output_size: Side length (px) of the square output image.

    Returns:
        The cropped grid as a numpy array (BGR).
    """

    # --- 1. Load image ---
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")

    # --- 2. Convert to grayscale ---
    # Colour info isn't needed for finding the grid border.
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # --- 3. Binary threshold (dark lines → white, background → black) ---
    # THRESH_BINARY_INV flips so the grid lines become bright contours.
    # Threshold value 100 works for most dark-on-light grids; raise it
    # (e.g. 150) if the background is very light, lower it if lines are faint.
    _, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)

    # --- 4. Find contours ---
    # RETR_EXTERNAL: only outermost contours — ignores inner grid lines.
    # CHAIN_APPROX_SIMPLE: compresses straight segments to save memory.
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        raise RuntimeError("No contours found — check threshold value or image quality.")

    # --- 5. Pick the largest contour (assumed to be the grid border) ---
    largest = max(contours, key=cv2.contourArea)

    # --- 6. Approximate the contour to a polygon ---
    # arcLength gives the perimeter; epsilon controls how aggressively corners
    # are simplified. 0.08 × perimeter works well for hand-drawn / imperfect borders.
    # Decrease epsilon (e.g. 0.02) for crisp printed grids with sharp corners.
    perimeter = cv2.arcLength(largest, True)
    approx = cv2.approxPolyDP(largest, 0.08 * perimeter, True)

    if len(approx) != 4:
        # Fallback: just use the axis-aligned bounding box
        print(f"Warning: expected 4 corners, got {len(approx)}. Using bounding box.")
        x, y, w, h = cv2.boundingRect(largest)
        cropped = img[y : y + h, x : x + w]
        cropped = cv2.resize(cropped, (output_size, output_size))
        cv2.imwrite(output_path, cropped)
        return cropped

    # --- 7. Order the 4 corners consistently: TL, TR, BR, BL ---
    pts = approx.reshape(4, 2).astype(np.float32)

    # Top-left has smallest (x+y), bottom-right has largest (x+y)
    s = pts.sum(axis=1)
    # Top-right has smallest (y-x), bottom-left has largest (y-x)
    d = np.diff(pts, axis=1).ravel()

    rect = np.array([
        pts[np.argmin(s)],   # top-left
        pts[np.argmin(d)],   # top-right
        pts[np.argmax(s)],   # bottom-right
        pts[np.argmax(d)],   # bottom-left
    ], dtype=np.float32)

    # --- 8. Perspective warp → flat square ---
    # getPerspectiveTransform maps the 4 detected corners to a perfect square.
    # This corrects any tilt or camera angle in the original photo.
    dst = np.array([
        [0,            0           ],
        [output_size,  0           ],
        [output_size,  output_size ],
        [0,            output_size ],
    ], dtype=np.float32)

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(img, M, (output_size, output_size))

    # --- 9. Save and return ---
    cv2.imwrite(output_path, warped)

    print(f"Saved: {output_path}  ({output_size}x{output_size} px)")

    return warped

def _process_grid_cells(
    input_path,
    output_dir: Path,
    grid_size=3,
    pad_ratio=0.12,
    target_size=(30, 30)
):
    """
    Process grid image into normalized 30x30 black-white cells.

    Steps:
    - split into NxN grid
    - crop padding (remove borders)
    - remove red -> white
    - convert to grayscale
    - boost contrast
    - edge sharpen
    - threshold to pure B/W
    - resize
    - save as rowxcol
    """

    img = Image.open(input_path).convert("RGB")
    w, h = img.size

    cell_w = w // grid_size
    cell_h = h // grid_size

    pad_w = int(cell_w * pad_ratio)
    pad_h = int(cell_h * pad_ratio)

    def replace_red_with_white(image):
        pixels = image.load()
        width, height = image.size

        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]

                # detect red-ish pixels
                if r > 140 and g < 120 and b < 120:
                    pixels[x, y] = (255, 255, 255)

        return image

    def to_binary(image):
        # grayscale
        image = image.convert("L")

        # boost contrast hard
        image = ImageEnhance.Contrast(image).enhance(3.0)

        # sharpen edges
        image = image.filter(ImageFilter.SHARPEN)

        # threshold → pure black/white
        image = image.point(lambda p: 255 if p > 128 else 0)

        return image

    for row in range(grid_size):
        for col in range(grid_size):

            # crop with padding removal
            x1 = col * cell_w + pad_w
            y1 = row * cell_h + pad_h
            x2 = (col + 1) * cell_w - pad_w
            y2 = (row + 1) * cell_h - pad_h

            cell = img.crop((x1, y1, x2, y2))

            # clean colors
            cell = replace_red_with_white(cell)

            # normalize to B/W + sharpen
            cell = to_binary(cell)

            # resize to 30x30
            cell = cell.resize(target_size, Image.NEAREST)

            # naming: 1x1, 1x2, ...
            # A1, 
            # filename = f"{chr(64 + row // 3 + 1)}{col + 1}.png"
            filename = f"{chr(65 + col)}{row + 1}.png"
            final_path = output_dir / filename
            cell.save(final_path)


    print(f"Grid cells for {input_path} rdy.")

def img_processing(file_name: str, output_folder_path: Path) -> None:

    _extract_grid(
        image_path=f"my_Solutions/Data_Bank/{file_name}",
        output_path=f"my_Solutions/S02E02/IMG/grid_tbl_{file_name}",
        output_size=900,
    )

    _process_grid_cells(
        input_path=f"my_Solutions/S02E02/IMG/grid_tbl_{file_name}",
        output_dir=output_folder_path,
        grid_size=3, # 3x3
        pad_ratio=0.15, # 
        target_size=(30, 30) # in px
    )

    print(f"Done for {file_name}")

    return None

def classify_shape(img_path: str) -> str:
    px = np.array(Image.open(img_path).convert("L")) < 128

    h, w = px.shape
    r, c = h // 3, w // 3

    N = px[  :r,   c:2*c].any()
    S = px[2*r:,   c:2*c].any()
    E = px[r:2*r, 2*c:  ].any()
    W = px[r:2*r,   :c  ].any()

    return "".join(d for d, flag in zip("NESW", (N, E, S, W)) if flag)