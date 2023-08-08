from brownie import RouterStrategy, Contract, accounts, web3, ZERO_ADDRESS

def check_strategy_losses():
    hit = False
    r = Contract(web3.ens.resolve('helper.v2.registry.ychad.eth'))
    vaults = list(r.getVaults())
    for v in vaults:
        if v == '0x321d570790fd2f109Fe4e55aa419Adf2fce0c842':
            hit = True
        if hit == False:
            continue
        v = Contract(v)
        for i in range(0,20):
            s = v.withdrawalQueue(i)
            if s == ZERO_ADDRESS:
                break
            try:
                s = Contract(s)
            except:
                print(s)
                continue
            try:
                eta = s.estimatedTotalAssets()
            except:
                print(f'⚠️ Unable to query ETA on: {v.address} {s.address}')
                continue
            td = v.strategies(s)['totalDebt']
            if td > 0:
                d = 10**v.decimals()
                print("Assets: ",eta/d)
                print("Debt  : ",td/d)
                if eta == 0:
                    print(f'🚨 ETA is 0: {v.address} {s.address}')
                    continue
                diff = abs(eta - td)
                percent_diff = diff / eta * 100
                if percent_diff >= 10:
                    print(f'🚨 Diff > 10% {v.address} {s.address}')


def main():
    wavey = accounts.load('wavey')
    old_vault = '0xdCD90C7f6324cfa40d7169ef80b12031770B4325'
    factory_vault = '0x5B8C556B8b2a78696F0B9B830B3d67623122E270'
    helper = Contract('0xec85C894be162268c834b784CC232398E3E89A12',owner=wavey)
    new_registry = Contract(helper.newRegistry())
    all_vaults = list(helper.getVaults())
    versions = [
        "0.3.0",
        "0.3.1",
        "0.3.2",
    ]
    txn_args = {
        'max_fee': int(80e9),
        'priority_fee': int(3.5e9),
        'from':wavey
    }
    router = ZERO_ADDRESS
    router = Contract('0x9084B5a98E3b4B257affd82AE4a1753f87906DcE',owner=wavey)

    for v in all_vaults:
        if v == old_vault:
            continue
        v = Contract(v)
        api_old = v.apiVersion()
        if api_old in versions:
            token = v.token()
            if not is_curve_lp(token):
                continue
            latest = new_registry.latestVault(token)
            if latest != v.address:
                symbol = v.symbol()
                print(f'\n\n{symbol.replace(".","")}\nOLD: {v.address}\nNew: {latest}')
                strat_name = f'Router-Modified-{symbol}-{api_old.replace(".","")}-{Contract(latest).apiVersion().replace(".","")}'
                if router == ZERO_ADDRESS: # Deploy if not already
                    router = Contract('0x9084B5a98E3b4B257affd82AE4a1753f87906DcE',owner=wavey)
                    # router = wavey.deploy(
                    #     RouterStrategy, 
                    #     old_vault, 
                    #     factory_vault, 
                    #     'Router-Modified-yvCurveStETH',
                    #     max_fee=40e9,
                    #     priority_fee=1e9
                    # )
                    # RouterStrategy.publish_source(router)
                    # router = wavey.deploy(RouterStrategy, v.address, latest, strat_name, max_fee=80e9, priority_fee=3e9, publish_source=True)
                    router = RouterStrategy.at(router.address, owner=wavey)
                    # router.setKeeper(web3.ens.resolve('keeper.ychad.eth'),txn_args)
                    router.setRewards(web3.ens.resolve('treasury.ychad.eth'),{'from':wavey})
                    router.setStrategist(web3.ens.resolve('brain.ychad.eth'),txn_args)
                    print(f"Router Deployed: {router.address}")
                else: # Clone if already deployed
                    tx = router.cloneRouter(
                        v.address,
                        web3.ens.resolve('brain.ychad.eth'),
                        web3.ens.resolve('treasury.ychad.eth'),
                        web3.ens.resolve('keeper.ychad.eth'),
                        latest,
                        strat_name,
                        txn_args
                    )
                    print(f"New Router cloned: {tx.events['Cloned']['clone']}")

def is_curve_lp(token):
    meta = Contract('0xF98B45FA17DE75FB1aD0e7aFD971b0ca00e379fC')
    return meta.get_pool_from_lp_token(token) != ZERO_ADDRESS