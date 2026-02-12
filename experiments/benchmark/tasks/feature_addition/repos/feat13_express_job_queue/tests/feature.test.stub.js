/**
 * STUB: Feature tests for Job Queue with Retry.
 *
 * TODO: Implement these tests when the base repo is built.
 *
 * Tests should verify:
 * - POST /api/jobs enqueues a job
 * - GET /api/jobs/:id returns job status
 * - Worker processes jobs from queue
 * - Failed jobs retry up to 3 times
 * - Retries use exponential backoff
 * - Jobs exceeding retries go to dead-letter queue
 * - GET /api/jobs/dead-letter lists failed jobs
 */
