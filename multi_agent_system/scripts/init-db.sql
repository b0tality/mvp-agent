-- ============================================================================
-- 多智能体应用开发系统 - 数据库初始化脚本
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 创建数据库（如果不存在）
-- ----------------------------------------------------------------------------
-- 注意：此脚本在 PostgreSQL 容器首次启动时自动执行

-- ----------------------------------------------------------------------------
-- 创建扩展
-- ----------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- 全文搜索

-- ----------------------------------------------------------------------------
-- 创建枚举类型
-- ----------------------------------------------------------------------------
DO $$ BEGIN
    CREATE TYPE agent_type AS ENUM (
        'requirements',
        'technical',
        'mvp',
        'code_review',
        'testing',
        'deployment'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE task_status AS ENUM (
        'pending',
        'in_progress',
        'completed',
        'failed',
        'cancelled'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE severity_level AS ENUM (
        'critical',
        'high',
        'medium',
        'low',
        'info'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ----------------------------------------------------------------------------
-- 创建表
-- ----------------------------------------------------------------------------

-- 项目表
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status task_status DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- 需求表
CREATE TABLE IF NOT EXISTS requirements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    user_input TEXT NOT NULL,
    functional_requirements JSONB DEFAULT '[]'::jsonb,
    non_functional_requirements JSONB DEFAULT '[]'::jsonb,
    user_stories JSONB DEFAULT '[]'::jsonb,
    acceptance_criteria JSONB DEFAULT '[]'::jsonb,
    priority_matrix JSONB DEFAULT '{}'::jsonb,
    status task_status DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 技术方案表
CREATE TABLE IF NOT EXISTS technical_solutions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    requirement_id UUID REFERENCES requirements(id) ON DELETE CASCADE,
    system_architecture JSONB DEFAULT '{}'::jsonb,
    tech_stack JSONB DEFAULT '{}'::jsonb,
    api_design JSONB DEFAULT '{}'::jsonb,
    database_design JSONB DEFAULT '{}'::jsonb,
    security_design JSONB DEFAULT '{}'::jsonb,
    cost_estimation JSONB DEFAULT '{}'::jsonb,
    status task_status DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 代码文件表
CREATE TABLE IF NOT EXISTS code_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    technical_solution_id UUID REFERENCES technical_solutions(id) ON DELETE CASCADE,
    file_path VARCHAR(500) NOT NULL,
    file_content TEXT,
    language VARCHAR(50),
    description TEXT,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 代码审查表
CREATE TABLE IF NOT EXISTS code_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    overall_score DECIMAL(5,2),
    code_quality_score DECIMAL(5,2),
    security_score DECIMAL(5,2),
    performance_score DECIMAL(5,2),
    total_issues INTEGER DEFAULT 0,
    critical_issues INTEGER DEFAULT 0,
    high_issues INTEGER DEFAULT 0,
    medium_issues INTEGER DEFAULT 0,
    low_issues INTEGER DEFAULT 0,
    approved BOOLEAN DEFAULT false,
    review_notes TEXT,
    issues JSONB DEFAULT '[]'::jsonb,
    refactoring_suggestions JSONB DEFAULT '[]'::jsonb,
    status task_status DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 测试结果表
CREATE TABLE IF NOT EXISTS test_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    total_tests INTEGER DEFAULT 0,
    passed_tests INTEGER DEFAULT 0,
    failed_tests INTEGER DEFAULT 0,
    skipped_tests INTEGER DEFAULT 0,
    line_coverage DECIMAL(5,2),
    branch_coverage DECIMAL(5,2),
    function_coverage DECIMAL(5,2),
    overall_coverage DECIMAL(5,2),
    bugs JSONB DEFAULT '[]'::jsonb,
    test_report JSONB DEFAULT '{}'::jsonb,
    status task_status DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 部署配置表
CREATE TABLE IF NOT EXISTS deployments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    deployment_plan JSONB DEFAULT '{}'::jsonb,
    docker_config JSONB DEFAULT '{}'::jsonb,
    kubernetes_config JSONB DEFAULT '{}'::jsonb,
    cicd_config JSONB DEFAULT '{}'::jsonb,
    monitoring_config JSONB DEFAULT '{}'::jsonb,
    deployment_docs TEXT,
    runbook TEXT,
    status task_status DEFAULT 'pending',
    deployed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 任务表
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    agent_type agent_type NOT NULL,
    task_name VARCHAR(255) NOT NULL,
    description TEXT,
    status task_status DEFAULT 'pending',
    input_data JSONB DEFAULT '{}'::jsonb,
    output_data JSONB DEFAULT '{}'::jsonb,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 消息日志表
CREATE TABLE IF NOT EXISTS message_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    from_agent agent_type,
    to_agent agent_type,
    message_type VARCHAR(50),
    content JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 错误日志表
CREATE TABLE IF NOT EXISTS error_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    agent_type agent_type,
    error_type VARCHAR(100),
    error_message TEXT,
    stack_trace TEXT,
    severity severity_level DEFAULT 'medium',
    resolved BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 创建索引
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_requirements_project_id ON requirements(project_id);
CREATE INDEX IF NOT EXISTS idx_technical_solutions_project_id ON technical_solutions(project_id);
CREATE INDEX IF NOT EXISTS idx_code_files_project_id ON code_files(project_id);
CREATE INDEX IF NOT EXISTS idx_code_reviews_project_id ON code_reviews(project_id);
CREATE INDEX IF NOT EXISTS idx_test_results_project_id ON test_results(project_id);
CREATE INDEX IF NOT EXISTS idx_deployments_project_id ON deployments(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_agent_type ON tasks(agent_type);
CREATE INDEX IF NOT EXISTS idx_message_logs_project_id ON message_logs(project_id);
CREATE INDEX IF NOT EXISTS idx_error_logs_project_id ON error_logs(project_id);
CREATE INDEX IF NOT EXISTS idx_error_logs_severity ON error_logs(severity);

-- ----------------------------------------------------------------------------
-- 创建更新时间触发器
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为所有表添加更新时间触发器
DO $$ 
DECLARE 
    t text;
BEGIN
    FOR t IN 
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
    LOOP
        EXECUTE format(
            'CREATE TRIGGER update_%s_updated_at BEFORE UPDATE ON %s FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()',
            t, t
        );
    END LOOP;
END;
$$;

-- ----------------------------------------------------------------------------
-- 插入初始数据
-- ----------------------------------------------------------------------------
INSERT INTO projects (id, name, description, status) 
VALUES (
    '00000000-0000-0000-0000-000000000001',
    '示例项目',
    '这是一个示例项目，用于演示系统功能',
    'pending'
) ON CONFLICT (id) DO NOTHING;

-- ----------------------------------------------------------------------------
-- 创建视图
-- ----------------------------------------------------------------------------

-- 项目概览视图
CREATE OR REPLACE VIEW project_overview AS
SELECT 
    p.id,
    p.name,
    p.status as project_status,
    p.created_at,
    r.status as requirements_status,
    ts.status as technical_status,
    cr.approved as code_review_approved,
    cr.overall_score as code_review_score,
    tr.passed_tests,
    tr.total_tests,
    tr.overall_coverage,
    d.status as deployment_status
FROM projects p
LEFT JOIN requirements r ON p.id = r.project_id
LEFT JOIN technical_solutions ts ON p.id = ts.project_id
LEFT JOIN code_reviews cr ON p.id = cr.project_id
LEFT JOIN test_results tr ON p.id = tr.project_id
LEFT JOIN deployments d ON p.id = d.project_id;

-- 任务统计视图
CREATE OR REPLACE VIEW task_statistics AS
SELECT 
    project_id,
    agent_type,
    COUNT(*) as total_tasks,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_tasks,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_tasks,
    COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress_tasks,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_execution_time
FROM tasks
GROUP BY project_id, agent_type;

-- 完成！
