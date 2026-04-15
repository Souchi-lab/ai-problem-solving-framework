export interface RunSummary {
  name: string
  taxonomy: string
  phase: string
  next_role: string
  child_count: number
  has_plan_review: boolean
  has_build_review: boolean
  has_review_review: boolean
  has_improve_review: boolean
  last_modified: number
  priority: 'Now' | 'Next' | 'Later' | 'Unranked'
  priority_reason?: string | null
  human_blocker_active?: boolean
}

export interface ArtifactPreview {
  name: string
  exists: boolean
  size: number
  mtime: number
  preview: string
}

export interface OperatorAction {
  id: string
  label: string
  command: string
  execution_type: 'act' | 'build' | 'rerun' | 'human'
  warning_level: 'none' | 'caution' | 'danger'
  enabled: boolean
  description: string
  primary: boolean
  comment_artifact?: string | null
  requires_comment?: boolean
}

export interface ChildRunSummary {
  name: string
  child_name: string
  phase: string
  next_role: string
  operator_command: string
  primary_action_label: string
  has_children: boolean
}

export interface SpecialistVisibility {
  phase: string
  mode: 'explicit' | 'inferred' | 'unresolved' | 'not_applicable'
  specialist_code: string
  reason: string
  has_gap: boolean
}

export interface ExecutionVisibility {
  role: string
  execution_type: 'cli' | 'human' | 'future-api' | 'not_applicable'
  target: string
  workspace: string
  mode: 'explicit' | 'default' | 'not_applicable'
  reason: string
}

export interface ModelVisibility {
  role: string
  provider: string
  model: string
  mode: 'explicit' | 'default' | 'human' | 'auto' | 'wrapper-backed' | 'unset' | 'not_applicable'
  reason: string
}

export interface AssignmentSummary {
  phase: string
  role: string
  execution: ExecutionVisibility
  model: ModelVisibility
}

export interface JudgeRecommendation {
  decision: 'Adopt' | 'Revise' | 'Reject' | 'Unknown'
  suggested_action_id?: string | null
  suggested_action_label?: string | null
  suggested_return_phase?: string | null
  target_role?: string | null
  target_execution_type?: string | null
  target_provider?: string | null
  target_model?: string | null
  target_specialist_code?: string | null
  target_specialist_mode?: string | null
  confidence: 'low' | 'medium' | 'high'
  rationale: string
  review_verdict?: string | null
  counts_note?: string | null
  critical_count: number
  major_count: number
  minor_count: number
  human_owned_blocker?: boolean
  human_blocker_summary?: string | null
  human_blocker_source?: string | null
  human_actions?: string[]
}

export interface HumanBlockerStatus {
  active: boolean
  summary?: string | null
  source?: string | null
  actions: string[]
}

export interface RunDetail {
  name: string
  taxonomy: string
  phase: string
  next_role: string
  decision_reason: string
  artifacts: ArtifactPreview[]
  operator_command: string
  operator_actions?: OperatorAction[]
  children?: ChildRunSummary[]
  specialist_visibility: SpecialistVisibility
  assignment_summary: AssignmentSummary
  judge_recommendation?: JudgeRecommendation | null
  human_blocker?: HumanBlockerStatus | null
  priority: 'Now' | 'Next' | 'Later' | 'Unranked'
  priority_reason?: string | null
}

export interface MatrixRow {
  name: string
  taxonomy: string
  phase: string
  next_role: string
  priority: 'Now' | 'Next' | 'Later' | 'Unranked'
  priority_reason?: string | null
  plan_action?: OperatorAction | null
  build_action?: OperatorAction | null
  review_action?: OperatorAction | null
  rerun_action?: OperatorAction | null
}

export interface ExecutionResult {
  action_id: string
  command: string
  status: 'SUCCESS' | 'PARTIAL' | 'FAILED' | 'HUMAN'
  exit_code: number
  stdout: string
  stderr: string
}

export interface SaveCommentResult {
  action_id: string
  artifact_name: string
  artifact_path: string
  appended_at: string
}

export interface ActionExecutionRecord {
  id: number
  taxonomy: string
  run_name: string
  action_id: string
  action_type: string
  command: string
  triggered_at: string
  finished_at?: string | null
  result_status: 'PENDING' | 'SUCCESS' | 'PARTIAL' | 'FAILED' | 'HUMAN'
  exit_code?: number | null
  stdout_summary?: string | null
  stderr_summary?: string | null
}

export interface HistoricalExecutionLog {
  execution_id: number
  available: boolean
  stdout?: string | null
  stderr?: string | null
  stdout_summary?: string | null
  stderr_summary?: string | null
}

export interface RerunCommentRecord {
  id: number
  taxonomy: string
  run_name: string
  action_id: string
  execution_id?: number | null
  comment_artifact: string
  comment_body: string
  created_at: string
}

export interface RunHistory {
  latest_execution?: ActionExecutionRecord | null
  latest_rerun_comment?: RerunCommentRecord | null
}

export interface ViewerConfig {
  execution_mode: 'wrapper' | 'provider'
  cli_tool_mode: 'claude' | 'codex' | 'both'
  act_wrapper_backend: 'claude-cli' | 'codex-cli'
  build_wrapper_backend: 'claude-cli' | 'codex-cli'
  config_path: string
  config_exists: boolean
  dotenv_path: string
  dotenv_exists: boolean
  settings_path: string
  framework_root: string
  runs_dir: string
  template_dir: string
  default_openai_model: string
  default_anthropic_model: string
  default_gemini_model: string
  openai_api_key_configured: boolean
  anthropic_api_key_configured: boolean
  gemini_api_key_configured: boolean
  execution_mode_source: 'env' | 'viewer_config' | 'default'
  act_wrapper_backend_source: 'env' | 'viewer_config' | 'default'
  build_wrapper_backend_source: 'env' | 'viewer_config' | 'default'
  build_max_turns: number
  run_detail_refresh_ms: number
}

export interface CodexArtifactUpdate {
  artifact_name: string
  operation: 'propose'
}

export interface CodexBridgeResult {
  status: 'completed' | 'review_required' | 'blocked'
  summary: string
  next_steps: string[]
  suggested_action_id?: string | null
  preset_id: 'finish-after-build' | 'review-and-close'
  role_mode: 'architect' | 'finisher'
  provider: string
  model: string
  artifact_updates: CodexArtifactUpdate[]
}

export interface ModalConfig {
  title: string
  message: string
  onConfirm: (inputValue?: string) => void | Promise<void>
  confirmLabel?: string
  cancelLabel?: string
  tone?: 'default' | 'danger'
  inputLabel?: string
  inputPlaceholder?: string
  inputDefaultValue?: string
  inputRequired?: boolean
}

export interface AgentOSActionFeedback {
  kind: 'running' | 'blocked' | 'success' | 'failure'
  title: string
  detail: string
  actionId?: string | null
}

export interface RunningExecutionState {
  actionId: string
  startedAt: number
}

export interface AutoLoopStatus {
  running: boolean
  stop_pending: boolean
  stop_reason?: string
  last_exit?: number
}

export interface RallyMessage {
  artifact: string
  speaker: string
  title: string
  content: string  // raw markdown; empty string when artifact does not exist
  exists: boolean
}

// ── Agent OS interfaces ─────────────────────────────────────────────────────

export interface RunStateInfo {
  run_id: string
  current_phase: string
  phase_status: string
  current_owner: string
  retry_count: number
  last_error: string
  active_handoff_id: string
  gate_failures: string[]
  phase_entered_at?: string
}

export interface ArtifactEntryInfo {
  artifact_name: string
  artifact_type: string
  owner_role: string
  written_by: string
  status: string
  updated_at: string
  revision: number
  source_handoff_id: string
}

export interface GateResultInfo {
  gate_type: string
  passed: boolean
  reason: string
}

export interface ForceAuditEntryInfo {
  timestamp: string
  command: string
  target_file: string
  role: string
  had_reason: boolean
  reason: string
  override_kind: string
}

export interface RecoveryCheckpointInfo {
  checkpoint_id: string
  phase: string
  phase_status: string
  created_at: string
  related_event_id?: string | null
  summary?: string | null
}

export interface RecoverySnapshotInfo {
  snapshot_id: string
  source_phase: string
  captured_at: string
  file_count: number
  target_paths: string[]
  content_hashes: string[]
}

export interface RecoveryApplyTraceInfo {
  event_id: string
  event_type: string
  timestamp: string
  status: string
  target_kind: string
  target_id: string
  reason?: string | null
  outcome_summary?: string | null
}

export interface SpecialistCandidateItem {
  code: string
  name: string
  score: number
  reason: string
  use_when: string
  path?: string | null
  scope: string
  out_of_scope: string
  evaluation_criteria: string
  is_recommended: boolean
  is_current: boolean
}

export interface SpecialistCandidatesData {
  phase: string
  role: string
  current_mode: string
  current_code: string
  candidates: SpecialistCandidateItem[]
}

export interface AgentOSInfo {
  run_state: RunStateInfo | null
  artifact_manifest: ArtifactEntryInfo[] | null
  gate_results: GateResultInfo[]
  force_audit: ForceAuditEntryInfo[] | null
  recovery_checkpoints: RecoveryCheckpointInfo[]
  recovery_snapshots: RecoverySnapshotInfo[]
  recovery_apply_traces: RecoveryApplyTraceInfo[]
}

export interface CreateSpecialistResult {
  created: boolean
  role: 'Planner' | 'Builder' | 'Critic'
  specialist_code: string
  title: string
  scope: string
  use_when: string
  out_of_scope: string
  evaluation_criteria: string
  relative_path: string
  registry_path: string
  mapping_name: string
  assigned_to_run: boolean
}
