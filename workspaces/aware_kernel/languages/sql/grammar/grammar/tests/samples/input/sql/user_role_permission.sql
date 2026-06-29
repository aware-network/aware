CREATE TABLE public.permission (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

COMMENT ON TABLE public.permission IS 'System permissions';

CREATE TABLE public.role_permission (
    role_id UUID NOT NULL REFERENCES public.role(id),
    permission_id UUID NOT NULL REFERENCES public.permission(id)
);

COMMENT ON TABLE public.role_permission IS 'Mapping between roles and permissions';
COMMENT ON COLUMN public.role_permission.role_id IS 'reverse';
COMMENT ON COLUMN public.role_permission.permission_id IS 'forward';

CREATE TABLE public.user_role_permission_audit (
    id UUID PRIMARY KEY,
    user_role_id UUID NOT NULL REFERENCES public.user_role(user_id, role_id),
    permission_id UUID NOT NULL REFERENCES public.permission(id),
    action TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.user_role_permission_audit IS 'Audit log for user role permission changes';
COMMENT ON COLUMN public.user_role_permission_audit.user_role_id IS 'reverse';
COMMENT ON COLUMN public.user_role_permission_audit.permission_id IS 'forward';
