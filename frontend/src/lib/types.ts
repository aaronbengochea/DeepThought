export interface User {
  email: string;
  name: string;
  created_at: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface SignInResponse {
  token: string;
  email: string;
}

export interface Pair {
  pair_id: string;
  val1: number;
  val2: number;
  created_at: string;
}

export interface PairCreate {
  val1: number;
  val2: number;
}

export interface AgentStepOutput {
  agent_name: string;
  output: Record<string, unknown>;
  duration_ms: number;
}

export interface OperationLog {
  log_id: string;
  pair_id: string;
  operation: string;
  agent_steps: AgentStepOutput[];
  result: string;
  success: boolean;
  created_at: string;
}

export interface OperateRequest {
  operation: string;
}
