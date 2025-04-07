// a smart contract to work with the DFS manager https://github.com/jcarbonnell/DFS_manager
use near_sdk::borsh::{self, BorshDeserialize, BorshSerialize};
use near_sdk::{near, env, log, PanicOnDefault, AccountId};
use near_sdk::store::IterableMap;
use serde::Serialize;

#[near(contract_state)]
#[derive(PanicOnDefault)]
pub struct Contract {
    owner: AccountId,
    transactions: IterableMap<String, Transaction>,
}

#[derive(BorshSerialize, BorshDeserialize, Serialize, Clone)]
pub struct Transaction {
    group_id: String,
    user_id: AccountId,
    file_hash: String,
    ipfs_hash: String,
}

#[near]
impl Contract {
    #[init]
    pub fn new() -> Self {
        Self {
            owner: "devbot.near".parse().expect("Invalid account ID"),
            transactions: IterableMap::new(b"t"),
        }
    }

    #[payable]
    pub fn record_transaction(
        &mut self,
        group_id: String,
        user_id: AccountId,
        file_hash: String,
        ipfs_hash: String,
    ) -> String {
        assert_eq!(env::predecessor_account_id(), self.owner, "Only devbot.near can record transactions");
        let trans_id = hex::encode(env::sha256(
            &(group_id.clone() + &user_id.to_string() + &file_hash + &ipfs_hash + &env::block_timestamp().to_string()).into_bytes()
        ));
        let tx = Transaction { group_id, user_id, file_hash, ipfs_hash };
        self.transactions.insert(trans_id.clone(), tx);
        log!("Transaction recorded: {}", trans_id);
        trans_id
    }

    pub fn get_transaction(&self, trans_id: String) -> Option<Transaction> {
        self.transactions.get(&trans_id).cloned()
    }

    pub fn check_token_ownership(&self, account_id: AccountId) -> bool {
        // Mock response: assume ownership for testing
        log!("Mock check: assuming {} owns a token", account_id);
        true
    }    
}

#[cfg(test)]
mod tests {
    use super::*;
    use near_sdk::test_utils::{VMContextBuilder, get_logs};
    use near_sdk::testing_env;

    #[test]
    fn test_record_transaction() {
        let mut context = VMContextBuilder::new();
        context.predecessor_account_id("devbot.near".parse().unwrap());
        testing_env!(context.build());
        let mut contract = Contract::new();
        let trans_id = contract.record_transaction(
            "group1".to_string(),
            "user.near".parse().unwrap(),
            "abc123".to_string(),
            "QmTest".to_string(),
        );
        assert_eq!(get_logs(), vec![format!("Transaction recorded: {}", trans_id)]);
        let tx = contract.get_transaction(trans_id.clone()).unwrap();
        assert_eq!(tx.group_id, "group1");
        assert_eq!(tx.ipfs_hash, "QmTest");
    }

    #[test]
    fn test_check_token_ownership() {
        let context = VMContextBuilder::new();
        testing_env!(context.build());
        let contract = Contract::new();
        let result = contract.check_token_ownership("user.near".parse().unwrap());
        assert_eq!(result, true);
        assert_eq!(get_logs(), vec!["Mock check: assuming user.near owns a token"]);
    }
}