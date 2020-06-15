import brownie
import pytest


@pytest.fixture(scope="module")
def epoch(accounts, escrow, lp_token):
    lp_token._mint_for_testing(10**24, {'from': accounts[0]})
    lp_token.approve(escrow, 10**24, {'from': accounts[0]})
    escrow.deposit(10**18, {'from': accounts[0]})

    yield escrow.epoch()


def test_admin_only_enable_failsafe(accounts, escrow):
    with brownie.reverts("dev: admin only"):
        escrow.toggle_failsafe({'from': accounts[1]})

    escrow.toggle_failsafe({'from': accounts[0]})

    with brownie.reverts("dev: admin only"):
        escrow.toggle_failsafe({'from': accounts[1]})


def test_admin_only_disable_failsafe(accounts, escrow):
    escrow.toggle_failsafe({'from': accounts[0]})

    with brownie.reverts("dev: admin only"):
        escrow.toggle_failsafe({'from': accounts[1]})


def test_toggle_failsafe(accounts, escrow):
    assert not escrow.failsafe()

    escrow.toggle_failsafe({'from': accounts[0]})
    assert escrow.failsafe()

    escrow.toggle_failsafe({'from': accounts[0]})
    assert not escrow.failsafe()


def test_transfer(accounts, escrow, lp_token, epoch):
    escrow.toggle_failsafe()
    escrow.transfer(accounts[1], 10**18, {'from': accounts[0]})

    assert escrow.epoch() == epoch


def test_transferFrom(accounts, escrow, lp_token, epoch):
    escrow.toggle_failsafe()
    escrow.approve(accounts[2], 10**18, {'from': accounts[0]})
    escrow.transferFrom(accounts[0], accounts[1], 10**18, {'from': accounts[2]})

    assert escrow.epoch() == epoch


def test_deposit(accounts, escrow, lp_token, epoch):
    escrow.toggle_failsafe()
    escrow.deposit(10**18, {'from': accounts[0]})

    assert escrow.epoch() == epoch


def test_withdraw(accounts, escrow, lp_token, epoch):
    escrow.toggle_failsafe()
    escrow.withdraw(10**18, {'from': accounts[0]})

    assert escrow.epoch() == epoch
