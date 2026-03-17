# Java ezSpec 生成參考

## ezSpec Java 生成（Fluent API）

AI 自動生成的 ezSpec 測試，開發人員**不需要手寫 step definition**：

```java
// tests/acceptance/CreateWorkflowAcceptanceTest.java
// Auto-generated from acceptance.yaml

/**
 * AC1: Create a valid workflow successfully
 * Validates:
 * - then: workflow is created with correct boardId
 * - then: workflow is not deleted (isDeleted = false)
 * - then: workflow has no lanes/stages initially
 * - then: WorkflowCreated event is published
 */
@EzScenario(rule = SUCCESSFUL_CREATION_RULE)
public void should_create_workflow_successfully() {
    feature.newScenario()
        .Given("a user wants to create a workflow for a board", ScenarioEnvironment env -> {
            String workflowId = UUID.randomUUID().toString();
            String boardId = UUID.randomUUID().toString();
            String userId = "test-user";

            env.put("workflowId", workflowId)
               .put("boardId", boardId)
               .put("userId", userId)
               .put("name", "Development Workflow");
        })
        .When("the workflow is created", ScenarioEnvironment env -> {...})
        .ThenSuccess(ScenarioEnvironment env -> {...})
        .And("the workflow should be persisted with correct boardId", ScenarioEnvironment env -> {...})
        .And("the workflow should not be deleted", ScenarioEnvironment env -> {...})
        .And("the workflow should have no root stages initially", ScenarioEnvironment env -> {...})
        .And("a WorkflowCreated event should be published", ScenarioEnvironment env -> {
            await().atMost(timeout: 5, TimeUnit.SECONDS).untilAsserted(() -> {
                assertThat(notifyFakeHandleAllEventsService.getHandledEventsSize()).isEqualTo(expected: 1);
                assertThat(notifyFakeHandleAllEventsService.handledEventTimes(WorkflowEvents.WorkflowCreated.class)).isEqualTo(1);
            });

            WorkflowEvents.WorkflowCreated event = (WorkflowEvents.WorkflowCreated) notifyFakeHandleAllEventsService.getEvent(0);
            var input = env.get("input", CreateWorkflowInput.class);
            assertThat(event.workflowId().value()).isEqualTo(input.workflowId);
            assertThat(event.boardId().value()).isEqualTo(input.boardId);
            assertThat(event.name()).isEqualTo(input.name);
        })
        .Execute();
}
```

### ezSpec 生成規則

1. **方法命名**：`should_{action}_{outcome}` 格式
2. **JavaDoc 註解**：包含 AC ID 和 Validates 項目
3. **Fluent API**：`.Given()` → `.When()` → `.ThenSuccess()` / `.ThenFailure()` → `.And()` → `.Execute()`
4. **Lambda 環境**：使用 `ScenarioEnvironment` 傳遞狀態
5. **事件驗證**：使用 `await().atMost()` 處理非同步事件
        boardId: "board-123"
        name: "Sprint 1"
        operatorId: "user-456"

    - name: "invalidWorkflowInput"
      type: "CreateWorkflowInput"
      value:
        boardId: ""
        name: ""
        operatorId: "user-456"
```

---

## Error Case ezSpec 範例

```java
/**
 * AC2: Reject workflow creation when not authorized
 * Validates:
 * - frame_concerns: WF-FC-AUTH
 */
@EzScenario(rule = AUTHORIZATION_RULE)
public void should_reject_when_not_authorized() {
    feature.newScenario()
        .Given("a user is not authorized to create workflows", ScenarioEnvironment env -> {
            String boardId = UUID.randomUUID().toString();
            String userId = "unauthorized-user";

            // Mock authorization service to deny
            when(authorizationService.hasCapability(userId, "create_workflow", boardId))
                .thenReturn(false);

            env.put("boardId", boardId)
               .put("userId", userId);
        })
        .When("the user attempts to create a workflow", ScenarioEnvironment env -> {
            var input = CreateWorkflowInput.builder()
                .boardId(env.get("boardId", String.class))
                .name("Test Workflow")
                .operatorId(env.get("userId", String.class))
                .build();
            env.put("input", input);

            try {
                useCase.execute(input);
                env.put("error", null);
            } catch (Exception e) {
                env.put("error", e);
            }
        })
        .ThenFailure(AuthorizationException.class, ScenarioEnvironment env -> {
            var error = env.get("error", Exception.class);
            assertThat(error).isInstanceOf(AuthorizationException.class);
        })
        .And("no workflow should be created", ScenarioEnvironment env -> {
            var input = env.get("input", CreateWorkflowInput.class);
            var workflow = workflowRepository.findById(WorkflowId.of(input.workflowId));
            assertThat(workflow).isEmpty();
        })
        .And("no domain event should be published", ScenarioEnvironment env -> {
            assertThat(notifyFakeHandleAllEventsService.getHandledEventsSize()).isEqualTo(0);
        })
        .Execute();
}
```
