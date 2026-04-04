// Type definitions for GUI components

export interface HealthStatus {
  status: string;
  sp_cli_available: boolean;
}

export interface Project {
  name: string;
  path: string;
  description?: string;
}

export interface Pipeline {
  name: string;
  path: string;
  full_path: string;
  file?: string;
  description?: string;
}

export interface ContentConfig {
  project_path: string;
  stages: Stage[];
  success?: boolean;
  error?: string;
}

export interface Stage {
  name: string;
  directory: string;
  format: string;
  immutable?: boolean;
  protected?: boolean;
  file_permissions?: string;
}

export interface ContentFile {
  name: string;
  path: string;
  stage: string;
  status?: string;
  size?: number;
  modified?: string;
  metadata?: Record<string, unknown>;
}

export interface GitStatus {
  branch: string;
  files: GitFile[];
  ahead?: number;
  behind?: number;
  staged_count?: number;
  unstaged_count?: number;
}

export interface GitFile {
  path: string;
  status: string;
  staged?: boolean;
}

export interface OutputLine {
  type: 'status' | 'heartbeat' | 'stdout' | 'stderr' | 'success' | 'error' | 'section_header' | 'file_link' | 'telemetry';
  text: string;
}

export interface PipelineConfig {
  vars?: Record<string, unknown>;
  variables?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface DiffLine {
  type: 'add' | 'remove' | 'context' | 'header';
  content: string;
  lineNumber?: number;
}

export interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  size?: number;
  modified?: string;
  children?: FileNode[];
  isExpanded?: boolean;
}
