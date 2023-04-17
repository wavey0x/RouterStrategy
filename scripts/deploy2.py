from brownie import RouterStrategy, Contract, accounts, web3, ZERO_ADDRESS

def main():
    wavey = accounts.load('wavey')
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
        'priority_fee': int(3e9)
    }
    router = ZERO_ADDRESS
    for v in all_vaults:
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
                strat_name = f'Router-{symbol}-{api_old.replace(".","")}-{Contract(latest).apiVersion().replace(".","")}'
                if router == ZERO_ADDRESS: # Deploy if not already
                    router = RouterStrategy.at('0xA5F565CFBF40464C18a1aDf1d7203D9A1B5CEE60',owner=wavey)
                    router = Contract(router.address,owner=wavey)
                    # RouterStrategy.publish_source(router)
                    continue
                    router = wavey.deploy(RouterStrategy, v.address, latest, strat_name, max_fee=80e9, priority_fee=3e9, publish_source=True)
                    router = RouterStrategy.at(router.address, owner=wavey)
                    router.setKeeper(web3.ens.resolve('keeper.ychad.eth'))
                    router.setRewards(web3.ens.resolve('treasury.ychad.eth'))
                    router.setStrategist(web3.ens.resolve('brain.ychad.eth'))
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