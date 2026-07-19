# Verity Task Summary

- group: `openzeppelin/erc4626_virtual_offset_deposit/deposit_redeem_round_trip_bound`
- suite: `v0.2`
- tasks: `1`
- check command: `./harness/check.sh`

## Policy

- Edit only files listed under editable files.
- Do not import hidden Proofs modules or Benchmark/GeneratedPreview.
- Do not use `sorry`, `admit`, or new `axiom` declarations.
- In fair comparisons, do not rely on benchmark-specific Grindset helpers or task-name-specific proof knowledge.

## Task 1: `openzeppelin/erc4626_virtual_offset_deposit/deposit_redeem_round_trip_bound`

- theorem: `Benchmark.Cases.OpenZeppelin.ERC4626VirtualOffsetDeposit.deposit_redeem_round_trip_bound`
- target module: `Benchmark.Generated.OpenZeppelin.ERC4626VirtualOffsetDeposit.Tasks.DepositRedeemRoundTripBound`
- editable files: `Benchmark/Generated/OpenZeppelin/ERC4626VirtualOffsetDeposit/Tasks/DepositRedeemRoundTripBound.lean`
- implementation files: `cases/openzeppelin/erc4626_virtual_offset_deposit/verity/Contract.lean, Benchmark/Cases/OpenZeppelin/ERC4626VirtualOffsetDeposit/Contract.lean`
- specification files: `cases/openzeppelin/erc4626_virtual_offset_deposit/verity/Specs.lean, Benchmark/Cases/OpenZeppelin/ERC4626VirtualOffsetDeposit/Specs.lean`

### Relevant Symbols

- `Benchmark/Cases/OpenZeppelin/ERC4626VirtualOffsetDeposit/Contract.lean`: def virtualAssets : Uint256
- `Benchmark/Cases/OpenZeppelin/ERC4626VirtualOffsetDeposit/Contract.lean`: def virtualShares : Uint256
- `Benchmark/Cases/OpenZeppelin/ERC4626VirtualOffsetDeposit/Contract.lean`: def previewDepositAmount (assets totalAssets totalShares : Uint256) : Uint256
- `Benchmark/Cases/OpenZeppelin/ERC4626VirtualOffsetDeposit/Contract.lean`: def previewRedeemAmount (shares totalAssets totalShares : Uint256) : Uint256
- `Benchmark/Cases/OpenZeppelin/ERC4626VirtualOffsetDeposit/Specs.lean`: def deposit_redeem_round_trip_bound_spec

### Current Editable File

`Benchmark/Generated/OpenZeppelin/ERC4626VirtualOffsetDeposit/Tasks/DepositRedeemRoundTripBound.lean`

```lean
import Benchmark.Cases.OpenZeppelin.ERC4626VirtualOffsetDeposit.Specs
import Verity.Stdlib.Math
import Benchmark.Grindset

namespace Benchmark.Cases.OpenZeppelin.ERC4626VirtualOffsetDeposit

open Verity
open Verity.EVM.Uint256
open Verity.Stdlib.Math

/--
Depositing `assets` and immediately redeeming the minted shares never returns
more than `assets`, and the round-trip loss is bounded by one share's asset
value rounded up (`oneShareAssetsUp`).
-/
theorem deposit_redeem_round_trip_bound
    (assets : Uint256) (s : ContractState)
    (hAssetsDenom : add (s.storage 0) virtualAssets ≠ 0)
    (hSharesDenom : add (s.storage 1) virtualShares ≠ 0)
    (hMul : (assets : Nat) * ((add (s.storage 1) virtualShares : Uint256) : Nat)
      <= MAX_UINT256) :
    deposit_redeem_round_trip_bound_spec assets s := by
  unfold deposit_redeem_round_trip_bound_spec
  grind

end Benchmark.Cases.OpenZeppelin.ERC4626VirtualOffsetDeposit
```
