# Commands 
## Repo
Sticking to repo for this Take Home: tkrajina__gpxpy.09fc46b3
### To obtain a list of all repo names
<pre>  python3 -c "from swesmith.profiles import registry; print('\n'.join(sorted(registry.keys())))"  </pre>


### Create Instances
<pre>  python3 -m swesmith.bug_gen.handshake.func_signature_modification \
    tkrajina__gpxpy.09fc46b3 \
    -c configs/bug_gen/class_basic.yml \
    --max_bugs 1 \
    -w 1 </pre>

### Collect Patches
<pre> python -m swesmith.bug_gen.collect_patches logs/bug_gen/tkrajina__gpxpy.09fc46b3 </pre>


### Run Validation
Step 1: 
<pre>  python -m swesmith.harness.valid logs/bug_gen/tkrajina__gpxpy.09fc46b3_all_patches.json --redo_existing  </pre>

Results: 
``` Validation: 100%|██████████████████████████████████████████████████| 94/94 [06:30<00:00,  4.16s/it, fail=4, timeout=0, 0_f2p=29, 1+_f2p=61]
All instances run.
Total instances: 92
- Timed out: 4
- Fail to pass: 0 (27); 1+ (60)
- Other: 0 
```

Step 2: Gather all the patches
<pre>  python -m swesmith.harness.gather logs/run_validation/tkrajina__gpxpy.09fc46b3  </pre>

Results:
```
(venv) ashachigurupati@Ashas-MBP SWE-smith % python -m swesmith.harness.gather logs/run_validation/tkrajina__gpxpy.09fc46b3
run_id='tkrajina__gpxpy.09fc46b3'
Out Path: logs/task_insts/tkrajina__gpxpy.09fc46b3.json
Found 0 existing task instances
Will process 92 instances
Conversion:   0%|                                                                                                                                                                                | 0/92 [00:00<?, ?it/s]/Users/ashachigurupati/SWE-smith/venv/lib/python3.11/site-packages/ghapi/core.py:114: UserWarning: Neither GITHUB_TOKEN nor GITHUB_JWT_TOKEN found: running as unauthenticated
  else: warn('Neither GITHUB_TOKEN nor GITHUB_JWT_TOKEN found: running as unauthenticated')
Conversion: 100%|█████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 92/92 [00:12<00:00,  7.53it/s, new_tasks=56, skipped=32]
Cleaning up...
[tkrajina__gpxpy.09fc46b3] Removed local clone
Wrote 60 instances to logs/task_insts/tkrajina__gpxpy.09fc46b3.json
- 32 skipped
- 60 new instances
```

### Evaluate

<pre> python -m swesmith.harness.eval \
    --dataset_path logs/task_insts/tkrajina__gpxpy.09fc46b3.json \
    --predictions_path gold \
    --run_id sanity </pre>

Results:
```
(venv) ashachigurupati@Ashas-MBP SWE-smith % python -m swesmith.harness.eval \
    --dataset_path logs/task_insts/tkrajina__gpxpy.09fc46b3.json \
    --predictions_path gold \
    --run_id sanity

Using gold predictions for eval (ignoring `predictions_path` argument)
Evaluation: 100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 60/60 [00:20<00:00,  2.86it/s, ✓=0, ✖=0, timeout=0, error=60]
All instances run.
Resolved 0/60 instances.
Wrote report to logs/run_evaluation/sanity/report.json
```


## Same Repo, New Bug Generation 

 In order to re-do the entire process, with a different bug/task instance generation logic
 ### Delete the following

- delete the previously created instances : delete ` logs/bug_gen/... ` everything under this one.
- delete  ` logs/run_validation/tkrajina__gpxpy.09fc46b3/ `
- delete ` logs/task_insts/tkrajina__gpxpy.09fc46b3.json `




## Appendix
### Obtain a list of all repo names
<pre> ``` python3 -c "from swesmith.profiles import registry; print('\n'.join(sorted(registry.keys())))" ``` </pre>

### Obtain a list of all downloaded environment images, that you can do a Docker Pull On
<pre> ```python3 -m swesmith.build_repo.create_images``` </pre>

### Docked pull commands
```
docker pull swebench/swesmith.x86_64.tkrajina_1776_gpxpy.09fc46b3
docker run -it --rm swebench/swesmith.x86_64.tkrajina_1776_gpxpy.09fc46b3

docker pull swebench/swesmith.arm64.stanfordnlp_1776_dspy.651a4c71

docker pull swebench/swesmith.x86_64.instagram_1776_monkeytype.70c3acf6
docker run -it --rm swebench/swesmith.x86_64.instagram_1776_monkeytype.70c3acf6
 ```



