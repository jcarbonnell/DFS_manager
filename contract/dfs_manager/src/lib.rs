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
    #[cfg(test)]
    mock_promise_result: Option<bool>, // Test-only field to mock promise result
}

#[derive(BorshSerialize, BorshDeserialize, Serialize, Deserialize, Clone, JsonSchema)]
#[serde(crate = "near_sdk::serde")]
pub struct Transaction {
    group_id: String,
    user_id: String,
    file_hash: String,
    ipfs_hash: String,
}

#[derive(BorshSerialize, BorshDeserialize, Clone)]
pub struct Group {
    owner: AccountId,
    group_key: Option<String>, // Stores the symmetric group key
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
            #[cfg(test)]
            mock_promise_result: None,
        }
    }

    #[cfg(test)]
    pub fn set_mock_promise_result(&mut self, result: bool) {
        self.mock_promise_result = Some(result);
    }

    // Step 1: Register a new group
    #[payable]
    pub fn register_group(&mut self, group_id: String) {
        assert!(!self.groups.contains_key(&group_id), "Group already exists");
        let caller = env::predecessor_account_id();
        assert!(
            caller == self.owner || caller.as_str().ends_with(".devbot.near"),
            "Only contract owner or devbot agents can register a group"
        );
        let group = Group {
            owner: caller.clone(),
            group_key: None,
        };
        self.groups.insert(group_id.clone(), group);
        self.group_members.insert(group_id.clone(), Vec::new());
        log!("Group {} registered by {}", group_id, caller);
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
        assert!(
            caller == self.owner || caller.as_str().ends_with(".devbot.near"),
            "Only devbot agents can record transactions"
        );
        let trans_id = hex::encode(env::sha256(
            &(group_id.clone() + &user_id.to_string() + &file_hash + &ipfs_hash + &env::block_timestamp().to_string()).into_bytes()
        ));
        let tx = Transaction {
            group_id,
            user_id: user_id.to_string(),
            file_hash,
            ipfs_hash,
        };
        self.transactions.insert(trans_id.clone(), tx);
        log!("Transaction recorded: {}", trans_id);
        trans_id
    }

    // Step 6: Add a member to a group
    #[payable]
    pub fn add_group_member(&mut self, group_id: String, user_id: AccountId) {
        let group = self.groups.get(&group_id).expect("Group not found");
        let caller = env::predecessor_account_id();
        assert!(
            caller == group.owner || caller == self.owner || caller.as_str().ends_with(".devbot.near"),
            "Only group owner, auth-agent, or devbot agents can add members"
        );
        // Step 4: Check token ownership via cross-contract call to 1000fans.testnet
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
        #[cfg(test)]
        {
            if let Some(owns_token) = self.mock_promise_result {
                assert!(owns_token, "User does not own a 1000fans token");
                let members = self.group_members.get(&group_id).expect("Group not found");
                let mut members = members.to_vec();
                if !members.contains(&user_id) {
                    members.push(user_id.clone());
                    self.group_members.insert(group_id.clone(), members);
                    log!("User {} added to group {}", user_id, group_id);
                } else {
                    log!("User {} is already a member of group {}", user_id, group_id);
                }
                return;
            }
        }

        assert_eq!(env::promise_results_count(), 1, "Expected one promise result");
        match env::promise_result(0) {
            PromiseResult::Successful(value) => {
                let owns_token: bool = near_sdk::serde_json::from_slice(&value).expect("Invalid response");
                assert!(owns_token, "User does not own a 1000fans token");
                let members = self.group_members.get(&group_id).expect("Group not found");
                let mut members = members.to_vec();
                if !members.contains(&user_id) {
                    members.push(user_id.clone());
                    self.group_members.insert(group_id.clone(), members);
                    log!("User {} added to group {}", user_id, group_id);
                } else {
                    log!("User {} is already a member of group {}", user_id, group_id);
                }
            }
            _ => env::panic_str("Failed to check token ownership"),
        }
    }

    // Step 6: Revoke a group member
    #[payable]
    pub fn revoke_group_member(&mut self, group_id: String, user_id: AccountId) {
        let group = self.groups.get(&group_id).expect("Group not found");
        let caller = env::predecessor_account_id();
        assert!(
            caller == group.owner || caller == self.owner || caller.as_str().ends_with(".devbot.near"),
            "Only group owner, auth-agent, or devbot agents can revoke members"
        );
        let members = self.group_members.get(&group_id).expect("Group not found");
        let mut members = members.to_vec();
        if let Some(index) = members.iter().position(|x| x == &user_id) {
            members.remove(index);
            self.group_members.insert(group_id.clone(), members);
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

    // Step 6: Store the group key (called by storage-agent)
    #[payable]
    pub fn store_group_key(&mut self, group_id: String, key: String) {
        let group = self.groups.get(&group_id).expect("Group not found");
        let caller = env::predecessor_account_id();
        assert!(
            caller == group.owner || caller == self.owner || caller.as_str().ends_with(".devbot.near"),
            "Only group owner or devbot agents can store group key"
        );
        assert!(!key.is_empty(), "Group key cannot be empty");
        let mut group = group.clone();
        group.group_key = Some(key.clone());
        self.groups.insert(group_id.clone(), group);
        log!("Group key stored for group {}", group_id);
    }

    // Step 6: Retrieve the group key (called by storage-agent or auth-agent)
    pub fn get_group_key(&self, group_id: String, user_id: AccountId) -> String {
        let group = self.groups.get(&group_id).expect("Group not found");
        assert!(self.is_authorized(group_id.clone(), user_id.clone()), "User not authorized");
        let caller = env::predecessor_account_id();
        assert!(
            caller == group.owner || caller == self.owner || caller.as_str().ends_with(".devbot.near") || caller == user_id,
            "Only group owner, devbot agents, or the user can retrieve the group key"
        );
        group.group_key.clone().expect("No group key set")
    }

    // Step 7: Retrieve a transaction
    pub fn get_transaction(&self, trans_id: String) -> Option<Transaction> {
        self.transactions.get(&trans_id).cloned()
    }

    // Step 15: Rotate the group key (called by storage-agent)
    #[payable]
    pub fn rotate_group_key(&mut self, group_id: String, new_key: String) {
        let group = self.groups.get(&group_id).expect("Group not found");
        let caller = env::predecessor_account_id();
        assert!(
            caller == group.owner || caller == self.owner || caller.as_str().ends_with(".devbot.near"),
            "Only group owner or devbot agents can rotate group key"
        );
        assert!(!new_key.is_empty(), "New group key cannot be empty");
        let mut group = group.clone();
        group.group_key = Some(new_key.clone());
        self.groups.insert(group_id.clone(), group);
        log!("Group key rotated for group {}", group_id);
        // Note: Updating IPFS files will be handled by update_group_files
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
    use near_sdk::{testing_env, NearToken};

    fn setup_context(predecessor: AccountId) -> VMContextBuilder {
        let mut context = VMContextBuilder::new();
        context
            .predecessor_account_id(predecessor)
            .current_account_id("devbot.near".parse().unwrap())
            .account_balance(NearToken::from_yoctonear(100_000_000_000_000_000_000_000_000))
            .attached_deposit(NearToken::from_yoctonear(1_000_000_000_000_000_000_000_000));
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
        // Initialize contract with devbot.near as owner
        let context = setup_context("devbot.near".parse().unwrap());
        testing_env!(context.build());
        let mut contract = Contract::new();

        // Try to register group with random.near
        let context = setup_context("random.near".parse().unwrap());
        testing_env!(context.build());
        contract.register_group("group1".to_string());
    }

    #[test]
    fn test_add_group_member() {
        let context = setup_context("auth-agent.devbot.near".parse().unwrap());
        testing_env!(context.build());
        let mut contract = Contract::new();
        contract.register_group("group1".to_string());

        // Trigger cross-contract call
        testing_env!(context.build());
        contract.add_group_member("group1".to_string(), "user.near".parse().unwrap());

        // Simulate successful promise result
        let context = setup_context("devbot.near".parse().unwrap());
        testing_env!(context.build());
        contract.set_mock_promise_result(true);
        contract.add_group_member_callback("group1".to_string(), "user.near".parse().unwrap());

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

        // Trigger cross-contract call
        testing_env!(context.build());
        contract.add_group_member("group1".to_string(), "user.near".parse().unwrap());

        // Simulate failed promise result
        let context = setup_context("devbot.near".parse().unwrap());
        testing_env!(context.build());
        contract.set_mock_promise_result(false);
        contract.add_group_member_callback("group1".to_string(), "user.near".parse().unwrap());
    }

    #[test]
    fn test_revoke_group_member() {
        let context = setup_context("auth-agent.devbot.near".parse().unwrap());
        testing_env!(context.build());
        let mut contract = Contract::new();
        contract.register_group("group1".to_string());
        // Add member
        testing_env!(context.build());
        contract.add_group_member("group1".to_string(), "user.near".parse().unwrap());
        let context = setup_context("devbot.near".parse().unwrap());
        testing_env!(context.build());
        contract.set_mock_promise_result(true);
        contract.add_group_member_callback("group1".to_string(), "user.near".parse().unwrap());
        // Revoke member with group owner (auth-agent.devbot.near)
        let context = setup_context("auth-agent.devbot.near".parse().unwrap());
        testing_env!(context.build());
        contract.revoke_group_member("group1".to_string(), "user.near".parse().unwrap());
        assert!(!contract.is_authorized("group1".to_string(), "user.near".parse().unwrap()));
        assert_eq!(get_logs().last().unwrap(), "User user.near revoked from group group1");
    }

    #[test]
    fn test_is_authorized() {
        let context = setup_context("auth-agent.devbot.near".parse().unwrap());
        testing_env!(context.build());
        let mut contract = Contract::new();
        contract.register_group("group1".to_string());
        // Add member
        testing_env!(context.build());
        contract.add_group_member("group1".to_string(), "user.near".parse().unwrap());
        let context = setup_context("devbot.near".parse().unwrap());
        testing_env!(context.build());
        contract.set_mock_promise_result(true);
        contract.add_group_member_callback("group1".to_string(), "user.near".parse().unwrap());
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
        testing_env!(context.build());
        contract.add_group_member("group1".to_string(), "user.near".parse().unwrap());
        let context = setup_context("devbot.near".parse().unwrap());
        testing_env!(context.build());
        contract.set_mock_promise_result(true);
        contract.add_group_member_callback("group1".to_string(), "user.near".parse().unwrap());
        // Record transaction with auth-agent.devbot.near
        let context = setup_context("auth-agent.devbot.near".parse().unwrap());
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
    fn test_store_group_key() {
        let context = setup_context("storage-agent.devbot.near".parse().unwrap());
        testing_env!(context.build());
        let mut contract = Contract::new();
        contract.register_group("group1".to_string());
        contract.store_group_key("group1".to_string(), "symmetric_key_123".to_string());
        let group = contract.groups.get(&"group1".to_string()).expect("Group not found");
        assert_eq!(group.group_key, Some("symmetric_key_123".to_string()));
        assert_eq!(get_logs().last().unwrap(), "Group key stored for group group1");
    }

    #[test]
    #[should_panic(expected = "Only group owner or devbot agents can store group key")]
    fn test_store_group_key_unauthorized() {
        let context = setup_context("auth-agent.devbot.near".parse().unwrap()); // Authorized account registers group
        testing_env!(context.build());
        let mut contract = Contract::new();
        contract.register_group("group1".to_string());
        let context = setup_context("random.near".parse().unwrap()); // Unauthorized caller
        testing_env!(context.build());
        contract.store_group_key("group1".to_string(), "symmetric_key_123".to_string());
    }

    #[test]
    #[should_panic(expected = "Group key cannot be empty")]
    fn test_store_group_key_empty() {
        let context = setup_context("storage-agent.devbot.near".parse().unwrap());
        testing_env!(context.build());
        let mut contract = Contract::new();
        contract.register_group("group1".to_string());
        contract.store_group_key("group1".to_string(), "".to_string());
    }

    #[test]
    fn test_get_group_key() {
        let context = setup_context("auth-agent.devbot.near".parse().unwrap());
        testing_env!(context.build());
        let mut contract = Contract::new();
        contract.register_group("group1".to_string());
        contract.store_group_key("group1".to_string(), "symmetric_key_123".to_string());
        contract.add_group_member("group1".to_string(), "user.near".parse().unwrap());
        let context = setup_context("devbot.near".parse().unwrap());
        testing_env!(context.build());
        contract.set_mock_promise_result(true);
        contract.add_group_member_callback("group1".to_string(), "user.near".parse().unwrap());
        let context = setup_context("user.near".parse().unwrap());
        testing_env!(context.build());
        let key = contract.get_group_key("group1".to_string(), "user.near".parse().unwrap());
        assert_eq!(key, "symmetric_key_123");
    }

    #[test]
    #[should_panic(expected = "User not authorized")]
    fn test_get_group_key_unauthorized() {
        let context = setup_context("auth-agent.devbot.near".parse().unwrap());
        testing_env!(context.build());
        let mut contract = Contract::new();
        contract.register_group("group1".to_string());
        contract.store_group_key("group1".to_string(), "symmetric_key_123".to_string());
        let context = setup_context("user.near".parse().unwrap());
        testing_env!(context.build());
        contract.get_group_key("group1".to_string(), "user.near".parse().unwrap());
    }

    #[test]
    #[should_panic(expected = "Only group owner, devbot agents, or the user can retrieve the group key")]
    fn test_get_group_key_wrong_caller() {
        let context = setup_context("auth-agent.devbot.near".parse().unwrap());
        testing_env!(context.build());
        let mut contract = Contract::new();
        contract.register_group("group1".to_string());
        contract.store_group_key("group1".to_string(), "symmetric_key_123".to_string());
        contract.add_group_member("group1".to_string(), "user.near".parse().unwrap());
        let context = setup_context("devbot.near".parse().unwrap());
        testing_env!(context.build());
        contract.set_mock_promise_result(true);
        contract.add_group_member_callback("group1".to_string(), "user.near".parse().unwrap());
        let context = setup_context("other.near".parse().unwrap());
        testing_env!(context.build());
        contract.get_group_key("group1".to_string(), "user.near".parse().unwrap());
    }

    #[test]
    fn test_rotate_group_key() {
        let context = setup_context("storage-agent.devbot.near".parse().unwrap());
        testing_env!(context.build());
        let mut contract = Contract::new();
        contract.register_group("group1".to_string());
        contract.store_group_key("group1".to_string(), "symmetric_key_123".to_string());
        contract.rotate_group_key("group1".to_string(), "new_symmetric_key_456".to_string());
        let group = contract.groups.get(&"group1".to_string()).expect("Group not found");
        assert_eq!(group.group_key, Some("new_symmetric_key_456".to_string()));
        assert_eq!(get_logs().last().unwrap(), "Group key rotated for group group1");
    }

    #[test]
    #[should_panic(expected = "Only group owner or devbot agents can rotate group key")]
    fn test_rotate_group_key_unauthorized() {
        let context = setup_context("auth-agent.devbot.near".parse().unwrap()); // Authorized account registers group
        testing_env!(context.build());
        let mut contract = Contract::new();
        contract.register_group("group1".to_string());
        contract.store_group_key("group1".to_string(), "symmetric_key_123".to_string());
        let context = setup_context("random.near".parse().unwrap()); // Unauthorized caller
        testing_env!(context.build());
        contract.rotate_group_key("group1".to_string(), "new_symmetric_key_456".to_string());
    }

    #[test]
    #[should_panic(expected = "New group key cannot be empty")]
    fn test_rotate_group_key_empty() {
        let context = setup_context("storage-agent.devbot.near".parse().unwrap());
        testing_env!(context.build());
        let mut contract = Contract::new();
        contract.register_group("group1".to_string());
        contract.store_group_key("group1".to_string(), "symmetric_key_123".to_string());
        contract.rotate_group_key("group1".to_string(), "".to_string());
    }
}