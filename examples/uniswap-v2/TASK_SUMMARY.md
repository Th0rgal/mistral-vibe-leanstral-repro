# Verity Task Summary

- group: `uniswap_v2/pair_fee_adjusted_swap/swap_enforces_fee_adjusted_invariant`
- suite: `v0.2`
- tasks: `1`
- check command: `./harness/check.sh`

## Policy

- Edit only files listed under editable files.
- Do not import hidden Proofs modules or Benchmark/GeneratedPreview.
- Do not use `sorry`, `admit`, or new `axiom` declarations.
- In fair comparisons, do not rely on benchmark-specific Grindset helpers or task-name-specific proof knowledge.

## Task 1: `uniswap_v2/pair_fee_adjusted_swap/swap_enforces_fee_adjusted_invariant`

- theorem: `Benchmark.Cases.UniswapV2.PairFeeAdjustedSwap.applySwap_enforces_fee_adjusted_invariant`
- target module: `Benchmark.Generated.UniswapV2.PairFeeAdjustedSwap.Tasks.SwapEnforcesFeeAdjustedInvariant`
- editable files: `Benchmark/Generated/UniswapV2/PairFeeAdjustedSwap/Tasks/SwapEnforcesFeeAdjustedInvariant.lean`
- implementation files: `cases/uniswap_v2/pair_fee_adjusted_swap/verity/Contract.lean, Benchmark/Cases/UniswapV2/PairFeeAdjustedSwap/Contract.lean`
- specification files: `cases/uniswap_v2/pair_fee_adjusted_swap/verity/Specs.lean, Benchmark/Cases/UniswapV2/PairFeeAdjustedSwap/Specs.lean`

### Relevant Symbols

- `Benchmark/Cases/UniswapV2/PairFeeAdjustedSwap/Contract.lean`: Benchmark.Cases.UniswapV2.PairFeeAdjustedSwap.function applySwap
- `Benchmark/Cases/UniswapV2/PairFeeAdjustedSwap/Specs.lean`: def applySwap_enforces_fee_adjusted_invariant_spec

### Current Editable File

`Benchmark/Generated/UniswapV2/PairFeeAdjustedSwap/Tasks/SwapEnforcesFeeAdjustedInvariant.lean`

```lean
import Benchmark.Cases.UniswapV2.PairFeeAdjustedSwap.Specs
import Benchmark.Grindset

namespace Benchmark.Cases.UniswapV2.PairFeeAdjustedSwap

open Verity
open Verity.EVM.Uint256

/-- Executing `applySwap` is only possible when the fee-adjusted product guard holds. -/
theorem applySwap_enforces_fee_adjusted_invariant
    (balance0 balance1 amount0In amount1In : Uint256) (s : ContractState)
    (hInput : amount0In != 0 || amount1In != 0)
    (hFee0 : mul balance0 1000 >= mul amount0In 3)
    (hFee1 : mul balance1 1000 >= mul amount1In 3)
    (hK : mul (sub (mul balance0 1000) (mul amount0In 3))
        (sub (mul balance1 1000) (mul amount1In 3))
        >= mul (mul (s.storage 0) (s.storage 1)) 1000000) :
    let s' := ((PairFeeAdjustedSwap.applySwap balance0 balance1 amount0In amount1In).run s).snd
    applySwap_enforces_fee_adjusted_invariant_spec balance0 balance1 amount0In amount1In s s' := by
  exact ?_

end Benchmark.Cases.UniswapV2.PairFeeAdjustedSwap
```
