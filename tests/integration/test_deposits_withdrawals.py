import brownie
from brownie import rpc
from brownie.test import strategy


class StateMachine:
    """
    Validate that deposits and withdrawals work correctly over time.

    Strategies
    ----------
    st_sender : Account
        Account to perform deposit or withdrawal from
    st_value : int
        Amount to deposit or withdraw
    st_time : int
        Amount of time to advance the clock
    """

    st_sender = strategy("address", length=5)
    st_receiver = strategy("address", length=5)
    st_value = strategy("uint64")
    st_time = strategy("uint", max_value=86400 * 365)

    def __init__(self, accounts, escrow, mock_lp_token):
        self.accounts = accounts
        self.escrow = escrow
        self.token = mock_lp_token

    def setup(self):
        self.balances = {i: 0 for i in self.accounts}

    def rule_deposit(self, st_sender, st_value):
        """
        Make a deposit into the `LiquidityGauge` contract.

        Because of the upper bound of `st_value` relative to the initial account
        balances, this rule should never fail.
        """
        balance = self.token.balanceOf(st_sender)

        self.escrow.deposit(st_value, {"from": st_sender})
        self.balances[st_sender] += st_value

        assert self.token.balanceOf(st_sender) == balance - st_value

    def rule_withdraw(self, st_sender, st_value):
        """
        Attempt to withdraw from the `LiquidityGauge` contract.
        """
        if self.balances[st_sender] < st_value:
            # fail path - insufficient balance
            with brownie.reverts():
                self.escrow.withdraw(st_value, {"from": st_sender})
            return

        # success path
        balance = self.token.balanceOf(st_sender)
        self.escrow.withdraw(st_value, {"from": st_sender})
        self.balances[st_sender] -= st_value

        assert self.token.balanceOf(st_sender) == balance + st_value

    def rule_advance_time(self, st_time):
        """
        Advance the clock.
        """
        rpc.sleep(st_time)

    def rule_transfer(self, st_sender, st_receiver, st_value):
        """
        Transfer tokens.
        """
        if self.balances[st_sender] < st_value:
            with brownie.reverts():
                self.escrow.transfer(st_receiver, st_value, {"from": st_sender})
            return

        self.escrow.transfer(st_receiver, st_value, {"from": st_sender})
        self.balances[st_sender] -= st_value
        self.balances[st_receiver] += st_value

    def invariant_balances(self):
        """
        Validate expected balances against actual balances.
        """
        for account, balance in self.balances.items():
            assert self.escrow.balanceOf(account) == balance

    def invariant_total_supply(self):
        """
        Validate expected total supply against actual total supply.
        """
        assert self.escrow.totalSupply() == sum(self.balances.values())

    def teardown(self):
        """
        Final check to ensure that all balances may be withdrawn.
        """
        for account, balance in ((k, v) for k, v in self.balances.items() if v):
            initial = self.token.balanceOf(account)
            self.escrow.withdraw(balance, {"from": account})

            assert self.token.balanceOf(account) == initial + balance


def test_state_machine(state_machine, accounts, escrow, lp_token, no_call_coverage):
    # fund accounts to be used in the test
    for acct in accounts[:5]:
        lp_token._mint_for_testing(10**21, {'from': acct})
        lp_token.approve(escrow, 2 ** 256 - 1, {"from": acct})

    # because this is a simple state machine, we use more steps than normal
    settings = {"stateful_step_count": 25}

    state_machine(StateMachine, accounts[:5], escrow, lp_token, settings=settings)
