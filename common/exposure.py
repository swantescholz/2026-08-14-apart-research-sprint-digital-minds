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
from common.seeding import rng_for, shuffled_permutation


def make_snapshot(root_seed: int, ordered_keys: list[str], *tags: str | int) -> list[str]:
    """Return image keys shuffled into presentation order for this snapshot.
    permutation[i] is the key shown as "Image i+1".

    Independent uniform shuffle per snapshot. Kept for reference and for the
    unbalanced case; `balanced_snapshot` is what the evals actually use --
    see its docstring for why.
    """
    return shuffled_permutation(root_seed, ordered_keys, "snapshot", *tags)


def balanced_snapshot(root_seed: int, ordered_keys: list[str], snapshot_idx: int,
                       *tags: str | int) -> list[str]:
    """Position-balanced snapshot: across each block of len(keys) snapshots,
    every image occupies every position exactly once.

    Why this and not an independent shuffle per snapshot: independent shuffles
    only balance position *in expectation*, and 20 draws is nowhere near
    enough to get there. Measured on the first full qwen eval2 run (20
    independent shuffles), tech_2 drew position 6 five times and position 9
    once -- and since that model turned out to have a real primacy bias
    (it picked the earlier of the two tech images 75.6% of the time,
    p<0.0001), that lumpy position assignment leaks straight into the
    image-level choice shares the eval exists to measure.

    A cyclic Latin square fixes the marginal: each block of 10 snapshots is
    one base permutation and its 10 rotations, so every image sits at every
    position exactly once per block.

    That alone is NOT enough, and the first version of this function got it
    wrong. Rotations preserve *relative order*: if two images sit d apart in
    the base permutation, one precedes the other in exactly (n-d)/n of the
    rotations, never half. Measured consequence -- under a pure Latin square,
    tech_2 preceded tech_1 in only 25% of eval2 trials (an independent shuffle
    gives a fair 50%), which is worse for exactly the head-to-head comparison
    the primacy bias distorts.

    So each base permutation is paired with its REVERSE. If a precedes b in
    (n-d)/n of one block's rotations, it precedes b in d/n of the reversed
    block's -- averaging to exactly 1/2. Marginal balance is unaffected, since
    reversing then rotating is still a Latin square. Both properties then hold
    by construction:

      * every image occupies every position equally often, and
      * for every pair, each ordering occurs equally often.

    Exact pairwise balance needs an even number of blocks, i.e. n_snapshots a
    multiple of 2*len(keys) (20 here). An odd final block leaves a small
    residual imbalance; `position_balance_report` quantifies it for whatever
    n a run actually used.
    """
    n = len(ordered_keys)
    block, rotation = divmod(snapshot_idx, n)
    # Blocks pair up: 0 and 1 share a base (second reversed), 2 and 3, ...
    base = shuffled_permutation(root_seed, ordered_keys, "snapshot_block", block // 2, *tags)
    if block % 2 == 1:
        base = base[::-1]
    # Which rotation a given snapshot index gets is itself shuffled, so
    # snapshot order doesn't correlate with position drift within a block.
    order = rng_for(root_seed, "rotation_order", block, *tags).permutation(n)
    r = int(order[rotation])
    return base[r:] + base[:r]


def position_balance_report(perms: list[list[str]], keys: list[str]) -> dict:
    """Measure the two balance properties on the permutations actually used.

    Returns worst-case deviations so a run can assert its design held rather
    than assume it. `pairwise_max_dev` is the largest |P(a before b) - 0.5|
    over all pairs; `marginal_max_dev` the largest |count - expected| over all
    (image, position) cells.
    """
    n, m = len(keys), len(perms)
    idx = {k: i for i, k in enumerate(keys)}
    counts = [[0] * n for _ in range(n)]
    before = [[0] * n for _ in range(n)]
    for perm in perms:
        pos = {k: j for j, k in enumerate(perm)}
        for k, j in pos.items():
            counts[idx[k]][j] += 1
        for a in keys:
            for b in keys:
                if a != b and pos[a] < pos[b]:
                    before[idx[a]][idx[b]] += 1
    expected = m / n
    marginal_max_dev = max(abs(c - expected) for row in counts for c in row)
    pairwise_max_dev = max(abs(before[i][j] / m - 0.5)
                            for i in range(n) for j in range(n) if i != j)
    return {"n_snapshots": m, "marginal_max_dev": marginal_max_dev,
            "pairwise_max_dev": pairwise_max_dev,
            "marginal_balanced": marginal_max_dev < 1e-9,
            "pairwise_balanced": pairwise_max_dev < 1e-9}


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
