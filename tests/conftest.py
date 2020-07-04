import pytest
from brownie import compile_source

POOL_MOCK = """
from vyper.interfaces import ERC20

@external
def claim_airdrop(_addr: address, _value: uint256):
    ERC20(_addr).transfer(msg.sender, _value)
    """


# isolation setup

@pytest.fixture(autouse=True)
def isolation_setup(fn_isolation):
    pass


# named accounts

@pytest.fixture(scope="session")
def alice(accounts):
    yield accounts[0]


@pytest.fixture(scope="session")
def bob(accounts):
    yield accounts[1]


@pytest.fixture(scope="session")
def charlie(accounts):
    yield accounts[2]


# contract deployments

@pytest.fixture(scope="module")
def lp_token(ERC20_Revert, alice):
    yield ERC20_Revert.deploy("LP Token", "LP", 18, {'from': alice})


@pytest.fixture(scope="module")
def escrow(AirdropEscrow, alice, lp_token):
    yield AirdropEscrow.deploy("Airdrop Escrow", "AIR", lp_token, {'from': alice})


@pytest.fixture(scope="module")
def pool(alice):
    deployer = compile_source(POOL_MOCK).Vyper
    yield deployer.deploy({'from': alice})


@pytest.fixture(scope="module")
def airdrop_token(ERC20_Revert, alice):
    yield ERC20_Revert.deploy("Airdrop One", "AD1", 18, {'from': alice})
