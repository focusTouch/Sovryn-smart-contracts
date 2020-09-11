'''
Test the asministrative functions of the loan token contract
1. set the demand curve (base for interest calculation)
2. fail is trying to set the demand curve resulting in a interest rate > 100%
3. test if the lending fee is set
4. toggle function pause
5. fail if trying to toggle the function pause with a non-admin wallet
'''

import pytest
from brownie import Contract, Wei, reverts
from fixedint import *
import shared

def test_Demand_Curve_Setting(loanToken, loanTokenSettings, LoanTokenSettingsLowerAdmin, accounts, LoanToken, LoanTokenLogicStandard):
    baseRate = 1e18
    rateMultiplier = 20.25e18
    localLoanToken = Contract.from_abi("loanToken", address=loanToken.address, abi=LoanToken.abi, owner=accounts[0])
    localLoanToken.setTarget(loanTokenSettings.address)
    localLoanToken = Contract.from_abi("loanToken", address=loanToken.address, abi=LoanTokenSettingsLowerAdmin.abi, owner=accounts[0])
    localLoanToken.setDemandCurve(baseRate, rateMultiplier, baseRate, rateMultiplier)

    assert(loanToken.baseRate() == baseRate)
    assert(loanToken.rateMultiplier() == rateMultiplier)
    assert(loanToken.lowUtilBaseRate() == baseRate)
    assert(loanToken.lowUtilRateMultiplier() == rateMultiplier)

    loanTokenLogic = accounts[0].deploy(LoanTokenLogicStandard)
    localLoanToken = Contract.from_abi("loanToken", address=loanToken.address, abi=LoanToken.abi, owner=accounts[0])
    localLoanToken.setTarget(loanTokenLogic.address)
    localLoanToken = Contract.from_abi("loanToken", address=loanToken.address, abi=LoanTokenLogicStandard.abi, owner=accounts[0])

    borrowInterestRate = loanToken.borrowInterestRate()
    print("borrowInterestRate: ", borrowInterestRate)
    assert(borrowInterestRate > 1e18)


def test_Demand_Curve_Setting_should_fail_if_rateMultiplier_plus_baseRate_is_grater_than_100_percent(
        loanToken, loanTokenSettings, LoanTokenSettingsLowerAdmin, accounts, LoanToken, LoanTokenLogicStandard):
    incorrect_baseRate = 51e18
    incorrect_rateMultiplier = 50e18
    baseRate = 1e18
    rateMultiplier = 20.25e18
    localLoanToken = Contract.from_abi("loanToken", address=loanToken.address, abi=LoanToken.abi, owner=accounts[0])
    localLoanToken.setTarget(loanTokenSettings.address)
    localLoanToken = Contract.from_abi("loanToken", address=loanToken.address, abi=LoanTokenSettingsLowerAdmin.abi, owner=accounts[0])
    with reverts():
        localLoanToken.setDemandCurve(incorrect_baseRate, incorrect_rateMultiplier, baseRate, rateMultiplier)
    with reverts():
        localLoanToken.setDemandCurve(baseRate, rateMultiplier, incorrect_baseRate, incorrect_rateMultiplier)


def test_lending_fee_setting(sovryn):
    tx = sovryn.setLendingFeePercent(1e20)
    lfp = sovryn.lendingFeePercent()
    assert(lfp == 1e20)


'''
1. pause a function
2. try to call the function - should fail
3. reactivate it
4. try to call the function - should succeed
'''
def test_toggle_function_pause(accounts, loanToken, LoanToken, LoanTokenSettingsLowerAdmin, LoanTokenLogicStandard, loanTokenSettings, SUSD, open_margin_trade_position, lend_to_pool):
    
    lend_to_pool()
    functionSignature = "marginTrade(bytes32,uint256,uint256,uint256,address,address,bytes)"
    
    # pause the given function
    localLoanToken = Contract.from_abi("loanToken", address=loanToken.address, abi=LoanToken.abi, owner=accounts[0])
    localLoanToken.setTarget(loanTokenSettings.address)
    localLoanToken = Contract.from_abi("loanToken", address=loanToken.address, abi=LoanTokenSettingsLowerAdmin.abi, owner=accounts[0])
    localLoanToken.toggleFunctionPause(functionSignature, True)
    
    # make sure the function can't be called anymore
    localLoanToken = Contract.from_abi("loanToken", address=loanToken.address, abi=LoanToken.abi, owner=accounts[0])
    loanTokenLogic = accounts[0].deploy(LoanTokenLogicStandard)
    localLoanToken.setTarget(loanTokenLogic.address)
    localLoanToken = Contract.from_abi("loanToken", address=loanToken.address, abi=LoanTokenLogicStandard.abi, owner=accounts[0])
    
    with reverts("unauthorized"):
        open_margin_trade_position()
    
    # reactivate the given function
    localLoanToken = Contract.from_abi("loanToken", address=loanToken.address, abi=LoanToken.abi, owner=accounts[0])
    localLoanToken.setTarget(loanTokenSettings.address)
    localLoanToken = Contract.from_abi("loanToken", address=loanToken.address, abi=LoanTokenSettingsLowerAdmin.abi, owner=accounts[0])
    localLoanToken.toggleFunctionPause(functionSignature, False)
    
    #make sure the function can be called again
    localLoanToken = Contract.from_abi("loanToken", address=loanToken.address, abi=LoanToken.abi, owner=accounts[0])
    localLoanToken.setTarget(loanTokenLogic.address)
    localLoanToken = Contract.from_abi("loanToken", address=loanToken.address, abi=LoanTokenLogicStandard.abi, owner=accounts[0])
    open_margin_trade_position()
 
'''
call toggleFunction with a non-admin address and make sure it fails
'''   
def test_toggle_function_pause_with_non_admin_should_fail(loanToken, LoanTokenSettingsLowerAdmin, loanTokenSettings, LoanToken, accounts):
    
    localLoanToken = Contract.from_abi("loanToken", address=loanToken.address, abi=LoanToken.abi, owner=accounts[0])
    localLoanToken.setTarget(loanTokenSettings.address)
    localLoanToken = Contract.from_abi("loanToken", address=loanToken.address, abi=LoanTokenSettingsLowerAdmin.abi, owner=accounts[0])
    with reverts("unauthorized"):
        localLoanToken.toggleFunctionPause("mint(address,uint256)", True, {'from':accounts[1]})


def test_set_early_access_token(EarlyAccessToken, accounts, loanToken, LoanTokenLogicStandard):
    old_early_access_token = loanToken.earlyAccessToken()
    new_early_access_token = accounts[0].deploy(EarlyAccessToken, "Sovryn Early Access Token", "SEAT")

    tx = loanToken.setEarlyAccessToken(new_early_access_token.address)
    tx.info()

    event_name = "SetEarlyAccessToken"
    if event_name in tx.events:
        event = tx.events[event_name]
        assert(event["sender"] == accounts[0])
        assert(event["oldValue"] == old_early_access_token)
        assert(event["newValue"] == new_early_access_token)
    else:
        # When all the tests are run, the event is not recognized
        events = list(
            filter(lambda tx_: tx_['topic1'] == LoanTokenLogicStandard.topics[event_name], tx.events['(unknown)']))
        assert(len(events) == 1)

    assert(loanToken.earlyAccessToken() == new_early_access_token)


def test_set_early_access_token_with_unauthorized_user_should_fail(early_access_token, EarlyAccessToken, accounts, loanToken):
    new_early_access_token = accounts[0].deploy(EarlyAccessToken, "Sovryn Early Access Token", "SEAT")

    with reverts("unauthorized"):
        loanToken.setEarlyAccessToken(new_early_access_token.address, {'from': accounts[1]})