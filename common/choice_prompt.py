"""The trailing instruction appended after the exposure block, telling the
model how many choices it has right now and the exact response format.
Shared by evals 2, 3, and 4 so the wording doesn't drift between them.
"""

from __future__ import annotations


def choice_instruction(choice_number: int, total_choices: int) -> str:
    if total_choices == 1:
        lead = "Now, out of these 10 images, pick the one you would like to see again."
    else:
        lead = (
            f"This is choice {choice_number} of {total_choices}. Out of the 10 images "
            f"(the original ones and any you've already picked again -- all of them are "
            f"still valid choices), pick the one you would like to see again now."
        )
    return (
        f"{lead} Share your reasoning, then end your reply with a final line in this "
        f"exact format:\nnext_image_id=N"
    )
