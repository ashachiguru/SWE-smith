"""
Purpose:
    Perform Tags-Aware LLM bug generation on a repository. This method tailors LLM
    prompts to specific CodeEntity attributes, ensuring high-difficulty,
    contextually relevant code modifications.

Description:
    Given a target repository, this module:
        1. Applies a Priority Hierarchy to extracted tags, prioritizing rare/complex 
           attributes over routine ones.
        2. Curates a specific LLM prompt by filtering for the top-priority tags 
           up to a defined 'Maximum Prompt Limit', and including the "bug generation ideas" 
           associated with those tags into the prompt.
        3. Invokes the LLM to rewrite the code implementation, injecting 
           sophisticated bugs based on the selected context-aware prompts.
        4. Saves the modified state for task instance validation.


Usage:
    python -m swesmith.bug_gen.tags_aware_llm.tag_aware_modify \
        <repo> \
        --model <model> \
        --config_file <path> \
        --max_bugs <int> \
        -w <int>

Arguments:
    repo           Repository identifier (e.g., tkrajina__gpxpy.09fc46b3).
    --model        Model name in LiteLLM format (e.g., anthropic/claude-3-5-sonnet).
    --config_file  YAML file defining tag priorities and prompt mappings.
    --max_bugs     Total limit for generated bugs across the repository.
    -w             Number of parallel workers for concurrent LLM calls.

Example:
    python -m swesmith.bug_gen.tags_aware_llm.tag_aware_modify \
        tkrajina__gpxpy.09fc46b3 \
        --model anthropic/claude-3-haiku-20240307 \
        --config_file configs/bug_gen/tag_to_bug_mapping.yml \
        --max_bugs 1000 -w 1
"""

import argparse
import json
import litellm
import logging
import os
import random
import shutil
import subprocess
import yaml

from concurrent.futures import ThreadPoolExecutor, as_completed
from litellm import completion
from litellm.cost_calculator import completion_cost
from swesmith.bug_gen.llm.utils import (
    PROMPT_KEYS,
    extract_code_block,
)
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

TAG_AWARE_LM_MODIFY = "tag_aware_lm_modify"
TAG_PRIORITY_KEYS = [
    "HAS_OFF_BY_ONE",
    "HAS_LOOP",
    "HAS_IF_ELSE",
    "HAS_IF",
    "HAS_EXCEPTION",
    "HAS_FUNCTION_CALL",
    "HAS_LIST_INDEXING",
    "HAS_LIST_COMPREHENSION",
    "HAS_RETURN",
    "HAS_ARITHMETIC",
    "HAS_ASSIGNMENT",
    "HAS_BOOL_OP",
    "IS_FUNCTION",
]

logging.getLogger("LiteLLM").setLevel(logging.WARNING)
litellm.drop_params = True
litellm.suppress_debug_info = True
random.seed(24)

def _build_tag_bug_types(
    candidate: CodeEntity,
    tag_to_bug_type: dict[str, str],
    max_tag_bug_types: int = 3,
) -> str:
    selected = []
    for key in TAG_PRIORITY_KEYS:
        if len(selected) >= max_tag_bug_types:
            break
        attr_name = key.lower()
        if getattr(candidate, attr_name, False) and tag_to_bug_type.get(key):
            selected.append(f"- {tag_to_bug_type[key]}")

    if not selected:
        return "- Introduce a subtle logical bug while preserving signature and syntax."
    return "\n".join(selected)



def main(
    repo: str,
    config_file: str,
    model: str,
    n_workers: int,
    redo_existing: bool = False,
    max_bugs: int | None = None,
    **kwargs,
):
    configs = yaml.safe_load(open(config_file))
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
        bug_dir = get_bug_directory(log_dir, candidate)
        if not redo_existing:
            if bug_dir.exists() and any(
                [
                    str(x).startswith(f"{PREFIX_BUG}__{configs['name']}")
                    for x in os.listdir(bug_dir)
                ]
            ):
                return {"n_bugs_generated": 0, "cost": 0.0}

        # Get prompt content
        prompt_content = {
            "src_code": candidate.src_code,
            "tag_bug_types": _build_tag_bug_types(
                candidate,
                configs.get("tag_to_bug_type", {}),
                configs.get("max_tag_bug_types", 3),
            ),
        }

        # Generate a rewrite
        messages = [
            {
                "content": configs[k].format(**prompt_content),
                "role": "user" if k != "system" else "system",
            }
            for k in PROMPT_KEYS # ['system', 'demonstration', 'instance']
            if k in configs  # 'name', 'system', 'instance'
        ]

        messages = [x for x in messages if x["content"]]
    
        try:
            response: Any = completion(
                model=model, messages=messages, n=1, temperature=0)
        except litellm.ContextWindowExceededError:
            return {"n_generation_failed": 1, "cost": 0.0}
        choice = response.choices[0]
        message = choice.message

        # Apply the rewrite
        code_block = extract_code_block(message.content)
        explanation = message.content.split("```", 1)[0].strip()
        
        cost = completion_cost(completion_response=response)
        rewrite = BugRewrite(
            rewrite=code_block,
            explanation=explanation,
            strategy=TAG_AWARE_LM_MODIFY,
            cost=cost,
            output=message.content,
        )
        # Capture base commit BEFORE applying the bug
        base_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo).decode().strip()

        apply_code_change(candidate, rewrite)
        patch = get_patch(repo, reset_changes=True)
        if not patch or len(patch.strip()) == 0:
            return {"n_generation_failed": 0, "cost": cost}

        # Log the bug
        bug_dir.mkdir(parents=True, exist_ok=True)
        uuid_str = f"{configs['name']}__{rewrite.get_hash()}"
        metadata_path = f"{PREFIX_METADATA}__{uuid_str}.json"
        bug_path = f"{PREFIX_BUG}__{uuid_str}.diff"

        with open(bug_dir / metadata_path, "w") as f:
            metadata = rewrite.to_dict()
            metadata["base_commit"] = base_commit
            metadata["repo"] = repo
            json.dump(metadata, f, indent=2)
        with open(bug_dir / bug_path, "w") as f:
            f.write(patch)
        print(f"Wrote bug to {bug_dir / bug_path}")

        return {"n_bugs_generated": 1, "cost": 0.0}

    stats = {"cost": 0.0, "n_bugs_generated": 0, "n_generation_failed": 0}
    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = [
            executor.submit(_process_candidate, candidate) for candidate in candidates
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
        required=True,
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
