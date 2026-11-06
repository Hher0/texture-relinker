# SPDX-License-Identifier: GPL-3.0-or-later
"""Matching logic. No bpy import, so it can be tested headless."""

import difflib
import os
import re
from collections import Counter, namedtuple

IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".tga", ".tif", ".tiff",
    ".exr", ".hdr", ".bmp", ".webp",
}

# Score tiers. Exact filename beats same stem, which beats any fuzzy match.
SCORE_EXACT = 1.0
SCORE_SAME_STEM = 0.95
SCORE_FUZZY_MAX = 0.94
# Names that differ in a number (_08 vs _09, 2k vs 4k) are usually different files.
SCORE_NUMBER_MISMATCH_FACTOR = 0.6

NO_IMAGES_IN_FOLDER = "No images directly in this folder. Pick the folder that contains the textures"

_SEPARATORS = re.compile(r"[\s_\-.]+")


def filename_of(path):
    """Last part of a path. Understands both / and \\ so a Windows path
    stored in a .blend still works on macOS and Linux."""
    return re.split(r"[\\/]", path)[-1]


def folder_of(path):
    """Everything before the file name, keeping the trailing slash."""
    return path[: len(path) - len(filename_of(path))]


def normalize_stem(path):
    """'Wood_Diffuse.png' -> 'wooddiffuse'."""
    stem = os.path.splitext(filename_of(path))[0]
    return _SEPARATORS.sub("", stem).lower()


def numbers_in(path):
    """Numbers in a file name, in order: 'studio_08_4k.exr' -> (8, 4)."""
    stem = os.path.splitext(filename_of(path))[0]
    return tuple(int(n) for n in re.findall(r"\d+", stem))


def score(missing_path, candidate_path):
    """Return a match score in [0, 1]. 1.0 means the same filename."""
    if filename_of(missing_path).lower() == filename_of(candidate_path).lower():
        return SCORE_EXACT
    a, b = normalize_stem(missing_path), normalize_stem(candidate_path)
    if not a or not b:
        return 0.0
    if a == b:
        return SCORE_SAME_STEM  # different extension or different separators
    fuzzy = difflib.SequenceMatcher(None, a, b).ratio()
    if numbers_in(missing_path) != numbers_in(candidate_path):
        fuzzy *= SCORE_NUMBER_MISMATCH_FACTOR
    return min(fuzzy, SCORE_FUZZY_MAX)


def passes_threshold(match_score, threshold):
    """True when a score reaches the threshold.

    The slider stores single-precision floats (0.8 comes back as 0.80000001),
    so allow a tiny tolerance.
    """
    return match_score + 1e-6 >= threshold


def list_image_files(folder, recursive=False):
    """Image files in folder (optionally recursive)."""
    found = []
    if not os.path.isdir(folder):
        return found
    if recursive:
        for root, _dirs, files in os.walk(folder):
            found.extend(os.path.join(root, f) for f in files)
    else:
        found = [os.path.join(folder, f) for f in os.listdir(folder)]
    return [p for p in found
            if os.path.isfile(p) and os.path.splitext(p)[1].lower() in IMAGE_EXTENSIONS]


# A candidate file with the parts score() needs, worked out once per search
# instead of once per missing image.
Candidate = namedtuple("Candidate", "path name stem numbers letters")


def prepare_candidates(paths):
    """Candidate files in sorted order, ready for best_match_in()."""
    result = []
    for path in sorted(paths):
        stem = normalize_stem(path)
        result.append(Candidate(path, filename_of(path).lower(), stem, numbers_in(path), Counter(stem)))
    return result


def best_match(missing_path, candidates, threshold=0.8):
    """Return (candidate, score) for the best candidate at or above threshold.

    Returns (None, 0.0) when nothing qualifies. Ties go to the first
    candidate in sorted order so results are the same on every run.
    """
    return best_match_in(missing_path, prepare_candidates(candidates), threshold)


def best_match_in(missing_path, candidates, threshold=0.8):
    """best_match() for candidates from prepare_candidates(). Gives the same
    result as calling score() on every candidate, but skips the slow fuzzy
    comparison when a cheap upper bound shows a candidate cannot win."""
    name = filename_of(missing_path).lower()
    stem = normalize_stem(missing_path)
    numbers = numbers_in(missing_path)
    letters = Counter(stem)
    matcher = difflib.SequenceMatcher(None, stem, "")
    best, best_score = None, 0.0
    for candidate in candidates:
        if candidate.name == name:
            s = SCORE_EXACT
        elif not stem or not candidate.stem:
            s = 0.0
        elif candidate.stem == stem:
            s = SCORE_SAME_STEM
        else:
            factor = 1.0 if candidate.numbers == numbers else SCORE_NUMBER_MISMATCH_FACTOR
            # difflib's ratio is at most 2 * shared letters / total length.
            shared = sum((letters & candidate.letters).values())
            upper_bound = min(2.0 * shared / (len(stem) + len(candidate.stem)) * factor, SCORE_FUZZY_MAX)
            if upper_bound <= best_score:
                continue
            matcher.set_seq2(candidate.stem)
            s = min(matcher.ratio() * factor, SCORE_FUZZY_MAX)
        if s > best_score:
            best, best_score = candidate.path, s
            if best_score == SCORE_EXACT:
                break  # nothing scores higher, and ties keep the first one
    if best is not None and passes_threshold(best_score, threshold):
        return best, best_score
    return None, 0.0


def match_status(searched, candidate, match_score, threshold):
    """Status key for one missing image: 'missing', 'no_match', 'below' or 'match'."""
    if not searched:
        return "missing"
    if not candidate:
        return "no_match"
    if passes_threshold(match_score, threshold):
        return "match"
    return "below"


def match_summary(status, match_score):
    """Status line for the panel. The candidate file name goes on its own line below it,
    so neither gets cut off in a narrow sidebar."""
    if status == "no_match":
        return "No file found in the search folder"
    if status == "below":
        return f"No good match (best {match_score:.0%})"
    return f"Match {match_score:.0%}"


def list_image_files_in(folders, recursive=False):
    """Image files from several folders, without duplicates, in a stable order."""
    seen, result = set(), []
    for folder in folders:
        for path in sorted(list_image_files(folder, recursive)):
            if path not in seen:
                seen.add(path)
                result.append(path)
    return result


def udim_tile_path(pattern, number):
    """Replace the <UDIM> or <UVTILE> token in a path with a tile number."""
    u, v = (number - 1001) % 10 + 1, (number - 1001) // 10 + 1
    return pattern.replace("<UDIM>", str(number)).replace("<UVTILE>", f"u{u}_v{v}")


def format_relink_report(entries):
    """Plain-text report. entries: (image name, old path, new path, score) tuples."""
    lines = ["Texture Relinker report", "", f"Relinked {len(entries)} image(s)", ""]
    for name, old_path, new_path, match_score in entries:
        lines += [name, f"  was: {old_path}", f"  now: {new_path} (match {match_score:.0%})", ""]
    return "\n".join(lines)
