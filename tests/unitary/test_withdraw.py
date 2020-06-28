import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def module_setup(accounts, escrow, lp_token):
    for i in range(2):
        lp_token._mint_for_testing(10**24, {'from': accounts[i]})
        lp_token.approve(escrow, 10**24, {'from': accounts[i]})
        escrow.deposit(10**24, {'from': accounts[i]})


def test_initial_getter_amounts(alice, escrow, lp_token):
    assert lp_token.balanceOf(alice) == 0
    assert escrow.balanceOf(alice) == 10**24
    assert escrow.totalSupply() == 10**24 * 2


def test_withdraw(alice, escrow, lp_token):
    balance = escrow.balanceOf(alice)
    total_supply = escrow.totalSupply()

    escrow.withdraw(10**18, {'from': alice})

    assert lp_token.balanceOf(alice) == 10**18
    assert escrow.balanceOf(alice) == balance - 10**18
    assert escrow.totalSupply() == total_supply - 10**18


def test_multiple_withdraw(alice, escrow, lp_token):
    balance = escrow.balanceOf(alice)
    total_supply = escrow.totalSupply()

    escrow.withdraw(31337, {'from': alice})
    escrow.withdraw(42, {'from': alice})

    assert lp_token.balanceOf(alice) == 31337 + 42
    assert escrow.balanceOf(alice) == balance - 31337 - 42
    assert escrow.totalSupply() == total_supply - 31337 - 42


def test_withdraw_zero(alice, escrow, lp_token):
    balance = escrow.balanceOf(alice)
    total_supply = escrow.totalSupply()
    escrow.withdraw(0, {'from': alice})

    assert lp_token.balanceOf(alice) == 0
    assert escrow.balanceOf(alice) == balance
    assert escrow.totalSupply() == total_supply


def test_withdraw_zero_balance_zero(alice, charlie, escrow, lp_token):
    total_supply = escrow.totalSupply()
    escrow.withdraw(0, {'from': charlie})

    assert lp_token.balanceOf(charlie) == 0
    assert escrow.balanceOf(charlie) == 0
    assert escrow.totalSupply() == total_supply


def test_withdraw_all(alice, escrow, lp_token):
    balance = escrow.balanceOf(alice)
    total_supply = escrow.totalSupply()
    escrow.withdraw(balance, {'from': alice})

    assert lp_token.balanceOf(alice) == balance
    assert escrow.balanceOf(alice) == 0
    assert escrow.totalSupply() == total_supply - balance


def test_deposit_multiple_accounts(alice, bob, escrow, lp_token):
    balance1 = escrow.balanceOf(alice)
    balance2 = escrow.balanceOf(bob)
    total_supply = escrow.totalSupply()

    escrow.withdraw(5318008, {'from': alice})
    escrow.withdraw(71077345, {'from': bob})

    assert lp_token.balanceOf(alice) == 5318008
    assert escrow.balanceOf(alice) == balance1 - 5318008

    assert lp_token.balanceOf(bob) == 71077345
    assert escrow.balanceOf(bob) == balance2 - 71077345

    assert escrow.totalSupply() == total_supply - 5318008 - 71077345


def test_withdraw_amount_too_large(alice, escrow, lp_token):
    balance = escrow.balanceOf(alice)
    with brownie.reverts():
        escrow.withdraw(balance + 1, {'from': alice})
