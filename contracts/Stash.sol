// SPDX-License-Identifier: AGPL-3.0

pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

import {SafeERC20,IERC20} from "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";

interface IStrategy {
    function want() external view returns(address);
}

contract Stash {
    using SafeERC20 for IERC20;

    address constant public owner = 0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52;

    event StrategyApproved(address strategy);
    event StrategyRevoked(address strategy);

    function approveStrategy(address strategy) external {
        require(msg.sender == owner, "!Authorized");
        IERC20 token = IERC20(IStrategy(strategy).want());
        token.approve(strategy, uint256(-1));
        emit StrategyApproved(strategy);
    }

    function revokeStrategy(address strategy) external {
        require(msg.sender == owner, "!Authorized");
        IERC20 token = IERC20(IStrategy(strategy).want());
        if (token.allowance(address(this), strategy) > 0) {
            token.approve(strategy, 0);
            emit StrategyRevoked(strategy);
        }
    }

    function sweep(IERC20 token) external {
        require(msg.sender == owner, "!Authorized");
        token.safeTransfer(owner, token.balanceOf(address(this)));
    }
}