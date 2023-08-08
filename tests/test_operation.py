import pytest
from brownie import Contract, ZERO_ADDRESS, Wei, chain, accounts, reverts


def test_migrate(origin_vault, destination_vault, strategy, gov, loss_checker, stash):
    whale = accounts.at('0x99ac10631F69C753DDb595D074422a0922D9056B',force=True)
    old_vault = origin_vault

    # At this point, all funds are already removed from existing strats
    # We only have to harvest into our router strat, which is already at 100% DR
    strategy.setFeeLossTolerance(100_000e18,{"from": gov})
    tx = strategy.harvest({"from": gov})

    chain.sleep(60 * 60 * 24 * 2)

    # No sells, means no profit yet
    # Let's set mgmt fee pretty high
    origin_vault.setManagementFee(500, {"from": gov})

    expectedLoss = loss_checker.check_loss(0, 0, strategy)
    print(f'EXPECTED LOSS AMOUNT = {expectedLoss}')
    expected_loss = emulate_fees(strategy, origin_vault)

    pps = old_vault.pricePerShare()
    tx = strategy.harvest({"from": gov})
    print(f"pps1: {pps}")
    print(f"pps2: {old_vault.pricePerShare()}")
    try:
        print(f"🪂 AirdropAmt: {tx.events['OffsetLossOnFee']['amount']/1e18}")
    except:
        print(f"👌 No Airdrop")
    assert old_vault.pricePerShare() >= pps

    chain.sleep(60 * 60 * 24 * 2)
    # Let's transfer some want to the checker that it can sweep
    whale = accounts.at('0x99ac10631F69C753DDb595D074422a0922D9056B', force=True)

    pps = origin_vault.pricePerShare()
    # strategy.setFeeLossTolerance(100e18,{"from": gov})
    tx = strategy.harvest({"from": gov})
    chain.sleep(60*60)
    print(f"pps1: {pps}")
    print(f"pps2: {old_vault.pricePerShare()}")
    try:
        print(f"🪂 AirdropAmt: {tx.events['OffsetLossOnFee']['amount']/1e18}")
    except:
        print(f"👌 No Airdrop")
    assert old_vault.pricePerShare() >= pps

    # strategy.setFeeLossTolerance(100e18,{"from": gov})

    totalShares = origin_vault.totalSupply()
    tx = strategy.harvest({"from": gov})
    totalSharesAfter = origin_vault.totalSupply()
    assert totalSharesAfter <= totalShares + (
        strategy.feeLossTolerance() * 
        origin_vault.pricePerShare() / 
        1e18
    )

    print(tx.events['Harvested'])


def emulate_fees(strategy, origin_vault):
    SECS_PER_YEAR = 31_557_600
    MAX_BPS = 10_000
    v = origin_vault
    mgmt_fee = v.managementFee()
    params = v.strategies(strategy).dict()
    last = v.lastReport()
    current = chain.time()
    time_since = current - last
    total_assets = v.totalAssets()
    gov_fee = total_assets * time_since * mgmt_fee / MAX_BPS / SECS_PER_YEAR
    return gov_fee

def test_sweep(gov, stash, strategy):
    want = Contract(strategy.want(),owner=gov)
    # Test access control
    with reverts():
        stash.sweep(want, {'from':accounts[0]})

    bal_before = want.balanceOf(gov)
    tx = stash.sweep(want)
    bal_after = want.balanceOf(gov)
    print(f'Amount Swept: {(bal_after - bal_before)/1e18}')
    assert bal_after > bal_before
