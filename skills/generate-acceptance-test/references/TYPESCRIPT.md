# TypeScript 測試生成參考

## TypeScript 測試骨架生成

```typescript
// tests/acceptance/CreateWorkflow.spec.ts
// Auto-generated from acceptance.yaml

import { describe, it, beforeEach, expect } from 'vitest';
import { CreateWorkflowUseCase } from '@/application/use-cases/CreateWorkflowUseCase';
import { InMemoryWorkflowRepository } from '@/infrastructure/repositories/InMemoryWorkflowRepository';
import { MockEventPublisher } from '@/tests/mocks/MockEventPublisher';
import { AuthFixture, BoardFixture } from '@/tests/fixtures';

describe('Feature: Create Workflow', () => {
  let useCase: CreateWorkflowUseCase;
  let workflowRepository: InMemoryWorkflowRepository;
  let eventPublisher: MockEventPublisher;

  beforeEach(() => {
    workflowRepository = new InMemoryWorkflowRepository();
    eventPublisher = new MockEventPublisher();
    useCase = new CreateWorkflowUseCase(
      /* dependencies injected */
    );
  });

  // ===== AT1: Successfully create workflow =====
  // Validates: POST1, INV1
  // Tags: @smoke @api
  describe('Scenario: Successfully create workflow', () => {
    it('should create workflow with generated ID', async () => {
      // Given
      const user = AuthFixture.authenticatedUser();
      const board = await BoardFixture.exists('board-123');
      await BoardFixture.memberOf(user.id, board.id);

      // When
      const input = {
        boardId: 'board-123',
        name: 'Sprint 1',
        operatorId: user.id,
      };
      const result = await useCase.execute(input);

      // Then
      expect(result.workflowId).toBeDefined();
      expect(result.workflowId).not.toBeNull();
    });

    it('should publish WorkflowCreated event', async () => {
      // Given
      const user = AuthFixture.authenticatedUser();
      await BoardFixture.memberOf(user.id, 'board-123');

      // When
      await useCase.execute({
        boardId: 'board-123',
        name: 'Sprint 1',
        operatorId: user.id,
      });

      // Then
      expect(eventPublisher.published).toContainEqual(
        expect.objectContaining({ type: 'WorkflowCreatedEvent' })
      );
    });
  });

  // ===== AT2: Fail when user is not authorized =====
  // Validates: XC1 (Authorization)
  // Tags: @security
  describe('Scenario: Fail when user is not authorized', () => {
    it('should throw UnauthorizedError', async () => {
      // Given
      const user = AuthFixture.authenticatedUser();
      // User is NOT a board member

      // When & Then
      await expect(
        useCase.execute({
          boardId: 'board-123',
          name: 'Sprint 1',
          operatorId: user.id,
        })
      ).rejects.toThrow(UnauthorizedError);
    });

    it('should not create any workflow', async () => {
      // Given
      const user = AuthFixture.authenticatedUser();
      const initialCount = await workflowRepository.count();

      // When
      try {
        await useCase.execute({
          boardId: 'board-123',
          name: 'Sprint 1',
          operatorId: user.id,
        });
      } catch (e) {
        // Expected
      }

      // Then
      expect(await workflowRepository.count()).toBe(initialCount);
    });
  });

  // ===== AT3: Handle concurrent workflow creation =====
  // Validates: FC2 (Concurrency)
  // Tags: @concurrency
  describe('Scenario: Handle concurrent workflow creation', () => {
    it('should only create one workflow', async () => {
      // Given
      const user1 = AuthFixture.authenticatedUser('user-1');
      const user2 = AuthFixture.authenticatedUser('user-2');
      await BoardFixture.memberOf(user1.id, 'board-123');
      await BoardFixture.memberOf(user2.id, 'board-123');

      // When: Concurrent execution
      const [result1, result2] = await Promise.allSettled([
        useCase.execute({ boardId: 'board-123', name: 'Sprint 1', operatorId: user1.id }),
        useCase.execute({ boardId: 'board-123', name: 'Sprint 1', operatorId: user2.id }),
      ]);

      // Then
      const fulfilled = [result1, result2].filter(r => r.status === 'fulfilled');
      const rejected = [result1, result2].filter(r => r.status === 'rejected');

      expect(fulfilled.length).toBe(1);
      expect(rejected.length).toBe(1);
      expect(rejected[0].reason).toBeInstanceOf(ConflictError);
    });
  });
});
```

---

## TypeScript: Cucumber.js 生成

```typescript
// tests/acceptance/features/create-workflow.feature
// Auto-generated from acceptance.yaml

Feature: Create Workflow
  As a board member
  I want to create a workflow for my board
  So that I can organize my work

  @smoke @api @AC1
  Scenario: Create a valid workflow successfully
    Given a boardId "board-001" is provided
    And a user "user-123" is authorized to create workflows for that boardId
    When the user requests to create a workflow with name "First workflow"
    Then the request should succeed
    And a Workflow should be created with name "First workflow"
    And the Workflow should belong to Board "board-001"
    And the Workflow should be active
    And a WorkflowCreated event should be published

  @security @AC2
  Scenario: Reject workflow creation when not authorized
    Given a boardId "board-001" is provided
    And a user "unauthorized-user" is NOT authorized to create workflows
    When the user attempts to create a workflow
    Then the request should fail with "AuthorizationError"
    And no Workflow should be created
```

```typescript
// tests/acceptance/steps/create-workflow.steps.ts
// Auto-generated step definitions for Cucumber.js

import { Given, When, Then, Before, After } from '@cucumber/cucumber';
import { expect } from 'chai';
import { CreateWorkflowUseCase } from '@/application/use-cases/CreateWorkflowUseCase';
import { InMemoryWorkflowRepository } from '@/infrastructure/repositories/InMemoryWorkflowRepository';
import { MockEventPublisher } from '@/tests/mocks/MockEventPublisher';
import { MockAuthorizationService } from '@/tests/mocks/MockAuthorizationService';

interface World {
  repository: InMemoryWorkflowRepository;
  eventPublisher: MockEventPublisher;
  authService: MockAuthorizationService;
  useCase: CreateWorkflowUseCase;
  input: { boardId: string; name: string; operatorId: string };
  result: { workflowId: string } | null;
  error: Error | null;
}

Before(function (this: World) {
  this.repository = new InMemoryWorkflowRepository();
  this.eventPublisher = new MockEventPublisher();
  this.authService = new MockAuthorizationService();
  this.useCase = new CreateWorkflowUseCase(
    this.repository,
    this.eventPublisher,
    this.authService
  );
  this.result = null;
  this.error = null;
});

// ===== Given Steps =====

Given('a boardId {string} is provided', function (this: World, boardId: string) {
  this.input = { ...this.input, boardId };
});

Given(
  'a user {string} is authorized to create workflows for that boardId',
  function (this: World, userId: string) {
    this.input = { ...this.input, operatorId: userId };
    this.authService.allowCapability(userId, 'create_workflow', this.input.boardId);
  }
);

Given(
  'a user {string} is NOT authorized to create workflows',
  function (this: World, userId: string) {
    this.input = { ...this.input, operatorId: userId };
    this.authService.denyAll();
  }
);

// ===== When Steps =====

When(
  'the user requests to create a workflow with name {string}',
  async function (this: World, name: string) {
    this.input = { ...this.input, name };
    try {
      this.result = await this.useCase.execute(this.input);
    } catch (e) {
      this.error = e as Error;
    }
  }
);

When('the user attempts to create a workflow', async function (this: World) {
  this.input = { ...this.input, name: 'Test Workflow' };
  try {
    this.result = await this.useCase.execute(this.input);
  } catch (e) {
    this.error = e as Error;
  }
});

// ===== Then Steps =====

Then('the request should succeed', function (this: World) {
  expect(this.error).to.be.null;
  expect(this.result).to.not.be.null;
});

Then('the request should fail with {string}', function (this: World, errorType: string) {
  expect(this.error).to.not.be.null;
  expect(this.error!.name).to.equal(errorType);
});

Then(
  'a Workflow should be created with name {string}',
  async function (this: World, name: string) {
    const workflow = await this.repository.findById(this.result!.workflowId);
    expect(workflow).to.not.be.null;
    expect(workflow!.name).to.equal(name);
  }
);

Then(
  'the Workflow should belong to Board {string}',
  async function (this: World, boardId: string) {
    const workflow = await this.repository.findById(this.result!.workflowId);
    expect(workflow!.boardId).to.equal(boardId);
  }
);

Then('the Workflow should be active', async function (this: World) {
  const workflow = await this.repository.findById(this.result!.workflowId);
  expect(workflow!.isDeleted).to.be.false;
});

Then('a WorkflowCreated event should be published', function (this: World) {
  expect(this.eventPublisher.events).to.have.lengthOf(1);
  expect(this.eventPublisher.events[0].type).to.equal('WorkflowCreated');
});

Then('no Workflow should be created', async function (this: World) {
  const count = await this.repository.count();
  expect(count).to.equal(0);
});
```

### TypeScript: Jest-Cucumber 替代方案

```typescript
// tests/acceptance/create-workflow.spec.ts
// Using jest-cucumber for tighter Jest integration

import { defineFeature, loadFeature } from 'jest-cucumber';
import { CreateWorkflowUseCase } from '@/application/use-cases/CreateWorkflowUseCase';
import { InMemoryWorkflowRepository } from '@/infrastructure/repositories/InMemoryWorkflowRepository';
import { MockEventPublisher } from '@/tests/mocks/MockEventPublisher';
import { MockAuthorizationService } from '@/tests/mocks/MockAuthorizationService';

const feature = loadFeature('./features/create-workflow.feature');

defineFeature(feature, (test) => {
  let repository: InMemoryWorkflowRepository;
  let eventPublisher: MockEventPublisher;
  let authService: MockAuthorizationService;
  let useCase: CreateWorkflowUseCase;
  let input: { boardId: string; name: string; operatorId: string };
  let result: { workflowId: string } | null;
  let error: Error | null;

  beforeEach(() => {
    repository = new InMemoryWorkflowRepository();
    eventPublisher = new MockEventPublisher();
    authService = new MockAuthorizationService();
    useCase = new CreateWorkflowUseCase(repository, eventPublisher, authService);
    result = null;
    error = null;
  });

  test('Create a valid workflow successfully', ({ given, and, when, then }) => {
    given(/^a boardId "(.*)" is provided$/, (boardId: string) => {
      input = { ...input, boardId };
    });

    and(/^a user "(.*)" is authorized to create workflows for that boardId$/, (userId: string) => {
      input = { ...input, operatorId: userId };
      authService.allowCapability(userId, 'create_workflow', input.boardId);
    });

    when(/^the user requests to create a workflow with name "(.*)"$/, async (name: string) => {
      input = { ...input, name };
      try {
        result = await useCase.execute(input);
      } catch (e) {
        error = e as Error;
      }
    });

    then('the request should succeed', () => {
      expect(error).toBeNull();
      expect(result).not.toBeNull();
    });

    and(/^a Workflow should be created with name "(.*)"$/, async (name: string) => {
      const workflow = await repository.findById(result!.workflowId);
      expect(workflow?.name).toBe(name);
    });

    and('a WorkflowCreated event should be published', () => {
      expect(eventPublisher.events).toHaveLength(1);
      expect(eventPublisher.events[0].type).toBe('WorkflowCreated');
    });
  });
});
```
