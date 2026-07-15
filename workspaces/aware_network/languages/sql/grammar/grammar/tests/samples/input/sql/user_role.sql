CREATE TABLE public.role (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE public.user_role (
    user_id UUID NOT NULL REFERENCES public.user(id),
    role_id UUID NOT NULL REFERENCES public.role(id),
    assigned_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (user_id, role_id)
);

COMMENT ON COLUMN public.user_role.user_id IS 'forward:lazy; reverse:eager';
COMMENT ON COLUMN public.user_role.role_id IS 'forward; reverse:lazy';
