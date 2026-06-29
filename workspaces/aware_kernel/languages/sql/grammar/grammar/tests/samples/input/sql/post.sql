CREATE TABLE public.post (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    user_id UUID NOT NULL REFERENCES public.user(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE public.post IS 'User posts';
COMMENT ON COLUMN public.post.user_id IS 'forward:lazy; reverse:eager';
