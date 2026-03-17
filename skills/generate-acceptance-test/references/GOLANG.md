# Go 測試生成參考

## Go 測試骨架生成（testify）

```go
// tests/acceptance/create_workflow_test.go
// Auto-generated from acceptance.yaml

package acceptance

import (
    "context"
    "testing"
    "sync"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"

    "myapp/application/usecase"
    "myapp/tests/fixtures"
    "myapp/tests/mocks"
)

func TestCreateWorkflow(t *testing.T) {
    // ===== AT1: Successfully create workflow =====
    t.Run("Scenario: Successfully create workflow", func(t *testing.T) {
        t.Run("should create workflow with generated ID", func(t *testing.T) {
            // Given
            user := fixtures.AuthenticatedUser(t)
            board := fixtures.BoardExists(t, "board-123")
            fixtures.MemberOf(t, user.ID, board.ID)

            repo := mocks.NewInMemoryWorkflowRepository()
            eventPub := mocks.NewMockEventPublisher()
            uc := usecase.NewCreateWorkflowUseCase(repo, eventPub)

            // When
            input := usecase.CreateWorkflowInput{
                BoardID:    "board-123",
                Name:       "Sprint 1",
                OperatorID: user.ID,
            }
            result, err := uc.Execute(context.Background(), input)

            // Then
            require.NoError(t, err)
            assert.NotEmpty(t, result.WorkflowID)
        })

        t.Run("should publish WorkflowCreated event", func(t *testing.T) {
            // Given
            user := fixtures.AuthenticatedUser(t)
            fixtures.MemberOf(t, user.ID, "board-123")

            repo := mocks.NewInMemoryWorkflowRepository()
            eventPub := mocks.NewMockEventPublisher()
            uc := usecase.NewCreateWorkflowUseCase(repo, eventPub)

            // When
            _, err := uc.Execute(context.Background(), usecase.CreateWorkflowInput{
                BoardID:    "board-123",
                Name:       "Sprint 1",
                OperatorID: user.ID,
            })

            // Then
            require.NoError(t, err)
            assert.Contains(t, eventPub.Published(), "WorkflowCreatedEvent")
        })
    })

    // ===== AT2: Fail when user is not authorized =====
    t.Run("Scenario: Fail when user is not authorized", func(t *testing.T) {
        t.Run("should return UnauthorizedError", func(t *testing.T) {
            // Given
            user := fixtures.AuthenticatedUser(t)
            // User is NOT a board member

            repo := mocks.NewInMemoryWorkflowRepository()
            eventPub := mocks.NewMockEventPublisher()
            authSvc := mocks.NewDenyAllAuthorizationService()
            uc := usecase.NewCreateWorkflowUseCase(repo, eventPub, authSvc)

            // When
            _, err := uc.Execute(context.Background(), usecase.CreateWorkflowInput{
                BoardID:    "board-123",
                Name:       "Sprint 1",
                OperatorID: user.ID,
            })

            // Then
            assert.ErrorIs(t, err, domain.ErrUnauthorized)
        })
    })

    // ===== AT3: Handle concurrent workflow creation =====
    t.Run("Scenario: Handle concurrent workflow creation", func(t *testing.T) {
        t.Run("should only create one workflow", func(t *testing.T) {
            // Given
            user1 := fixtures.AuthenticatedUser(t)
            user2 := fixtures.AuthenticatedUser(t)
            fixtures.MemberOf(t, user1.ID, "board-123")
            fixtures.MemberOf(t, user2.ID, "board-123")

            repo := mocks.NewInMemoryWorkflowRepository()
            eventPub := mocks.NewMockEventPublisher()
            uc := usecase.NewCreateWorkflowUseCase(repo, eventPub)

            // When: Concurrent execution
            var wg sync.WaitGroup
            results := make(chan error, 2)

            for _, userID := range []string{user1.ID, user2.ID} {
                wg.Add(1)
                go func(uid string) {
                    defer wg.Done()
                    _, err := uc.Execute(context.Background(), usecase.CreateWorkflowInput{
                        BoardID:    "board-123",
                        Name:       "Sprint 1",
                        OperatorID: uid,
                    })
                    results <- err
                }(userID)
            }
            wg.Wait()
            close(results)

            // Then
            var successCount, conflictCount int
            for err := range results {
                if err == nil {
                    successCount++
                } else if errors.Is(err, domain.ErrConflict) {
                    conflictCount++
                }
            }

            assert.Equal(t, 1, successCount)
            assert.Equal(t, 1, conflictCount)
        })
    })
}
```

---

## Go: Ginkgo + Gomega 生成

```go
// tests/acceptance/create_workflow_test.go
// Auto-generated from acceptance.yaml
// Framework: Ginkgo v2 + Gomega

package acceptance_test

import (
    "context"
    "testing"

    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"

    "myapp/application/usecase"
    "myapp/domain"
    "myapp/tests/fixtures"
    "myapp/tests/mocks"
)

func TestCreateWorkflow(t *testing.T) {
    RegisterFailHandler(Fail)
    RunSpecs(t, "Create Workflow Suite")
}

var _ = Describe("Feature: Create Workflow", func() {
    var (
        repo     *mocks.InMemoryWorkflowRepository
        eventPub *mocks.MockEventPublisher
        authSvc  *mocks.MockAuthorizationService
        uc       *usecase.CreateWorkflowUseCase
    )

    BeforeEach(func() {
        repo = mocks.NewInMemoryWorkflowRepository()
        eventPub = mocks.NewMockEventPublisher()
        authSvc = mocks.NewMockAuthorizationService()
        uc = usecase.NewCreateWorkflowUseCase(repo, eventPub, authSvc)
    })

    // ===== AC1: Create a valid workflow successfully =====
    // Trace: CBF-REQ-1
    // Frame Concerns: WF-FC-AUTH, FC2
    Describe("Scenario: Create a valid workflow successfully", Label("smoke", "api", "AC1"), func() {
        var (
            ctx    context.Context
            input  usecase.CreateWorkflowInput
            result *usecase.CreateWorkflowOutput
            err    error
        )

        BeforeEach(func() {
            ctx = context.Background()
        })

        When("a user is authorized and requests to create a workflow", func() {
            BeforeEach(func() {
                // Given
                user := fixtures.AuthenticatedUser()
                authSvc.AllowCapability(user.ID, "create_workflow", "board-001")

                // When
                input = usecase.CreateWorkflowInput{
                    BoardID:    "board-001",
                    Name:       "First workflow",
                    OperatorID: user.ID,
                }
                result, err = uc.Execute(ctx, input)
            })

            It("should succeed", func() {
                Expect(err).NotTo(HaveOccurred())
            })

            It("should create a workflow with the correct boardId", func() {
                Expect(result.WorkflowID).NotTo(BeEmpty())

                workflow, err := repo.FindByID(ctx, result.WorkflowID)
                Expect(err).NotTo(HaveOccurred())
                Expect(workflow.BoardID).To(Equal("board-001"))
            })

            It("should have the correct name", func() {
                workflow, _ := repo.FindByID(ctx, result.WorkflowID)
                Expect(workflow.Name).To(Equal("First workflow"))
            })

            It("should be active (not deleted)", func() {
                workflow, _ := repo.FindByID(ctx, result.WorkflowID)
                Expect(workflow.IsDeleted).To(BeFalse())
            })

            It("should start with empty structure", func() {
                workflow, _ := repo.FindByID(ctx, result.WorkflowID)
                Expect(workflow.Stages).To(BeEmpty())
                Expect(workflow.Lanes).To(BeEmpty())
            })

            It("should publish WorkflowCreated event", func() {
                Eventually(func() int {
                    return eventPub.EventCount()
                }).Should(Equal(1))

                event := eventPub.LastEvent()
                Expect(event).To(BeAssignableToTypeOf(&domain.WorkflowCreatedEvent{}))
            })
        })
    })

    // ===== AC2: Reject when not authorized =====
    // Frame Concerns: WF-FC-AUTH
    Describe("Scenario: Reject workflow creation when not authorized", Label("security", "AC2"), func() {
        When("a user is NOT authorized", func() {
            var err error

            BeforeEach(func() {
                // Given: user is not authorized
                authSvc.DenyAll()

                // When
                input := usecase.CreateWorkflowInput{
                    BoardID:    "board-001",
                    Name:       "Test Workflow",
                    OperatorID: "unauthorized-user",
                }
                _, err = uc.Execute(context.Background(), input)
            })

            It("should return AuthorizationError", func() {
                Expect(err).To(MatchError(domain.ErrUnauthorized))
            })

            It("should not create any workflow", func() {
                count, _ := repo.Count(context.Background())
                Expect(count).To(Equal(0))
            })

            It("should not publish any event", func() {
                Expect(eventPub.EventCount()).To(Equal(0))
            })
        })
    })

    // ===== Table-Driven Tests =====
    DescribeTable("Scenario: Validation errors",
        func(boardID, name, expectedError string) {
            authSvc.AllowAll()

            input := usecase.CreateWorkflowInput{
                BoardID:    boardID,
                Name:       name,
                OperatorID: "user-123",
            }
            _, err := uc.Execute(context.Background(), input)

            Expect(err).To(HaveOccurred())
            Expect(err.Error()).To(ContainSubstring(expectedError))
        },
        Entry("empty boardId", "", "Workflow", "boardId is required"),
        Entry("empty name", "board-001", "", "name is required"),
        Entry("name too long", "board-001", string(make([]byte, 256)), "name exceeds max length"),
    )
})
```
