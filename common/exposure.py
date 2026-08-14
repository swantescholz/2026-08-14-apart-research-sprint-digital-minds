"""The shared exposure block used by evals 2, 3, and 4.

A "snapshot" = one shuffle permutation of the 10 image keys + the single user
turn that shows all 10, in that order, each explicitly labelled immediately
before its image. ID = position in the shuffle, 1-10.

This is built as ONE user turn (a list of interleaved text/image content
blocks), never ten separate turns -- that avoids role-alternation issues and
any risk of OpenRouter silently merging turns.
"""

from __future__ import annotations

from common.images_util import image_content_block, text_block
from common.seeding import shuffled_permutation


def make_snapshot(root_seed: int, ordered_keys: list[str], *tags: str | int) -> list[str]:
    """Return image keys shuffled into presentation order for this snapshot.
    permutation[i] is the key shown as "Image i+1"."""
    return shuffled_permutation(root_seed, ordered_keys, "snapshot", *tags)


def system_prompt(n_choices: int, eval_name: str) -> str:
    choice_word = "choice" if n_choices == 1 else "choices"
    return (
        f"You will be shown 10 images, labelled Image 1 through Image 10. "
        f"All 10 were deliberately chosen as stimuli for this study -- some "
        f"of them are minimal or abstract by design (e.g. solid colors or "
        f"random noise), not errors or placeholders. Look at each one.\n\n"
        f"After you have seen all 10, you will get exactly {n_choices} {choice_word} "
        f"to pick an image to view again, one at a time. This is the full extent "
        f"of the interaction -- there is no hidden continuation and no scoring "
        f"beyond what you see. [{eval_name}]"
    )


def exposure_content_blocks(snapshot_keys: list[str], stimuli: dict) -> list[dict]:
    """snapshot_keys[i] is the internal key shown as Image i+1."""
    blocks: list[dict] = []
    for i, key in enumerate(snapshot_keys, start=1):
        blocks.append(text_block(f"Image {i}:"))
        blocks.append(image_content_block(stimuli[key]["path"]))
    return blocks
