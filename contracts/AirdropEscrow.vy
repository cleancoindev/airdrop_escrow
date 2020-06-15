from vyper.interfaces import ERC20


contract FullERC20:
    def decimals() -> uint256: constant


contract Curve:
    def claim_airdrop(addr: address, value: uint256): modifying


implements: ERC20

Transfer: event({_from: indexed(address), _to: indexed(address), _value: uint256})
Approval: event({_owner: indexed(address), _spender: indexed(address), _value: uint256})
Claim: event({_owner: indexed(address), _token: indexed(address), _value: uint256})

name: public(string[64])
symbol: public(string[32])
decimals: public(uint256)

balanceOf: public(map(address, uint256))
totalSupply: public(uint256)
prev_totalSupply: uint256
allowances: map(address, map(address, uint256))

admin: public(address)
failsafe: public(bool)

wrapped_token: public(address)
airdropped_tokens: public(address[255])
token_to_pool: public(map(address, address))
n_tokens: int128
redeemed_token_balances: map(address, uint256)

# External untransferrable deposit contracts which have balanceOf
# Everyone can claim for those
external_escrows: public(map(address, bool))

epoch: public(int128)  # Epoch where anything at all changes
user_epoch: public(map(address, int128))  # User epoch number
token_epoch: public(map(address, int128))  # Airdropped token epoch number

epoch_time: public(map(int128, uint256))  # epoch -> time
user_epochs: public(map(address, int128[10000000000000000]))  # Epochs where user changes deposits
token_epochs: public(map(address, int128[10000000000000000]))  # Epochs when new tokens drop
token_funded_balances: public(map(address, uint256[10000000000000000]))  # Balance of tokens which dropped without subtracting withdrawals
token_rates: public(map(address, uint256[10000000000000000]))

user_token_cursor_u: public(map(address, map(address, int128)))  # user -> token -> last claimed id in user_epochs
user_token_cursor_t: public(map(address, map(address, int128)))  # user -> token -> last claimed id in token_epochs

integral_inv_supply: public(uint256[10000000000000000])
user_balances: public(map(address, uint256[10000000000000000]))
claimed_token_of: public(map(address, map(address, uint256)))


@public
def __init__(_name: string[64], _symbol: string[32], token: address):
    self.name = _name
    self.symbol = _symbol
    self.decimals = FullERC20(token).decimals()
    self.wrapped_token = token
    self.admin = msg.sender


@public
@constant
def allowance(_owner : address, _spender : address) -> uint256:
    """
    @dev Function to check the amount of tokens that an owner allowed to a spender.
    @param _owner The address which owns the funds.
    @param _spender The address which will spend the funds.
    @return An uint256 specifying the amount of tokens still available for the spender.
    """
    return self.allowances[_owner][_spender]


@private
def _checkpoint(addrs: address[2] = [ZERO_ADDRESS,ZERO_ADDRESS]):
    _epoch: int128 = self.epoch
    _prev_supply: uint256 = self.prev_totalSupply
    _time : uint256 = as_unitless_number(block.timestamp)

    # Save integral(dt / supply)
    if _prev_supply != 0:
        _integral_inv_supply: uint256 = self.integral_inv_supply[_epoch]
        _integral_inv_supply += 10 ** 36 * (_time - self.epoch_time[_epoch]) / _prev_supply
        self.integral_inv_supply[_epoch + 1] = _integral_inv_supply
    _epoch += 1

    # Save user balances over epochs
    # Zero epoch is always zero
    for addr in addrs:
        if addr == ZERO_ADDRESS:
            break
        _user_epoch: int128 = self.user_epoch[addr] + 1
        self.user_balances[addr][_user_epoch] = self.balanceOf[addr]
        self.user_epoch[addr] = _user_epoch
        self.user_epochs[addr][_user_epoch] = _epoch

    # Handle airdrops which could have happened in the meantime
    for token in self.airdropped_tokens:
        if token == ZERO_ADDRESS:
            break
        pool: address = self.token_to_pool[token]
        if pool != ZERO_ADDRESS:
            _value: uint256 = ERC20(token).balanceOf(pool)
            if _value > 0:
                Curve(pool).claim_airdrop(token, _value)
        _token_epoch: int128 = self.token_epoch[token]
        _prev_balance: uint256 = self.token_funded_balances[token][_token_epoch]
        _balance: uint256 = ERC20(token).balanceOf(self)
        _balance += self.redeemed_token_balances[token]
        if _balance > _prev_balance:
            dt: uint256 = _time - self.epoch_time[self.token_epochs[token][_token_epoch]]
            if dt == 0:
                continue
            self.token_rates[token][_token_epoch] = (_balance - _prev_balance) / dt
            _token_epoch += 1
            self.token_epochs[token][_token_epoch] = _epoch
            self.token_epoch[token] = _token_epoch
            self.token_funded_balances[token][_token_epoch] = _balance

    self.epoch = _epoch
    self.epoch_time[_epoch] = _time
    self.prev_totalSupply = self.totalSupply


@public
def transfer(_to : address, _value : uint256) -> bool:
    """
    @dev Transfer token for a specified address
    @param _to The address to transfer to.
    @param _value The amount to be transferred.
    """
    # NOTE: vyper does not allow underflows
    #       so the following subtraction would revert on insufficient balance
    if _value != 0:
        self.balanceOf[msg.sender] -= _value
        self.balanceOf[_to] += _value
        if not self.failsafe:
            self._checkpoint([msg.sender, _to])
    log.Transfer(msg.sender, _to, _value)
    return True


@public
def transferFrom(_from : address, _to : address, _value : uint256) -> bool:
    """
     @dev Transfer tokens from one address to another.
     @param _from address The address which you want to send tokens from
     @param _to address The address which you want to transfer to
     @param _value uint256 the amount of tokens to be transferred
    """
    # NOTE: vyper does not allow underflows
    #       so the following subtraction would revert on insufficient balance
    if _value != 0:
        self.balanceOf[_from] -= _value
        self.balanceOf[_to] += _value
        self.allowances[_from][msg.sender] -= _value
        if not self.failsafe:
            self._checkpoint([_from, _to])
    log.Transfer(_from, _to, _value)
    return True


@public
def approve(_spender : address, _value : uint256) -> bool:
    """
    @dev Approve the passed address to spend the specified amount of tokens on behalf of msg.sender.
         Beware that changing an allowance with this method brings the risk that someone may use both the old
         and the new allowance by unfortunate transaction ordering. One possible solution to mitigate this
         race condition is to first reduce the spender's allowance to 0 and set the desired value afterwards:
         https://github.com/ethereum/EIPs/issues/20#issuecomment-263524729
    @param _spender The address which will spend the funds.
    @param _value The amount of tokens to be spent.
    """
    assert _value == 0 or self.allowances[msg.sender][_spender] == 0
    self.allowances[msg.sender][_spender] = _value
    log.Approval(msg.sender, _spender, _value)
    return True


@public
@nonreentrant('lock')
def deposit(_value: uint256):
    """
    @dev Deposit tokens to escrow
    @param _value Amount to deposit
    """
    ERC20(self.wrapped_token).transferFrom(msg.sender, self, _value)
    if _value != 0:
        self.totalSupply += _value
        self.balanceOf[msg.sender] += _value
        if not self.failsafe:
            self._checkpoint([msg.sender, ZERO_ADDRESS])
    log.Transfer(ZERO_ADDRESS, msg.sender, _value)


@public
@nonreentrant('lock')
def withdraw(_value: uint256):
    """
    @dev Withdraw tokens from the escrow
    @param _value Amount to withdraw
    """
    if _value != 0:
        self.totalSupply -= _value
        self.balanceOf[msg.sender] -= _value
        if not self.failsafe:
            self._checkpoint([msg.sender, ZERO_ADDRESS])
    ERC20(self.wrapped_token).transfer(msg.sender, _value)
    log.Transfer(msg.sender, ZERO_ADDRESS, _value)


@private
@constant
def _calc_claim(_sender: address, _token: address, read_only: bool = False) -> (int128, int128, uint256):
    _token_epoch: int128 = self.token_epoch[_token]
    earned: uint256 = 0
    max_token_cursor: int128 = self.token_epoch[_token]
    max_user_cursor: int128 = self.user_epoch[_sender]
    cursor_t: int128 = self.user_token_cursor_t[_sender][_token]
    cursor_u: int128 = self.user_token_cursor_u[_sender][_token]
    epoch_user: int128 = self.user_epochs[_sender][cursor_u]
    epoch_token: int128 = self.token_epochs[_token][cursor_t]
    rate: uint256 = 0
    user_balance: uint256 = 0
    old_rate_cursor: int128 = -1
    old_balance_cursor: int128 = -1
    cursor_epoch: int128 = min(epoch_user, epoch_token)
    I0: uint256 = self.integral_inv_supply[cursor_epoch]
    # zip-join epochs of two cursors
    # and updated earned on every point

    for i in range(500):
        # Rate for the current dt
        if epoch_user >= epoch_token:
            if old_rate_cursor != cursor_t:
                rate = self.token_rates[_token][cursor_t]
                old_rate_cursor = epoch_token
        else:
            if old_rate_cursor != cursor_t-1 and cursor_t > 0:
                rate = self.token_rates[_token][cursor_t-1]
                old_rate_cursor = cursor_t - 1

        # Balance for the current dt
        user_balance = 0  # Value for epoch_user == 0
        if epoch_user > 0:
            if epoch_user < epoch_token:
                if cursor_u != old_balance_cursor:
                    user_balance = self.user_balances[_sender][cursor_u]
                    old_balance_cursor = cursor_u
            else:
                if cursor_u-1 != old_balance_cursor:
                    user_balance = self.user_balances[_sender][cursor_u-1]
                    old_balance_cursor = cursor_u - 1

        # measure integral1 here
        # measure integral2 after step+
        # earned += dI * balance * rate
        # user_integral not needed, need user balances instead TODO

        finish_loop: bool = False

        if cursor_u >= max_user_cursor:
            # This is actually the current user checkpoint
            finish_loop = True
        else:
            if epoch_user < epoch_token:
                cursor_u += 1
                epoch_user = self.user_epochs[_sender][cursor_u]
            else:
                if cursor_t >= max_token_cursor:
                    finish_loop = True
                else:
                    cursor_t += 1
                    epoch_token = self.token_epochs[_token][cursor_t]

        cursor_epoch = min(epoch_user, epoch_token)
        I1: uint256 = self.integral_inv_supply[cursor_epoch]
        dI: uint256 = I1 - I0
        I0 = I1
        # dI = 10 ** 36 * integral(dt / totalSupply)

        # earned += integral(user_balance / totalSupply * rate * dt)
        # arranged to prevent over- and underflows
        earned += ((dI * rate) / 10 ** 18) * user_balance / 10 ** 18

        if finish_loop:
            break

    if read_only:
        dI: uint256 = (self.integral_inv_supply[self.epoch] - I0)
        dI += 10 ** 36 * (as_unitless_number(block.timestamp) - self.epoch_time[self.epoch]) / self.totalSupply
        earned += ((dI * rate) / 10 ** 18) * user_balance / 10 ** 18

    return cursor_t, cursor_u, earned


@public
@constant
def balanceOfAirdrop(_token: address, _user: address) -> uint256:
    """
    @dev _Approximate_ calculation of what amount can be claimed. Use for information only!
    """
    if self.token_epoch[_token] > 0 or self.user_epoch[msg.sender] > 0:
        return 0
    cursor_t: int128 = 0
    cursor_u: int128 = 0
    earned: uint256 = 0
    cursor_t, cursor_u, earned = self._calc_claim(_user, _token, True)
    return earned


@public
@nonreentrant('lock')
def claim(_token: address, _for: address = ZERO_ADDRESS):
    """
    @dev Claim all the airdropped tokens
    @param _token Token address
    @param _for Claim for the escrow (everyone can): needed for external escrows
    """
    _user: address = msg.sender
    if _for != ZERO_ADDRESS:
        assert self.external_escrows[_for]
        _user = _for

    assert self.token_epoch[_token] > 0, "Airdrops in this token are not yet received"
    assert self.user_epoch[_user] > 0, "User must have some deposits"
    self._checkpoint([_user, ZERO_ADDRESS])

    cursor_t: int128 = 0
    cursor_u: int128 = 0
    earned: uint256 = 0
    cursor_t, cursor_u, earned = self._calc_claim(_user, _token)

    # Save state
    self.user_token_cursor_t[_user][_token] = cursor_t
    self.user_token_cursor_u[_user][_token] = cursor_u

    # Transfer tokens
    if earned > 0:
        self.claimed_token_of[_user][_token] += earned
        assert_modifiable(ERC20(_token).transfer(_user, earned))
        log.Claim(_user, _token, earned)


@public
def set_admin(_admin: address):
    assert msg.sender == self.admin  # dev: admin only
    self.admin = _admin


@public
def toggle_failsafe():
    assert msg.sender == self.admin  # dev: admin only
    self.failsafe = not self.failsafe


@public
def add_token(addr: address, pool: address = ZERO_ADDRESS):
    assert msg.sender == self.admin  # dev: admin only
    assert self.token_epoch[addr] == 0
    self._checkpoint()
    n: int128 = self.n_tokens
    self.airdropped_tokens[n] = addr
    self.n_tokens = n + 1
    self.token_epochs[addr][0] = self.epoch
    if pool != ZERO_ADDRESS:
        self.token_to_pool[addr] = pool


@public
def toggle_external_escrow(addr: address):
    assert msg.sender == self.admin  # dev: admin only
    assert addr != ZERO_ADDRESS  # dev: zero address
    self.external_escrows[addr] = not self.external_escrows[addr]


@public
def remove_token(i: int128):
    assert msg.sender == self.admin  # dev: admin only
    self._checkpoint()
    n: int128 = self.n_tokens - 1
    self.airdropped_tokens[i] = self.airdropped_tokens[n]
    self.airdropped_tokens[n] = ZERO_ADDRESS
    self.n_tokens = n
