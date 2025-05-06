// A smart contract to work with the DFS manager https://github.com/jcarbonnell/DFS_manager
use near_sdk::borsh::{self, BorshDeserialize, BorshSerialize};
use near_sdk::{near_bindgen, env, log, PanicOnDefault, AccountId, PromiseResult, Gas};
use near_sdk::store::{IterableMap, LookupMap};
use near_sdk::serde::{Deserialize, Serialize};
use schemars::JsonSchema;

#[near_bindgen]
#[derive(PanicOnDefault, BorshDeserialize, BorshSerialize)]
pub struct Contract {
    owner: AccountId,
    transactions: IterableMap<String, Transaction>,
    groups: LookupMap<String, Group>,
    group_members: LookupMap<String, Vec<AccountId>>,
}

// Use a wrapper type for Transaction to handle JsonSchema for AccountId
#[derive(BorshSerialize, BorshDeserialize, Serialize, Deserialize, Clone, JsonSchema)]
#[serde(crate = "near_sdk::serde")]
pub struct Transaction {
    group_id: String,
    user_id: String, // Changed to String to satisfy JsonSchema
    file_hash: String,
    ipfs_hash: String,
}

#[derive(BorshSerialize, BorshDeserialize)]
pub struct Group {
    owner: AccountId,
    group_key: Option<String>, // Will be used in Phase 2
}

#[near_bindgen]
impl Contract {
    #[init]
    pub fn new() -> Self {
        Self {
            owner: env::predecessor_account_id(),
            transactions: IterableMap::new(b"t"),
            groups: LookupMap::new(b"g"),
            group_members: LookupMap::new(b"m"),
        }
    }

    // Step 1: Register a new group
    #[payable]
    pub fn register_group(&mut self, group_id: String) {
        assert!(!self.groups.contains_key(&group_id), "Group already exists");
        let caller = env::predecessor_account_id();
        // Only auth-agent or manager-agent can register a group
        assert!(
            caller == self.owner || caller.as_str().ends_with(".devbot.near"),
            "Only contract owner or devbot agents can register a group"
        );
        let group = Group {
            owner: caller.clone(),
            group_key: None, // will be set in store_group_key
        };
        self.groups.insert(group_id.clone(), group);
        self.group_members.insert(group_id.clone(), Vec::new());
        log!("Group {} registered by {}", group_id, caller);
    }

    // Step 6: Add a member to a group
    #[payable]
    pub fn add_group_member(&mut self, group_id: String, user_id: AccountId) {
        let group = self.groups.get(&group_id).expect("Group not found");
        let caller = env::predecessor_account_id();
        // Only group owner, auth-agent, or nft-agent can add members
        assert!(
            caller == group.owner || caller == self.owner || caller.as_str().ends_with(".devbot.near"),
            "Only group owner, auth-agent, or devbot agents can add members"
        );
        // Check NFT ownership via cross-contract call to 1000fans.testnet
        ext_nft::ext("1000fans.testnet".parse().unwrap())
            .with_static_gas(Gas::from_tgas(10))
            .owns_token(user_id.clone())
            .then(
                Self::ext(env::current_account_id())
                    .with_static_gas(Gas::from_tgas(10))
                    .add_group_member_callback(group_id, user_id)
            );
    }

    #[private]
    pub fn add_group_member_callback(&mut self, group_id: String, user_id: AccountId) {
        assert_eq!(env::promise_results_count(), 1, "Expected one promise result");
        match env::promise_result(0) {
            PromiseResult::Successful(value) => {
                let owns_token: bool = near_sdk::serde_json::from_slice(&value).expect("Invalid response");
                assert!(owns_token, "User does not own a 1000fans token");
                let members = self.group_members.get(&group_id).expect("Group not found");
                let mut members = members.to_vec(); // Clone to own the Vec
                if !members.contains(&user_id) {
                    members.push(user_id.clone());
                    self.group_members.insert(group_id.clone(), members); // Clone group_id
                    log!("User {} added to group {}", user_id, group_id);
                } else {
                    log!("User {} is already a member of group {}", user_id, group_id);
                }
            }
            _ => env::panic_str("Failed to check token ownership"),
        }
    }

    // Step 10: Revoke a group member
    #[payable]
    pub fn revoke_group_member(&mut self, group_id: String, user_id: AccountId) {
        let group = self.groups.get(&group_id).expect("Group not found");
        let caller = env::predecessor_account_id();
        // Only group owner, auth-agent, or nft-agent can revoke members
        assert!(
            caller == group.owner || caller == self.owner || caller.as_str().ends_with(".devbot.near"),
            "Only group owner, auth-agent, or devbot agents can revoke members"
        );
        let members = self.group_members.get(&group_id).expect("Group not found");
        let mut members = members.to_vec(); // Clone to own the Vec
        if let Some(index) = members.iter().position(|x| x == &user_id) {
            members.remove(index);
            self.group_members.insert(group_id.clone(), members); // Clone group_id
            log!("User {} revoked from group {}", user_id, group_id);
        } else {
            log!("User {} is not a member of group {}", user_id, group_id);
        }
    }

    // Steps 6-8: Check if a user is authorized to access a group
    pub fn is_authorized(&self, group_id: String, user_id: AccountId) -> bool {
        let members = self.group_members.get(&group_id).expect("Group not found");
        members.contains(&user_id)
    }

    // Step 3: Record a transaction
    #[payable]
    pub fn record_transaction(
        &mut self,
        group_id: String,
        user_id: AccountId,
        file_hash: String,
        ipfs_hash: String,
    ) -> String {
        assert!(self.groups.contains_key(&group_id), "Group not found");
        assert!(self.is_authorized(group_id.clone(), user_id.clone()), "User not authorized");
        let caller = env::predecessor_account_id();
        assert_eq!(caller, self.owner, "Only devbot agents can record transactions");
        let trans_id = hex::encode(env::sha256(
            &(group_id.clone() + &user_id.to_string() + &file_hash + &ipfs_hash + &env::block_timestamp().to_string()).into_bytes()
        ));
        let tx = Transaction {
            group_id,
            user_id: user_id.to_string(), // Convert to String for serialization
            file_hash,
            ipfs_hash,
        };
        self.transactions.insert(trans_id.clone(), tx);
        log!("Transaction recorded: {}", trans_id);
        trans_id
    }

    // Retrieve a transaction
    pub fn get_transaction(&self, trans_id: String) -> Option<Transaction> {
        self.transactions.get(&trans_id).cloned()
    }

    // Mock token ownership (to be replaced)
    pub fn check_token_ownership(&self, account_id: AccountId) -> bool {
        log!("Mock check: assuming {} owns a token", account_id);
        true
    }
}

// External interface for cross-contract calls
#[near_sdk::ext_contract(ext_nft)]
pub trait ExtNft {
    fn owns_token(&self, account_id: AccountId) -> bool;
}

#[cfg(test)]
mod tests {
    use super::*;
    use near_sdk::test_utils::{VMContextBuilder, get_logs};
    use near_sdk::testing_env;
    use near_parameters::vm::Config as VMConfig;
    use near_sdk::RuntimeFeesConfig;

    fn setup_context(predecessor: AccountId) -> VMContextBuilder {
        let mut context = VMContextBuilder::new();
        context
            .predecessor_account_id(predecessor)
            .current_account_id("devbot.near".parse().unwrap());
        context
    }

    #[test]
    fn test_register_group() {
        let context = setup_context("auth-agent.devbot.near".parse().unwrap());
        testing_env!(context.build());
        let mut contract = Contract::new();
        contract.register_group("group1".to_string());
        assert!(contract.groups.contains_key(&"group1".to_string()));
        assert_eq!(get_logs(), vec!["Group group1 registered by auth-agent.devbot.near"]);
    }

    #[test]
    #[should_panic(expected = "Only contract owner or devbot agents can register a group")]
    fn test_register_group_unauthorized() {
        let context = setup_context("random.near".parse().unwrap());
        testing_env!(context.build());
        let mut contract = Contract::new();
        contract.register_group("group1".to_string());
    }

    #[test]
    fn test_add_group_member() {
        let context = setup_context("auth-agent.devbot.near".parse().unwrap());
        testing_env!(context.build());
        let mut contract = Contract::new();
        contract.register_group("group1".to_string());

        // Mock cross-contract call result
        testing_env!(
            context.build(),
            VMConfig::test(),
            RuntimeFeesConfig::test(),
            HashMap::new(),
            vec![PromiseResult::Successful(serde_json::to_vec(&true).unwrap())]
        );
        contract.add_group_member("group1".to_string(), "user.near".parse().unwrap());
        assert!(contract.is_authorized("group1".to_string(), "user.near".parse().unwrap()));
        assert_eq!(get_logs().last().unwrap(), "User user.near added to group group1");
    }

    #[test]
    #[should_panic(expected = "User does not own a 1000fans token")]
    fn test_add_group_member_no_nft() {
        let context = setup_context("auth-agent.devbot.near".parse().unwrap());
        testing_env!(context.build());
        let mut contract = Contract::new();
        contract.register_group("group1".to_string());

        // Mock cross-contract call result (no NFT)
        testing_env!(
            context.build(),
            VMConfig::test(),
            RuntimeFeesConfig::test(),
            HashMap::new(),
            vec![PromiseResult::Successful(serde_json::to_vec(&false).unwrap())]
        );
        contract.add_group_member("group1".to_string(), "user.near".parse().unwrap());
    }

    #[test]
    fn test_revoke_group_member() {
        let context = setup_context("auth-agent.devbot.near".parse().unwrap());
        testing_env!(context.build());
        let mut contract = Contract::new();
        contract.register_group("group1".to_string());

        // Add member
        testing_env!(
            context.build(),
            VMConfig::test(),
            RuntimeFeesConfig::test(),
            HashMap::new(),
            vec![PromiseResult::Successful(serde_json::to_vec(&true).unwrap())]
        );
        contract.add_group_member("group1".to_string(), "user.near".parse().unwrap());

        // Revoke member
        testing_env!(context.build());
        contract.revoke_group_member("group1".to_string(), "user.near".parse().unwrap());
        assert!(!contract.is_authorized("group1".to_string(), "user.near".parse().unwrap()));
        assert_eq!(get_logs().last().unwrap(), "User user.near revoked from group user.near");
    }

    #[test]
    fn test_is_authorized() {
        let context = setup_context("auth-agent.devbot.near".parse().unwrap());
        testing_env!(context.build());
        let mut contract = Contract::new();
        contract.register_group("group1".to_string());

        // Add member
        testing_env!(
            context.build(),
            VMConfig::test(),
            RuntimeFeesConfig::test(),
            HashMap::new(),
            vec![PromiseResult::Successful(serde_json::to_vec(&true).unwrap())]
        );
        contract.add_group_member("group1".to_string(), "user.near".parse().unwrap());

        assert!(contract.is_authorized("group1".to_string(), "user.near".parse().unwrap()));
        assert!(!contract.is_authorized("group1".to_string(), "other.near".parse().unwrap()));
    }

    #[test]
    fn test_record_transaction() {
        let context = setup_context("auth-agent.devbot.near".parse().unwrap());
        testing_env!(context.build());
        let mut contract = Contract::new();
        contract.register_group("group1".to_string());

        // Add member
        testing_env!(
            context.build(),
            VMConfig::test(),
            RuntimeFeesConfig::test(),
            HashMap::new(),
            vec![PromiseResult::Successful(serde_json::to_vec(&true).unwrap())]
        );
        contract.add_group_member("group1".to_string(), "user.near".parse().unwrap());

        // Record transaction
        let context = setup_context("devbot.near".parse().unwrap());
        testing_env!(context.build());
        let trans_id = contract.record_transaction(
            "group1".to_string(),
            "user.near".parse().unwrap(),
            "abc123".to_string(),
            "QmTest".to_string(),
        );
        assert_eq!(get_logs().last().unwrap(), &format!("Transaction recorded: {}", trans_id));
        let tx = contract.get_transaction(trans_id.clone()).unwrap();
        assert_eq!(tx.group_id, "group1");
        assert_eq!(tx.ipfs_hash, "QmTest");
    }

    #[test]
    fn test_check_token_ownership() {
        let context = setup_context("devbot.near".parse().unwrap());
        testing_env!(context.build());
        let contract = Contract::new();
        let result = contract.check_token_ownership("user.near".parse().unwrap());
        assert_eq!(result, true);
        assert_eq!(get_logs(), vec!["Mock check: assuming user.near owns a token"]);
    }
}