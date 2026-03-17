# Rust 測試生成參考

## Rust: cucumber-rs 生成

```rust
// tests/acceptance/create_workflow.rs
// Auto-generated from acceptance.yaml
// Framework: cucumber-rs

use cucumber::{given, when, then, World};
use async_trait::async_trait;
use std::sync::Arc;
use tokio::sync::Mutex;

use myapp::application::use_cases::{CreateWorkflowUseCase, CreateWorkflowInput, CreateWorkflowOutput};
use myapp::domain::{WorkflowRepository, EventPublisher, AuthorizationService};
use myapp::domain::errors::DomainError;
use myapp::infrastructure::repositories::InMemoryWorkflowRepository;
use myapp::tests::mocks::{MockEventPublisher, MockAuthorizationService};

// ===== World Definition =====

#[derive(Debug, World)]
#[world(init = Self::new)]
pub struct CreateWorkflowWorld {
    repository: Arc<Mutex<InMemoryWorkflowRepository>>,
    event_publisher: Arc<Mutex<MockEventPublisher>>,
    auth_service: Arc<Mutex<MockAuthorizationService>>,
    input: Option<CreateWorkflowInput>,
    result: Option<Result<CreateWorkflowOutput, DomainError>>,
}

impl CreateWorkflowWorld {
    fn new() -> Self {
        Self {
            repository: Arc::new(Mutex::new(InMemoryWorkflowRepository::new())),
            event_publisher: Arc::new(Mutex::new(MockEventPublisher::new())),
            auth_service: Arc::new(Mutex::new(MockAuthorizationService::new())),
            input: None,
            result: None,
        }
    }
}

// ===== AC1: Create a valid workflow successfully =====
// Trace: CBF-REQ-1
// Frame Concerns: WF-FC-AUTH, FC2

#[given(expr = "a boardId {string} is provided")]
async fn given_board_id(world: &mut CreateWorkflowWorld, board_id: String) {
    world.input = Some(CreateWorkflowInput {
        board_id,
        name: String::new(),
        operator_id: String::new(),
    });
}

#[given(expr = "a user {string} is authorized to create workflows for that boardId")]
async fn given_user_authorized(world: &mut CreateWorkflowWorld, user_id: String) {
    let mut input = world.input.take().unwrap();
    input.operator_id = user_id.clone();
    world.input = Some(input);

    let mut auth = world.auth_service.lock().await;
    auth.allow_capability(&user_id, "create_workflow", &world.input.as_ref().unwrap().board_id);
}

#[given(expr = "a user {string} is NOT authorized to create workflows")]
async fn given_user_not_authorized(world: &mut CreateWorkflowWorld, user_id: String) {
    let mut input = world.input.take().unwrap();
    input.operator_id = user_id;
    world.input = Some(input);

    let mut auth = world.auth_service.lock().await;
    auth.deny_all();
}

#[when(expr = "the user requests to create a workflow with name {string}")]
async fn when_create_workflow(world: &mut CreateWorkflowWorld, name: String) {
    let mut input = world.input.take().unwrap();
    input.name = name;
    world.input = Some(input.clone());

    let use_case = CreateWorkflowUseCase::new(
        world.repository.clone(),
        world.event_publisher.clone(),
        world.auth_service.clone(),
    );

    world.result = Some(use_case.execute(input).await);
}

#[when("the user attempts to create a workflow")]
async fn when_attempt_create(world: &mut CreateWorkflowWorld) {
    let mut input = world.input.take().unwrap();
    input.name = "Test Workflow".to_string();
    world.input = Some(input.clone());

    let use_case = CreateWorkflowUseCase::new(
        world.repository.clone(),
        world.event_publisher.clone(),
        world.auth_service.clone(),
    );

    world.result = Some(use_case.execute(input).await);
}

#[then("the request should succeed")]
async fn then_success(world: &mut CreateWorkflowWorld) {
    assert!(world.result.as_ref().unwrap().is_ok(), "Expected success but got error");
}

#[then(expr = "the request should fail with {string}")]
async fn then_fail_with(world: &mut CreateWorkflowWorld, error_type: String) {
    let result = world.result.as_ref().unwrap();
    assert!(result.is_err(), "Expected error but got success");

    let err = result.as_ref().unwrap_err();
    match error_type.as_str() {
        "AuthorizationError" => assert!(matches!(err, DomainError::Unauthorized(_))),
        "ValidationError" => assert!(matches!(err, DomainError::Validation(_))),
        _ => panic!("Unknown error type: {}", error_type),
    }
}

#[then(expr = "a Workflow should be created with name {string}")]
async fn then_workflow_created(world: &mut CreateWorkflowWorld, name: String) {
    let result = world.result.as_ref().unwrap().as_ref().unwrap();
    let repo = world.repository.lock().await;
    let workflow = repo.find_by_id(&result.workflow_id).await.unwrap().unwrap();

    assert_eq!(workflow.name, name);
}

#[then(expr = "the Workflow should belong to Board {string}")]
async fn then_workflow_belongs_to_board(world: &mut CreateWorkflowWorld, board_id: String) {
    let result = world.result.as_ref().unwrap().as_ref().unwrap();
    let repo = world.repository.lock().await;
    let workflow = repo.find_by_id(&result.workflow_id).await.unwrap().unwrap();

    assert_eq!(workflow.board_id, board_id);
}

#[then("the Workflow should be active")]
async fn then_workflow_active(world: &mut CreateWorkflowWorld) {
    let result = world.result.as_ref().unwrap().as_ref().unwrap();
    let repo = world.repository.lock().await;
    let workflow = repo.find_by_id(&result.workflow_id).await.unwrap().unwrap();

    assert!(!workflow.is_deleted);
}

#[then("a WorkflowCreated event should be published")]
async fn then_event_published(world: &mut CreateWorkflowWorld) {
    let publisher = world.event_publisher.lock().await;
    assert_eq!(publisher.event_count(), 1);
    assert!(publisher.has_event_type("WorkflowCreated"));
}

#[then("no Workflow should be created")]
async fn then_no_workflow(world: &mut CreateWorkflowWorld) {
    let repo = world.repository.lock().await;
    assert_eq!(repo.count().await, 0);
}

// ===== Test Runner =====

#[tokio::main]
async fn main() {
    CreateWorkflowWorld::run("tests/features/create-workflow.feature").await;
}
```

### Rust: Cargo.toml 依賴

```toml
[dev-dependencies]
cucumber = { version = "0.20", features = ["macros"] }
async-trait = "0.1"
tokio = { version = "1", features = ["full", "test-util"] }
```
