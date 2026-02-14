# *Tags-Aware LLM Modify*

This bug generation methodology ensures that LLM prompts are tailored specifically to the context of the target code.

## *1. Core Definitions*

* *Code Context* :  (Interchangeable with Code Tags or Tags) refers to the context of the target code. 

* *Code Entity* : The fundamental building block of our repository parsing process. A collection of these entities constitutes the complete repository. Each code_entity is an object (typically representing a function).
    *  *Attribute* Each code entity contains attributes like `IS_FUNCTION` or `HAS_LOOP` to provide granular insight into code operations.

## *2. Methodology: Code Context-Driven Prompting*
We develop a mapping between specific CodeEntity attributes and  targeted LLM prompts. For instance, if an entity contains the `HAS_LIST_INDEXING` attribute, the system curates a prompt that includes instructions to the LLM to introduce off-by-one errors. Typical injections include shifting the index start to 1 instead of 0 or terminating a range prematurely.

This methodology addresses a specific shortcoming observed in the LM Modify method. Previous experiments involving broad bug generation prompts—applied without Code Context—resulted in the LLM defaulting to trivial changes, such as simple variable re-assignments. Consequently, the LM Modify method yields a difficulty rating that is predominantly "Easy." This places it on par with Procedural Bug Generation, which relies on a static, pre-set mapping between context and concrete code changes rather than dynamic, context-aware bug injection

## *3. Optimization Strategies*
This methodology is projected to yield higher-complexity bugs than current approaches based on the following:

1. By tailoring bug generation to the Code Context, we ensure a diverse range of prompts rather than a uniform set. This creates the necessary space for unique, context-specific prompts to manifest.
Crucially, this mapping prioritizes prompts that inject high-difficulty bugs, forcing the LLM away from its tendency to default to trivial changes.

2. Beyond Code Context mapping, we implement two additional constraints to refine the output: a Code Tag Priority Hierarchy and a Maximum Prompt Limit .

    - *Tag Prioritization* : We rank Code Tags based on frequency. Routine tags (e.g., `HAS_ASSIGNMENT` or `HAS_ARITHMETIC`) are assigned low priority, while rarer, more complex tags receive high priority.

    - *Max Prompts* : By capping the input at five prompts and applying this priority order, we systematically filter out common tags and their associated bug ideas.

3. While Procedural Modifications are highly Code Context aware, they rely on fixed/static logic, resulting in a model that is "Easy". Our LLM based bug generation introduces complexity and diversity. 

## *4. Future Direction: Iterative Injection & Sequential Prompting*

An additional extension to the Tag-Aware LLM Modify method involves sequential prompting. Instead of a single-pass modification, we apply prompts iteratively to the same code snippet, layering each new bug atop the previous injection. This process continues until all Context-Aware prompts for that segment are exhausted. The advantages and trade-offs of this direction include:

* Comprehensive Coverage: It ensures every identified prompt is implemented, maximizing the utilization of the extracted Code Context.
* Increased Complexity: Layering multiple bugs can create compound logic errors that are significantly harder to detect than isolated changes.
* Loss of Stochasticity: We sacrifice the benefits of random prompt selection, potentially creating more predictable sequences.

This iterative approach represents a promising direction for exploring high-density, multi-fault bug generation.

## *5. Handshake Bug Generation Method*
The Handshake method is a specialized, trivial bug generation strategy that simply blanks out an entire function body.
Primary Purpose: Used as a diagnostic tool to debug Apple Silicon (M1/M2) architecture issues and verify external integrations (e.g., Anthropic API connectivity).
Result: While it consistently produces validated task instances, its utility is limited to environment "smoke testing" rather than generating complex logical bugs.

# Commands 
## *Build Environment*
<pre>
docker pull swebench/swesmith.x86_64.tkrajina_1776_gpxpy.09fc46b3
docker run -it --rm swebench/swesmith.x86_64.tkrajina_1776_gpxpy.09fc46b3
</pre>
If using Apple Silicon M3 Chip, 
<pre>
docker tag swebench/swesmith.x86_64.tkrajina_1776_gpxpy.09fc46b3 swebench/swesmith.arm64.tkrajina_1776_gpxpy.09fc46b3
</pre>
or 

## *Create Instances*
<pre>

</pre>
Results are uploaded to logs/bug_gen/tkrajina__gpxpy.09fc46b3

## *Collect Patches*
<pre>
python -m swesmith.bug_gen.collect_patches logs/bug_gen/tkrajina__gpxpy.09fc46b3
</pre>
Results are found in logs/bug_gen/tkrajina__gpxpy.09fc46b3_all_patches.json

## Run Validation
<pre>
python -m swesmith.harness.valid logs/bug_gen/tkrajina__gpxpy.09fc46b3_all_patches.json --redo_existing
</pre>

Results are found in logs/run_validation/tkrajina__gpxpy.09fc46b3

## Gather Validated Logs
<pre>
python -m swesmith.harness.gather logs/run_validation/tkrajina__gpxpy.09fc46b3
</pre>
Results are found in logs/task_insts/tkrajina__gpxpy.09fc46b3.json

## Run Evaluation
<pre>
python -m swesmith.harness.eval \
    --dataset_path logs/task_insts/tkrajina__gpxpy.09fc46b3.json \
    --predictions_path gold \
    --run_id sanity
</pre>
Results are found in logs/run_evaluation/sanity/tkrajina__gpxpy.09fc46b3.*

```
Using gold predictions for eval (ignoring `predictions_path` argument)
Found 0 completed evaluations. Remaining: 50
Evaluation: 100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 50/50 [00:16<00:00,  3.06it/s, ✓=0, ✖=0, timeout=0, error=50]
All instances run.
Resolved 0/50 instances.
Wrote report to logs/run_evaluation/sanity/report.json
```


# Resources
Custom Anthropic Key used. 