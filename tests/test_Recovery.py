#!/usr/bin/python3
 
# test script for testing recovery of Rbtc and tokens
# for now we do not require complete test coverage. just make sure, the regular calls are successful.
import textwrap

import pytest
from brownie import Contract, Wei, reverts
from fixedint import *
import shared



@pytest.fixture(scope="module", autouse=True)
def loanToken(LoanToken, LoanTokenLogicStandard, LoanTokenSettingsLowerAdmin, SUSD, WETH, accounts, sovryn, Constants, priceFeeds, swapsImpl):

    loanTokenLogic = accounts[0].deploy(LoanTokenLogicStandard)
    #Deploying loan token using the loan logic as target for delegate calls
    loanToken = accounts[0].deploy(LoanToken, loanTokenLogic.address, sovryn.address, WETH.address)
    #Initialize loanTokenAddress
    loanToken.initialize(SUSD, "SUSD", "SUSD")
    #setting the logic ABI for the loan token contract
    loanToken = Contract.from_abi("loanToken", address=loanToken.address, abi=LoanTokenLogicStandard.abi, owner=accounts[0])

    # loan token Price should be equals to initial price
    assert loanToken.tokenPrice() == loanToken.initialPrice()
    initial_total_supply = loanToken.totalSupply()
    # loan token total supply should be zero
    assert initial_total_supply == loanToken.totalSupply()

    return loanToken
    
@pytest.fixture(scope="module", autouse=True)
def loanTokenWBTC(LoanToken, LoanTokenLogicWeth, LoanTokenSettingsLowerAdmin, SUSD, WETH, accounts, sovryn, Constants, priceFeeds, swapsImpl):

    loanTokenLogic = accounts[0].deploy(LoanTokenLogicWeth)
    # Deploying loan token using the loan logic as target for delegate calls
    loanToken = accounts[0].deploy(LoanToken, loanTokenLogic.address, sovryn.address, WETH.address)
    # Initialize loanTokenAddress
    loanToken.initialize(WETH, "iWBTC", "iWBTC")
    # setting the logic ABI for the loan token contract
    loanToken = Contract.from_abi("loanToken", address=loanToken.address, abi=LoanTokenLogicWeth.abi, owner=accounts[0])

    # loan token Price should be equals to initial price
    assert loanToken.tokenPrice() == loanToken.initialPrice()
    initial_total_supply = loanToken.totalSupply()
    # loan token total supply should be zero
    assert initial_total_supply == loanToken.totalSupply()

    return loanToken




@pytest.fixture(scope="module", autouse=True)   
def loanTokenSettingsRecovery(accounts, LoanTokenSettings):
    loanTokenSettings = accounts[0].deploy(LoanTokenSettings)
    return loanTokenSettings


'''
1. Mint some tokens and transfer to the loanToken contract
2. Test withdrawal of minted tokens
3. Assure recovery fails because only invalid tokens are allowed to withdraw
'''
def test_recover_Susd(accounts, sovryn, loanToken, SUSD, loanTokenSettingsRecovery, LoanToken, LoanTokenSettings):
    localLoanToken = Contract.from_abi("loanToken", address=loanToken.address, abi=LoanToken.abi, owner=accounts[0])
    localLoanToken.setTarget(loanTokenSettingsRecovery.address)
    localLoanToken = Contract.from_abi("loanToken", address=loanToken.address, abi=LoanTokenSettings.abi, owner=accounts[0])
    
    tokenAddress = SUSD.address 
    receiver = accounts[1]
    amount = 100e18
    SUSD.mint(loanToken.address, amount)

    with reverts("invalid token"):
        tx = localLoanToken.recoverToken(tokenAddress, receiver, amount, {'from': accounts[0]})

    
    

'''
1. Mint some tokens and transfer to the loanToken contract
2. Test withdrawal of minted tokens
3. Assure Balance of the receiver increased by the amount of minted tokens and balance of loanToken is 0
'''
def test_recover_RbtcTokens(accounts, sovryn, loanToken, RBTC, loanTokenSettingsRecovery, LoanToken, LoanTokenSettings):
    localLoanToken = Contract.from_abi("loanToken", address=loanToken.address, abi=LoanToken.abi, owner=accounts[0])
    localLoanToken.setTarget(loanTokenSettingsRecovery.address)
    localLoanToken = Contract.from_abi("loanToken", address=loanToken.address, abi=LoanTokenSettings.abi, owner=accounts[0])
    
    balReceiverBefore = RBTC.balanceOf(accounts[1].address)
    tokenAddress = RBTC.address 
    receiver = accounts[1]
    amount = 100e18
    RBTC.mint(loanToken.address, amount)

    tx = localLoanToken.recoverToken(tokenAddress, receiver, amount, {'from': accounts[0]})

    transferEvent = tx.events['Transfer']

    assert(RBTC.balanceOf(loanToken.address) == 0) 
    assert(RBTC.balanceOf(accounts[1].address)==balReceiverBefore+amount) 
    assert(transferEvent["to"]==accounts[1])
    assert(transferEvent["value"]==amount) 
    
    
'''
Assure the contract does not allow to receive RBTC directly
'''
def test_send_Rbtc(accounts, loanToken):
    amount = 1e17
    with reverts():
        accounts[0].transfer(loanToken.address, amount)
     


'''
LoanTokenSettings.recoverBTC cannot be tested because there is no way to send RBTC to the smart contract and it remaining on the contract.
'''