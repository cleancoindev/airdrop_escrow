import brownie

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_toggle_external_escrow(alice, bob, escrow):
    assert not escrow.external_escrows(bob)
    escrow.toggle_external_escrow(bob, {'from': alice})
    assert escrow.external_escrows(bob)
    escrow.toggle_external_escrow(bob, {'from': alice})
    assert not escrow.external_escrows(bob)


def test_admin_only(bob, escrow):
    with brownie.reverts("dev: admin only"):
        escrow.toggle_external_escrow(bob, {'from': bob})


def test_zero_address(alice, escrow):
    with brownie.reverts("dev: zero address"):
        escrow.toggle_external_escrow(ZERO_ADDRESS, {'from': alice})
