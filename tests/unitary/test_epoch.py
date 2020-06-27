import pytest


@pytest.fixture(scope="module")
def epoch(accounts, escrow, lp_token):
    lp_token._mint_for_testing(10**24, {'from': accounts[0]})
    lp_token.approve(escrow, 10**24, {'from': accounts[0]})
    escrow.deposit(10**18, {'from': accounts[0]})

    yield escrow.epoch()


def test_transfer(accounts, escrow, lp_token, epoch):
    escrow.transfer(accounts[1], 10**18, {'from': accounts[0]})

    assert escrow.epoch() == epoch + 1


def test_transferFrom(accounts, escrow, lp_token, epoch):
    escrow.approve(accounts[2], 10**18, {'from': accounts[0]})
    escrow.transferFrom(accounts[0], accounts[1], 10**18, {'from': accounts[2]})

    assert escrow.epoch() == epoch + 1


def test_deposit(accounts, escrow, lp_token, epoch):
    escrow.deposit(10**18, {'from': accounts[0]})

    assert escrow.epoch() == epoch + 1


def test_withdraw(accounts, escrow, lp_token, epoch):
    escrow.withdraw(10**18, {'from': accounts[0]})

    assert escrow.epoch() == epoch + 1


def test_add_token(accounts, escrow, airdrop_token, epoch):
    escrow.add_token(airdrop_token, {'from': accounts[0]})

    assert escrow.epoch() == epoch + 1


def test_remove_token(accounts, escrow, airdrop_token, epoch):
    escrow.add_token(airdrop_token, {'from': accounts[0]})
    escrow.remove_token(1, {'from': accounts[0]})

    assert escrow.epoch() == epoch + 2


def test_claim(rpc, accounts, escrow, airdrop_token, epoch):
    airdrop_token._mint_for_testing(10**18, {'from': accounts[0]})
    airdrop_token.transfer(escrow, 10**18, {'from': accounts[0]})
    escrow.add_token(airdrop_token, {'from': accounts[0]})
    rpc.sleep(1)  # Need at least 1 second to have non-infinite rates
    escrow.claim(airdrop_token, {'from': accounts[0]})

    assert escrow.epoch() == epoch + 2


def test_transfer_zero(accounts, escrow, lp_token, epoch):
    escrow.transfer(accounts[1], 0, {'from': accounts[0]})

    assert escrow.epoch() == epoch


def test_transferFrom_zero(accounts, escrow, lp_token, epoch):
    escrow.transferFrom(accounts[0], accounts[1], 0, {'from': accounts[2]})

    assert escrow.epoch() == epoch


def test_deposit_zero(accounts, escrow, lp_token, epoch):
    escrow.deposit(0, {'from': accounts[0]})

    assert escrow.epoch() == epoch


def test_withdraw_zero(accounts, escrow, lp_token, epoch):
    escrow.withdraw(0, {'from': accounts[0]})

    assert escrow.epoch() == epoch
