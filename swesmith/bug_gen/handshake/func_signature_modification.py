"""
Purpose: Given a repository, blank out various functions/classes, then ask the model to rewrite them.

Usage: python -m swesmith.bug_gen.llm.rewrite \
    --model <model> \
    repo  # e.g., tkrajina__gpxpy.09fc46b3

Where model follows the litellm format.

Example:

python -m swesmith.bug_gen.llm.rewrite tkrajina__gpxpy.09fc46b3 --model claude-3-7-sonnet-20250219
"""

import argparse
import json
# import litellm
import logging
import os
import random
import shutil
import subprocess
import yaml

from concurrent.futures import ThreadPoolExecutor, as_completed
# from litellm import completion
# from litellm.cost_calculator import completion_cost
# from swesmith.bug_gen.llm.utils import (
#     PROMPT_KEYS,
#     extract_code_block,
# )
from swesmith.bug_gen.utils import (
    apply_code_change,
    get_bug_directory,
    get_patch,
)
from swesmith.constants import (
    LOG_DIR_BUG_GEN,
    PREFIX_BUG,
    PREFIX_METADATA,
    BugRewrite,
    CodeEntity,
)
from swesmith.profiles import registry
from tqdm.auto import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm
from typing import Any


LM_REWRITE = "lm_rewrite"

logging.getLogger("LiteLLM").setLevel(logging.WARNING)
# litellm.drop_params = True
# litellm.suppress_debug_info = True
random.seed(24)


def main(
    repo: str,
    config_file: str,
    model: str,
    n_workers: int,
    redo_existing: bool = False,
    max_bugs: int | None = None,
    **kwargs,
):
    # configs = yaml.safe_load(open(config_file))
    rp = registry.get(repo)
    rp.clone()

    print(f"Extracting entities from {repo}...")
    candidates = rp.extract_entities()
    if max_bugs:
        random.shuffle(candidates)
        candidates = candidates[:max_bugs]

    # Set up logging
    log_dir = LOG_DIR_BUG_GEN / repo
    log_dir.mkdir(parents=True, exist_ok=True)
    print(f"Logging bugs to {log_dir}")
    if not redo_existing:
        print("Skipping existing bugs.")
    
    def _process_candidate(candidate: CodeEntity) -> dict[str, Any]:
        bug_dir = get_bug_directory(log_dir, idx, candidate)
        # if not redo_existing:
            # if bug_dir.exists() and any(
            #     [
            #         str(x).startswith(f"{PREFIX_BUG}__{configs['name']}")
            #         for x in os.listdir(bug_dir)
            #     ]
            # ):
            #     return {"n_bugs_generated": 0, "cost": 0.0}

        # try:
        #     # Blank out the function body
        #     blank_function = BugRewrite(
        #         rewrite=candidate.stub,
        #         # your code changes go here
        #         explanation="Blanked out the function body.",
        #         strategy=LM_REWRITE,
        #     )
        #     apply_code_change(candidate, blank_function)
        # except Exception:
        #     return {"n_generation_failed": 1, "cost": 0.0}
        # code_block = "" #modified_function_signature() 

        rewrite = BugRewrite(
            rewrite=candidate.stub,
            explanation="Modified the function signature : explanation",
            strategy=LM_REWRITE,
            cost=0.0
        )
        print("Applying code change...", rewrite.rewrite)
        apply_code_change(candidate, rewrite)
        patch = get_patch(repo, reset_changes=True)
        if not patch or len(patch.strip()) == 0:
            return {"n_generation_failed": 0, "cost": 0.0}

        # Log the bug
        bug_dir.mkdir(parents=True, exist_ok=True)
        # uuid_str = f"{configs['name']}__{rewrite.get_hash()}"
        # uuid_str = "blanked_out_the_function_body"
        uuid_str = f"{idx}___{rewrite.get_hash()}"
        metadata_path = f"{PREFIX_METADATA}__{uuid_str}.json"
        bug_path = f"{PREFIX_BUG}__{uuid_str}.diff"

        with open(bug_dir / metadata_path, "w") as f:
            json.dump(rewrite.to_dict(), f, indent=2)
        with open(bug_dir / bug_path, "w") as f:
            f.write(patch)
        print(f"Wrote bug to {bug_dir / bug_path}")

        return {"n_bugs_generated": 1, "cost": 0.0}

    stats = {"cost": 0.0, "n_bugs_generated": 0, "n_generation_failed": 0}
    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = [
            executor.submit(_process_candidate, idx,candidate) for idx, candidate in enumerate(candidates)
        ]

        with logging_redirect_tqdm():
            with tqdm(total=len(candidates), desc="Candidates") as pbar:
                for future in as_completed(futures):
                    cost = future.result()
                    for k, v in cost.items():
                        stats[k] += v
                    pbar.set_postfix(stats, refresh=True)
                    pbar.update(1)

    shutil.rmtree(repo)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate bug patches for functions/classes/objects in a repository."
    )
    parser.add_argument(
        "repo", type=str, help="Repository to generate bug patches for."
    )
    parser.add_argument(
        "-c",
        "--config_file",
        type=str,
        help="Path to the configuration file.",
        required=False,
    )
    parser.add_argument("--model", type=str, help="Model to use for rewriting.")
    parser.add_argument(
        "-w", "--n_workers", type=int, help="Number of workers to use", default=1
    )
    parser.add_argument(
        "--redo_existing", action="store_true", help="Redo existing bugs."
    )
    parser.add_argument(
        "-m", "--max_bugs", type=int, help="Maximum number of bugs to generate."
    )
    args = parser.parse_args()
    main(**vars(args))
