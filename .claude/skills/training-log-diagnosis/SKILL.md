---
name: training-log-diagnosis
description: Use when analyzing training logs for AI/ML jobs. Trigger words include training log, loss, grad_norm, gradient explosion, training failed, epoch, mAP, NCCL heartbeat, 训练日志, 分析日志, 梯度爆炸.
---

# Training Log Deep Diagnosis

## Overview

Systematically analyze AI/ML training logs to identify root causes beyond simple error matching. Understand training dynamics — loss trajectory, gradient health, phase transitions, data quality — not just final error messages.

**Core principle:** Read logs as a timeline of training dynamics, not a bag of error keywords.

## The Diagnostic Framework

### Phase 1: Orientation (5 seconds)

Before diving into details, answer:

1. **What framework?** MMDetection, HuggingFace, PyTorch Lightning, DeepSpeed, Megatron...
2. **How many GPUs/nodes?** Single-node vs multi-node distributed
3. **What's the final status?** Success, Failed, Killed, Timeout
4. **How long did it run?** Minutes, hours, days
5. **Where in the log is the crash?** Beginning (setup), middle (training), end (eval/save)

### Phase 2: Timeline Reconstruction

Read the log **chronologically** and build a mental timeline:

```
Start → Init → Data Loading → Training Loop → [Crash Point] → Error
                                    ↓
                              Epoch progression
                              Loss trajectory
                              Grad norm trajectory
                              Checkpoint saves
                              Eval phases
```

Key transitions to identify:
- Training → Evaluation (COCO eval, validation)
- Normal → Abnormal (loss spike, grad explosion)
- Running → Crash (signal, exception, timeout)

### Phase 3: Quantitative Analysis

Extract and compare **numerical trends**, not just error strings:

| Metric | Normal | Warning | Critical |
|--------|--------|---------|----------|
| grad_norm | stable, < 10 | > 50 | > 100 or spike > 10x |
| loss | decreasing | flat for > 10 epochs | sudden 2x+ increase |
| lr | follows schedule | too high for task | N/A |
| memory | stable | growing slowly | OOM |
| eval mAP | improving | stagnant | very low (< 0.1) |

### Phase 4: Root Cause Identification

Apply these diagnostic patterns IN ORDER:

#### Pattern 1: Gradient Explosion
- **Signal:** grad_norm suddenly spikes > 10x in 1-2 steps
- **Consequence:** Loss jumps and never recovers
- **Root cause:** LR too high, bad data sample, numerical instability
- **Fix:** Add grad_clip, lower LR, check data quality at trigger point

#### Pattern 2: Loss Plateau After Spike
- **Signal:** Loss jumps then stays flat for many epochs
- **Implication:** Model parameters corrupted, gradient clipping alone won't help retroactively
- **Fix:** Resume from checkpoint BEFORE the spike, add grad_clip, lower LR

#### Pattern 3: NCCL Heartbeat Timeout During Eval
- **Signal:** Training completes → Eval starts → Heartbeat timeout on non-zero ranks
- **Mechanism:** Only rank 0 does COCO eval; other ranks idle; NCCL watchdog thinks they're dead
- **Fix:** Set `TORCH_NCCL_HEARTBEAT_TIMEOUT_SEC=1800`, optimize eval speed

#### Pattern 4: NaN/Inf Propagation
- **Signal:** loss=nan or grad_norm=inf appears
- **Consequence:** All subsequent training is garbage
- **Fix:** AMP GradScaler, gradient clipping, lower LR, check data normalization

#### Pattern 5: Data Quality Issues
- **Signal:** Repeated "Failed to decode image" warnings on same file
- **Impact:** Wasted compute, potential gradient anomalies
- **Fix:** Clean dataset, validate all images before training

#### Pattern 6: Training Complete But Post-Processing Crash
- **Signal:** Checkpoint saved at final epoch → crash during eval/save
- **Implication:** Training data is NOT lost
- **Fix:** Fix the post-processing issue; checkpoint is usable

### Phase 5: Report Structure

Always deliver diagnosis in this structure:

```
1. 概况 (Overview)
   - Task type, framework, GPU count, duration
   
2. 致命错误 (Fatal Error)
   - What crashed and when (exact timeline)
   - Root cause mechanism (WHY it crashed, not just WHAT)
   
3. 隐藏问题 (Hidden Issues)  
   - Training dynamics problems (grad explosion, loss plateau)
   - These are often MORE important than the crash itself
   
4. 次要问题 (Minor Issues)
   - Data warnings, non-fatal errors
   
5. 修复建议 (Recommendations)
   - Prioritized: P0 (must fix), P1 (should fix), P2 (nice to have)
   - Each with concrete commands or config changes
```

## Key Principles

| Principle | Description |
|-----------|-------------|
| Timeline first | Reconstruct chronological order before pattern matching |
| Quantitative | Extract actual numbers, don't just grep for "error" |
| Phase-aware | Same error means different things in training vs eval |
| Hidden > Visible | The gradient explosion is worse than the NCCL timeout |
| Fix at source | Don't fix symptoms (NCCL timeout); fix cause (eval too slow) |

## Anti-Patterns

**Don't do these:**

- Grep for "error" and stop at the first match
- Ignore INFO-level logs (training metrics are there!)
- Treat the crash message as the root cause (it's often a symptom)
- Miss the training dynamics story (loss trend, grad_norm trend)
- Ignore "warnings" (repeated data decode failures matter)

## Integration with diagnosis-api

This analytical approach is implemented as `TrainingLogSkill` in:

```
hpc-diagnosis-api/app/skills/builtin/training_log.py
```

The skill automatically:
1. Fetches training logs (both error and info level)
2. Parses MMDetection/HuggingFace training metrics
3. Detects gradient explosion, loss plateau, NaN/Inf
4. Correlates NCCL heartbeat timeout with eval phase
5. Identifies corrupt data patterns
6. Generates prioritized recommendations
