import pytest
from brownie import compile_source

POOL_MOCK = """
from vyper.interfaces import ERC20

@public
def claim_airdrop(addr: address, value: uint256):
    ERC20(addr).transfer(msg.sender, value)
    """


@pytest.fixture(autouse=True)
def isolation_setup(fn_isolation):
    pass


@pytest.fixture(scope="module")
def lp_token(ERC20_Revert, accounts):
    yield ERC20_Revert.deploy("LP Token", "LP", 18, {'from': accounts[0]})


@pytest.fixture(scope="module")
def escrow(AirdropEscrow, accounts, lp_token):
    yield AirdropEscrow.deploy("Airdrop Escrow", "AIR", lp_token, {'from': accounts[0]})


@pytest.fixture(scope="module")
def pool(accounts):
    deployer = compile_source(POOL_MOCK).Vyper
    yield deployer.deploy({'from': accounts[0]})


@pytest.fixture(scope="module")
def airdrop_token(ERC20_Revert, accounts):
    yield ERC20_Revert.deploy("Airdrop One", "AD1", 18, {'from': accounts[0]})
