# Verity Task Summary

- group: `1inch/xycswap_curve_safety/quote_exact_in_curve_safety`
- suite: `v0.2`
- tasks: `1`
- check command: `./harness/check.sh`

## Policy

- Edit only files listed under editable files.
- Do not import hidden Proofs modules or Benchmark/GeneratedPreview.
- Do not use `sorry`, `admit`, or new `axiom` declarations.
- In fair comparisons, do not rely on benchmark-specific Grindset helpers or task-name-specific proof knowledge.

## Task 1: `1inch/xycswap_curve_safety/quote_exact_in_curve_safety`

- theorem: `Benchmark.Cases.OneInch.XYCSwapCurveSafety.quoteExactIn_curve_safety`
- target module: `Benchmark.Generated.OneInch.XYCSwapCurveSafety.Tasks.QuoteExactInCurveSafety`
- editable files: `Benchmark/Generated/OneInch/XYCSwapCurveSafety/Tasks/QuoteExactInCurveSafety.lean`
- implementation files: `cases/1inch/xycswap_curve_safety/verity/Contract.lean, Benchmark/Cases/OneInch/XYCSwapCurveSafety/Contract.lean`
- specification files: `cases/1inch/xycswap_curve_safety/verity/Specs.lean, Benchmark/Cases/OneInch/XYCSwapCurveSafety/Specs.lean`

### Relevant Symbols

- `Benchmark/Cases/OneInch/XYCSwapCurveSafety/Contract.lean`: storage amountOut : Uint256 := slot 0
- `Benchmark/Cases/OneInch/XYCSwapCurveSafety/Contract.lean`: Benchmark.Cases.OneInch.XYCSwapCurveSafety.function quoteExactIn
- `cases/1inch/xycswap_curve_safety/verity/Specs.lean`: def amountInWithFee (amountIn feeBps : Uint256) : Uint256
- `cases/1inch/xycswap_curve_safety/verity/Specs.lean`: def curveDenominator (balanceIn amountIn feeBps : Uint256) : Uint256
- `cases/1inch/xycswap_curve_safety/verity/Specs.lean`: def quoteExactInOutput (balanceIn balanceOut amountIn feeBps : Uint256) : Uint256
- `cases/1inch/xycswap_curve_safety/verity/Specs.lean`: def quoteExactIn_curve_safety_spec

### Current Editable File

`Benchmark/Generated/OneInch/XYCSwapCurveSafety/Tasks/QuoteExactInCurveSafety.lean`

```lean
import Benchmark.Cases.OneInch.XYCSwapCurveSafety.Specs
import Benchmark.Grindset

namespace Benchmark.Cases.OneInch.XYCSwapCurveSafety

open Verity
open Verity.EVM.Uint256

/--
Curve safety: the output of _quoteExactIn satisfies the fee-adjusted
constant-product constraint. The output amount times the denominator is at
most the fee-adjusted input times the output balance.
-/
theorem quoteExactIn_curve_safety
    (balanceIn balanceOut amountIn feeBps : Uint256)
    (hFeeRange : feeBps.val ≤ 10000)
    (hFeeMulNoOvf : amountIn.val * (10000 - feeBps.val) < modulus)
    (hDenomNoOvf : balanceIn.val
      + (amountIn.val * (10000 - feeBps.val) / 10000) < modulus)
    (hProductNoOvf :
      (amountIn.val * (10000 - feeBps.val) / 10000) * balanceOut.val < modulus) :
    quoteExactIn_curve_safety_spec balanceIn balanceOut amountIn feeBps := by
  exact ?_

end Benchmark.Cases.OneInch.XYCSwapCurveSafety
```
